from __future__ import annotations

import argparse
import hashlib
import json
import mmap
import os
import shlex
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

SCHEMA = "finite-ram-lab.fr-p9-010-phase-overlap-residency/v0.1"
MODES = ("KEEP_WARM", "FAULT_IN")


def _materialize_private_capability(
    payload_path: Path,
    *,
    payload_bytes: int,
    expected_digest: str,
) -> tuple[mmap.mmap, int]:
    """Materialize a private anonymous runtime copy without a large Python bytes buffer."""

    capability = mmap.mmap(-1, payload_bytes, access=mmap.ACCESS_WRITE)
    view = memoryview(capability)
    try:
        with payload_path.open("rb", buffering=0) as handle:
            offset = 0
            while offset < payload_bytes:
                count = handle.readinto(view[offset:])
                if not count:
                    break
                offset += count
        if offset != payload_bytes:
            raise RuntimeError(f"short_capability_read:{offset}:{payload_bytes}")
    finally:
        view.release()

    touch_checksum = 0
    for offset in range(0, payload_bytes, 4096):
        touch_checksum ^= capability[offset]
    digest = hashlib.sha256(capability).hexdigest()
    if digest != expected_digest:
        capability.close()
        raise RuntimeError("capability_digest_mismatch")
    return capability, touch_checksum


