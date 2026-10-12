from __future__ import annotations

import argparse
import hashlib
import json
import random
import statistics
import time
from pathlib import Path
from typing import Any, Callable

import finite_ram_lab.adaptive_cache_engine as ace
from .sim import generate_trace, lru_faults, opt_faults


def _old(seed: int) -> tuple[int, int, bytes]:
    trace = generate_trace("shifting_hotset", random.Random(seed), 12000, 257, 41)
    return (
        lru_faults(trace, 41),
        opt_faults(trace, 41),
        hashlib.sha256(bytes(x % 256 for x in trace)).digest(),
    )


def _new(seed: int) -> tuple[int, int, bytes]:
    trace = generate_trace("shifting_hotset", random.Random(seed), 12000, 257, 41)
    prepared = ace.prepare_trace(trace)
    return (
        prepared.faults("lru", 41),
        prepared.faults("opt", 41),
        hashlib.sha256(bytes(x % 256 for x in trace)).digest(),
    )


def _bench(fn: Callable[[int], Any], *, n: int, seed: int) -> dict[str, float]:
    values: list[float] = []
    for i in range(n):
        t0 = time.perf_counter_ns()
        fn(seed + i)
        values.append((time.perf_counter_ns() - t0) / 1e6)
    values.sort()
    return {
        "n": float(n),
        "median_ms": float(statistics.median(values)),
        "p95_ms": float(values[max(0, int(0.95 * n) - 1)]),
        "min_ms": float(values[0]),
        "max_ms": float(values[-1]),
    }


def run(*, iterations: int, seed: int, rebuild_native: bool) -> dict[str, Any]:
    for offset in range(10):
        if _old(seed + offset) != _new(seed + offset):
            raise RuntimeError(f"semantic mismatch at seed {seed + offset}")

    # Warm the content-addressed accelerator before steady-state measurement.
    _new(seed)
    old = _bench(_old, n=iterations, seed=seed)
    new = _bench(_new, n=iterations, seed=seed)

    trace = generate_trace("shifting_hotset", random.Random(seed), 12000, 257, 41)
    prepared = ace.prepare_trace(trace)
    functional = {
        "profile": prepared.profile(),
        "compare": prepared.compare([17, 41, 83, 127]),
        "minimum_capacity": {
            "lru_10pct": prepared.minimum_capacity("lru", 0.10),
            "opt_10pct": prepared.minimum_capacity("opt", 0.10),
            "lru_5pct": prepared.minimum_capacity("lru", 0.05),
            "opt_5pct": prepared.minimum_capacity("opt", 0.05),
        },
        "lru_curve_points": len(prepared.lru_curve()),
    }

    rebuild: dict[str, Any] | None = None
    if rebuild_native:
        status = ace.native_status()
        if status["available"] and status["cache_path"]:
            path = Path(status["cache_path"])
            old_size = path.stat().st_size
            path.unlink()
            ace._NATIVE = None
            t0 = time.perf_counter_ns()
            rebuilt = ace.native_status()
            rebuild_ms = (time.perf_counter_ns() - t0) / 1e6
            rebuilt_path = Path(rebuilt["cache_path"])
            ace._NATIVE = None
            t1 = time.perf_counter_ns()
            cached = ace.native_status()
            cached_load_ms = (time.perf_counter_ns() - t1) / 1e6
            if _old(seed) != _new(seed):
                raise RuntimeError("semantic mismatch after native rebuild")
            rebuild = {
                "artifact_bytes": old_size,
                "digest": rebuilt["digest"],
                "same_path": str(path) == str(rebuilt_path),
                "rebuilt_exists": rebuilt_path.exists(),
                "rebuild_ms": rebuild_ms,
                "cached_reload_ms": cached_load_ms,
            }

    return {
        "experiment_id": "FRL-REINSTALL-007-FINAL-VALIDATION-v2",
        "parity_seeds": 10,
        "old_workload": old,
        "adaptive_workload": new,
        "median_speedup": old["median_ms"] / new["median_ms"],
        "median_reduction_pct": (1.0 - new["median_ms"] / old["median_ms"]) * 100.0,
        "functional": functional,
        "native_rebuild": rebuild,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True)
    p.add_argument("--iterations", type=int, default=100)
    p.add_argument("--seed", type=int, default=20261012)
    p.add_argument("--rebuild-native", action="store_true")
    args = p.parse_args()
    result = run(
        iterations=args.iterations,
        seed=args.seed,
        rebuild_native=args.rebuild_native,
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
