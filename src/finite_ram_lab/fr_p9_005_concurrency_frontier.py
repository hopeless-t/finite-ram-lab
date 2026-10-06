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

SCHEMA = "finite-ram-lab.fr-p9-005-concurrency-frontier/v0.1"


def _payload_chunk() -> bytes:
    seed = b"catfood-lab-fr-p9-005-concurrency-frontier|"
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


def _job_digest(mapped: mmap.mmap, job_id: int, rounds: int) -> str:
    state = hashlib.sha256(f"job:{job_id}".encode()).digest()
    for _ in range(rounds):
        h = hashlib.sha256()
        h.update(state)
        h.update(mapped)
        state = h.digest()
    return state.hex()


def _child(
    payload_path: Path,
    ready_path: Path,
    start_path: Path,
    result_path: Path,
    *,
    worker_index: int,
    worker_count: int,
    jobs: int,
    rounds: int,
) -> int:
    with payload_path.open("rb") as handle:
        mapped = mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ)

    # Fault pages before the start barrier so the experiment is primarily about
    # useful concurrent work and residual worker/process residency, not cold load.
    touch_checksum = 0
    for index in range(0, len(mapped), 4096):
        touch_checksum ^= mapped[index]

    ready_path.write_text(
        json.dumps(
            {
                "pid": os.getpid(),
                "worker_index": worker_index,
                "worker_count": worker_count,
                "touch_checksum": touch_checksum,
            },
            sort_keys=True,
        )
    )

    while not start_path.exists():
        time.sleep(0.001)
    t0_ns = int(start_path.read_text())

    rows: list[dict[str, Any]] = []
    for job_id in range(worker_index, jobs, worker_count):
        start_ns = time.monotonic_ns()
        digest = _job_digest(mapped, job_id, rounds)
        end_ns = time.monotonic_ns()
        rows.append(
            {
                "job_id": job_id,
                "start_ns": start_ns,
                "end_ns": end_ns,
                "queue_wait_ns": start_ns - t0_ns,
                "service_ns": end_ns - start_ns,
                "sojourn_ns": end_ns - t0_ns,
                "digest": digest,
            }
        )

    result_path.write_text(json.dumps({"jobs": rows}, sort_keys=True))
    mapped.close()
    return 0


def _wait_ready(paths: list[Path], processes: list[subprocess.Popen[str]], timeout: float = 20.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if all(path.exists() for path in paths):
            return
        for process in processes:
            if process.poll() is not None:
                stderr = process.stderr.read() if process.stderr is not None else ""
                raise RuntimeError(f"child_exited_early:{process.returncode}:{stderr}")
        time.sleep(0.01)
    raise TimeoutError("child_ready_timeout")


def _run_once(
    *,
    payload_path: Path,
    workers: int,
    jobs: int,
    rounds: int,
    run_dir: Path,
) -> dict[str, Any]:
    ready_paths = [run_dir / f"ready-{index}.json" for index in range(workers)]
    result_paths = [run_dir / f"result-{index}.json" for index in range(workers)]
    start_path = run_dir / "start.ns"

    processes: list[subprocess.Popen[str]] = []
    try:
        for index in range(workers):
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "finite_ram_lab.fr_p9_005_concurrency_frontier",
                    "--child",
                    "--payload-path",
                    str(payload_path),
                    "--ready-path",
                    str(ready_paths[index]),
                    "--start-path",
                    str(start_path),
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

        _wait_ready(ready_paths, processes)
        time.sleep(0.05)
        pss_kib = sum(_read_pss_kib(int(json.loads(path.read_text())["pid"])) for path in ready_paths)

        t0_ns = time.monotonic_ns()
        start_path.write_text(str(t0_ns))

        for process in processes:
            process.wait(timeout=120)
            if process.returncode != 0:
                stderr = process.stderr.read() if process.stderr is not None else ""
                raise RuntimeError(f"child_failed:{process.returncode}:{stderr}")

        job_rows: list[dict[str, Any]] = []
        for path in result_paths:
            job_rows.extend(json.loads(path.read_text())["jobs"])
        job_rows.sort(key=lambda row: row["job_id"])

        if len(job_rows) != jobs:
            raise RuntimeError(f"job_count_mismatch:{len(job_rows)}:{jobs}")
        if [row["job_id"] for row in job_rows] != list(range(jobs)):
            raise RuntimeError("job_identity_mismatch")

        end_ns = max(int(row["end_ns"]) for row in job_rows)
        wall_ns = end_ns - t0_ns
        queue_waits = [int(row["queue_wait_ns"]) for row in job_rows]
        services = [int(row["service_ns"]) for row in job_rows]
        sojourns = [int(row["sojourn_ns"]) for row in job_rows]

        return {
            "workers": workers,
            "jobs": jobs,
            "rounds": rounds,
            "total_pss_kib": pss_kib,
            "wall_ns": wall_ns,
            "jobs_per_second": jobs / (wall_ns / 1_000_000_000),
            "p95_queue_wait_ns": _percentile(queue_waits, 0.95),
            "p95_service_ns": _percentile(services, 0.95),
            "p95_sojourn_ns": _percentile(sojourns, 0.95),
            "digests": {str(row["job_id"]): row["digest"] for row in job_rows},
        }
    finally:
        for process in processes:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)


