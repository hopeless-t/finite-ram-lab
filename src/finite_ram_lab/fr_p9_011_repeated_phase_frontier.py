from __future__ import annotations

import argparse
import json
import mmap
import os
import shlex
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from finite_ram_lab.fr_p9_009_cgroup_quota_replan import (
    MIB,
    _atomic_json,
    _create_cgroup,
    _job_digest,
    _read_events,
    _write_payload,
)
from finite_ram_lab.fr_p9_010_phase_overlap_residency import (
    _materialize_private_capability,
)

SCHEMA = "finite-ram-lab.fr-p9-011-repeated-phase-frontier/v0.1"
MODES = ("KEEP_WARM", "FAULT_IN")


def _materialize_workspace(
    workspace_bytes: int,
    worker_index: int,
    transition_index: int,
) -> tuple[mmap.mmap, int]:
    workspace = mmap.mmap(-1, workspace_bytes, access=mmap.ACCESS_WRITE)
    checksum = 0
    for offset in range(0, workspace_bytes, 4096):
        value = (worker_index + transition_index + offset // 4096) & 0xFF
        workspace[offset] = value
        checksum ^= value
    return workspace, checksum


def child(
    *,
    mode: str,
    payload_path: Path,
    payload_bytes: int,
    expected_digest: str,
    workspace_mib: int,
    ready_path: Path,
    work_start_path: Path,
    result_path: Path,
    worker_index: int,
    worker_count: int,
    jobs_per_transition: int,
    rounds: int,
    transitions: int,
) -> int:
    if mode not in MODES:
        raise ValueError(f"unknown_mode:{mode}")
    if transitions < 1:
        raise ValueError("transitions_must_be_positive")

    capability: mmap.mmap | None = None
    prestart_materialize_ns = 0
    prestart_capability_checksum: int | None = None
    if mode == "KEEP_WARM":
        start_ns = time.monotonic_ns()
        capability, prestart_capability_checksum = _materialize_private_capability(
            payload_path,
            payload_bytes=payload_bytes,
            expected_digest=expected_digest,
        )
        prestart_materialize_ns = time.monotonic_ns() - start_ns

    _atomic_json(
        ready_path,
        {
            "pid": os.getpid(),
            "worker_index": worker_index,
            "mode": mode,
            "transitions": transitions,
            "capability_loaded_before_ready": capability is not None,
            "prestart_materialize_ns": prestart_materialize_ns,
        },
    )

    deadline = time.monotonic() + 60
    while not work_start_path.exists():
        if time.monotonic() > deadline:
            raise TimeoutError("work_start_timeout")
        time.sleep(0.001)

    transition_rows: list[dict[str, Any]] = []
    for transition_index in range(transitions):
        workspace, workspace_checksum = _materialize_workspace(
            workspace_mib * MIB,
            worker_index,
            transition_index,
        )
        workspace.close()
        # Give the kernel a brief scheduling point after phase-A lifetime ends
        # before FAULT_IN materializes phase-B capability state.
        time.sleep(0.005)

        materialize_ns = 0
        if mode == "FAULT_IN":
            start_ns = time.monotonic_ns()
            capability, capability_checksum = _materialize_private_capability(
                payload_path,
                payload_bytes=payload_bytes,
                expected_digest=expected_digest,
            )
            materialize_ns = time.monotonic_ns() - start_ns
        else:
            if capability is None or prestart_capability_checksum is None:
                raise RuntimeError("keep_warm_capability_missing")
            capability_checksum = prestart_capability_checksum

        jobs: list[dict[str, Any]] = []
        for local_job_id in range(worker_index, jobs_per_transition, worker_count):
            global_job_id = transition_index * jobs_per_transition + local_job_id
            start_ns = time.monotonic_ns()
            digest = _job_digest(capability, global_job_id, rounds)
            end_ns = time.monotonic_ns()
            jobs.append(
                {
                    "transition_index": transition_index,
                    "local_job_id": local_job_id,
                    "global_job_id": global_job_id,
                    "digest": digest,
                    "service_ns": end_ns - start_ns,
                }
            )

        transition_rows.append(
            {
                "transition_index": transition_index,
                "workspace_checksum": workspace_checksum,
                "capability_checksum": capability_checksum,
                "materialize_ns": materialize_ns,
                "jobs": jobs,
            }
        )

        if mode == "FAULT_IN":
            if capability is None:
                raise RuntimeError("fault_in_capability_missing")
            capability.close()
            capability = None

    if capability is not None:
        capability.close()

    _atomic_json(
        result_path,
        {
            "mode": mode,
            "worker_index": worker_index,
            "transitions": transitions,
            "prestart_materialize_ns": prestart_materialize_ns,
            "transition_rows": transition_rows,
        },
    )
    return 0


def _launch_worker(
    *,
    cg: Path,
    mode: str,
    payload_path: Path,
    payload_bytes: int,
    expected_digest: str,
    workspace_mib: int,
    ready_path: Path,
    work_start_path: Path,
    result_path: Path,
    worker_index: int,
    workers: int,
    jobs_per_transition: int,
    rounds: int,
    transitions: int,
) -> subprocess.Popen[str]:
    args = [
        sys.executable,
        "-m",
        "finite_ram_lab.fr_p9_011_repeated_phase_frontier",
        "--child",
        "--mode",
        mode,
        "--payload-path",
        str(payload_path),
        "--payload-bytes",
        str(payload_bytes),
        "--expected-digest",
        expected_digest,
        "--workspace-mib",
        str(workspace_mib),
        "--ready-path",
        str(ready_path),
        "--work-start-path",
        str(work_start_path),
        "--result-path",
        str(result_path),
        "--worker-index",
        str(worker_index),
        "--workers",
        str(workers),
        "--jobs-per-transition",
        str(jobs_per_transition),
        "--rounds",
        str(rounds),
        "--transitions",
        str(transitions),
    ]
    exec_line = " ".join(shlex.quote(value) for value in args)
    command = f"echo $$ > {shlex.quote(str(cg / 'cgroup.procs'))}; exec {exec_line}"
    return subprocess.Popen(
        ["sudo", "sh", "-c", command],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _wait_ready_or_exit(
    ready_paths: list[Path],
    processes: list[subprocess.Popen[str]],
    *,
    timeout: float = 30.0,
) -> str:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if all(path.exists() for path in ready_paths):
            return "READY"
        if any(process.poll() is not None for process in processes):
            return "EARLY_EXIT"
        time.sleep(0.01)
    return "TIMEOUT"


def _collect_stderr(processes: list[subprocess.Popen[str]]) -> list[str]:
    rows: list[str] = []
    for process in processes:
        if process.stderr is not None and process.poll() is not None:
            rows.append(process.stderr.read())
        else:
            rows.append("")
    return rows


def run_group(
    *,
    workers: int,
    mode: str,
    transitions: int,
    memory_max_bytes: int,
    payload_path: Path,
    payload_bytes: int,
    expected_digest: str,
    workspace_mib: int,
    jobs_per_transition: int,
    rounds: int,
    run_root: Path,
    label: str,
) -> dict[str, Any]:
    cg = _create_cgroup(
        f"fr-p9-011-{os.getpid()}-{label}-{time.monotonic_ns()}",
        memory_max_bytes,
    )
    run_dir = run_root / label
    run_dir.mkdir()
    ready_paths = [run_dir / f"ready-{index}.json" for index in range(workers)]
    result_paths = [run_dir / f"result-{index}.json" for index in range(workers)]
    work_start_path = run_dir / "work-start.ns"
    processes: list[subprocess.Popen[str]] = []
    before_events = _read_events(cg)
    state = "UNKNOWN"
    work_wall_ns = 0
    try:
        for index in range(workers):
            processes.append(
                _launch_worker(
                    cg=cg,
                    mode=mode,
                    payload_path=payload_path,
                    payload_bytes=payload_bytes,
                    expected_digest=expected_digest,
                    workspace_mib=workspace_mib,
                    ready_path=ready_paths[index],
                    work_start_path=work_start_path,
                    result_path=result_paths[index],
                    worker_index=index,
                    workers=workers,
                    jobs_per_transition=jobs_per_transition,
                    rounds=rounds,
                    transitions=transitions,
                )
            )

        state = _wait_ready_or_exit(ready_paths, processes)
        if state == "READY":
            group_start_ns = time.monotonic_ns()
            work_start_path.write_text(str(group_start_ns))
            deadline = time.monotonic() + 120
            while time.monotonic() < deadline and any(p.poll() is None for p in processes):
                time.sleep(0.01)
            work_wall_ns = time.monotonic_ns() - group_start_ns
            if any(p.poll() is None for p in processes):
                state = "WORK_TIMEOUT"
            else:
                state = "COMPLETED" if all(p.returncode == 0 for p in processes) else "WORK_EXIT"

        for process in processes:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)

        after_events = _read_events(cg)
        memory_peak = int((cg / "memory.peak").read_text().strip())
        result_receipts: list[dict[str, Any]] = []
        if all(path.exists() for path in result_paths):
            result_receipts = [json.loads(path.read_text()) for path in result_paths]

        job_digests: dict[str, str] = {}
        workspace_signature: list[tuple[int, int, int]] = []
        materialize_ns_total = 0
        materialization_count = 0
        for receipt in result_receipts:
            worker_index = int(receipt["worker_index"])
            prestart = int(receipt["prestart_materialize_ns"])
            if prestart > 0:
                materialize_ns_total += prestart
                materialization_count += 1
            for transition in receipt["transition_rows"]:
                transition_index = int(transition["transition_index"])
                workspace_signature.append(
                    (
                        worker_index,
                        transition_index,
                        int(transition["workspace_checksum"]),
                    )
                )
                per_transition_ns = int(transition["materialize_ns"])
                if per_transition_ns > 0:
                    materialize_ns_total += per_transition_ns
                    materialization_count += 1
                for job in transition["jobs"]:
                    job_digests[str(job["global_job_id"])] = str(job["digest"])

        return {
            "label": label,
            "workers": workers,
            "mode": mode,
            "transitions": transitions,
            "state": state,
            "memory_max_bytes": memory_max_bytes,
            "memory_peak_bytes": memory_peak,
            "work_wall_ns": work_wall_ns,
            "materialize_ns_total": materialize_ns_total,
            "materialization_count": materialization_count,
            "workspace_signature": sorted(workspace_signature),
            "job_digests": job_digests,
            "oom_delta": after_events.get("oom", 0) - before_events.get("oom", 0),
            "oom_kill_delta": after_events.get("oom_kill", 0) - before_events.get("oom_kill", 0),
            "returncodes": [process.returncode for process in processes],
            "stderr": _collect_stderr(processes),
        }
    finally:
        for process in processes:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)
        subprocess.run(["sudo", "rmdir", str(cg)], check=False)


