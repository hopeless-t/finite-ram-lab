from __future__ import annotations

import argparse
import hashlib
import json
import math
import mmap
import os
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

SCHEMA = "finite-ram-lab.fr-p9-007-hosted-joint-frontier/v0.1"


def _payload_chunk() -> bytes:
    seed = b"catfood-lab-fr-p9-007-hosted-joint-frontier|"
    return (seed * ((1024 * 1024 // len(seed)) + 1))[: 1024 * 1024]


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


def _publish_text_atomic(path: Path, content: str) -> None:
    """Publish a barrier/receipt only after its content is complete.

    The first hosted attempt exposed a TOCTOU race: `Path.exists()` can become
    true after `write_text()` creates the file but before the JSON/timestamp is
    fully visible to another process. Publish through a sibling temporary file
    and `os.replace()` so existence means complete content.
    """

    tmp = path.with_name(
        f".{path.name}.{os.getpid()}.{time.monotonic_ns()}.tmp"
    )
    tmp.write_text(content)
    os.replace(tmp, path)


def _publish_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    _publish_text_atomic(path, json.dumps(payload, sort_keys=True))


def _read_pss_kib(pid: int) -> int:
    for line in Path(f"/proc/{pid}/smaps_rollup").read_text().splitlines():
        if line.startswith("Pss:"):
            return int(line.split()[1])
    raise RuntimeError(f"pss_not_found:{pid}")


def _percentile(values: list[int], q: float) -> int:
    if not values:
        raise ValueError("empty_values")
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil(q * len(ordered)) - 1))
    return int(ordered[index])


def _map_touch_verify(path: Path) -> tuple[mmap.mmap, str, int]:
    start_ns = time.monotonic_ns()
    with path.open("rb") as handle:
        mapped = mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ)
    checksum = 0
    for offset in range(0, len(mapped), 4096):
        checksum ^= mapped[offset]
    digest = hashlib.sha256(mapped).hexdigest()
    elapsed_ns = time.monotonic_ns() - start_ns
    if checksum < 0:  # impossible, keeps the touch result live
        raise RuntimeError("touch_checksum_invalid")
    return mapped, digest, elapsed_ns


def _job_digest(mapped: mmap.mmap, job_id: int, rounds: int) -> str:
    state = hashlib.sha256(f"job:{job_id}".encode()).digest()
    for _ in range(rounds):
        h = hashlib.sha256()
        h.update(state)
        h.update(mapped)
        state = h.digest()
    return state.hex()


def _child(
    *,
    mode: str,
    payload_path: Path,
    expected_digest: str,
    ready_path: Path,
    load_start_path: Path,
    loaded_path: Path,
    work_start_path: Path,
    result_path: Path,
    worker_index: int,
    worker_count: int,
    jobs: int,
    rounds: int,
) -> int:
    mapped: mmap.mmap | None = None
    prepare_ns = 0
    capability_digest: str | None = None

    if mode == "KEEP_WARM":
        mapped, capability_digest, prepare_ns = _map_touch_verify(payload_path)
        if capability_digest != expected_digest:
            raise RuntimeError("keep_warm_prepare_digest_mismatch")
    elif mode != "FAULT_IN":
        raise ValueError(f"unknown_mode:{mode}")

    _publish_json_atomic(
        ready_path,
        {
            "pid": os.getpid(),
            "mode": mode,
            "prepare_ns": prepare_ns,
            "capability_digest": capability_digest,
        },
    )

    while not load_start_path.exists():
        time.sleep(0.001)
    load_start_ns = int(load_start_path.read_text())

    if mode == "FAULT_IN":
        mapped, capability_digest, resume_ns = _map_touch_verify(payload_path)
        if capability_digest != expected_digest:
            raise RuntimeError("fault_in_digest_mismatch")
    else:
        resume_ns = 0

    assert mapped is not None
    _publish_json_atomic(
        loaded_path,
        {
            "pid": os.getpid(),
            "mode": mode,
            "resume_ns": resume_ns,
            "loaded_at_ns": time.monotonic_ns(),
            "load_start_ns": load_start_ns,
            "capability_digest": capability_digest,
        },
    )

    while not work_start_path.exists():
        time.sleep(0.001)
    work_start_ns = int(work_start_path.read_text())

    job_rows: list[dict[str, Any]] = []
    for job_id in range(worker_index, jobs, worker_count):
        start_ns = time.monotonic_ns()
        digest = _job_digest(mapped, job_id, rounds)
        end_ns = time.monotonic_ns()
        job_rows.append(
            {
                "job_id": job_id,
                "start_ns": start_ns,
                "end_ns": end_ns,
                "queue_wait_ns": start_ns - work_start_ns,
                "service_ns": end_ns - start_ns,
                "sojourn_ns": end_ns - work_start_ns,
                "digest": digest,
            }
        )

    _publish_json_atomic(result_path, {"jobs": job_rows})
    mapped.close()
    return 0