def _materialize_workspace(workspace_bytes: int, worker_index: int) -> tuple[mmap.mmap, int]:
    workspace = mmap.mmap(-1, workspace_bytes, access=mmap.ACCESS_WRITE)
    checksum = 0
    for offset in range(0, workspace_bytes, 4096):
        value = (worker_index + offset // 4096) & 0xFF
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
    jobs: int,
    rounds: int,
) -> int:
    if mode not in MODES:
        raise ValueError(f"unknown_mode:{mode}")

    workspace, workspace_checksum = _materialize_workspace(
        workspace_mib * MIB,
        worker_index,
    )
    capability: mmap.mmap | None = None
    prestart_capability_checksum: int | None = None

    if mode == "KEEP_WARM":
        capability, prestart_capability_checksum = _materialize_private_capability(
            payload_path,
            payload_bytes=payload_bytes,
            expected_digest=expected_digest,
        )

    _atomic_json(
        ready_path,
        {
            "pid": os.getpid(),
            "worker_index": worker_index,
            "mode": mode,
            "workspace_mib": workspace_mib,
            "workspace_checksum": workspace_checksum,
            "capability_loaded_before_ready": capability is not None,
            "prestart_capability_checksum": prestart_capability_checksum,
        },
    )

    deadline = time.monotonic() + 60
    while not work_start_path.exists():
        if time.monotonic() > deadline:
            raise TimeoutError("work_start_timeout")
        time.sleep(0.001)

    # Phase transition: the private phase-A workspace is no longer semantically
    # live. Explicitly unmap it before FAULT_IN materializes the capability.
    workspace.close()
    time.sleep(0.01)

    resume_start_ns = time.monotonic_ns()
    if mode == "FAULT_IN":
        capability, capability_checksum = _materialize_private_capability(
            payload_path,
            payload_bytes=payload_bytes,
            expected_digest=expected_digest,
        )
    else:
        if capability is None or prestart_capability_checksum is None:
            raise RuntimeError("keep_warm_capability_missing")
        capability_checksum = prestart_capability_checksum
    resume_end_ns = time.monotonic_ns()

    work_start_ns = time.monotonic_ns()
    rows: list[dict[str, Any]] = []
    for job_id in range(worker_index, jobs, worker_count):
        start_ns = time.monotonic_ns()
        digest = _job_digest(capability, job_id, rounds)
        end_ns = time.monotonic_ns()
        rows.append(
            {
                "job_id": job_id,
                "digest": digest,
                "start_ns": start_ns,
                "end_ns": end_ns,
                "sojourn_ns": end_ns - work_start_ns,
            }
        )

    _atomic_json(
        result_path,
        {
            "mode": mode,
            "workspace_checksum": workspace_checksum,
            "capability_checksum": capability_checksum,
            "resume_ns": resume_end_ns - resume_start_ns,
            "jobs": rows,
        },
    )
    capability.close()
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
    jobs: int,
    rounds: int,
) -> subprocess.Popen[str]:
    args = [
        sys.executable,
        "-m",
        "finite_ram_lab.fr_p9_010_phase_overlap_residency",
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
        "--jobs",
        str(jobs),
        "--rounds",
        str(rounds),
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
    memory_max_bytes: int,
    payload_path: Path,
    payload_bytes: int,
    expected_digest: str,
    workspace_mib: int,
    jobs: int,
    rounds: int,
    run_root: Path,
    label: str,
) -> dict[str, Any]:
    if mode not in MODES:
        raise ValueError(f"unknown_mode:{mode}")
    cg = _create_cgroup(
        f"fr-p9-010-{os.getpid()}-{label}-{time.monotonic_ns()}",
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
    ready_memory_current = -1
    ready_memory_peak = -1
    ready_pids: list[int] = []
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
                    jobs=jobs,
                    rounds=rounds,
                )
            )

        state = _wait_ready_or_exit(ready_paths, processes)
        ready_memory_current = int((cg / "memory.current").read_text().strip())
        ready_memory_peak = int((cg / "memory.peak").read_text().strip())
        ready_pids = [int(v) for v in (cg / "cgroup.procs").read_text().split()]

        if state == "READY":
            work_start_path.write_text(str(time.monotonic_ns()))
            deadline = time.monotonic() + 60
            while time.monotonic() < deadline and any(p.poll() is None for p in processes):
                time.sleep(0.01)
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
        returncodes = [process.returncode for process in processes]

        ready_receipts: list[dict[str, Any]] = []
        for path in ready_paths:
            if path.exists():
                ready_receipts.append(json.loads(path.read_text()))

        job_rows: list[dict[str, Any]] = []
        result_receipts: list[dict[str, Any]] = []
        if all(path.exists() for path in result_paths):
            for path in result_paths:
                receipt = json.loads(path.read_text())
                result_receipts.append(receipt)
                job_rows.extend(receipt["jobs"])
            job_rows.sort(key=lambda row: row["job_id"])

        return {
            "label": label,
            "workers": workers,
            "mode": mode,
            "memory_max_bytes": memory_max_bytes,
            "state": state,
            "ready_memory_current_bytes": ready_memory_current,
            "ready_memory_peak_bytes": ready_memory_peak,
            "memory_peak_bytes": memory_peak,
            "cgroup_pids_at_ready_or_exit": ready_pids,
            "memory_events_before": before_events,
            "memory_events_after": after_events,
            "oom_delta": after_events.get("oom", 0) - before_events.get("oom", 0),
            "oom_kill_delta": after_events.get("oom_kill", 0) - before_events.get("oom_kill", 0),
            "returncodes": returncodes,
            "stderr": _collect_stderr(processes),
            "ready_receipts": ready_receipts,
            "result_receipts": result_receipts,
            "job_digests": {str(row["job_id"]): row["digest"] for row in job_rows},
        }
    finally:
        for process in processes:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)
        subprocess.run(["sudo", "rmdir", str(cg)], check=False)