def pareto_modes(rows: list[dict[str, Any]]) -> list[str]:
    """Return modes non-dominated on lower peak bytes and lower materialize time."""
    frontier: list[str] = []
    for candidate in rows:
        dominated = False
        for other in rows:
            if other is candidate:
                continue
            no_worse = (
                int(other["memory_peak_bytes"]) <= int(candidate["memory_peak_bytes"])
                and int(other["materialize_ns_total"]) <= int(candidate["materialize_ns_total"])
            )
            strictly_better = (
                int(other["memory_peak_bytes"]) < int(candidate["memory_peak_bytes"])
                or int(other["materialize_ns_total"]) < int(candidate["materialize_ns_total"])
            )
            if no_worse and strictly_better:
                dominated = True
                break
        if not dominated:
            frontier.append(str(candidate["mode"]))
    return sorted(frontier)


def _median_int(values: list[int]) -> int:
    return int(statistics.median(values))


def _linear_fit(xs: list[int], ys: list[int]) -> dict[str, float | None]:
    if len(xs) != len(ys) or len(xs) < 2:
        return {"slope": None, "intercept": None, "r2": None}
    xbar = sum(xs) / len(xs)
    ybar = sum(ys) / len(ys)
    sxx = sum((x - xbar) ** 2 for x in xs)
    if sxx == 0:
        return {"slope": None, "intercept": None, "r2": None}
    slope = sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys)) / sxx
    intercept = ybar - slope * xbar
    sst = sum((y - ybar) ** 2 for y in ys)
    sse = sum((y - (intercept + slope * x)) ** 2 for x, y in zip(xs, ys))
    r2 = None if sst == 0 else 1.0 - sse / sst
    return {"slope": slope, "intercept": intercept, "r2": r2}