def _median_int(values: list[int]) -> int:
    return int(statistics.median(values))


def summarize_runs(rows: list[dict[str, Any]], workers: int) -> dict[str, Any]:
    selected = [row for row in rows if row["workers"] == workers]
    if not selected:
        raise ValueError(f"missing_worker_count:{workers}")
    digest_maps = [row["digests"] for row in selected]
    semantic_stable = all(item == digest_maps[0] for item in digest_maps[1:])
    return {
        "workers": workers,
        "repetitions": len(selected),
        "median_total_pss_kib": _median_int([int(row["total_pss_kib"]) for row in selected]),
        "median_wall_ns": _median_int([int(row["wall_ns"]) for row in selected]),
        "median_jobs_per_second": statistics.median(float(row["jobs_per_second"]) for row in selected),
        "median_p95_queue_wait_ns": _median_int([int(row["p95_queue_wait_ns"]) for row in selected]),
        "median_p95_service_ns": _median_int([int(row["p95_service_ns"]) for row in selected]),
        "median_p95_sojourn_ns": _median_int([int(row["p95_sojourn_ns"]) for row in selected]),
        "semantic_stable_within_worker_count": semantic_stable,
        "digests": digest_maps[0],
    }


def _dominates(a: dict[str, Any], b: dict[str, Any]) -> bool:
    fields = (
        "median_total_pss_kib",
        "median_wall_ns",
        "median_p95_queue_wait_ns",
        "median_p95_service_ns",
        "median_p95_sojourn_ns",
    )
    no_worse = all(float(a[field]) <= float(b[field]) for field in fields)
    strictly_better = any(float(a[field]) < float(b[field]) for field in fields)
    return no_worse and strictly_better


def pareto_workers(summaries: list[dict[str, Any]]) -> list[int]:
    frontier: list[int] = []
    for candidate in summaries:
        if not any(
            _dominates(other, candidate)
            for other in summaries
            if other["workers"] != candidate["workers"]
        ):
            frontier.append(int(candidate["workers"]))
    return sorted(frontier)


