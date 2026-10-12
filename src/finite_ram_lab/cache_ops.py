from __future__ import annotations

import hashlib
import json
import random
import statistics
import time
from pathlib import Path
from typing import Any, Callable, Hashable, Sequence

from .adaptive_cache_engine import PreparedTrace, native_status, prepare_trace
from .sim import generate_trace, lru_faults, opt_faults

TRACE_FAMILIES = ("stable_hotset", "sequential_scan", "shifting_hotset", "bursty")


def parse_capacities(value: str | Sequence[int]) -> list[int]:
    if isinstance(value, str):
        raw = [part.strip() for part in value.split(",") if part.strip()]
        caps = [int(part) for part in raw]
    else:
        caps = [int(c) for c in value]
    if not caps or any(c <= 0 for c in caps):
        raise ValueError("capacities must contain positive integers")
    return list(dict.fromkeys(caps))


def load_trace_json(path: str | Path) -> list[Hashable]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list) or not data:
        raise ValueError("trace JSON must be a non-empty array")
    for value in data:
        try:
            hash(value)
        except TypeError as exc:
            raise ValueError("trace values must be JSON scalars or otherwise hashable") from exc
    return data


def synthetic_trace(
    *,
    family: str,
    seed: int,
    length: int,
    universe: int,
    capacity_anchor: int,
) -> list[int]:
    if family not in TRACE_FAMILIES:
        raise ValueError(f"unknown trace family: {family}")
    return generate_trace(
        family,
        random.Random(seed),
        length,
        universe,
        capacity_anchor,
    )


def analyze_trace(
    trace: Sequence[Hashable],
    *,
    capacities: Sequence[int],
    fault_rates: Sequence[float] = (0.10, 0.05),
    backend: str = "auto",
    workers: int | str = "auto",
) -> dict[str, Any]:
    prepared = prepare_trace(trace)
    caps = parse_capacities(capacities)
    compare = prepared.compare(caps, backend=backend, workers=workers)
    recommendations: dict[str, dict[str, int | None]] = {}
    for rate in fault_rates:
        if not (0.0 <= rate <= 1.0):
            raise ValueError("fault rates must be in [0, 1]")
        key = f"{rate:.6g}"
        recommendations[key] = {
            "lru": prepared.minimum_capacity("lru", rate, backend=backend),
            "opt": prepared.minimum_capacity("opt", rate, backend=backend),
        }
    return {
        "engine": "adaptive-cache-v1",
        "profile": prepared.profile(),
        "capacities": caps,
        "compare": compare,
        "minimum_capacity_by_fault_rate": recommendations,
        "lru_curve_points": len(prepared.lru_curve(backend=backend)),
        "backend_requested": backend,
        "workers_requested": workers,
    }


def _median_ms(fn: Callable[[], Any], repeats: int) -> dict[str, float]:
    values: list[float] = []
    for _ in range(repeats):
        t0 = time.perf_counter_ns()
        fn()
        values.append((time.perf_counter_ns() - t0) / 1e6)
    values.sort()
    return {
        "n": float(repeats),
        "median_ms": float(statistics.median(values)),
        "p95_ms": float(values[max(0, int(repeats * 0.95) - 1)]),
        "min_ms": float(values[0]),
        "max_ms": float(values[-1]),
    }


def benchmark_trace(
    trace: Sequence[Hashable],
    *,
    capacities: Sequence[int],
    anchor_capacity: int,
    repeats: int = 30,
    backend: str = "auto",
    workers: int | str = "auto",
) -> dict[str, Any]:
    if repeats <= 0:
        raise ValueError("repeats must be positive")
    caps = parse_capacities(capacities)
    original = list(trace)
    prepared = prepare_trace(original)

    # Correctness gate before timing.
    scalar_lru = {c: lru_faults(original, c) for c in caps}
    scalar_opt = {c: opt_faults(original, c) for c in caps}
    adaptive_lru = prepared.lru_sweep(caps, backend=backend)
    adaptive_opt = prepared.opt_sweep(caps, backend=backend, workers=workers)
    if scalar_lru != adaptive_lru or scalar_opt != adaptive_opt:
        raise RuntimeError("adaptive engine failed scalar parity gate")

    full_caps = list(range(1, prepared.unique_pages + 1))
    # Warm reusable native state/thread pool before steady-state timings.
    prepared.lru_curve(backend=backend)
    prepared.opt_sweep(caps, backend=backend, workers=workers)

    tasks: dict[str, Callable[[], Any]] = {
        "scalar_anchor_pair": lambda: (
            lru_faults(original, anchor_capacity),
            opt_faults(original, anchor_capacity),
        ),
        "adaptive_anchor_pair": lambda: (
            prepared.faults("lru", anchor_capacity, backend=backend),
            prepared.faults("opt", anchor_capacity, backend=backend),
        ),
        "scalar_mixed_sweep": lambda: (
            [lru_faults(original, c) for c in caps],
            [opt_faults(original, c) for c in caps],
        ),
        "adaptive_mixed_sweep": lambda: prepared.sweep(
            caps,
            backend=backend,
            workers=workers,
        ),
        "adaptive_lru_curve_cached": lambda: prepared.lru_curve(backend=backend),
        "adaptive_opt_full_curve": lambda: prepared.opt_sweep(
            full_caps,
            backend=backend,
            workers=workers,
        ),
    }
    timings = {name: _median_ms(fn, repeats) for name, fn in tasks.items()}

    # Fresh preparation is intentionally separate from reusable-query latency.
    prep_timing = _median_ms(lambda: prepare_trace(original), repeats)
    timings["prepare_trace"] = prep_timing

    scalar_pair = timings["scalar_anchor_pair"]["median_ms"]
    adaptive_pair = timings["adaptive_anchor_pair"]["median_ms"]
    scalar_mixed = timings["scalar_mixed_sweep"]["median_ms"]
    adaptive_mixed = timings["adaptive_mixed_sweep"]["median_ms"]

    return {
        "benchmark": "adaptive-cache-operational-v1",
        "profile": prepared.profile(),
        "backend_requested": backend,
        "workers_requested": workers,
        "anchor_capacity": anchor_capacity,
        "capacities": caps,
        "parity": {
            "status": "PASS",
            "lru": adaptive_lru,
            "opt": adaptive_opt,
        },
        "timings": timings,
        "speedups": {
            "anchor_pair": scalar_pair / adaptive_pair,
            "mixed_sweep": scalar_mixed / adaptive_mixed,
        },
    }


def trace_digest(trace: Sequence[Hashable]) -> str:
    payload = json.dumps(list(trace), ensure_ascii=False, separators=(",", ":"), sort_keys=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def operational_status() -> dict[str, Any]:
    return {
        "engine": "adaptive-cache-v1",
        "native": native_status(),
        "trace_families": list(TRACE_FAMILIES),
        "capabilities": [
            "single_lru",
            "single_opt",
            "mixed_sweep",
            "full_lru_curve",
            "full_opt_curve",
            "lru_opt_compare",
            "minimum_capacity_for_fault_rate",
            "python_fallback",
            "content_addressed_native_acceleration",
            "bounded_parallel_opt_sweep",
        ],
    }