def run_panel(
    *,
    payload_mib: int = 8,
    workspace_mib: int = 16,
    workers: int = 4,
    jobs_per_transition: int = 12,
    rounds: int = 4,
    transition_counts: tuple[int, ...] = (1, 2, 4, 8),
    repetitions: int = 2,
    high_quota_mib: int = 256,
) -> dict[str, Any]:
    controllers = (Path("/sys/fs/cgroup") / "cgroup.controllers").read_text().split()
    if "memory" not in controllers:
        raise RuntimeError("memory_controller_unavailable")
    if not transition_counts or any(value < 1 for value in transition_counts):
        raise ValueError("transition_counts_must_be_positive")
    if repetitions < 1:
        raise ValueError("repetitions_must_be_positive")

    with tempfile.TemporaryDirectory(prefix="fr-p9-011-repeated-") as tmp:
        root = Path(tmp)
        payload_path = root / "capability.bin"
        payload_bytes = payload_mib * MIB
        expected_digest = _write_payload(payload_path, payload_bytes)
        high_quota_bytes = high_quota_mib * MIB

        runs: list[dict[str, Any]] = []
        for transitions in transition_counts:
            for rep in range(repetitions):
                order = MODES if rep % 2 == 0 else tuple(reversed(MODES))
                for mode in order:
                    runs.append(
                        run_group(
                            workers=workers,
                            mode=mode,
                            transitions=transitions,
                            memory_max_bytes=high_quota_bytes,
                            payload_path=payload_path,
                            payload_bytes=payload_bytes,
                            expected_digest=expected_digest,
                            workspace_mib=workspace_mib,
                            jobs_per_transition=jobs_per_transition,
                            rounds=rounds,
                            run_root=root,
                            label=f"t{transitions}-{mode.lower()}-r{rep}",
                        )
                    )

    grouped: dict[tuple[int, str], list[dict[str, Any]]] = {}
    for row in runs:
        grouped.setdefault((int(row["transitions"]), str(row["mode"])), []).append(row)

    horizon_summaries: list[dict[str, Any]] = []
    semantic_checks: list[bool] = []
    no_oom_checks: list[bool] = []
    materialization_count_checks: list[bool] = []

    for transitions in transition_counts:
        horizon_rows = [row for row in runs if int(row["transitions"]) == transitions]
        reference = horizon_rows[0]
        semantic_checks.extend(
            row["state"] == "COMPLETED"
            and row["job_digests"] == reference["job_digests"]
            and row["workspace_signature"] == reference["workspace_signature"]
            for row in horizon_rows
        )
        no_oom_checks.extend(
            int(row["oom_kill_delta"]) == 0 and int(row["oom_delta"]) == 0
            for row in horizon_rows
        )

        summaries_by_mode: dict[str, dict[str, Any]] = {}
        for mode in MODES:
            rows = grouped[(transitions, mode)]
            expected_materializations = workers if mode == "KEEP_WARM" else workers * transitions
            materialization_count_checks.extend(
                int(row["materialization_count"]) == expected_materializations for row in rows
            )
            summaries_by_mode[mode] = {
                "mode": mode,
                "transitions": transitions,
                "memory_peak_bytes": _median_int([int(row["memory_peak_bytes"]) for row in rows]),
                "materialize_ns_total": _median_int([int(row["materialize_ns_total"]) for row in rows]),
                "work_wall_ns": _median_int([int(row["work_wall_ns"]) for row in rows]),
                "materialization_count": expected_materializations,
            }

        warm = summaries_by_mode["KEEP_WARM"]
        fault = summaries_by_mode["FAULT_IN"]
        pair = [warm, fault]
        horizon_summaries.append(
            {
                "transitions": transitions,
                "KEEP_WARM": warm,
                "FAULT_IN": fault,
                "peak_saving_bytes_fault_in": int(warm["memory_peak_bytes"]) - int(fault["memory_peak_bytes"]),
                "incremental_materialize_ns_fault_in": int(fault["materialize_ns_total"]) - int(warm["materialize_ns_total"]),
                "pareto_modes": pareto_modes(pair),
            }
        )

    fault_materialize = [
        int(summary["FAULT_IN"]["materialize_ns_total"]) for summary in horizon_summaries
    ]
    fit = _linear_fit(list(transition_counts), fault_materialize)
    min_transition = min(transition_counts)
    max_transition = max(transition_counts)
    min_summary = next(row for row in horizon_summaries if row["transitions"] == min_transition)
    max_summary = next(row for row in horizon_summaries if row["transitions"] == max_transition)

    checks = {
        "all_runs_complete_and_preserve_semantics": all(semantic_checks),
        "high_quota_runs_have_no_kernel_oom": all(no_oom_checks),
        "materialization_counts_match_lifetime_policy": all(materialization_count_checks),
        "fault_in_has_lower_peak_at_every_horizon": all(
            int(row["peak_saving_bytes_fault_in"]) >= 8 * MIB for row in horizon_summaries
        ),
        "keep_warm_has_lower_materialize_time_at_every_horizon": all(
            int(row["incremental_materialize_ns_fault_in"]) > 0 for row in horizon_summaries
        ),
        "both_modes_remain_typed_pareto_at_every_horizon": all(
            row["pareto_modes"] == ["FAULT_IN", "KEEP_WARM"] for row in horizon_summaries
        ),
        "long_horizon_fault_in_materialize_tax_exceeds_short_horizon": (
            int(max_summary["FAULT_IN"]["materialize_ns_total"])
            > int(min_summary["FAULT_IN"]["materialize_ns_total"])
        ),
        "lifetime_policy_does_not_grant_authority": True,
        "lifetime_policy_does_not_grant_retry_permission": True,
    }

    return {
        "schema": SCHEMA,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "classification": "HOSTED_LINUX_CGROUP_V2_REPEATED_PHASE_RESIDENCY_PROXY",
        "fixture": {
            "payload_mib": payload_mib,
            "workspace_mib": workspace_mib,
            "workers": workers,
            "jobs_per_transition": jobs_per_transition,
            "rounds": rounds,
            "transition_counts": list(transition_counts),
            "repetitions": repetitions,
            "high_quota_mib": high_quota_mib,
        },
        "runs": runs,
        "horizon_summaries": horizon_summaries,
        "fault_in_materialize_linear_fit": fit,
        "checks": checks,
        "decision": (
            "TREAT_RESIDENCY_LIFETIME_AS_HORIZON_DEPENDENT;"
            "FAULT_IN_CAN_BUY_LOWER_PEAK_MEMORY_AT_THE_COST_OF_REPEATED_MATERIALIZATION;"
            "KEEP_THE_RESULT_TYPED_UNTIL_AN_EXTERNAL_MEMORY_OR_LATENCY_PRICE_EXISTS"
        ),
        "typed_objectives": [
            "kernel_memory_peak_bytes",
            "materialize_ns_total",
            "work_wall_ns",
            "materialization_count",
            "job_semantics",
        ],
        "scalar_gain": None,
        "authority_effect": "NONE",
        "retry_authority": False,
        "next_falsifier": (
            "introduce a bounded memory-price/latency-SLO family and compile the repeated-transition "
            "typed frontier into explicit policy regions without claiming a universal scalar winner"
        ),
        "claim_ceiling": (
            "HOSTED_GITHUB_LINUX_CGROUP_V2_REPEATED_PHASE_AND_HASHING_PROXY_ONLY_"
            "NO_UNIVERSAL_RESIDENCY_POLICY_OR_APPLICATION_PERFORMANCE_CLAIM"
        ),
    }