def run_hosted_proxy(
    *,
    payload_bytes: int = 4 * 1024 * 1024,
    worker_counts: tuple[int, ...] = (1, 2, 4),
    jobs: int = 12,
    rounds: int = 8,
    repetitions: int = 2,
) -> dict[str, Any]:
    if repetitions < 2:
        raise ValueError("repetitions_must_be_at_least_two")
    if jobs < max(worker_counts):
        raise ValueError("jobs_must_cover_workers")

    with tempfile.TemporaryDirectory(prefix="fr-p9-005-") as tmp:
        root = Path(tmp)
        payload_path = root / "capability.bin"
        payload_digest = _write_payload(payload_path, payload_bytes)
        rows: list[dict[str, Any]] = []

        # Alternate count order across repetitions to reduce monotonic run-order bias.
        orders = (worker_counts, tuple(reversed(worker_counts)))
        for repetition in range(repetitions):
            for workers in orders[repetition % len(orders)]:
                run_dir = root / f"r{repetition}-w{workers}"
                run_dir.mkdir()
                row = _run_once(
                    payload_path=payload_path,
                    workers=workers,
                    jobs=jobs,
                    rounds=rounds,
                    run_dir=run_dir,
                )
                row["repetition"] = repetition
                rows.append(row)

    summaries = [summarize_runs(rows, workers) for workers in worker_counts]
    reference_digests = summaries[0]["digests"]
    semantic_cross_count = all(summary["digests"] == reference_digests for summary in summaries[1:])
    frontier = pareto_workers(summaries)
    fastest = min(summaries, key=lambda row: row["median_wall_ns"])["workers"]
    lowest_pss = min(summaries, key=lambda row: row["median_total_pss_kib"])["workers"]

    checks = {
        "semantic_results_stable_across_repetitions": all(
            summary["semantic_stable_within_worker_count"] for summary in summaries
        ),
        "semantic_results_stable_across_worker_counts": semantic_cross_count,
        "all_metrics_positive": all(
            summary["median_total_pss_kib"] > 0
            and summary["median_wall_ns"] > 0
            and summary["median_jobs_per_second"] > 0
            and summary["median_p95_service_ns"] > 0
            and summary["median_p95_sojourn_ns"] > 0
            for summary in summaries
        ),
        "pareto_frontier_nonempty": bool(frontier),
        "worker_count_not_predeclared_as_winner": True,
        "no_scalar_gain_without_external_price": True,
    }

    return {
        "schema": SCHEMA,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "classification": "HOSTED_SHARED_CAPABILITY_CONCURRENCY_TYPED_FRONTIER",
        "probe": {
            "payload_bytes": payload_bytes,
            "payload_digest": payload_digest,
            "worker_counts": list(worker_counts),
            "jobs": jobs,
            "rounds": rounds,
            "repetitions": repetitions,
            "capability_placement": "read-only shared mmap, prefaulted before start barrier",
        },
        "summaries": summaries,
        "pareto_worker_counts": frontier,
        "observed_fastest_worker_count": int(fastest),
        "observed_lowest_pss_worker_count": int(lowest_pss),
        "checks": checks,
        "decision": (
            "SELECT_CONCURRENCY_FROM_A_MEASURED_TYPED_FRONTIER_OR_EXPLICIT_CONSTRAINTS_NOT_BY_MAXIMIZING_WORKER_COUNT"
        ),
        "typed_objectives": [
            "total_pss_kib",
            "wall_ns",
            "p95_queue_wait_ns",
            "p95_service_ns",
            "p95_sojourn_ns",
        ],
        "scalar_gain": None,
        "authority_effect": "NONE",
        "invariants": [
            "shared residency savings != net parallel speedup",
            "worker count != useful concurrency",
            "fastest observed worker count != universal optimum",
            "lowest-PSS worker count != universal optimum",
            "shared capability availability != execution authority",
        ],
        "next_falsifier": (
            "add memory pressure and phase fault-in so concurrency planning must choose worker count together with residency policy"
        ),
        "claim_ceiling": (
            "HOSTED_GITHUB_LINUX_SHARED_MMAP_BATCH_CONCURRENCY_PROXY_ONLY_NO_UNIVERSAL_WORKER_COUNT_OR_APPLICATION_THROUGHPUT_CLAIM"
        ),
    }


def run_synthetic_panel() -> dict[str, Any]:
    summaries = [
        {
            "workers": 1,
            "median_total_pss_kib": 20000,
            "median_wall_ns": 400,
            "median_p95_queue_wait_ns": 300,
            "median_p95_service_ns": 100,
            "median_p95_sojourn_ns": 400,
        },
        {
            "workers": 2,
            "median_total_pss_kib": 26000,
            "median_wall_ns": 240,
            "median_p95_queue_wait_ns": 130,
            "median_p95_service_ns": 110,
            "median_p95_sojourn_ns": 240,
        },
        {
            "workers": 4,
            "median_total_pss_kib": 38000,
            "median_wall_ns": 220,
            "median_p95_queue_wait_ns": 80,
            "median_p95_service_ns": 160,
            "median_p95_sojourn_ns": 220,
        },
    ]
    frontier = pareto_workers(summaries)
    checks = {
        "all_three_remain_typed_tradeoffs": frontier == [1, 2, 4],
        "no_scalar_gain": True,
    }
    return {
        "schema": SCHEMA,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "classification": "SYNTHETIC_CONCURRENCY_TYPED_FRONTIER",
        "pareto_worker_counts": frontier,
        "checks": checks,
        "scalar_gain": None,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--physical", action="store_true")
    parser.add_argument("--payload-mib", type=int, default=4)
    parser.add_argument("--jobs", type=int, default=12)
    parser.add_argument("--rounds", type=int, default=8)
    parser.add_argument("--repetitions", type=int, default=2)
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--payload-path")
    parser.add_argument("--ready-path")
    parser.add_argument("--start-path")
    parser.add_argument("--result-path")
    parser.add_argument("--worker-index", type=int, default=0)
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()

    if args.child:
        if not all((args.payload_path, args.ready_path, args.start_path, args.result_path)):
            raise SystemExit("child arguments missing")
        return _child(
            Path(args.payload_path),
            Path(args.ready_path),
            Path(args.start_path),
            Path(args.result_path),
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
        )
        if args.physical
        else run_synthetic_panel()
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
