from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any

from .memcg005gc_controlled_spawn import (
    _stop,
    _wait_cpu,
    environment_receipt,
    geometry_receipt,
)
from .premeasure_q64_callpath import _normalize_stack
from .small_residual_refill1_capture import (
    Q64_EVENT,
    REFILL_EVENT,
    _profile_zero_miss,
    _set_event,
)
from .startup_stock_seed_cpuset_falsifier import (
    _cpuset_effective,
    _expand_cpuset,
    _start_cpuset_constrained,
)
from .startup_stock_seed_phase import (
    _delta_counts,
    _profile_counts,
)
from .transaction_trace_observer import _event_row
from .transactional_spawn_native import (
    observed_window,
    touch_with_transaction_marker,
    write_marker,
)


STARTUP_TOUCH = 91
RELEASE_TOUCH = 92


def load_spec(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _probe_dir(trace_path: Path, event: str) -> Path:
    return trace_path.parent / "events" / "kprobes" / event


def _remove_stacktrace(trace_path: Path, event: str) -> None:
    try:
        (_probe_dir(trace_path, event) / "trigger").write_text(
            "!stacktrace\n",
            encoding="utf-8",
        )
    except OSError:
        pass


def close_probes(trace_path: Path) -> None:
    for event in (Q64_EVENT, REFILL_EVENT):
        try:
            _set_event(
                trace_path,
                event,
                enabled=False,
            )
        except OSError:
            pass
        _remove_stacktrace(trace_path, event)


def _window_lines(
    text: str,
    *,
    trial_id: str,
    phase: str,
    touch_number: int,
) -> list[str]:
    pre = (
        f"FRL_TX trial={trial_id} epoch=0 phase={phase} "
        f"touch={touch_number} PRE"
    )
    post = (
        f"FRL_TX trial={trial_id} epoch=0 phase={phase} "
        f"touch={touch_number} POST"
    )
    lines = text.splitlines()
    start = next(
        (i for i, line in enumerate(lines) if pre in line),
        None,
    )
    if start is None:
        return []
    end = next(
        (
            i
            for i, line in enumerate(lines[start + 1 :], start + 1)
            if post in line
        ),
        None,
    )
    if end is None:
        return []
    return lines[start : end + 1]


def parse_refill1_stacks(
    lines: list[str],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    active: dict[str, Any] | None = None

    for line in lines:
        if f"{REFILL_EVENT}:" in line:
            row = _event_row(line)
            active = {
                **row,
                "stack": [],
                "frames": [],
            }
            out.append(active)
            continue

        if active is not None:
            if "=>" in line:
                active["stack"].append(line.strip())
                continue
            if "FRL_TX " in line:
                active = None

    for item in out:
        item["frames"] = _normalize_stack(
            list(item.get("stack", []))
        )

    return out


def provenance_class(frames: list[str]) -> str:
    if "obj_cgroup_uncharge_pages" in frames:
        return "OBJCG_UNCHARGE_REFILL1"
    if "mem_cgroup_sk_uncharge" in frames:
        return "SOCKET_UNCHARGE_REFILL1"
    if "try_charge_memcg" in frames:
        return "TRY_CHARGE_EXCESS_REFILL1"
    return "OTHER_REFILL1_CALLER"


def classify_identity(
    *,
    first_q64_touch: int,
    owner_refill1_rows: list[dict[str, Any]],
) -> tuple[str, str | None]:
    s0 = int(first_q64_touch) - 1

    if s0 == 0:
        if owner_refill1_rows:
            return "T1_WITH_OWNER_REFILL1", None
        return "T1_NO_OWNER_REFILL1", None

    if not owner_refill1_rows:
        return "DELAY_WITHOUT_OWNER_REFILL1", None

    refill_sum = sum(
        int(row.get("nr_pages", 0))
        for row in owner_refill1_rows
    )
    if refill_sum != s0:
        return "OWNER_REFILL1_RESIDUAL_MISMATCH", None

    if not all(row.get("frames") for row in owner_refill1_rows):
        return "OWNER_REFILL1_STACK_MISSING", None

    classes = {
        provenance_class(
            list(row.get("frames", []))
        )
        for row in owner_refill1_rows
    }
    if len(classes) != 1:
        return "MULTIPLE_REFILL1_PROVENANCE_CLASSES", None

    return "PROVENANCE_CAPTURED", next(iter(classes))


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
    design = spec["design"]
    trial_id = f"{block}:{identity}"
    root = out_root / f"trial-{block}-{identity}"
    root.mkdir(parents=True, exist_ok=True)
    name = (
        f"fr-prov-{os.getenv('GITHUB_RUN_ID', 'local')}-"
        f"{block}-{identity}"
    )

    unit = None
    try:
        close_probes(trace_path)

        before_startup_refill = _profile_counts(
            trace_path,
            REFILL_EVENT,
        )
        _set_event(
            trace_path,
            REFILL_EVENT,
            enabled=False,
            filter_text=(
                "nr_pages == 1 && common_pid == 1"
            ),
        )
        (_probe_dir(trace_path, REFILL_EVENT) / "trigger").write_text(
            "stacktrace\n",
            encoding="utf-8",
        )
        _set_event(
            trace_path,
            REFILL_EVENT,
            enabled=True,
        )

        write_marker(
            trace_marker,
            trial_id=trial_id,
            epoch=0,
            phase="OBSERVE",
            touch_number=STARTUP_TOUCH,
            edge="PRE",
        )
        unit = _start_cpuset_constrained(
            worker=worker,
            root=root,
            name=name,
            prep_cpu=prep_cpu,
            max_pages=int(design["max_pages"]),
            safe_len=int(design["safe_len_pages"]),
            worker_uid=worker_uid,
        )
        write_marker(
            trace_marker,
            trial_id=trial_id,
            epoch=0,
            phase="OBSERVE",
            touch_number=STARTUP_TOUCH,
            edge="POST",
        )

        _set_event(
            trace_path,
            REFILL_EVENT,
            enabled=False,
        )
        _remove_stacktrace(
            trace_path,
            REFILL_EVENT,
        )
        after_startup_refill = _profile_counts(
            trace_path,
            REFILL_EVENT,
        )
        startup_refill_profile = _delta_counts(
            before_startup_refill,
            after_startup_refill,
        )

        target_pid = int(unit["pid"])
        startup_effective = _cpuset_effective(unit["cg"])

        startup_text = trace_path.read_text(
            encoding="utf-8",
            errors="replace",
        )
        startup_lines = _window_lines(
            startup_text,
            trial_id=trial_id,
            phase="OBSERVE",
            touch_number=STARTUP_TOUCH,
        )
        startup_refill1_rows = parse_refill1_stacks(
            startup_lines
        )

        write_marker(
            trace_marker,
            trial_id=trial_id,
            epoch=0,
            phase="OBSERVE",
            touch_number=RELEASE_TOUCH,
            edge="PRE",
        )
        release_effective = _expand_cpuset(
            unit,
            prep_cpu=prep_cpu,
            stock_cpu=stock_cpu,
        )
        os.sched_setaffinity(target_pid, {stock_cpu})
        _wait_cpu(target_pid, stock_cpu)
        write_marker(
            trace_marker,
            trial_id=trial_id,
            epoch=0,
            phase="OBSERVE",
            touch_number=RELEASE_TOUCH,
            edge="POST",
        )

        geometry = geometry_receipt(unit, prep_cpu)
        geometry_valid = (
            bool(geometry["guard_cpu_match"])
            and bool(geometry["same_pte_table"])
        )

        page_size = int(geometry["page_size"])
        sequence = list(
            range(
                int(geometry["safe_start"]) + 1,
                int(geometry["safe_start"])
                + int(geometry["safe_len"]),
            )
        )

        first_q64_touch: int | None = None
        owner_counter: str | None = None
        owner_memcg: str | None = None
        invalidation_reason: str | None = None
        touches: list[dict[str, Any]] = []
        measured_probe_windows: list[dict[str, Any]] = []

        if geometry_valid:
            for touch_number in range(
                1,
                int(design["primary_bound_touch"]) + 1,
            ):
                before_q64 = _profile_counts(
                    trace_path,
                    Q64_EVENT,
                )
                before_refill63 = _profile_counts(
                    trace_path,
                    REFILL_EVENT,
                )

                _set_event(
                    trace_path,
                    Q64_EVENT,
                    enabled=True,
                    filter_text=(
                        "nr_pages == 64 && "
                        f"common_pid == {target_pid}"
                    ),
                )
                _set_event(
                    trace_path,
                    REFILL_EVENT,
                    enabled=True,
                    filter_text=(
                        "nr_pages == 63 && "
                        f"common_pid == {target_pid}"
                    ),
                )

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

                _set_event(
                    trace_path,
                    Q64_EVENT,
                    enabled=False,
                )
                _set_event(
                    trace_path,
                    REFILL_EVENT,
                    enabled=False,
                )

                after_q64 = _profile_counts(
                    trace_path,
                    Q64_EVENT,
                )
                after_refill63 = _profile_counts(
                    trace_path,
                    REFILL_EVENT,
                )
                q64_profile = _delta_counts(
                    before_q64,
                    after_q64,
                )
                refill63_profile = _delta_counts(
                    before_refill63,
                    after_refill63,
                )
                measured_probe_windows.append(
                    {
                        "touch": touch_number,
                        "q64_profile": q64_profile,
                        "refill63_profile": refill63_profile,
                    }
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
                q64_rows = [
                    event
                    for event in window.get("pc_try64", [])
                    if (
                        int(event.get("pid", -1))
                        == target_pid
                        and int(event.get("cpu", -1))
                        == stock_cpu
                    )
                ]
                refill63_rows = [
                    event
                    for event in window.get("refill63", [])
                    if (
                        int(event.get("pid", -1))
                        == target_pid
                        and int(event.get("cpu", -1))
                        == stock_cpu
                    )
                ]

                complete = (
                    int(window.get("pre_count", 0)) == 1
                    and int(window.get("post_count", 0)) == 1
                    and int(
                        window.get("marker_error_count", 0)
                    )
                    == 0
                )
                touches.append(
                    {
                        **row,
                        "touch_number": touch_number,
                        "trace_complete": complete,
                        "target_q64_count": len(q64_rows),
                        "target_refill63_count": len(
                            refill63_rows
                        ),
                    }
                )

                if not complete:
                    invalidation_reason = "TRACE_GAP"
                    break
                if not _profile_zero_miss(q64_profile):
                    invalidation_reason = "Q64_PROBE_MISS"
                    break
                if not _profile_zero_miss(refill63_profile):
                    invalidation_reason = "REFILL63_PROBE_MISS"
                    break
                if int(row.get("worker_error", 0)) != 0:
                    invalidation_reason = "WORKER_ERROR"
                    break
                if int(row.get("worker_touched", -1)) != touch_number:
                    invalidation_reason = (
                        "WORKER_TOUCH_SEQUENCE_MISMATCH"
                    )
                    break
                if int(row.get("observed_cpu", -1)) != stock_cpu:
                    invalidation_reason = "CPU_MISMATCH"
                    break
                if int(row.get("vmpte_delta_kib", 0)) != 0:
                    invalidation_reason = "PTE_GROWTH"
                    break
                if len(q64_rows) > 1:
                    invalidation_reason = (
                        "MULTIPLE_TARGET_Q64_IN_TOUCH"
                    )
                    break

                if len(q64_rows) == 1:
                    if len(refill63_rows) != 1:
                        invalidation_reason = (
                            "BOUNDARY_REFILL63_AMBIGUOUS"
                        )
                        break
                    first_q64_touch = touch_number
                    counter = q64_rows[0].get("counter")
                    memcg = refill63_rows[0].get("memcg")
                    if counter:
                        owner_counter = str(counter).lower()
                    if memcg:
                        owner_memcg = str(memcg).lower()
                    break
        else:
            invalidation_reason = "GEOMETRY_INVALID"

        owner_refill1_rows: list[dict[str, Any]] = []
        if owner_memcg is not None:
            owner_refill1_rows = [
                event
                for event in startup_refill1_rows
                if (
                    str(event.get("memcg", "")).lower()
                    == owner_memcg
                    and int(event.get("cpu", -1))
                    == stock_cpu
                    and int(event.get("pid", -1)) == 1
                    and int(event.get("nr_pages", -1)) == 1
                )
            ]

        cgroup_procs = sorted(
            int(x)
            for x in (unit["cg"] / "cgroup.procs")
            .read_text(encoding="utf-8")
            .split()
        )
        single_process = cgroup_procs == [target_pid]
        cpuset_ok = (
            startup_effective == {prep_cpu}
            and {prep_cpu, stock_cpu}.issubset(
                release_effective
            )
        )
        startup_coverage_ok = _profile_zero_miss(
            startup_refill_profile
        )
        measured_coverage_ok = all(
            _profile_zero_miss(item["q64_profile"])
            and _profile_zero_miss(
                item["refill63_profile"]
            )
            for item in measured_probe_windows
        )
        owner_ok = (
            first_q64_touch is not None
            and owner_counter is not None
            and owner_memcg is not None
        )
        base_valid = (
            invalidation_reason is None
            and startup_coverage_ok
            and measured_coverage_ok
            and cpuset_ok
            and single_process
            and owner_ok
        )

        if not base_valid:
            classification = "INVALID_OBSERVER"
            provenance = None
        else:
            classification, provenance = classify_identity(
                first_q64_touch=int(first_q64_touch),
                owner_refill1_rows=owner_refill1_rows,
            )

        return {
            "experiment_id": spec["experiment_id"],
            "trial_id": trial_id,
            "block": block,
            "identity": identity,
            "pid": target_pid,
            "prep_cpu": prep_cpu,
            "stock_cpu": stock_cpu,
            "startup_cpuset_effective": sorted(
                startup_effective
            ),
            "release_cpuset_effective": sorted(
                release_effective
            ),
            "cgroup_procs": cgroup_procs,
            "single_process": single_process,
            "geometry": geometry,
            "startup_refill_profile": startup_refill_profile,
            "startup_coverage_ok": startup_coverage_ok,
            "measured_probe_windows": measured_probe_windows,
            "measured_coverage_ok": measured_coverage_ok,
            "startup_refill1_rows": startup_refill1_rows,
            "owner_refill1_rows": owner_refill1_rows,
            "owner_refill1_count": len(owner_refill1_rows),
            "owner_refill1_sum": sum(
                int(row.get("nr_pages", 0))
                for row in owner_refill1_rows
            ),
            "first_q64_touch": first_q64_touch,
            "initial_residual_estimate": (
                None
                if first_q64_touch is None
                else first_q64_touch - 1
            ),
            "owner_counter": owner_counter,
            "owner_memcg": owner_memcg,
            "touches": touches,
            "invalidation_reason": invalidation_reason,
            "valid": base_valid,
            "classification": classification,
            "provenance_class": provenance,
        }
    finally:
        close_probes(trace_path)
        if unit is not None:
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
        raise RuntimeError(
            "refill1 provenance requires >=3 CPUs"
        )
    controller_cpu, prep_cpu, stock_cpu = (
        cpus[0],
        cpus[1],
        cpus[-1],
    )
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
    for identity in range(
        int(spec["design"]["identities_per_block"])
    ):
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
        "valid_count": sum(bool(row["valid"]) for row in rows),
        "classifications": dict(
            Counter(row["classification"] for row in rows)
        ),
        "provenance_classes": dict(
            Counter(
                row["provenance_class"]
                for row in rows
                if row.get("provenance_class") is not None
            )
        ),
        "captured_trials": [
            row["trial_id"]
            for row in rows
            if row["classification"] == "PROVENANCE_CAPTURED"
        ],
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
    captured = [
        row
        for row in trials
        if row.get("classification")
        == "PROVENANCE_CAPTURED"
    ]
    resolved = [
        row
        for row in captured
        if row.get("provenance_class")
        in {
            "OBJCG_UNCHARGE_REFILL1",
            "SOCKET_UNCHARGE_REFILL1",
            "TRY_CHARGE_EXCESS_REFILL1",
        }
    ]

    return {
        "experiment_id": spec["experiment_id"],
        "trial_count": len(trials),
        "valid_trial_count": sum(
            bool(row.get("valid")) for row in trials
        ),
        "classifications": dict(
            Counter(
                row.get("classification", "MISSING")
                for row in trials
            )
        ),
        "provenance_classes": dict(
            Counter(
                row.get("provenance_class")
                for row in captured
            )
        ),
        "first_q64_histogram": dict(
            Counter(
                int(row["first_q64_touch"])
                for row in trials
                if (
                    row.get("valid")
                    and row.get("first_q64_touch")
                    is not None
                )
            )
        ),
        "captured_count": len(captured),
        "captured_trials": [
            row["trial_id"] for row in captured
        ],
        "resolved_count": len(resolved),
        "resolved_trials": [
            row["trial_id"] for row in resolved
        ],
        "provenance_resolved": len(resolved) >= 1,
        "startup_probe_miss_trials": [
            row["trial_id"]
            for row in trials
            if not row.get("startup_coverage_ok", False)
        ],
        "measured_probe_miss_trials": [
            row["trial_id"]
            for row in trials
            if not row.get("measured_coverage_ok", False)
        ],
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
                "provenance_resolved": result[
                    "provenance_resolved"
                ],
                "trial_count": result["trial_count"],
                "valid_trial_count": result[
                    "valid_trial_count"
                ],
                "captured_count": result[
                    "captured_count"
                ],
                "captured_trials": result[
                    "captured_trials"
                ],
                "resolved_count": result[
                    "resolved_count"
                ],
                "resolved_trials": result[
                    "resolved_trials"
                ],
                "provenance_classes": result[
                    "provenance_classes"
                ],
                "classifications": result[
                    "classifications"
                ],
                "first_q64_histogram": result[
                    "first_q64_histogram"
                ],
                "startup_probe_miss_trials": result[
                    "startup_probe_miss_trials"
                ],
                "measured_probe_miss_trials": result[
                    "measured_probe_miss_trials"
                ],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
