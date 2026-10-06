from __future__ import annotations

import argparse
import hashlib
import json
import mmap
import os
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

SCHEMA = "finite-ram-lab.fr-p9-004-parallelism-residency-tax/v0.1"


def _payload_chunk() -> bytes:
    seed = b"catfood-lab-fr-p9-004-shared-capability|"
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
    path = Path(f"/proc/{pid}/smaps_rollup")
    for line in path.read_text().splitlines():
        if line.startswith("Pss:"):
            return int(line.split()[1])
    raise RuntimeError(f"pss_not_found:{pid}")


def _wait_for_ready(paths: list[Path], processes: list[subprocess.Popen[str]], timeout: float = 20.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if all(path.exists() for path in paths):
            return
        for process in processes:
            if process.poll() is not None:
                raise RuntimeError(f"child_exited_early:{process.returncode}")
        time.sleep(0.02)
    raise TimeoutError("child_ready_timeout")


def _child(mode: str, payload_path: Path, ready_path: Path, stop_path: Path) -> int:
    payload_ref: object | None = None
    digest: str | None = None
    touch_checksum = 0

    if mode == "PRIVATE_COPY":
        payload = bytearray(payload_path.read_bytes())
        for index in range(0, len(payload), 4096):
            touch_checksum ^= payload[index]
        digest = hashlib.sha256(memoryview(payload)).hexdigest()
        payload_ref = payload
    elif mode == "SHARED_MMAP":
        with payload_path.open("rb") as handle:
            mapped = mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ)
        for index in range(0, len(mapped), 4096):
            touch_checksum ^= mapped[index]
        digest = hashlib.sha256(mapped).hexdigest()
        payload_ref = mapped
    elif mode == "BASELINE":
        payload_ref = bytearray(4096)
    else:
        raise ValueError(f"unknown_mode:{mode}")

    ready_path.write_text(
        json.dumps(
            {
                "pid": os.getpid(),
                "mode": mode,
                "digest": digest,
                "touch_checksum": touch_checksum,
            },
            sort_keys=True,
        )
    )

    while not stop_path.exists():
        time.sleep(0.02)

    if isinstance(payload_ref, mmap.mmap):
        payload_ref.close()
    return 0


def _run_arm(
    *,
    mode: str,
    workers: int,
    payload_path: Path,
    expected_digest: str,
    run_dir: Path,
) -> dict[str, Any]:
    stop_path = run_dir / f"stop-{mode}-{workers}"
    ready_paths = [run_dir / f"ready-{mode}-{workers}-{index}.json" for index in range(workers)]
    for path in ready_paths + [stop_path]:
        path.unlink(missing_ok=True)

    processes: list[subprocess.Popen[str]] = []
    try:
        for index, ready in enumerate(ready_paths):
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "finite_ram_lab.fr_p9_004_parallelism_tax",
                    "--child",
                    "--mode",
                    mode,
                    "--payload-path",
                    str(payload_path),
                    "--ready-path",
                    str(ready),
                    "--stop-path",
                    str(stop_path),
                    "--child-index",
                    str(index),
                ],
                text=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
            processes.append(process)

        _wait_for_ready(ready_paths, processes)
        time.sleep(0.10)

        rows = [json.loads(path.read_text()) for path in ready_paths]
        pss_kib = [_read_pss_kib(int(row["pid"])) for row in rows]
        digests = [row["digest"] for row in rows if row["digest"] is not None]
        exact = not digests or all(digest == expected_digest for digest in digests)

        return {
            "mode": mode,
            "workers": workers,
            "pss_kib_per_worker": pss_kib,
            "total_pss_kib": sum(pss_kib),
            "semantic_digest_exact": exact,
            "touch_checksums": [row["touch_checksum"] for row in rows],
        }
    finally:
        stop_path.touch()
        for process in processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


def _median(values: list[int]) -> int:
    return int(statistics.median(values))