def _wait_paths(
    paths: list[Path],
    processes: list[subprocess.Popen[str]],
    *,
    timeout: float = 30.0,
) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if all(path.exists() for path in paths):
            return
        for process in processes:
            if process.poll() is not None:
                stderr = process.stderr.read() if process.stderr is not None else ""
                raise RuntimeError(f"child_exited_early:{process.returncode}:{stderr}")
        time.sleep(0.01)
    raise TimeoutError("child_barrier_timeout")


def _run_arm(
    *,
    mode: str,
    workers: int,
    payload_path: Path,
    expected_digest: str,
    payload_bytes: int,
    jobs: int,
    rounds: int,
    idle_gap_seconds: float,
    run_dir: Path,
) -> dict[str, Any]:
    ready_paths = [run_dir / f"ready-{i}.json" for i in range(workers)]
    loaded_paths = [run_dir / f"loaded-{i}.json" for i in range(workers)]
    result_paths = [run_dir / f"result-{i}.json" for i in range(workers)]
    load_start_path = run_dir / "load-start.ns"
    work_start_path = run_dir / "work-start.ns"

    processes: list[subprocess.Popen[str]] = []
    try:
        for index in range(workers):
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "finite_ram_lab.fr_p9_007_hosted_joint_frontier",
                    "--child",
                    "--mode",
                    mode,
                    "--payload-path",
                    str(payload_path),
                    "--expected-digest",
                    expected_digest,
                    "--ready-path",
                    str(ready_paths[index]),
                    "--load-start-path",
                    str(load_start_path),
                    "--loaded-path",
                    str(loaded_paths[index]),
                    "--work-start-path",
                    str(work_start_path),
                    "--result-path",
                    str(result_paths[index]),
                    "--worker-index",
                    str(index),
                    "--workers",
                    str(workers),
                    "--jobs",
                    str(jobs),
                    "--rounds",
                    str(rounds),
                ],
                text=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
            processes.append(process)

        _wait_paths(ready_paths, processes)
        ready = [json.loads(path.read_text()) for path in ready_paths]
        prestart_pss_kib = sum(_read_pss_kib(int(row["pid"])) for row in ready)

        idle_begin_ns = time.monotonic_ns()
        time.sleep(idle_gap_seconds)
        load_start_ns = time.monotonic_ns()
        idle_elapsed_ns = load_start_ns - idle_begin_ns
        _publish_text_atomic(load_start_path, str(load_start_ns))

        _wait_paths(loaded_paths, processes)
        loaded = [json.loads(path.read_text()) for path in loaded_paths]
        active_pss_kib = sum(_read_pss_kib(int(row["pid"])) for row in loaded)
        joint_resume_ns = max(int(row["loaded_at_ns"]) for row in loaded) - load_start_ns
        child_resume_ns = max(int(row["resume_ns"]) for row in loaded)

        work_start_ns = time.monotonic_ns()
        _publish_text_atomic(work_start_path, str(work_start_ns))

        for process in processes:
            process.wait(timeout=120)
            if process.returncode != 0:
                stderr = process.stderr.read() if process.stderr is not None else ""
                raise RuntimeError(f"child_failed:{process.returncode}:{stderr}")

        job_rows: list[dict[str, Any]] = []
        for path in result_paths:
            job_rows.extend(json.loads(path.read_text())["jobs"])
        job_rows.sort(key=lambda row: row["job_id"])
        if [row["job_id"] for row in job_rows] != list(range(jobs)):
            raise RuntimeError("job_identity_mismatch")

        work_end_ns = max(int(row["end_ns"]) for row in job_rows)
        queue = [int(row["queue_wait_ns"]) for row in job_rows]
        service = [int(row["service_ns"]) for row in job_rows]
        sojourn = [int(row["sojourn_ns"]) for row in job_rows]

        return {
            "mode": mode,
            "workers": workers,
            "prestart_pss_kib": prestart_pss_kib,
            "active_pss_kib": active_pss_kib,
            "joint_resume_ns": joint_resume_ns,
            "max_child_resume_ns": child_resume_ns,
            "work_wall_ns": work_end_ns - work_start_ns,
            "p95_queue_wait_ns": _percentile(queue, 0.95),
            "p95_service_ns": _percentile(service, 0.95),
            "p95_sojourn_ns": _percentile(sojourn, 0.95),
            "logical_fault_span_bytes": 0 if mode == "KEEP_WARM" else payload_bytes * workers,
            "idle_capability_byte_seconds": (
                payload_bytes * (idle_elapsed_ns / 1_000_000_000)
                if mode == "KEEP_WARM"
                else 0.0
            ),
            "idle_elapsed_ns": idle_elapsed_ns,
            "capability_digests": [row["capability_digest"] for row in loaded],
            "job_digests": {str(row["job_id"]): row["digest"] for row in job_rows},
        }
    finally:
        for process in processes:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)