def derive_overlap_quota_bytes(fault_peaks: list[int], warm_peaks: list[int]) -> int:
    if not fault_peaks or not warm_peaks:
        raise ValueError("missing_calibration_peaks")
    fault_required = max(fault_peaks)
    warm_floor = min(warm_peaks)
    gap = warm_floor - fault_required
    minimum_gap = 8 * MIB
    if gap < minimum_gap:
        raise RuntimeError(f"insufficient_overlap_separation:{gap}")
    headroom = max(2 * MIB, gap // 4)
    quota = fault_required + headroom
    if not (fault_required < quota < warm_floor):
        raise RuntimeError("invalid_overlap_quota")
    return quota


def _workspace_signature(row: dict[str, Any]) -> tuple[tuple[int, int], ...]:
    receipts = row.get("ready_receipts", [])
    return tuple(
        sorted(
            (int(receipt["worker_index"]), int(receipt["workspace_checksum"]))
            for receipt in receipts
        )
    )


def run_panel(
    *,
    payload_mib: int = 8,
    workspace_mib: int = 16,
    workers: int = 4,
    jobs: int = 12,
    rounds: int = 4,
    calibration_repetitions: int = 2,
    high_quota_mib: int = 256,
) -> dict[str, Any]:
    controllers = (Path("/sys/fs/cgroup") / "cgroup.controllers").read_text().split()
    if "memory" not in controllers:
        raise RuntimeError("memory_controller_unavailable")
    if workers < 2:
        raise ValueError("workers_must_be_at_least_two")

    with tempfile.TemporaryDirectory(prefix="fr-p9-010-overlap-") as tmp:
        root = Path(tmp)
        payload_path = root / "capability.bin"
        payload_bytes = payload_mib * MIB
        expected_digest = _write_payload(payload_path, payload_bytes)
        high_quota_bytes = high_quota_mib * MIB

        baseline_warm = [
            run_group(
                workers=workers,
                mode="KEEP_WARM",
                memory_max_bytes=high_quota_bytes,
                payload_path=payload_path,
                payload_bytes=payload_bytes,
                expected_digest=expected_digest,
                workspace_mib=workspace_mib,
                jobs=jobs,
                rounds=rounds,
                run_root=root,
                label=f"baseline-warm-r{rep}",
            )
            for rep in range(calibration_repetitions)
        ]
        baseline_fault = [
            run_group(
                workers=workers,
                mode="FAULT_IN",
                memory_max_bytes=high_quota_bytes,
                payload_path=payload_path,
                payload_bytes=payload_bytes,
                expected_digest=expected_digest,
                workspace_mib=workspace_mib,
                jobs=jobs,
                rounds=rounds,
                run_root=root,
                label=f"baseline-fault-r{rep}",
            )
            for rep in range(calibration_repetitions)
        ]

        baseline = baseline_warm + baseline_fault
        if any(row["state"] != "COMPLETED" for row in baseline):
            raise RuntimeError("high_quota_overlap_calibration_must_complete")
        baseline_digest = baseline[0]["job_digests"]
        if any(row["job_digests"] != baseline_digest for row in baseline):
            raise RuntimeError("baseline_semantics_mismatch")
        workspace_signature = _workspace_signature(baseline[0])
        if any(_workspace_signature(row) != workspace_signature for row in baseline):
            raise RuntimeError("phase_a_workspace_semantics_mismatch")

        warm_peaks = [int(row["memory_peak_bytes"]) for row in baseline_warm]
        fault_peaks = [int(row["memory_peak_bytes"]) for row in baseline_fault]
        tight_quota_bytes = derive_overlap_quota_bytes(fault_peaks, warm_peaks)

        tight_warm = run_group(
            workers=workers,
            mode="KEEP_WARM",
            memory_max_bytes=tight_quota_bytes,
            payload_path=payload_path,
            payload_bytes=payload_bytes,
            expected_digest=expected_digest,
            workspace_mib=workspace_mib,
            jobs=jobs,
            rounds=rounds,
            run_root=root,
            label="tight-warm",
        )
        tight_fault = run_group(
            workers=workers,
            mode="FAULT_IN",
            memory_max_bytes=tight_quota_bytes,
            payload_path=payload_path,
            payload_bytes=payload_bytes,
            expected_digest=expected_digest,
            workspace_mib=workspace_mib,
            jobs=jobs,
            rounds=rounds,
            run_root=root,
            label="tight-fault",
        )

    predicted_warm_feasible = min(warm_peaks) <= tight_quota_bytes
    predicted_fault_feasible = max(fault_peaks) <= tight_quota_bytes
    gap = min(warm_peaks) - max(fault_peaks)

    checks = {
        "high_quota_both_residency_modes_complete": all(row["state"] == "COMPLETED" for row in baseline),
        "high_quota_modes_preserve_job_semantics": all(row["job_digests"] == baseline_digest for row in baseline),
        "high_quota_modes_preserve_phase_a_semantics": all(_workspace_signature(row) == workspace_signature for row in baseline),
        "calibration_has_clear_phase_overlap_separation": gap >= 8 * MIB,
        "tight_quota_is_between_fault_and_warm_peaks": max(fault_peaks) < tight_quota_bytes < min(warm_peaks),
        "certificate_predicts_keep_warm_infeasible": not predicted_warm_feasible,
        "certificate_predicts_fault_in_feasible": predicted_fault_feasible,
        "tight_keep_warm_triggers_isolated_kernel_oom": tight_warm["oom_kill_delta"] > 0 and tight_warm["state"] != "COMPLETED",
        "tight_fault_in_completes_without_oom": tight_fault["state"] == "COMPLETED" and tight_fault["oom_kill_delta"] == 0,
        "fault_in_rescue_preserves_job_semantics": tight_fault["job_digests"] == baseline_digest,
        "fault_in_rescue_preserves_phase_a_semantics": _workspace_signature(tight_fault) == workspace_signature,
        "same_worker_count_and_same_kernel_quota": tight_warm["workers"] == tight_fault["workers"] == workers and tight_warm["memory_max_bytes"] == tight_fault["memory_max_bytes"] == tight_quota_bytes,
        "residency_schedule_does_not_grant_authority": True,
        "residency_schedule_does_not_grant_retry_permission": True,
    }

    return {
        "schema": SCHEMA,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "classification": "HOSTED_LINUX_CGROUP_V2_PHASE_OVERLAP_RESIDENCY_PROXY",
        "fixture": {
            "payload_mib": payload_mib,
            "workspace_mib": workspace_mib,
            "workers": workers,
            "jobs": jobs,
            "rounds": rounds,
            "calibration_repetitions": calibration_repetitions,
            "high_quota_mib": high_quota_mib,
        },
        "calibration": {
            "fault_in_peaks_bytes": fault_peaks,
            "fault_in_required_bytes": max(fault_peaks),
            "keep_warm_peaks_bytes": warm_peaks,
            "keep_warm_floor_bytes": min(warm_peaks),
            "physical_overlap_gap_bytes": gap,
        },
        "tight_quota_bytes": tight_quota_bytes,
        "baseline_keep_warm": baseline_warm,
        "baseline_fault_in": baseline_fault,
        "tight_keep_warm": tight_warm,
        "tight_fault_in": tight_fault,
        "checks": checks,
        "decision": "TREAT_PHASE_LIFETIME_OVERLAP_AS_A_PHYSICAL_RESIDENCY_VARIABLE;FAULT_IN_AFTER_RELEASE_CAN_PRESERVE_THE_SAME_CONCURRENCY_CLASS_UNDER_A_QUOTA_WHEN_KEEP_WARM_OVERLAP_CANNOT",
        "typed_objectives": [
            "kernel_memory_peak_bytes",
            "kernel_oom_events",
            "resume_ns",
            "phase_overlap",
            "job_semantics",
        ],
        "scalar_gain": None,
        "authority_effect": "NONE",
        "retry_authority": False,
        "invariants": [
            "semantic temperature != simultaneous physical residency",
            "phase-A state may be released before phase-B capability materialization when semantics permit",
            "kernel quota survival depends on lifetime overlap, not only total bytes ever used",
            "same worker count and same quota are required for the residency rescue comparison",
            "kernel OOM evidence != retry permission",
            "resource feasibility != execution authority",
        ],
        "next_falsifier": "measure the latency and coordination tax of staggered or just-in-time materialization across repeated phase transitions and test when lower peak residency loses on service objectives",
        "claim_ceiling": "HOSTED_GITHUB_LINUX_CGROUP_V2_PHASE_OVERLAP_AND_HASHING_PROXY_ONLY_NO_UNIVERSAL_RESIDENCY_POLICY_OR_APPLICATION_PERFORMANCE_CLAIM",
    }


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
    parser.add_argument("--jobs", type=int, default=12)
    parser.add_argument("--rounds", type=int, default=4)
    parser.add_argument("--payload-mib", type=int, default=8)
    parser.add_argument("--calibration-repetitions", type=int, default=2)
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
            jobs=args.jobs,
            rounds=args.rounds,
        )

    result = run_panel(
        payload_mib=args.payload_mib,
        workspace_mib=args.workspace_mib,
        workers=args.workers,
        jobs=args.jobs,
        rounds=args.rounds,
        calibration_repetitions=args.calibration_repetitions,
        high_quota_mib=args.high_quota_mib,
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