def summarize_repetitions(rows: list[dict[str, Any]], *, workers: int) -> dict[str, Any]:
    by_mode: dict[str, list[int]] = {"BASELINE": [], "PRIVATE_COPY": [], "SHARED_MMAP": []}
    exact = True
    for row in rows:
        if row["workers"] != workers:
            raise ValueError("worker_count_mismatch")
        by_mode[row["mode"]].append(int(row["total_pss_kib"]))
        exact = exact and bool(row["semantic_digest_exact"])

    if not all(by_mode.values()):
        raise ValueError("missing_mode_samples")

    medians = {mode: _median(samples) for mode, samples in by_mode.items()}
    baseline = medians["BASELINE"]
    private_growth = medians["PRIVATE_COPY"] - baseline
    shared_growth = medians["SHARED_MMAP"] - baseline

    return {
        "workers": workers,
        "median_total_pss_kib": medians,
        "normalized_growth_kib": {
            "PRIVATE_COPY": private_growth,
            "SHARED_MMAP": shared_growth,
        },
        "semantic_digest_exact": exact,
    }


def run_hosted_proxy(
    *,
    payload_bytes: int = 16 * 1024 * 1024,
    repetitions: int = 3,
    worker_counts: tuple[int, ...] = (1, 4),
) -> dict[str, Any]:
    if repetitions < 2:
        raise ValueError("repetitions_must_be_at_least_two")
    if any(workers <= 0 for workers in worker_counts):
        raise ValueError("worker_counts_must_be_positive")

    with tempfile.TemporaryDirectory(prefix="fr-p9-004-") as tmp:
        root = Path(tmp)
        payload_path = root / "capability.bin"
        expected_digest = _write_payload(payload_path, payload_bytes)

        summaries: dict[int, dict[str, Any]] = {}
        raw: list[dict[str, Any]] = []

        for workers in worker_counts:
            group_rows: list[dict[str, Any]] = []
            for repetition in range(repetitions):
                # Rotate arm order so one mode does not always receive the same
                # process-history position.
                orders = (
                    ("BASELINE", "PRIVATE_COPY", "SHARED_MMAP"),
                    ("SHARED_MMAP", "BASELINE", "PRIVATE_COPY"),
                    ("PRIVATE_COPY", "SHARED_MMAP", "BASELINE"),
                )
                order = orders[repetition % len(orders)]
                for mode in order:
                    run_dir = root / f"w{workers}-r{repetition}-{mode}"
                    run_dir.mkdir()
                    row = _run_arm(
                        mode=mode,
                        workers=workers,
                        payload_path=payload_path,
                        expected_digest=expected_digest,
                        run_dir=run_dir,
                    )
                    row["repetition"] = repetition
                    group_rows.append(row)
                    raw.append(row)
            summaries[workers] = summarize_repetitions(group_rows, workers=workers)

    one = summaries[min(worker_counts)]
    many = summaries[max(worker_counts)]
    private_one = one["normalized_growth_kib"]["PRIVATE_COPY"]
    private_many = many["normalized_growth_kib"]["PRIVATE_COPY"]
    shared_one = one["normalized_growth_kib"]["SHARED_MMAP"]
    shared_many = many["normalized_growth_kib"]["SHARED_MMAP"]

    private_scale = private_many / private_one if private_one > 0 else float("inf")
    shared_scale = shared_many / shared_one if shared_one > 0 else float("inf")
    shared_vs_private_many = shared_many / private_many if private_many > 0 else float("inf")

    checks = {
        "all_semantic_digests_exact": all(summary["semantic_digest_exact"] for summary in summaries.values()),
        "private_one_worker_growth_positive": private_one > 0,
        "shared_one_worker_growth_positive": shared_one > 0,
        "private_parallel_growth_scales_materially": private_scale >= 2.5,
        "shared_parallel_growth_scales_sublinearly": shared_scale <= 2.0,
        "shared_four_worker_growth_below_private": shared_vs_private_many <= 0.60,
        "no_throughput_or_universal_worker_count_claim": True,
    }

    return {
        "schema": SCHEMA,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "classification": "HOSTED_LINUX_PSS_PARALLELISM_RESIDENCY_PROXY",
        "probe": {
            "payload_bytes": payload_bytes,
            "repetitions": repetitions,
            "worker_counts": list(worker_counts),
            "expected_digest": expected_digest,
            "metric": "sum of worker PSS from /proc/<pid>/smaps_rollup with same-worker-count baseline subtraction",
        },
        "summaries": {str(key): value for key, value in summaries.items()},
        "scaling": {
            "private_growth_scale_many_vs_one": private_scale,
            "shared_growth_scale_many_vs_one": shared_scale,
            "shared_vs_private_growth_ratio_at_many": shared_vs_private_many,
        },
        "checks": checks,
        "decision": (
            "TREAT_PER_WORKER_PRIVATE_CAPABILITY_STATE_AS_A_PARALLELISM_RESIDENCY_TAX_AND_PREFER_VERIFIED_SHARED_IMMUTABLE_BACKING_WHEN_SEMANTICS_ALLOW"
        ),
        "invariants": [
            "parallel worker count != useful concurrency",
            "private capability replication can multiply resident state",
            "shared immutable backing can reduce the residency component of parallelism tax",
            "PSS reduction != throughput improvement",
            "shared availability != execution authority",
        ],
        "authority_effect": "NONE",
        "next_falsifier": (
            "add queueing/useful-progress measurements and contention so NetParallelGain includes both concurrency benefit and residency tax"
        ),
        "claim_ceiling": (
            "HOSTED_GITHUB_LINUX_PROCESS_PSS_PROXY_FOR_PRIVATE_COPY_VS_SHARED_MMAP_ONLY_NO_UNIVERSAL_WORKER_OR_THROUGHPUT_CLAIM"
        ),
    }