def _median_int(values: list[int]) -> int:
    return int(statistics.median(values))


def _summarize(rows: list[dict[str, Any]], *, mode: str, workers: int) -> dict[str, Any]:
    selected = [row for row in rows if row["mode"] == mode and row["workers"] == workers]
    if not selected:
        raise ValueError(f"missing_arm:{mode}:{workers}")
    job_maps = [row["job_digests"] for row in selected]
    capability_sets = [tuple(row["capability_digests"]) for row in selected]
    return {
        "mode": mode,
        "workers": workers,
        "repetitions": len(selected),
        "median_prestart_pss_kib": _median_int([int(row["prestart_pss_kib"]) for row in selected]),
        "median_active_pss_kib": _median_int([int(row["active_pss_kib"]) for row in selected]),
        "median_joint_resume_ns": _median_int([int(row["joint_resume_ns"]) for row in selected]),
        "median_max_child_resume_ns": _median_int([int(row["max_child_resume_ns"]) for row in selected]),
        "median_work_wall_ns": _median_int([int(row["work_wall_ns"]) for row in selected]),
        "median_p95_queue_wait_ns": _median_int([int(row["p95_queue_wait_ns"]) for row in selected]),
        "median_p95_service_ns": _median_int([int(row["p95_service_ns"]) for row in selected]),
        "median_p95_sojourn_ns": _median_int([int(row["p95_sojourn_ns"]) for row in selected]),
        "logical_fault_span_bytes": int(selected[0]["logical_fault_span_bytes"]),
        "median_idle_capability_byte_seconds": statistics.median(
            float(row["idle_capability_byte_seconds"]) for row in selected
        ),
        "job_digests_stable": all(item == job_maps[0] for item in job_maps[1:]),
        "capability_digests_stable": all(item == capability_sets[0] for item in capability_sets[1:]),
        "job_digests": job_maps[0],
    }


def _dominates(a: dict[str, Any], b: dict[str, Any]) -> bool:
    fields = (
        "median_prestart_pss_kib",
        "median_active_pss_kib",
        "median_joint_resume_ns",
        "median_work_wall_ns",
        "median_p95_sojourn_ns",
        "logical_fault_span_bytes",
        "median_idle_capability_byte_seconds",
    )
    no_worse = all(float(a[field]) <= float(b[field]) for field in fields)
    strict = any(float(a[field]) < float(b[field]) for field in fields)
    return no_worse and strict


def _pareto_ids(summaries: list[dict[str, Any]]) -> list[str]:
    frontier = []
    for candidate in summaries:
        if not any(other is not candidate and _dominates(other, candidate) for other in summaries):
            frontier.append(f"N{candidate['workers']}:{candidate['mode']}")
    return sorted(frontier)