def _parse_transition_counts(value: str) -> tuple[int, ...]:
    rows = tuple(int(part) for part in value.split(",") if part.strip())
    if not rows or any(item < 1 for item in rows):
        raise argparse.ArgumentTypeError("transition counts must be positive integers")
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--mode", choices=MODES)
    parser.add_argument("--payload-path", type=Path)
    parser.add_argument("--payload-bytes", type=int)
    parser.add_argument("--expected-digest")
    parser.add_argument("--workspace-mib", type=int, default=16)
    parser.add_argument("--ready-path", type=Path)
    parser.add_argument("--work-start-path", type=Path)
    parser.add_argument("--result-path", type=Path)
    parser.add_argument("--worker-index", type=int)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--jobs-per-transition", type=int, default=12)
    parser.add_argument("--rounds", type=int, default=4)
    parser.add_argument("--transitions", type=int, default=1)
    parser.add_argument("--payload-mib", type=int, default=8)
    parser.add_argument("--transition-counts", type=_parse_transition_counts, default=(1, 2, 4, 8))
    parser.add_argument("--repetitions", type=int, default=2)
    parser.add_argument("--high-quota-mib", type=int, default=256)
    args = parser.parse_args()

    if args.child:
        required = (
            args.mode,
            args.payload_path,
            args.payload_bytes,
            args.expected_digest,
            args.ready_path,
            args.work_start_path,
            args.result_path,
            args.worker_index,
        )
        if any(value is None for value in required):
            raise SystemExit("missing_child_argument")
        return child(
            mode=args.mode,
            payload_path=args.payload_path,
            payload_bytes=args.payload_bytes,
            expected_digest=args.expected_digest,
            workspace_mib=args.workspace_mib,
            ready_path=args.ready_path,
            work_start_path=args.work_start_path,
            result_path=args.result_path,
            worker_index=args.worker_index,
            worker_count=args.workers,
            jobs_per_transition=args.jobs_per_transition,
            rounds=args.rounds,
            transitions=args.transitions,
        )

    result = run_panel(
        payload_mib=args.payload_mib,
        workspace_mib=args.workspace_mib,
        workers=args.workers,
        jobs_per_transition=args.jobs_per_transition,
        rounds=args.rounds,
        transition_counts=args.transition_counts,
        repetitions=args.repetitions,
        high_quota_mib=args.high_quota_mib,
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
