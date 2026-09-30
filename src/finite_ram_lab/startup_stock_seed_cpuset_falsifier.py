from __future__ import annotations

import argparse
import json
import mmap
import os
from collections import Counter
from pathlib import Path
from typing import Any

from .memcg005gc_controlled_spawn import (
    CONTROL_BYTES,
    OFF_READY,
    _run,
    _start,
    _stop,
    _u32,
    _wait,
    _wait_cpu,
    environment_receipt,
    geometry_receipt,
)
from .startup_stock_seed_phase import (
    Q64_EVENT,
    REFILL_EVENT,
    _delta_counts,
    _profile_counts,
    _startup_lines,
    _target_events,
    bind_measured_q64_probe,
    close_probes,
    prepare_startup_probes,
)
from .transactional_spawn_native import (
    observed_window,
    touch_with_transaction_marker,
    write_marker,
)


STARTUP_TOUCH = 91
RELEASE_TOUCH = 92


def load_spec(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _parse_cpu_set(text: str) -> set[int]:
    out: set[int] = set()
    for piece in text.strip().split(","):
        piece = piece.strip()
        if not piece:
            continue
        if "-" in piece:
            lo, hi = piece.split("-", 1)
            out.update(range(int(lo), int(hi) + 1))
        else:
            out.add(int(piece))
    return out


def _cpuset_effective(cg: Path) -> set[int]:
    return _parse_cpu_set(
        (cg / "cpuset.cpus.effective").read_text(
            encoding="utf-8"
        )
    )


def _start_cpuset_constrained(
    *,
    worker: Path,
    root: Path,
    name: str,
    prep_cpu: int,
    max_pages: int,
    safe_len: int,
    worker_uid: int,
) -> dict[str, Any]:
    """Start a fresh worker with cgroup cpuset restricted from birth."""
    ctl = root / f"{name}.ctl"
    fd = os.open(
        ctl,
        os.O_RDWR | os.O_CREAT | os.O_TRUNC,
        0o600,
    )
    os.ftruncate(fd, CONTROL_BYTES)
    if int(worker_uid) != os.getuid():
        os.chown(ctl, int(worker_uid), -1)
    mm = mmap.mmap(
        fd,
        CONTROL_BYTES,
        access=mmap.ACCESS_WRITE,
    )

    try:
        _run(
            [
                "sudo",
                "systemd-run",
                "--quiet",
                "--collect",
                f"--unit={name}",
                f"--uid={int(worker_uid)}",
                "-p",
                "MemoryAccounting=yes",
                "-p",
                f"CPUAffinity={prep_cpu}",
                "-p",
                f"AllowedCPUs={prep_cpu}",
                str(worker),
                "--shared",
                str(ctl),
                "--max-pages",
                str(max_pages),
                "--safe-len",
                str(safe_len),
            ]
        )
        _wait(lambda: _u32(mm, OFF_READY) == 1)

        pid = int(
            _run(
                [
                    "systemctl",
                    "show",
                    f"{name}.service",
                    "--property=MainPID",
                    "--value",
                ]
            ).stdout.strip()
        )
        cgroup_text = _run(
            [
                "systemctl",
                "show",
                f"{name}.service",
                "--property=ControlGroup",
                "--value",
            ]
        ).stdout.strip()
        cg = Path("/sys/fs/cgroup") / cgroup_text.lstrip("/")
        _wait_cpu(pid, prep_cpu)

        return {
            "name": name,
            "pid": pid,
            "cg": cg,
            "fd": fd,
            "mm": mm,
        }
    except Exception:
        try:
            mm.close()
            os.close(fd)
        except Exception:
            pass
        _run(
            [
                "sudo",
                "systemctl",
                "stop",
                name + ".service",
            ],
            check=False,
        )
        raise


def _expand_cpuset(
    unit: dict[str, Any],
    *,
    prep_cpu: int,
    stock_cpu: int,
) -> set[int]:
    value = f"{prep_cpu},{stock_cpu}"
    _run(
        [
            "sudo",
            "systemctl",
            "set-property",
            "--runtime",
            unit["name"] + ".service",
            f"AllowedCPUs={value}",
        ]
    )

    wanted = {int(prep_cpu), int(stock_cpu)}

    def ready() -> bool:
        return wanted.issubset(_cpuset_effective(unit["cg"]))

    _wait(ready, 5.0)
    return _cpuset_effective(unit["cg"])


def _window_lines(
    text: str,
    *,
    trial_id: str,
    touch_number: int,
) -> list[str]:
    pre = (
        f"FRL_TX trial={trial_id} epoch=0 phase=OBSERVE "
        f"touch={touch_number} PRE"
    )
    post = (
        f"FRL_TX trial={trial_id} epoch=0 phase=OBSERVE "
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


def _count_target_stock_events(
    lines: list[str],
    *,
    target_pid: int,
    stock_cpu: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    q64 = _target_events(
        lines,
        target_pid=target_pid,
        event_name=Q64_EVENT,
        stock_cpu=stock_cpu,
    )
    refill = _target_events(
        lines,
        target_pid=target_pid,
        event_name=REFILL_EVENT,
        stock_cpu=stock_cpu,
    )
    return (
        [row for row in q64 if row.get("on_stock_cpu") is True],
        [row for row in refill if row.get("on_stock_cpu") is True],
    )


def _measure_boundary(
    *,
    unit: dict[str, Any],
    geometry: dict[str, Any],
    trace_marker: Path,
    trace_path: Path,
    trial_id: str,
    stock_cpu: int,
    primary_bound_touch: int,
) -> dict[str, Any]:
    target_pid = int(unit["pid"])
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

    for touch_number in range(1, primary_bound_touch + 1):
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

    return {
        "classification": classification,
        "invalidation_reason": invalidation_reason,
        "first_q64_touch": first_q64_touch,
        "initial_residual_estimate": (
            None
            if first_q64_touch is None
            else first_q64_touch - 1
        ),
        "touches": touches,
    }


def _causal_class(
    *,
    arm: str,
    startup_q64: int,
    startup_refill: int,
    release_q64: int,
    release_refill: int,
    first_q64_touch: int | None,
    valid: bool,
) -> str:
    if not valid:
        return "INVALID_OBSERVER"

    if arm == "CONTROL":
        if startup_q64 > 0 and startup_refill > 0:
            if first_q64_touch is not None and first_q64_touch > 1:
                return "CONTROL_SEED"
            return "CONTROL_SEED_NO_DELAY"
        return "CONTROL_NO_SEED"

    if startup_q64 > 0 or startup_refill > 0:
        return "CPUSET_STARTUP_LEAK"
    if release_q64 > 0 or release_refill > 0:
        return "CPUSET_RELEASE_GAP_SEED"
    if first_q64_touch == 1:
        return "CPUSET_SUPPRESSED"
    return "CPUSET_HIGH_T_WITHOUT_SEED"


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
    arm = design["arms"][identity % len(design["arms"])]
    trial_id = f"{block}:{identity}"
    root = out_root / f"trial-{block}-{identity}"
    root.mkdir(parents=True, exist_ok=True)
    name = (
        f"fr-seedfx-{os.getenv('GITHUB_RUN_ID', 'local')}-"
        f"{block}-{identity}"
    )

    before_q64 = _profile_counts(trace_path, Q64_EVENT)
    before_refill = _profile_counts(trace_path, REFILL_EVENT)
    prepare_startup_probes(trace_path, stack=False)

    unit = None
    try:
        write_marker(
            trace_marker,
            trial_id=trial_id,
            epoch=0,
            phase="OBSERVE",
            touch_number=STARTUP_TOUCH,
            edge="PRE",
        )
        if arm == "CONTROL":
            unit = _start(
                worker,
                root,
                name,
                prep_cpu,
                int(design["max_pages"]),
                int(design["safe_len_pages"]),
                worker_uid=worker_uid,
            )
        else:
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

        target_pid = int(unit["pid"])
        startup_effective = _cpuset_effective(unit["cg"])

        startup_text = trace_path.read_text(
            encoding="utf-8",
            errors="replace",
        )
        startup_lines = _window_lines(
            startup_text,
            trial_id=trial_id,
            touch_number=STARTUP_TOUCH,
        )
        startup_q64_rows, startup_refill_rows = (
            _count_target_stock_events(
                startup_lines,
                target_pid=target_pid,
                stock_cpu=stock_cpu,
            )
        )

        after_start_q64 = _profile_counts(trace_path, Q64_EVENT)
        after_start_refill = _profile_counts(trace_path, REFILL_EVENT)
        startup_q64_profile = _delta_counts(
            before_q64,
            after_start_q64,
        )
        startup_refill_profile = _delta_counts(
            before_refill,
            after_start_refill,
        )

        write_marker(
            trace_marker,
            trial_id=trial_id,
            epoch=0,
            phase="OBSERVE",
            touch_number=RELEASE_TOUCH,
            edge="PRE",
        )
        if arm == "CPUSET_PREP_ONLY":
            release_effective = _expand_cpuset(
                unit,
                prep_cpu=prep_cpu,
                stock_cpu=stock_cpu,
            )
        else:
            release_effective = _cpuset_effective(unit["cg"])

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

        release_text = trace_path.read_text(
            encoding="utf-8",
            errors="replace",
        )
        release_lines = _window_lines(
            release_text,
            trial_id=trial_id,
            touch_number=RELEASE_TOUCH,
        )
        release_q64_rows, release_refill_rows = (
            _count_target_stock_events(
                release_lines,
                target_pid=target_pid,
                stock_cpu=stock_cpu,
            )
        )

        after_release_q64 = _profile_counts(trace_path, Q64_EVENT)
        after_release_refill = _profile_counts(
            trace_path,
            REFILL_EVENT,
        )
        release_q64_profile = _delta_counts(
            after_start_q64,
            after_release_q64,
        )
        release_refill_profile = _delta_counts(
            after_start_refill,
            after_release_refill,
        )

        bind_measured_q64_probe(
            trace_path,
            target_pid=target_pid,
        )

        geometry = geometry_receipt(unit, prep_cpu)
        geometry_valid = (
            geometry["guard_cpu_match"]
            and geometry["same_pte_table"]
        )

        measure = (
            _measure_boundary(
                unit=unit,
                geometry=geometry,
                trace_marker=trace_marker,
                trace_path=trace_path,
                trial_id=trial_id,
                stock_cpu=stock_cpu,
                primary_bound_touch=int(
                    design["primary_bound_touch"]
                ),
            )
            if geometry_valid
            else {
                "classification": "GEOMETRY_INVALID",
                "invalidation_reason": "GEOMETRY_INVALID",
                "first_q64_touch": None,
                "initial_residual_estimate": None,
                "touches": [],
            }
        )

        cgroup_procs = sorted(
            int(x)
            for x in (unit["cg"] / "cgroup.procs")
            .read_text(encoding="utf-8")
            .split()
        )

        coverage_ok = all(
            profile is not None
            and int(profile.get("missed", -1)) == 0
            for profile in (
                startup_q64_profile,
                startup_refill_profile,
                release_q64_profile,
                release_refill_profile,
            )
        )
        cpuset_start_ok = (
            arm == "CONTROL"
            or startup_effective == {prep_cpu}
        )
        cpuset_release_ok = (
            arm == "CONTROL"
            or {prep_cpu, stock_cpu}.issubset(
                release_effective
            )
        )
        single_process = cgroup_procs == [target_pid]
        valid = (
            coverage_ok
            and geometry_valid
            and single_process
            and cpuset_start_ok
            and cpuset_release_ok
            and measure["classification"] == "WITHIN_BOUND"
        )

        causal_class = _causal_class(
            arm=arm,
            startup_q64=len(startup_q64_rows),
            startup_refill=len(startup_refill_rows),
            release_q64=len(release_q64_rows),
            release_refill=len(release_refill_rows),
            first_q64_touch=measure["first_q64_touch"],
            valid=valid,
        )

        return {
            "experiment_id": spec["experiment_id"],
            "trial_id": trial_id,
            "block": block,
            "identity": identity,
            "arm": arm,
            "pid": target_pid,
            "prep_cpu": prep_cpu,
            "stock_cpu": stock_cpu,
            "startup_cpuset_effective": sorted(
                startup_effective
            ),
            "release_cpuset_effective": sorted(
                release_effective
            ),
            "cpuset_start_ok": cpuset_start_ok,
            "cpuset_release_ok": cpuset_release_ok,
            "cgroup_procs": cgroup_procs,
            "single_process": single_process,
            "geometry": geometry,
            "startup_stock_cpu_q64_count": len(
                startup_q64_rows
            ),
            "startup_stock_cpu_refill63_count": len(
                startup_refill_rows
            ),
            "release_gap_stock_cpu_q64_count": len(
                release_q64_rows
            ),
            "release_gap_stock_cpu_refill63_count": len(
                release_refill_rows
            ),
            "startup_q64_profile": startup_q64_profile,
            "startup_refill_profile": startup_refill_profile,
            "release_q64_profile": release_q64_profile,
            "release_refill_profile": release_refill_profile,
            "coverage_ok": coverage_ok,
            **measure,
            "valid": valid,
            "causal_classification": causal_class,
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
            "startup seed cpuset falsifier requires >=3 CPUs"
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
        "causal_classifications": dict(
            Counter(
                row["causal_classification"]
                for row in rows
            )
        ),
        "first_q64_by_arm": {
            arm: [
                row["first_q64_touch"]
                for row in rows
                if (
                    row["arm"] == arm
                    and row.get("first_q64_touch") is not None
                )
            ]
            for arm in spec["design"]["arms"]
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
    arms = spec["design"]["arms"]

    by_arm: dict[str, dict[str, Any]] = {}
    for arm in arms:
        rows = [row for row in trials if row["arm"] == arm]
        by_arm[arm] = {
            "n": len(rows),
            "valid": sum(bool(row["valid"]) for row in rows),
            "causal_classifications": dict(
                Counter(
                    row["causal_classification"]
                    for row in rows
                )
            ),
            "startup_seed_trials": sum(
                int(row["startup_stock_cpu_q64_count"]) > 0
                and int(
                    row["startup_stock_cpu_refill63_count"]
                )
                > 0
                for row in rows
            ),
            "release_gap_seed_trials": sum(
                int(row["release_gap_stock_cpu_q64_count"])
                > 0
                or int(
                    row[
                        "release_gap_stock_cpu_refill63_count"
                    ]
                )
                > 0
                for row in rows
            ),
            "first_q64_histogram": dict(
                Counter(
                    int(row["first_q64_touch"])
                    for row in rows
                    if row.get("first_q64_touch") is not None
                )
            ),
            "high_t_gt1": sum(
                int(row.get("first_q64_touch") or 0) > 1
                for row in rows
            ),
        }

    control_seed = [
        row
        for row in trials
        if row["causal_classification"] == "CONTROL_SEED"
    ]
    intervention_valid = [
        row
        for row in trials
        if row["arm"] == "CPUSET_PREP_ONLY" and row["valid"]
    ]

    valid_trial_count = sum(
        bool(row["valid"]) for row in trials
    )

    causal_support = (
        len(trials) == int(spec["design"]["total_identities"])
        and valid_trial_count == len(trials)
        and len(control_seed) >= 1
        and all(
            row["causal_classification"]
            == "CPUSET_SUPPRESSED"
            for row in intervention_valid
        )
        and len(intervention_valid)
        == int(spec["design"]["n_per_arm"])
    )

    return {
        "experiment_id": spec["experiment_id"],
        "trial_count": len(trials),
        "valid_trial_count": valid_trial_count,
        "by_arm": by_arm,
        "control_seed_count": len(control_seed),
        "control_seed_trials": [
            row["trial_id"] for row in control_seed
        ],
        "intervention_valid_count": len(
            intervention_valid
        ),
        "intervention_suppressed_count": sum(
            row["causal_classification"]
            == "CPUSET_SUPPRESSED"
            for row in intervention_valid
        ),
        "intervention_startup_leak_count": sum(
            row["causal_classification"]
            == "CPUSET_STARTUP_LEAK"
            for row in trials
        ),
        "intervention_release_gap_seed_count": sum(
            row["causal_classification"]
            == "CPUSET_RELEASE_GAP_SEED"
            for row in trials
        ),
        "causal_support": causal_support,
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
                "causal_support": result["causal_support"],
                "valid_trial_count": result[
                    "valid_trial_count"
                ],
                "control_seed_count": result[
                    "control_seed_count"
                ],
                "intervention_valid_count": result[
                    "intervention_valid_count"
                ],
                "intervention_suppressed_count": result[
                    "intervention_suppressed_count"
                ],
                "intervention_startup_leak_count": result[
                    "intervention_startup_leak_count"
                ],
                "intervention_release_gap_seed_count": result[
                    "intervention_release_gap_seed_count"
                ],
                "by_arm": result["by_arm"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
