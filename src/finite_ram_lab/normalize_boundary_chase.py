from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any

from .memcg005gc_controlled_spawn import (
    _start,
    _stop,
    _vmpte_kib,
    _wait_cpu,
    environment_receipt,
    geometry_receipt,
)
from .transaction_trace_observer import _event_row
from .transactional_spawn_native import (
    observed_window,
    touch_with_transaction_marker,
)


PRIMARY_BOUND_TOUCH = 65
DIAGNOSTIC_MAX_TOUCH = 80


def load_spec(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _target_q64_rows(
    window: dict[str, Any],
    *,
    target_pid: int,
) -> list[dict[str, Any]]:
    return [
        row
        for row in window.get("pc_try64", [])
        if int(row.get("pid", -1)) == int(target_pid)
    ]


def _target_q64_rows_from_text(
    text: str,
    *,
    target_pid: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in text.splitlines():
        if "frl_pc_try64:" not in line:
            continue
        row = _event_row(line)
        if (
            int(row.get("pid", -1)) == int(target_pid)
            and int(row.get("nr_pages", 0)) == 64
        ):
            rows.append(row)
    return rows


def classify_boundary(
    *,
    first_q64_touch: int | None,
    invalidation_reason: str | None,
    primary_bound_touch: int = PRIMARY_BOUND_TOUCH,
    diagnostic_max_touch: int = DIAGNOSTIC_MAX_TOUCH,
) -> str:
    if invalidation_reason is not None:
        return invalidation_reason
    if first_q64_touch is None:
        return "BOUNDARY_NOT_FOUND"
    if first_q64_touch < primary_bound_touch:
        return "WITHIN_BOUND"
    if first_q64_touch == primary_bound_touch:
        return "MAX_STOCK_BOUNDARY"
    if first_q64_touch <= diagnostic_max_touch:
        return "STOCK_BOUND_VIOLATION_CANDIDATE"
    return "BOUNDARY_NOT_FOUND"


def _profile_q64_missed(path: Path) -> int | None:
    if not path.exists():
        return None
    for raw in path.read_text(
        encoding="utf-8",
        errors="replace",
    ).splitlines():
        parts = raw.split()
        if len(parts) != 3 or parts[0] != "frl_pc_try64":
            continue
        try:
            return int(parts[2])
        except ValueError:
            return None
    return None


def run_identity(
    *,
    spec: dict[str, Any],
    worker: Path,
    out_root: Path,
    trace_marker: Path,
    trace_path: Path,
    block: int,
    identity: int,
    prep_cpu: int,
    stock_cpu: int,
    worker_uid: int,
) -> dict[str, Any]:
    trial_id = f"{block}:{identity}"
    root = out_root / f"trial-{block}-{identity}"
    root.mkdir(parents=True, exist_ok=True)
    name = (
        f"fr-norm-{os.getenv('GITHUB_RUN_ID', 'local')}-"
        f"{block}-{identity}"
    )

    unit = _start(
        worker,
        root,
        name,
        prep_cpu,
        int(spec["max_pages"]),
        int(spec["safe_len_pages"]),
        worker_uid=worker_uid,
    )

    try:
        geometry = geometry_receipt(unit, prep_cpu)
        if not geometry["guard_cpu_match"] or not geometry["same_pte_table"]:
            return {
                "experiment_id": spec["experiment_id"],
                "block": block,
                "identity": identity,
                "trial_id": trial_id,
                "status": "GEOMETRY_INVALID",
                "geometry": geometry,
            }

        page_size = int(geometry["page_size"])
        sequence = list(
            range(
                int(geometry["safe_start"]) + 1,
                int(geometry["safe_start"])
                + int(geometry["safe_len"]),
            )
        )
        hard_max = int(spec["diagnostic_max_touch"])
        if len(sequence) < hard_max:
            raise RuntimeError("safe span shorter than diagnostic horizon")

        # The workflow clears trace before each block. Snapshot here marks the
        # beginning of this identity's stock-CPU observation interval.
        os.sched_setaffinity(unit["pid"], {stock_cpu})
        _wait_cpu(unit["pid"], stock_cpu)

        before_first_touch = trace_path.read_text(
            encoding="utf-8",
            errors="replace",
        )
        premeasurement_q64 = _target_q64_rows_from_text(
            before_first_touch,
            target_pid=unit["pid"],
        )

        touches: list[dict[str, Any]] = []
        first_q64_touch: int | None = None
        first_q64_rows: list[dict[str, Any]] = []
        invalidation_reason: str | None = None

        for touch_number in range(1, hard_max + 1):
            row = touch_with_transaction_marker(
                unit=unit,
                stock_cpu=stock_cpu,
                page_size=page_size,
                page_index=sequence[touch_number - 1],
                phase="NORMALIZE",
                touch_number=touch_number,
                trial_id=trial_id,
                epoch=0,
                trace_marker=trace_marker,
            )
            trace_text = trace_path.read_text(
                encoding="utf-8",
                errors="replace",
            )
            window = observed_window(
                trace_text=trace_text,
                trial_id=trial_id,
                epoch=0,
                phase="NORMALIZE",
                touch_number=touch_number,
            )
            q64_rows = _target_q64_rows(
                window,
                target_pid=unit["pid"],
            )

            row_out = {
                **row,
                "touch_number": touch_number,
                "trace_complete": (
                    int(window.get("pre_count", 0)) == 1
                    and int(window.get("post_count", 0)) == 1
                    and int(window.get("marker_error_count", 0)) == 0
                ),
                "target_q64_count": len(q64_rows),
                "target_q64_rows": q64_rows,
            }
            touches.append(row_out)

            if not row_out["trace_complete"]:
                invalidation_reason = "TRACE_GAP"
                break
            if int(row_out.get("worker_error", 0)) != 0:
                invalidation_reason = "WORKER_ERROR"
                break
            if int(row_out.get("observed_cpu", -1)) != int(stock_cpu):
                invalidation_reason = "CPU_MISMATCH"
                break
            if int(row_out.get("vmpte_delta_kib", 0)) != 0:
                invalidation_reason = "PTE_GROWTH"
                break
            if len(q64_rows) > 1:
                invalidation_reason = "MULTIPLE_TARGET_Q64_IN_TOUCH"
                break
            if len(q64_rows) == 1:
                first_q64_touch = touch_number
                first_q64_rows = q64_rows
                break

        classification = classify_boundary(
            first_q64_touch=first_q64_touch,
            invalidation_reason=invalidation_reason,
            primary_bound_touch=int(spec["primary_bound_touch"]),
            diagnostic_max_touch=hard_max,
        )

        cgroup_procs = sorted(
            int(x)
            for x in (unit["cg"] / "cgroup.procs")
            .read_text(encoding="utf-8")
            .split()
        )
        initial_residual_estimate = (
            first_q64_touch - 1
            if (
                first_q64_touch is not None
                and classification
                in {"WITHIN_BOUND", "MAX_STOCK_BOUNDARY"}
            )
            else None
        )

        return {
            "experiment_id": spec["experiment_id"],
            "block": block,
            "identity": identity,
            "trial_id": trial_id,
            "pid": int(unit["pid"]),
            "prep_cpu": prep_cpu,
            "stock_cpu": stock_cpu,
            "cgroup_procs": cgroup_procs,
            "geometry": geometry,
            "vmpte_after_geometry_kib": _vmpte_kib(unit["pid"]),
            "premeasurement_q64_count": len(premeasurement_q64),
            "premeasurement_q64": premeasurement_q64,
            "touches": touches,
            "first_q64_touch": first_q64_touch,
            "first_q64_rows": first_q64_rows,
            "initial_residual_estimate": initial_residual_estimate,
            "classification": classification,
            "invalidation_reason": invalidation_reason,
            "primary_bound_touch": int(spec["primary_bound_touch"]),
            "diagnostic_max_touch": hard_max,
        }
    finally:
        _stop(unit)


def run_block(
    *,
    spec: dict[str, Any],
    worker: Path,
    out_root: Path,
    trace_marker: Path,
    trace_path: Path,
    block: int,
    worker_uid: int,
) -> dict[str, Any]:
    cpus = sorted(os.sched_getaffinity(0))
    if len(cpus) < 3:
        raise RuntimeError("normalize boundary chase requires >=3 CPUs")
    controller_cpu, prep_cpu, stock_cpu = cpus[0], cpus[1], cpus[-1]
    os.sched_setaffinity(0, {controller_cpu})

    out_root.mkdir(parents=True, exist_ok=True)
    (out_root / "environment.json").write_text(
        json.dumps(
            environment_receipt(worker, cpus),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    rows: list[dict[str, Any]] = []
    per_block = int(spec["identities_per_block"])
    for identity in range(per_block):
        row = run_identity(
            spec=spec,
            worker=worker,
            out_root=out_root,
            trace_marker=trace_marker,
            trace_path=trace_path,
            block=block,
            identity=identity,
            prep_cpu=prep_cpu,
            stock_cpu=stock_cpu,
            worker_uid=worker_uid,
        )
        (out_root / f"trial-{block}-{identity}.json").write_text(
            json.dumps(row, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        rows.append(row)

    return {
        "experiment_id": spec["experiment_id"],
        "block": block,
        "trial_count": len(rows),
        "classifications": dict(
            Counter(row["classification"] for row in rows)
        ),
        "first_q64_touches": [
            row["first_q64_touch"]
            for row in rows
            if row.get("first_q64_touch") is not None
        ],
    }


def aggregate(
    spec: dict[str, Any],
    input_root: Path,
) -> dict[str, Any]:
    trials = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(input_root.rglob("trial-*.json"))
    ]
    classifications = Counter(
        trial.get("classification", "MISSING")
        for trial in trials
    )
    t_values = [
        int(trial["first_q64_touch"])
        for trial in trials
        if trial.get("first_q64_touch") is not None
    ]

    profile_paths = sorted(input_root.rglob("kprobe-profile.txt"))
    profile_missed = [
        _profile_q64_missed(path)
        for path in profile_paths
    ]
    coverage_pass = (
        len(profile_paths) > 0
        and all(value == 0 for value in profile_missed)
    )

    valid = [
        trial
        for trial in trials
        if trial.get("classification")
        in {
            "WITHIN_BOUND",
            "MAX_STOCK_BOUNDARY",
            "STOCK_BOUND_VIOLATION_CANDIDATE",
            "BOUNDARY_NOT_FOUND",
        }
    ]
    bound_violations = [
        trial
        for trial in valid
        if trial.get("classification")
        in {
            "STOCK_BOUND_VIOLATION_CANDIDATE",
            "BOUNDARY_NOT_FOUND",
        }
    ]

    return {
        "experiment_id": spec["experiment_id"],
        "trial_count": len(trials),
        "valid_trial_count": len(valid),
        "classifications": dict(classifications),
        "first_q64_histogram": dict(Counter(t_values)),
        "max_observed_first_q64_touch": max(t_values) if t_values else None,
        "max_stock_boundary_observed": any(t == 65 for t in t_values),
        "bound_violation_count": len(bound_violations),
        "probe_profile_count": len(profile_paths),
        "q64_probe_missed_by_block": profile_missed,
        "coverage_pass": coverage_pass,
        "stock_bound_pass": (
            len(trials) == int(spec["total_identities"])
            and len(valid) == len(trials)
            and len(bound_violations) == 0
            and coverage_pass
        ),
        "trials": trials,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run-block")
    run.add_argument("--spec", required=True)
    run.add_argument("--block", type=int, required=True)
    run.add_argument("--worker", required=True)
    run.add_argument("--out-root", required=True)
    run.add_argument("--trace-marker", required=True)
    run.add_argument("--trace-path", required=True)
    run.add_argument("--worker-uid", type=int, required=True)

    agg = sub.add_parser("aggregate")
    agg.add_argument("--spec", required=True)
    agg.add_argument("--input-root", required=True)
    agg.add_argument("--json-out", required=True)

    args = parser.parse_args()
    spec = load_spec(args.spec)

    if args.cmd == "run-block":
        result = run_block(
            spec=spec,
            worker=Path(args.worker).resolve(),
            out_root=Path(args.out_root),
            trace_marker=Path(args.trace_marker),
            trace_path=Path(args.trace_path),
            block=args.block,
            worker_uid=args.worker_uid,
        )
        print(json.dumps(result, sort_keys=True))
        return

    result = aggregate(spec, Path(args.input_root))
    out = Path(args.json_out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "stock_bound_pass": result["stock_bound_pass"],
                "coverage_pass": result["coverage_pass"],
                "trial_count": result["trial_count"],
                "valid_trial_count": result["valid_trial_count"],
                "max_stock_boundary_observed": result[
                    "max_stock_boundary_observed"
                ],
                "bound_violation_count": result["bound_violation_count"],
                "max_observed_first_q64_touch": result[
                    "max_observed_first_q64_touch"
                ],
                "classifications": result["classifications"],
                "first_q64_histogram": result["first_q64_histogram"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
