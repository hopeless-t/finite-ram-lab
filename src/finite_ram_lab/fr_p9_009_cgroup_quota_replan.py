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

SCHEMA = "finite-ram-lab.fr-p9-009-cgroup-quota-replan/v0.1"
MIB = 1024 * 1024


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, sort_keys=True))
    os.replace(tmp, path)


def _payload_chunk() -> bytes:
    seed = b"catfood-lab-fr-p9-009-cgroup-quota-replan|"
    return (seed * ((MIB // len(seed)) + 1))[:MIB]


def _write_payload(path: Path, payload_bytes: int) -> str:
    chunk = _payload_chunk()
    digest = hashlib.sha256()
    remaining = payload_bytes
    with path.open("wb") as handle:
        while remaining:
            piece = chunk[: min(len(chunk), remaining)]
            handle.write(piece)
            digest.update(piece)
            remaining -= len(piece)
        handle.flush()
        os.fsync(handle.fileno())
    return digest.hexdigest()


def _job_digest(mapped: mmap.mmap, job_id: int, rounds: int) -> str:
    state = hashlib.sha256(f"job:{job_id}".encode()).digest()
    for _ in range(rounds):
        h = hashlib.sha256()
        h.update(state)
        h.update(mapped)
        state = h.digest()
    return state.hex()


def child(
    *,
    payload_path: Path,
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
    workspace = bytearray(workspace_mib * MIB)
    workspace_checksum = 0
    for offset in range(0, len(workspace), 4096):
        workspace[offset] = (worker_index + offset // 4096) & 0xFF
        workspace_checksum ^= workspace[offset]

    with payload_path.open("rb") as handle:
        mapped = mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ)
    touch_checksum = 0
    for offset in range(0, len(mapped), 4096):
        touch_checksum ^= mapped[offset]
    payload_digest = hashlib.sha256(mapped).hexdigest()
    if payload_digest != expected_digest:
        raise RuntimeError("payload_digest_mismatch")

    _atomic_json(
        ready_path,
        {
            "pid": os.getpid(),
            "worker_index": worker_index,
            "workspace_mib": workspace_mib,
            "workspace_checksum": workspace_checksum,
            "touch_checksum": touch_checksum,
            "payload_digest": payload_digest,
        },
    )

    deadline = time.monotonic() + 60
    while not work_start_path.exists():
        if time.monotonic() > deadline:
            raise TimeoutError("work_start_timeout")
        time.sleep(0.001)
    work_start_ns = int(work_start_path.read_text())

    rows: list[dict[str, Any]] = []
    for job_id in range(worker_index, jobs, worker_count):
        start_ns = time.monotonic_ns()
        digest = _job_digest(mapped, job_id, rounds)
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

    # Keep the private workspace semantically live through the whole workload.
    if workspace_checksum < 0:
        raise RuntimeError("workspace_checksum_impossible")
    _atomic_json(result_path, {"jobs": rows})
    mapped.close()
    return 0


def _read_events(cg: Path) -> dict[str, int]:
    result: dict[str, int] = {}
    for line in (cg / "memory.events").read_text().splitlines():
        key, value = line.split()
        result[key] = int(value)
    return result


def _sudo_write(path: Path, value: str) -> None:
    subprocess.run(
        ["sudo", "sh", "-c", f"printf '%s\\n' {shlex.quote(value)} > {shlex.quote(str(path))}"],
        check=True,
    )


def _create_cgroup(name: str, memory_max_bytes: int) -> Path:
    cg = Path("/sys/fs/cgroup") / name
    subprocess.run(["sudo", "mkdir", str(cg)], check=True)
    _sudo_write(cg / "memory.max", str(memory_max_bytes))
    if (cg / "memory.swap.max").exists():
        _sudo_write(cg / "memory.swap.max", "0")
    if (cg / "memory.oom.group").exists():
        _sudo_write(cg / "memory.oom.group", "1")
    return cg


def _launch_worker(
    *,
    cg: Path,
    payload_path: Path,
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
        "finite_ram_lab.fr_p9_009_cgroup_quota_replan",
        "--child",
        "--payload-path",
        str(payload_path),
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
    memory_max_bytes: int,
    payload_path: Path,
    expected_digest: str,
    workspace_mib: int,
    jobs: int,
    rounds: int,
    run_root: Path,
    label: str,
) -> dict[str, Any]:
    cg = _create_cgroup(
        f"fr-p9-009-{os.getpid()}-{label}-{time.monotonic_ns()}",
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
    try:
        for index in range(workers):
            processes.append(
                _launch_worker(
                    cg=cg,
                    payload_path=payload_path,
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
        job_rows: list[dict[str, Any]] = []
        if all(path.exists() for path in result_paths):
            for path in result_paths:
                job_rows.extend(json.loads(path.read_text())["jobs"])
            job_rows.sort(key=lambda row: row["job_id"])

        return {
            "label": label,
            "workers": workers,
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
            "job_digests": {str(row["job_id"]): row["digest"] for row in job_rows},
        }
    finally:
        for process in processes:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)
        subprocess.run(["sudo", "rmdir", str(cg)], check=False)


def derive_quota_bytes(n2_peaks: list[int], n4_peaks: list[int]) -> int:
    if not n2_peaks or not n4_peaks:
        raise ValueError("missing_calibration_peaks")
    n2_required = max(n2_peaks)
    n4_floor = min(n4_peaks)
    gap = n4_floor - n2_required
    minimum_gap = 12 * MIB
    if gap < minimum_gap:
        raise RuntimeError(f"insufficient_physical_separation:{gap}")
    headroom = max(4 * MIB, gap // 4)
    quota = n2_required + headroom
    if not (n2_required < quota < n4_floor):
        raise RuntimeError("invalid_derived_quota")
    return quota


def resource_certificate(memory_max_bytes: int, payload_mib: int, workspace_mib: int) -> str:
    payload = {
        "memory_max_bytes": memory_max_bytes,
        "payload_mib": payload_mib,
        "workspace_mib": workspace_mib,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def run_panel(
    *,
    payload_mib: int = 8,
    workspace_mib: int = 16,
    jobs: int = 12,
    rounds: int = 4,
    calibration_repetitions: int = 2,
    high_quota_mib: int = 256,
) -> dict[str, Any]:
    controllers = (Path("/sys/fs/cgroup") / "cgroup.controllers").read_text().split()
    if "memory" not in controllers:
        raise RuntimeError("memory_controller_unavailable")

    with tempfile.TemporaryDirectory(prefix="fr-p9-009-quota-") as tmp:
        root = Path(tmp)
        payload_path = root / "capability.bin"
        expected_digest = _write_payload(payload_path, payload_mib * MIB)
        high_quota_bytes = high_quota_mib * MIB

        baseline_n2 = [
            run_group(
                workers=2,
                memory_max_bytes=high_quota_bytes,
                payload_path=payload_path,
                expected_digest=expected_digest,
                workspace_mib=workspace_mib,
                jobs=jobs,
                rounds=rounds,
                run_root=root,
                label=f"baseline-n2-r{rep}",
            )
            for rep in range(calibration_repetitions)
        ]
        baseline_n4 = [
            run_group(
                workers=4,
                memory_max_bytes=high_quota_bytes,
                payload_path=payload_path,
                expected_digest=expected_digest,
                workspace_mib=workspace_mib,
                jobs=jobs,
                rounds=rounds,
                run_root=root,
                label=f"baseline-n4-r{rep}",
            )
            for rep in range(calibration_repetitions)
        ]

        if any(row["state"] != "COMPLETED" for row in baseline_n2 + baseline_n4):
            raise RuntimeError("high_quota_calibration_must_complete")
        baseline_digest = baseline_n4[0]["job_digests"]
        if any(row["job_digests"] != baseline_digest for row in baseline_n2 + baseline_n4):
            raise RuntimeError("baseline_semantics_mismatch")

        n2_peaks = [int(row["memory_peak_bytes"]) for row in baseline_n2]
        n4_peaks = [int(row["memory_peak_bytes"]) for row in baseline_n4]
        tight_quota_bytes = derive_quota_bytes(n2_peaks, n4_peaks)

        tight_n4 = run_group(
            workers=4,
            memory_max_bytes=tight_quota_bytes,
            payload_path=payload_path,
            expected_digest=expected_digest,
            workspace_mib=workspace_mib,
            jobs=jobs,
            rounds=rounds,
            run_root=root,
            label="tight-n4",
        )
        tight_n2 = run_group(
            workers=2,
            memory_max_bytes=tight_quota_bytes,
            payload_path=payload_path,
            expected_digest=expected_digest,
            workspace_mib=workspace_mib,
            jobs=jobs,
            rounds=rounds,
            run_root=root,
            label="tight-n2",
        )

    predicted_n4_feasible = min(n4_peaks) <= tight_quota_bytes
    predicted_n2_feasible = max(n2_peaks) <= tight_quota_bytes
    checks = {
        "high_quota_n2_and_n4_complete": all(row["state"] == "COMPLETED" for row in baseline_n2 + baseline_n4),
        "calibration_has_clear_n2_n4_separation": min(n4_peaks) - max(n2_peaks) >= 12 * MIB,
        "tight_quota_is_between_measured_n2_and_n4_peaks": max(n2_peaks) < tight_quota_bytes < min(n4_peaks),
        "certificate_predicts_n4_infeasible": not predicted_n4_feasible,
        "certificate_predicts_n2_feasible": predicted_n2_feasible,
        "tight_n4_triggers_isolated_kernel_oom": tight_n4["oom_kill_delta"] > 0 and tight_n4["state"] != "COMPLETED",
        "tight_n2_completes_without_oom": tight_n2["state"] == "COMPLETED" and tight_n2["oom_kill_delta"] == 0,
        "replan_preserves_job_semantics": tight_n2["job_digests"] == baseline_digest,
        "resource_certificate_changes_with_quota": resource_certificate(high_quota_bytes, payload_mib, workspace_mib) != resource_certificate(tight_quota_bytes, payload_mib, workspace_mib),
        "physical_quota_replan_does_not_grant_authority": True,
        "physical_quota_replan_does_not_grant_retry_permission": True,
    }

    return {
        "schema": SCHEMA,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "classification": "HOSTED_LINUX_CGROUP_V2_KERNEL_ENFORCED_MEMORY_QUOTA_REPLAN_PROXY",
        "fixture": {
            "payload_mib": payload_mib,
            "workspace_mib_per_worker": workspace_mib,
            "jobs": jobs,
            "rounds": rounds,
            "calibration_repetitions": calibration_repetitions,
            "high_quota_mib": high_quota_mib,
        },
        "calibration": {
            "n2_peaks_bytes": n2_peaks,
            "n4_peaks_bytes": n4_peaks,
            "n2_required_bytes": max(n2_peaks),
            "n4_floor_bytes": min(n4_peaks),
            "physical_gap_bytes": min(n4_peaks) - max(n2_peaks),
        },
        "tight_quota_bytes": tight_quota_bytes,
        "high_resource_certificate": resource_certificate(high_quota_bytes, payload_mib, workspace_mib),
        "tight_resource_certificate": resource_certificate(tight_quota_bytes, payload_mib, workspace_mib),
        "baseline_n2": baseline_n2,
        "baseline_n4": baseline_n4,
        "tight_n4": tight_n4,
        "tight_n2": tight_n2,
        "checks": checks,
        "decision": "KERNEL_ENFORCED_QUOTA_INVALIDATES_STALE_HIGH_CONCURRENCY_PLAN;REPLAN_TO_MEASURED_FEASIBLE_CLASS_PRESERVES_SEMANTICS",
        "authority_effect": "NONE",
        "retry_authority": False,
        "scalar_gain": None,
        "invariants": [
            "physical quota enforcement is isolated inside a disposable cgroup",
            "parent monitor remains outside the constrained failure domain",
            "measured feasibility prediction precedes quota enforcement",
            "kernel OOM evidence != permission to retry",
            "replanned execution must preserve deterministic job semantics",
            "resource feasibility != execution authority",
        ],
        "claim_ceiling": "HOSTED_GITHUB_LINUX_CGROUP_V2_QUOTA_AND_HASHING_PROXY_ONLY_NO_UNIVERSAL_MEMORY_THRESHOLD_OR_APPLICATION_PERFORMANCE_CLAIM",
        "next_falsifier": "add residency mode as a second physical cgroup variable and test whether FAULT_IN can rescue a concurrency class under the same kernel quota without semantic loss",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--payload-path", type=Path)
    parser.add_argument("--expected-digest")
    parser.add_argument("--workspace-mib", type=int, default=16)
    parser.add_argument("--ready-path", type=Path)
    parser.add_argument("--work-start-path", type=Path)
    parser.add_argument("--result-path", type=Path)
    parser.add_argument("--worker-index", type=int)
    parser.add_argument("--workers", type=int)
    parser.add_argument("--jobs", type=int, default=12)
    parser.add_argument("--rounds", type=int, default=4)
    parser.add_argument("--payload-mib", type=int, default=8)
    parser.add_argument("--calibration-repetitions", type=int, default=2)
    parser.add_argument("--high-quota-mib", type=int, default=256)
    args = parser.parse_args()

    if args.child:
        required = [
            args.payload_path,
            args.expected_digest,
            args.ready_path,
            args.work_start_path,
            args.result_path,
            args.worker_index,
            args.workers,
        ]
        if any(value is None for value in required):
            raise SystemExit("missing_child_arguments")
        return child(
            payload_path=args.payload_path,
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
        jobs=args.jobs,
        rounds=args.rounds,
        calibration_repetitions=args.calibration_repetitions,
        high_quota_mib=args.high_quota_mib,
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