def run_synthetic_panel() -> dict[str, Any]:
    rows = [
        {"mode": "BASELINE", "workers": 1, "total_pss_kib": 10000, "semantic_digest_exact": True},
        {"mode": "PRIVATE_COPY", "workers": 1, "total_pss_kib": 26000, "semantic_digest_exact": True},
        {"mode": "SHARED_MMAP", "workers": 1, "total_pss_kib": 26000, "semantic_digest_exact": True},
        {"mode": "BASELINE", "workers": 4, "total_pss_kib": 40000, "semantic_digest_exact": True},
        {"mode": "PRIVATE_COPY", "workers": 4, "total_pss_kib": 104000, "semantic_digest_exact": True},
        {"mode": "SHARED_MMAP", "workers": 4, "total_pss_kib": 57000, "semantic_digest_exact": True},
    ]
    one = summarize_repetitions(rows[:3], workers=1)
    many = summarize_repetitions(rows[3:], workers=4)
    private_scale = many["normalized_growth_kib"]["PRIVATE_COPY"] / one["normalized_growth_kib"]["PRIVATE_COPY"]
    shared_scale = many["normalized_growth_kib"]["SHARED_MMAP"] / one["normalized_growth_kib"]["SHARED_MMAP"]
    checks = {
        "private_scales_four_x": private_scale == 4.0,
        "shared_scales_near_one_x": shared_scale < 1.1,
    }
    return {
        "schema": SCHEMA,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "classification": "SYNTHETIC_PARALLELISM_RESIDENCY_TAX",
        "one_worker": one,
        "four_workers": many,
        "checks": checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--physical", action="store_true")
    parser.add_argument("--payload-mib", type=int, default=16)
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--mode")
    parser.add_argument("--payload-path")
    parser.add_argument("--ready-path")
    parser.add_argument("--stop-path")
    parser.add_argument("--child-index", type=int, default=0)
    args = parser.parse_args()

    if args.child:
        if not all((args.mode, args.payload_path, args.ready_path, args.stop_path)):
            raise SystemExit("child arguments missing")
        return _child(
            args.mode,
            Path(args.payload_path),
            Path(args.ready_path),
            Path(args.stop_path),
        )

    if args.physical:
        result = run_hosted_proxy(
            payload_bytes=args.payload_mib * 1024 * 1024,
            repetitions=args.repetitions,
        )
    else:
        result = run_synthetic_panel()

    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