def run_hosted_proxy(
    *,
    payload_bytes: int = 8 * 1024 * 1024,
    worker_counts: tuple[int, ...] = (1, 2, 4),
    jobs: int = 12,
    rounds: int = 6,
    repetitions: int = 2,
    idle_gap_seconds: float = 0.20,
) -> dict[str, Any]:
    if repetitions < 2:
        raise ValueError("repetitions_must_be_at_least_two")
    if idle_gap_seconds <= 0:
        raise ValueError("idle_gap_must_be_positive")
    if jobs < max(worker_counts):
        raise ValueError("jobs_must_cover_workers")

    with tempfile.TemporaryDirectory(prefix="fr-p9-007-") as tmp:
        root = Path(tmp)
        payload_path = root / "capability.bin"
        expected_digest = _write_payload(payload_path, payload_bytes)
        rows: list[dict[str, Any]] = []

        combos = [(mode, workers) for workers in worker_counts for mode in ("KEEP_WARM", "FAULT_IN")]
        orders = (combos, tuple(reversed(combos)))
        for repetition in range(repetitions):
            for mode, workers in orders[repetition % len(orders)]:
                run_dir = root / f"r{repetition}-{mode}-w{workers}"
                run_dir.mkdir()
                row = _run_arm(
                    mode=mode,
                    workers=workers,
                    payload_path=payload_path,
                    expected_digest=expected_digest,
                    payload_bytes=payload_bytes,
                    jobs=jobs,
                    rounds=rounds,
                    idle_gap_seconds=idle_gap_seconds,
                    run_dir=run_dir,
                )
                row["repetition"] = repetition
                rows.append(row)

    summaries = [
        _summarize(rows, mode=mode, workers=workers)
        for workers in worker_counts
        for mode in ("KEEP_WARM", "FAULT_IN")
    ]
    reference_jobs = summaries[0]["job_digests"]
    semantic_jobs_equal = all(summary["job_digests"] == reference_jobs for summary in summaries[1:])
    prestart_pairs = {
        workers: {
            summary["mode"]: summary
            for summary in summaries
            if summary["workers"] == workers
        }
        for workers in worker_counts
    }
    frontier = _pareto_ids(summaries)

    checks = {
        "all_capability_digests_stable": all(summary["capability_digests_stable"] for summary in summaries),
        "all_job_digests_stable_within_arm": all(summary["job_digests_stable"] for summary in summaries),
        "job_semantics_equal_across_all_six_arms": semantic_jobs_equal,
        "fault_in_prestart_pss_lower_than_keep_warm_for_each_worker_count": all(
            prestart_pairs[workers]["FAULT_IN"]["median_prestart_pss_kib"]
            < prestart_pairs[workers]["KEEP_WARM"]["median_prestart_pss_kib"]
            for workers in worker_counts
        ),
        "keep_warm_has_zero_logical_fault_span": all(
            summary["logical_fault_span_bytes"] == 0
            for summary in summaries
            if summary["mode"] == "KEEP_WARM"
        ),
        "fault_in_has_positive_logical_fault_span": all(
            summary["logical_fault_span_bytes"] > 0
            for summary in summaries
            if summary["mode"] == "FAULT_IN"
        ),
        "fault_in_has_positive_resume_cost": all(
            summary["median_max_child_resume_ns"] > 0
            for summary in summaries
            if summary["mode"] == "FAULT_IN"
        ),
        "keep_warm_pays_positive_idle_byte_seconds": all(
            summary["median_idle_capability_byte_seconds"] > 0
            for summary in summaries
            if summary["mode"] == "KEEP_WARM"
        ),
        "typed_frontier_nonempty": bool(frontier),
        "no_predeclared_joint_winner": True,
        "no_scalar_gain_without_external_price": True,
    }

    return {
        "schema": SCHEMA,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "classification": "HOSTED_SAME_SURFACE_JOINT_RESIDENCY_CONCURRENCY_PROXY",
        "probe": {
            "payload_bytes": payload_bytes,
            "expected_digest": expected_digest,
            "worker_counts": list(worker_counts),
            "modes": ["KEEP_WARM", "FAULT_IN"],
            "jobs": jobs,
            "rounds": rounds,
            "repetitions": repetitions,
            "idle_gap_seconds_target": idle_gap_seconds,
            "memory_metric": "sum of worker PSS from /proc/<pid>/smaps_rollup",
            "fault_span_boundary": "logical mapped/touched span only; not device transfer bytes",
        },
        "summaries": summaries,
        "pareto_plan_ids": frontier,
        "checks": checks,
        "typed_objectives": [
            "prestart_pss_kib",
            "active_pss_kib",
            "resume_ns",
            "work_wall_ns",
            "p95_sojourn_ns",
            "logical_fault_span_bytes",
            "idle_capability_byte_seconds",
        ],
        "decision": (
            "PLAN_RESIDENCY_AND_CONCURRENCY_ON_ONE_MEASURED_SURFACE;DO_NOT_IMPORT_CROSS_PROXY_OPTIMA_AS_IF_PHYSICALLY_COMPOSABLE"
        ),
        "scalar_gain": None,
        "authority_effect": "NONE",
        "invariants": [
            "same-surface measurement precedes physical joint optimization",
            "warm trades idle residency for lower fault/resume work",
            "fault-in trades lower idle residency for load/resume work",
            "logical fault span != physical device traffic",
            "resource-optimal joint plan != execution authority",
        ],
        "next_falsifier": (
            "introduce an explicit finite PSS admission cap and test online joint replanning when the measured resource certificate changes between idle and work phases"
        ),
        "claim_ceiling": (
            "HOSTED_GITHUB_LINUX_SAME_SURFACE_PSS_AND_LATENCY_PROXY_ONLY_NO_UNIVERSAL_JOINT_POLICY_OR_DEVICE_IO_CLAIM"
        ),
    }


