from __future__ import annotations

import argparse
import json
import os
import re
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .memcg005gc_controlled_spawn import (
    _start,
    _stop,
    _wait_cpu,
    environment_receipt,
    geometry_receipt,
)
from .transaction_trace_observer import _event_row
from .normalize_boundary_chase import _profile_q64_missed
from .transactional_spawn_native import (
    observed_window,
    touch_with_transaction_marker,
    write_marker,
)


PROBE_EVENT = "frl_pc_try64"
STACK_FRAME_RE = re.compile(r"=>\s*(?P<frame>[A-Za-z0-9_.$]+)")


def load_spec(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _probe_dir(trace_path: Path) -> Path:
    return trace_path.parent / "events" / "kprobes" / PROBE_EVENT


def _remove_stacktrace(probe: Path) -> None:
    try:
        (probe / "trigger").write_text("!stacktrace\n", encoding="utf-8")
    except OSError:
        pass


def bind_q64_probe_to_pid(trace_path: Path, pid: int) -> None:
    probe = _probe_dir(trace_path)
    (probe / "enable").write_text("0\n", encoding="utf-8")
    _remove_stacktrace(probe)
    (probe / "filter").write_text(
        f"nr_pages == 64 && common_pid == {int(pid)}\n",
        encoding="utf-8",
    )
    (probe / "trigger").write_text(
        f"stacktrace if common_pid == {int(pid)}\n",
        encoding="utf-8",
    )
    (probe / "enable").write_text("1\n", encoding="utf-8")


def close_q64_probe(trace_path: Path) -> None:
    probe = _probe_dir(trace_path)
    (probe / "enable").write_text("0\n", encoding="utf-8")
    _remove_stacktrace(probe)
    (probe / "filter").write_text(
        "nr_pages == 64 && common_pid == 0\n",
        encoding="utf-8",
    )


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


def _normalize_stack(stack: list[str]) -> list[str]:
    frames: list[str] = []
    for line in stack:
        m = STACK_FRAME_RE.search(line)
        if m:
            frames.append(m.group("frame"))
    return frames


def parse_q64_stacks(
    text: str,
    *,
    trial_id: str,
    phase: str,
    touch_number: int,
    target_pid: int,
    stock_cpu: int,
) -> list[dict[str, Any]]:
    lines = _window_lines(
        text,
        trial_id=trial_id,
        phase=phase,
        touch_number=touch_number,
    )
    out: list[dict[str, Any]] = []
    active: dict[str, Any] | None = None

    for line in lines:
        if "frl_pc_try64:" in line:
            row = _event_row(line)
            active = None
            if (
                int(row.get("pid", -1)) == int(target_pid)
                and int(row.get("cpu", -1)) == int(stock_cpu)
                and int(row.get("nr_pages", 0)) == 64
            ):
                active = {**row, "stack": [], "frames": []}
                out.append(active)
            continue

        if active is not None and "=>" in line:
            stripped = line.strip()
            active["stack"].append(stripped)

    for item in out:
        item["frames"] = _normalize_stack(item["stack"])

    return out


def _profile_q64_missed(path: Path) -> int | None:
    if not path.exists():
        return None
    for raw in path.read_text(
        encoding="utf-8",
        errors="replace",
    ).splitlines():
        parts = raw.split()
        if len(parts) != 3 or parts[0] != PROBE_EVENT:
            continue
        try:
            return int(parts[2])
        except ValueError:
            return None
    return None


def _fingerprint(frames: list[str], depth: int = 8) -> str:
    if not frames:
        return "NO_STACK"
    return " > ".join(frames[:depth])


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
    settle_ms = int(
        design["settle_arms_ms"][identity % len(design["settle_arms_ms"])]
    )
    root = out_root / f"trial-{block}-{identity}"
    root.mkdir(parents=True, exist_ok=True)
    name = (
        f"fr-call-{os.getenv('GITHUB_RUN_ID', 'local')}-"
        f"{block}-{identity}"
    )

    unit = _start(
        worker,
        root,
        name,
        prep_cpu,
        int(design["max_pages"]),
        int(design["safe_len_pages"]),
        worker_uid=worker_uid,
    )

    try:
        geometry = geometry_receipt(unit, prep_cpu)
        if not geometry["guard_cpu_match"] or not geometry["same_pte_table"]:
            return {
                "experiment_id": spec["experiment_id"],
                "trial_id": trial_id,
                "block": block,
                "identity": identity,
                "settle_ms": settle_ms,
                "classification": "GEOMETRY_INVALID",
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
        max_touch = int(design["primary_bound_touch"])

        bind_q64_probe_to_pid(trace_path, unit["pid"])

        write_marker(
            trace_marker,
            trial_id=trial_id,
            epoch=0,
            phase="OBSERVE",
            touch_number=90,
            edge="PRE",
        )
        os.sched_setaffinity(unit["pid"], {stock_cpu})
        _wait_cpu(unit["pid"], stock_cpu)
        if settle_ms:
            time.sleep(settle_ms / 1000.0)
        write_marker(
            trace_marker,
            trial_id=trial_id,
            epoch=0,
            phase="OBSERVE",
            touch_number=90,
            edge="POST",
        )

        trace_text = trace_path.read_text(
            encoding="utf-8",
            errors="replace",
        )
        pre_q64 = parse_q64_stacks(
            trace_text,
            trial_id=trial_id,
            phase="OBSERVE",
            touch_number=90,
            target_pid=unit["pid"],
            stock_cpu=stock_cpu,
        )

        touches: list[dict[str, Any]] = []
        first_q64_touch: int | None = None
        invalidation_reason: str | None = None

        for touch_number in range(1, max_touch + 1):
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
            q64_rows = [
                event
                for event in window.get("pc_try64", [])
                if (
                    int(event.get("pid", -1)) == int(unit["pid"])
                    and int(event.get("cpu", -1)) == int(stock_cpu)
                )
            ]
            complete = (
                int(window.get("pre_count", 0)) == 1
                and int(window.get("post_count", 0)) == 1
                and int(window.get("marker_error_count", 0)) == 0
            )
            row_out = {
                **row,
                "touch_number": touch_number,
                "trace_complete": complete,
                "target_q64_count": len(q64_rows),
            }
            touches.append(row_out)

            if not complete:
                invalidation_reason = "TRACE_GAP"
                break
            if int(row.get("worker_error", 0)) != 0:
                invalidation_reason = "WORKER_ERROR"
                break
            if int(row.get("worker_touched", -1)) != touch_number:
                invalidation_reason = "WORKER_TOUCH_SEQUENCE_MISMATCH"
                break
            if int(row.get("observed_cpu", -1)) != int(stock_cpu):
                invalidation_reason = "CPU_MISMATCH"
                break
            if int(row.get("vmpte_delta_kib", 0)) != 0:
                invalidation_reason = "PTE_GROWTH"
                break
            if len(q64_rows) > 1:
                invalidation_reason = "MULTIPLE_TARGET_Q64_IN_TOUCH"
                break
            if len(q64_rows) == 1:
                first_q64_touch = touch_number
                break

        cgroup_procs = sorted(
            int(x)
            for x in (unit["cg"] / "cgroup.procs")
            .read_text(encoding="utf-8")
            .split()
        )

        if invalidation_reason is not None:
            classification = invalidation_reason
        elif first_q64_touch is None:
            classification = "STOCK_BOUND_VIOLATION_CANDIDATE"
        elif first_q64_touch <= max_touch:
            classification = "WITHIN_BOUND"
        else:
            classification = "STOCK_BOUND_VIOLATION_CANDIDATE"

        stack_receipt_complete = all(
            len(event.get("frames", [])) > 0
            for event in pre_q64
        )
        return {
            "experiment_id": spec["experiment_id"],
            "trial_id": trial_id,
            "block": block,
            "identity": identity,
            "settle_ms": settle_ms,
            "pid": int(unit["pid"]),
            "prep_cpu": prep_cpu,
            "stock_cpu": stock_cpu,
            "cgroup_procs": cgroup_procs,
            "geometry": geometry,
            "premeasurement_q64_count": len(pre_q64),
            "premeasurement_q64": pre_q64,
            "premeasurement_stack_receipt_complete": (
                stack_receipt_complete
            ),
            "first_q64_touch": first_q64_touch,
            "initial_residual_estimate": (
                first_q64_touch - 1
                if first_q64_touch is not None
                else None
            ),
            "touches": touches,
            "classification": classification,
            "invalidation_reason": invalidation_reason,
        }
    finally:
        try:
            close_q64_probe(trace_path)
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
        raise RuntimeError("premeasurement callpath experiment requires >=3 CPUs")
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
    for identity in range(int(spec["design"]["identities_per_block"])):
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
        "premeasurement_q64_count": sum(
            int(row.get("premeasurement_q64_count", 0))
            for row in rows
        ),
        "settle_summary": {
            str(ms): {
                "n": sum(row["settle_ms"] == ms for row in rows),
                "pre_q64_events": sum(
                    int(row.get("premeasurement_q64_count", 0))
                    for row in rows
                    if row["settle_ms"] == ms
                ),
            }
            for ms in spec["design"]["settle_arms_ms"]
        },
    }


def aggregate(
    spec: dict[str, Any],
    input_root: Path,
) -> dict[str, Any]:
    trials = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(input_root.rglob("trial-*.json"))
    ]

    profiles = sorted(input_root.rglob("kprobe-profile.txt"))
    missed = [_profile_q64_missed(path) for path in profiles]
    coverage_pass = (
        len(profiles) > 0
        and all(value == 0 for value in missed)
    )

    valid = [
        trial
        for trial in trials
        if trial.get("classification") == "WITHIN_BOUND"
    ]
    stack_complete = all(
        trial.get("premeasurement_stack_receipt_complete", False)
        or int(trial.get("premeasurement_q64_count", 0)) == 0
        for trial in trials
    )
    single_process = all(
        trial.get("cgroup_procs") == [trial.get("pid")]
        for trial in trials
    )

    fingerprints: Counter[str] = Counter()
    by_settle: dict[str, dict[str, Any]] = {}
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)

    for trial in trials:
        grouped[int(trial["settle_ms"])].append(trial)
        for event in trial.get("premeasurement_q64", []):
            fingerprints[_fingerprint(event.get("frames", []))] += 1

    for settle_ms, rows in sorted(grouped.items()):
        t_values = [
            int(row["first_q64_touch"])
            for row in rows
            if row.get("first_q64_touch") is not None
        ]
        by_settle[str(settle_ms)] = {
            "n": len(rows),
            "pre_q64_trial_count": sum(
                int(row.get("premeasurement_q64_count", 0)) > 0
                for row in rows
            ),
            "pre_q64_event_count": sum(
                int(row.get("premeasurement_q64_count", 0))
                for row in rows
            ),
            "first_q64_histogram": dict(Counter(t_values)),
            "mean_first_q64_touch": (
                sum(t_values) / len(t_values) if t_values else None
            ),
        }

    bound_violation_count = sum(
        trial.get("classification")
        == "STOCK_BOUND_VIOLATION_CANDIDATE"
        for trial in trials
    )

    return {
        "experiment_id": spec["experiment_id"],
        "trial_count": len(trials),
        "valid_trial_count": len(valid),
        "coverage_pass": coverage_pass,
        "q64_probe_missed_by_block": missed,
        "stack_receipt_complete": stack_complete,
        "single_process_all": single_process,
        "bound_violation_count": bound_violation_count,
        "classifications": dict(
            Counter(trial.get("classification") for trial in trials)
        ),
        "premeasurement_q64_event_count": sum(
            int(trial.get("premeasurement_q64_count", 0))
            for trial in trials
        ),
        "callpath_fingerprints": dict(fingerprints),
        "by_settle_ms": by_settle,
        "experiment_pass": (
            len(trials) == int(spec["design"]["total_identities"])
            and len(valid) == len(trials)
            and coverage_pass
            and stack_complete
            and single_process
            and bound_violation_count == 0
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
                "experiment_pass": result["experiment_pass"],
                "coverage_pass": result["coverage_pass"],
                "stack_receipt_complete": result[
                    "stack_receipt_complete"
                ],
                "single_process_all": result["single_process_all"],
                "bound_violation_count": result[
                    "bound_violation_count"
                ],
                "classifications": result["classifications"],
                "premeasurement_q64_event_count": result[
                    "premeasurement_q64_event_count"
                ],
                "by_settle_ms": result["by_settle_ms"],
                "callpath_fingerprints": result[
                    "callpath_fingerprints"
                ],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
