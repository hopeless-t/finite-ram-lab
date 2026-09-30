from __future__ import annotations

import argparse
import json
import os
import re
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
from .normalize_boundary_chase import _profile_q64_missed
from .premeasure_q64_callpath import _fingerprint, _normalize_stack
from .transaction_trace_observer import _event_row, _timestamp_ns
from .transactional_spawn_native import (
    observed_window,
    touch_with_transaction_marker,
    write_marker,
)


Q64_EVENT = "frl_pc_try64"
REFILL_EVENT = "frl_refill_stock"
EXEC_PID_RE = re.compile(r"\bpid=(?P<pid>\d+)\b")


def load_spec(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _probe_dir(trace_path: Path, event: str) -> Path:
    return trace_path.parent / "events" / "kprobes" / event


def _remove_stacktrace(probe: Path) -> None:
    try:
        (probe / "trigger").write_text("!stacktrace\n", encoding="utf-8")
    except OSError:
        pass


def _profile_counts(trace_path: Path, event: str) -> dict[str, int] | None:
    profile = trace_path.parent / "kprobe_profile"
    if not profile.exists():
        return None
    for raw in profile.read_text(
        encoding="utf-8",
        errors="replace",
    ).splitlines():
        parts = raw.split()
        if len(parts) != 3 or parts[0] != event:
            continue
        try:
            return {"hits": int(parts[1]), "missed": int(parts[2])}
        except ValueError:
            return None
    return None


def _delta_counts(
    before: dict[str, int] | None,
    after: dict[str, int] | None,
) -> dict[str, int] | None:
    if before is None or after is None:
        return None
    return {
        "hits": int(after["hits"]) - int(before["hits"]),
        "missed": int(after["missed"]) - int(before["missed"]),
    }


def prepare_startup_probes(
    trace_path: Path,
    *,
    stack: bool,
) -> None:
    q64 = _probe_dir(trace_path, Q64_EVENT)
    refill = _probe_dir(trace_path, REFILL_EVENT)

    (q64 / "enable").write_text("0\n", encoding="utf-8")
    _remove_stacktrace(q64)
    (q64 / "filter").write_text(
        "nr_pages == 64\n",
        encoding="utf-8",
    )
    if stack:
        (q64 / "trigger").write_text(
            "stacktrace\n",
            encoding="utf-8",
        )
    (q64 / "enable").write_text("1\n", encoding="utf-8")

    (refill / "enable").write_text("0\n", encoding="utf-8")
    (refill / "filter").write_text(
        "nr_pages == 63\n",
        encoding="utf-8",
    )
    (refill / "enable").write_text("1\n", encoding="utf-8")


def bind_measured_q64_probe(
    trace_path: Path,
    *,
    target_pid: int,
) -> None:
    q64 = _probe_dir(trace_path, Q64_EVENT)
    refill = _probe_dir(trace_path, REFILL_EVENT)

    (refill / "enable").write_text("0\n", encoding="utf-8")

    (q64 / "enable").write_text("0\n", encoding="utf-8")
    _remove_stacktrace(q64)
    (q64 / "filter").write_text(
        f"nr_pages == 64 && common_pid == {int(target_pid)}\n",
        encoding="utf-8",
    )
    (q64 / "enable").write_text("1\n", encoding="utf-8")


def close_probes(trace_path: Path) -> None:
    q64 = _probe_dir(trace_path, Q64_EVENT)
    refill = _probe_dir(trace_path, REFILL_EVENT)

    try:
        (q64 / "enable").write_text("0\n", encoding="utf-8")
        _remove_stacktrace(q64)
        (q64 / "filter").write_text(
            "nr_pages == 64 && common_pid == 0\n",
            encoding="utf-8",
        )
    except OSError:
        pass

    try:
        (refill / "enable").write_text("0\n", encoding="utf-8")
    except OSError:
        pass


def _startup_lines(
    text: str,
    *,
    trial_id: str,
) -> list[str]:
    pre = (
        f"FRL_TX trial={trial_id} epoch=0 phase=OBSERVE "
        "touch=91 PRE"
    )
    post = (
        f"FRL_TX trial={trial_id} epoch=0 phase=OBSERVE "
        "touch=91 POST"
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


def _target_events(
    lines: list[str],
    *,
    target_pid: int,
    event_name: str,
    stock_cpu: int,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    active: dict[str, Any] | None = None

    for line in lines:
        if f"{event_name}:" in line:
            row = _event_row(line)
            active = None
            if int(row.get("pid", -1)) == int(target_pid):
                active = {
                    **row,
                    "on_stock_cpu": (
                        int(row.get("cpu", -1)) == int(stock_cpu)
                    ),
                    "stack": [],
                    "frames": [],
                }
                out.append(active)
            continue

        if active is not None and "=>" in line:
            active["stack"].append(line.strip())

    for item in out:
        item["frames"] = _normalize_stack(item["stack"])

    return out


def _exec_timestamp_ns(
    lines: list[str],
    *,
    target_pid: int,
) -> int | None:
    for line in lines:
        if "sched_process_exec:" not in line:
            continue
        m = EXEC_PID_RE.search(line)
        if m and int(m.group("pid")) == int(target_pid):
            return _timestamp_ns(line)
    return None


def classify_startup_seed(
    *,
    q64_rows: list[dict[str, Any]],
    refill_rows: list[dict[str, Any]],
    exec_ns: int | None,
) -> str:
    stock_q64 = [
        row for row in q64_rows if row.get("on_stock_cpu") is True
    ]
    stock_refill = [
        row for row in refill_rows if row.get("on_stock_cpu") is True
    ]

    if not stock_q64:
        return "NO_STARTUP_SEED"
    if not stock_refill:
        return "STARTUP_Q64_WITHOUT_REFILL_RECEIPT"

    if exec_ns is None:
        return "STARTUP_STOCK_SEED_EXEC_BOUNDARY_UNKNOWN"

    first_q64_ns = min(
        int(row["timestamp_ns"])
        for row in stock_q64
        if row.get("timestamp_ns") is not None
    )
    if first_q64_ns < int(exec_ns):
        return "STARTUP_STOCK_SEED_PRE_EXEC"
    return "STARTUP_STOCK_SEED_POST_EXEC"


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
    observer_arm = design["observer_arms"][
        identity % len(design["observer_arms"])
    ]
    root = out_root / f"trial-{block}-{identity}"
    root.mkdir(parents=True, exist_ok=True)
    name = (
        f"fr-seed-{os.getenv('GITHUB_RUN_ID', 'local')}-"
        f"{block}-{identity}"
    )

    before_q64 = _profile_counts(trace_path, Q64_EVENT)
    before_refill = _profile_counts(trace_path, REFILL_EVENT)

    prepare_startup_probes(
        trace_path,
        stack=(observer_arm == "STACK"),
    )

    unit = None
    try:
        write_marker(
            trace_marker,
            trial_id=trial_id,
            epoch=0,
            phase="OBSERVE",
            touch_number=91,
            edge="PRE",
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
        write_marker(
            trace_marker,
            trial_id=trial_id,
            epoch=0,
            phase="OBSERVE",
            touch_number=91,
            edge="POST",
        )

        target_pid = int(unit["pid"])
        startup_trace = trace_path.read_text(
            encoding="utf-8",
            errors="replace",
        )
        startup_lines = _startup_lines(
            startup_trace,
            trial_id=trial_id,
        )

        q64_rows = _target_events(
            startup_lines,
            target_pid=target_pid,
            event_name=Q64_EVENT,
            stock_cpu=stock_cpu,
        )
        refill_rows = _target_events(
            startup_lines,
            target_pid=target_pid,
            event_name=REFILL_EVENT,
            stock_cpu=stock_cpu,
        )
        exec_ns = _exec_timestamp_ns(
            startup_lines,
            target_pid=target_pid,
        )
        startup_class = classify_startup_seed(
            q64_rows=q64_rows,
            refill_rows=refill_rows,
            exec_ns=exec_ns,
        )

        after_startup_q64 = _profile_counts(trace_path, Q64_EVENT)
        after_startup_refill = _profile_counts(trace_path, REFILL_EVENT)
        startup_q64_profile = _delta_counts(
            before_q64,
            after_startup_q64,
        )
        startup_refill_profile = _delta_counts(
            before_refill,
            after_startup_refill,
        )

        bind_measured_q64_probe(
            trace_path,
            target_pid=target_pid,
        )

        geometry = geometry_receipt(unit, prep_cpu)
        if not geometry["guard_cpu_match"] or not geometry["same_pte_table"]:
            return {
                "experiment_id": spec["experiment_id"],
                "trial_id": trial_id,
                "block": block,
                "identity": identity,
                "observer_arm": observer_arm,
                "startup_classification": startup_class,
                "classification": "GEOMETRY_INVALID",
                "geometry": geometry,
            }

        os.sched_setaffinity(target_pid, {stock_cpu})
        _wait_cpu(target_pid, stock_cpu)

        page_size = int(geometry["page_size"])
        sequence = list(
            range(
                int(geometry["safe_start"]) + 1,
                int(geometry["safe_start"])
                + int(geometry["safe_len"]),
            )
        )

        touches: list[dict[str, Any]] = []
        first_q64_touch: int | None = None
        invalidation_reason: str | None = None

        for touch_number in range(
            1,
            int(design["primary_bound_touch"]) + 1,
        ):
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
            q64 = [
                event
                for event in window.get("pc_try64", [])
                if (
                    int(event.get("pid", -1)) == target_pid
                    and int(event.get("cpu", -1)) == stock_cpu
                )
            ]
            complete = (
                int(window.get("pre_count", 0)) == 1
                and int(window.get("post_count", 0)) == 1
                and int(window.get("marker_error_count", 0)) == 0
            )
            touches.append(
                {
                    **row,
                    "touch_number": touch_number,
                    "trace_complete": complete,
                    "target_q64_count": len(q64),
                }
            )

            if not complete:
                invalidation_reason = "TRACE_GAP"
                break
            if int(row.get("worker_error", 0)) != 0:
                invalidation_reason = "WORKER_ERROR"
                break
            if int(row.get("worker_touched", -1)) != touch_number:
                invalidation_reason = "WORKER_TOUCH_SEQUENCE_MISMATCH"
                break
            if int(row.get("observed_cpu", -1)) != stock_cpu:
                invalidation_reason = "CPU_MISMATCH"
                break
            if int(row.get("vmpte_delta_kib", 0)) != 0:
                invalidation_reason = "PTE_GROWTH"
                break
            if len(q64) > 1:
                invalidation_reason = "MULTIPLE_TARGET_Q64_IN_TOUCH"
                break
            if len(q64) == 1:
                first_q64_touch = touch_number
                break

        if invalidation_reason is not None:
            classification = invalidation_reason
        elif first_q64_touch is None:
            classification = "STOCK_BOUND_VIOLATION_CANDIDATE"
        else:
            classification = "WITHIN_BOUND"

        cgroup_procs = sorted(
            int(x)
            for x in (unit["cg"] / "cgroup.procs")
            .read_text(encoding="utf-8")
            .split()
        )

        stock_q64 = [
            row for row in q64_rows if row.get("on_stock_cpu") is True
        ]
        stock_refill = [
            row for row in refill_rows if row.get("on_stock_cpu") is True
        ]

        return {
            "experiment_id": spec["experiment_id"],
            "trial_id": trial_id,
            "block": block,
            "identity": identity,
            "observer_arm": observer_arm,
            "pid": target_pid,
            "prep_cpu": prep_cpu,
            "stock_cpu": stock_cpu,
            "cgroup_procs": cgroup_procs,
            "geometry": geometry,
            "startup_exec_ns": exec_ns,
            "startup_q64": q64_rows,
            "startup_refill63": refill_rows,
            "startup_stock_cpu_q64_count": len(stock_q64),
            "startup_stock_cpu_refill63_count": len(stock_refill),
            "startup_q64_profile": startup_q64_profile,
            "startup_refill_profile": startup_refill_profile,
            "startup_classification": startup_class,
            "startup_stack_receipt_complete": (
                observer_arm != "STACK"
                or all(len(row.get("frames", [])) > 0 for row in q64_rows)
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
        raise RuntimeError("startup stock seed experiment requires >=3 CPUs")
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
        "startup_classifications": dict(
            Counter(row["startup_classification"] for row in rows)
        ),
        "startup_stock_cpu_q64_count": sum(
            int(row.get("startup_stock_cpu_q64_count", 0))
            for row in rows
        ),
    }


def aggregate(
    spec: dict[str, Any],
    input_root: Path,
) -> dict[str, Any]:
    trials = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(input_root.rglob("trial-*.json"))
    ]

    valid = [
        row
        for row in trials
        if row.get("classification") == "WITHIN_BOUND"
    ]
    single_process = all(
        row.get("cgroup_procs") == [row.get("pid")]
        for row in trials
    )
    startup_coverage = all(
        row.get("startup_q64_profile") is not None
        and row["startup_q64_profile"].get("missed") == 0
        and row.get("startup_refill_profile") is not None
        and row["startup_refill_profile"].get("missed") == 0
        for row in trials
    )
    stack_complete = all(
        row.get("startup_stack_receipt_complete", False)
        for row in trials
    )
    bound_violation_count = sum(
        row.get("classification") == "STOCK_BOUND_VIOLATION_CANDIDATE"
        for row in trials
    )

    by_arm: dict[str, dict[str, Any]] = {}
    fingerprints: Counter[str] = Counter()
    for arm in spec["design"]["observer_arms"]:
        rows = [row for row in trials if row["observer_arm"] == arm]
        by_arm[arm] = {
            "n": len(rows),
            "startup_seed_trial_count": sum(
                row["startup_classification"].startswith(
                    "STARTUP_STOCK_SEED"
                )
                for row in rows
            ),
            "startup_stock_cpu_q64_count": sum(
                int(row.get("startup_stock_cpu_q64_count", 0))
                for row in rows
            ),
            "startup_stock_cpu_refill63_count": sum(
                int(row.get("startup_stock_cpu_refill63_count", 0))
                for row in rows
            ),
            "first_q64_histogram": dict(
                Counter(
                    int(row["first_q64_touch"])
                    for row in rows
                    if row.get("first_q64_touch") is not None
                )
            ),
        }

        for row in rows:
            if arm != "STACK":
                continue
            for event in row.get("startup_q64", []):
                if event.get("on_stock_cpu") is True:
                    fingerprints[_fingerprint(event.get("frames", []))] += 1

    promoted = [
        row
        for row in trials
        if (
            row["startup_classification"].startswith(
                "STARTUP_STOCK_SEED"
            )
            and int(row.get("startup_stock_cpu_q64_count", 0)) > 0
            and int(row.get("startup_stock_cpu_refill63_count", 0)) > 0
            and row.get("first_q64_touch") is not None
            and int(row["first_q64_touch"]) > 1
            and row.get("startup_q64_profile", {}).get("missed") == 0
            and row.get("startup_refill_profile", {}).get("missed") == 0
        )
    ]

    return {
        "experiment_id": spec["experiment_id"],
        "trial_count": len(trials),
        "valid_trial_count": len(valid),
        "single_process_all": single_process,
        "startup_probe_coverage_pass": startup_coverage,
        "stack_receipt_complete": stack_complete,
        "bound_violation_count": bound_violation_count,
        "classifications": dict(
            Counter(row.get("classification") for row in trials)
        ),
        "startup_classifications": dict(
            Counter(row.get("startup_classification") for row in trials)
        ),
        "startup_stock_cpu_q64_count": sum(
            int(row.get("startup_stock_cpu_q64_count", 0))
            for row in trials
        ),
        "startup_stock_cpu_refill63_count": sum(
            int(row.get("startup_stock_cpu_refill63_count", 0))
            for row in trials
        ),
        "startup_seed_promoted_count": len(promoted),
        "startup_seed_promoted_trials": [
            row["trial_id"] for row in promoted
        ],
        "by_observer_arm": by_arm,
        "callpath_fingerprints": dict(fingerprints),
        "experiment_pass": (
            len(trials) == int(spec["design"]["total_identities"])
            and len(valid) == len(trials)
            and single_process
            and startup_coverage
            and stack_complete
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
                "startup_probe_coverage_pass": result[
                    "startup_probe_coverage_pass"
                ],
                "stack_receipt_complete": result[
                    "stack_receipt_complete"
                ],
                "bound_violation_count": result[
                    "bound_violation_count"
                ],
                "startup_classifications": result[
                    "startup_classifications"
                ],
                "startup_seed_promoted_count": result[
                    "startup_seed_promoted_count"
                ],
                "startup_seed_promoted_trials": result[
                    "startup_seed_promoted_trials"
                ],
                "by_observer_arm": result["by_observer_arm"],
                "callpath_fingerprints": result[
                    "callpath_fingerprints"
                ],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