def run_synthetic_panel() -> dict[str, Any]:
    summaries = [
        {
            "mode": "KEEP_WARM",
            "workers": 1,
            "median_prestart_pss_kib": 20,
            "median_active_pss_kib": 20,
            "median_joint_resume_ns": 1,
            "median_work_wall_ns": 100,
            "median_p95_sojourn_ns": 100,
            "logical_fault_span_bytes": 0,
            "median_idle_capability_byte_seconds": 8.0,
        },
        {
            "mode": "FAULT_IN",
            "workers": 1,
            "median_prestart_pss_kib": 10,
            "median_active_pss_kib": 20,
            "median_joint_resume_ns": 10,
            "median_work_wall_ns": 100,
            "median_p95_sojourn_ns": 100,
            "logical_fault_span_bytes": 8,
            "median_idle_capability_byte_seconds": 0.0,
        },
    ]
    frontier = _pareto_ids(summaries)
    checks = {
        "warm_and_fault_both_survive": frontier == ["N1:FAULT_IN", "N1:KEEP_WARM"],
        "no_scalar_gain": True,
    }
    return {
        "schema": SCHEMA,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "classification": "SYNTHETIC_SAME_SURFACE_JOINT_FRONTIER",
        "pareto_plan_ids": frontier,
        "checks": checks,
        "scalar_gain": None,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--physical", action="store_true")
    parser.add_argument("--payload-mib", type=int, default=8)
    parser.add_argument("--jobs", type=int, default=12)
    parser.add_argument("--rounds", type=int, default=6)
    parser.add_argument("--repetitions", type=int, default=2)
    parser.add_argument("--idle-gap-seconds", type=float, default=0.20)
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--mode")
    parser.add_argument("--payload-path")
    parser.add_argument("--expected-digest")
    parser.add_argument("--ready-path")
    parser.add_argument("--load-start-path")
    parser.add_argument("--loaded-path")
    parser.add_argument("--work-start-path")
    parser.add_argument("--result-path")
    parser.add_argument("--worker-index", type=int, default=0)
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()

    if args.child:
        required = (
            args.mode,
            args.payload_path,
            args.expected_digest,
            args.ready_path,
            args.load_start_path,
            args.loaded_path,
            args.work_start_path,
            args.result_path,
        )
        if not all(required):
            raise SystemExit("child arguments missing")
        return _child(
            mode=args.mode,
            payload_path=Path(args.payload_path),
            expected_digest=args.expected_digest,
            ready_path=Path(args.ready_path),
            load_start_path=Path(args.load_start_path),
            loaded_path=Path(args.loaded_path),
            work_start_path=Path(args.work_start_path),
            result_path=Path(args.result_path),
            worker_index=args.worker_index,
            worker_count=args.workers,
            jobs=args.jobs,
            rounds=args.rounds,
        )

    result = (
        run_hosted_proxy(
            payload_bytes=args.payload_mib * 1024 * 1024,
            jobs=args.jobs,
            rounds=args.rounds,
            repetitions=args.repetitions,
            idle_gap_seconds=args.idle_gap_seconds,
        )
        if args.physical
        else run_synthetic_panel()
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
