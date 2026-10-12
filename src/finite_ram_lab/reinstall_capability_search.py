from __future__ import annotations

import argparse
import json
import math
import random
import statistics
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .adaptive_cache_engine import PreparedTrace, native_status, prepare_trace
from .sim import generate_trace, lru_faults, opt_faults

FAMILIES = ("stable_hotset", "sequential_scan", "shifting_hotset", "bursty")


@dataclass(frozen=True)
class Candidate:
    name: str
    backend: str
    workers: int
    heap_max: int
    capability_level: int
    mode: str = "engine"


def _median_ms(fn: Callable[[], Any], repeats: int) -> float:
    vals: list[float] = []
    for _ in range(repeats):
        t0 = time.perf_counter_ns()
        fn()
        vals.append((time.perf_counter_ns() - t0) / 1e6)
    return float(statistics.median(vals))


def _reference_tasks(trace: list[int], capacities: list[int]) -> dict[str, Any]:
    unique = len(set(trace))
    full = list(range(1, unique + 1))
    return {
        "single_opt": lambda: opt_faults(trace, capacities[len(capacities) // 2]),
        "mixed_compare": lambda: (
            [lru_faults(trace, c) for c in capacities],
            [opt_faults(trace, c) for c in capacities],
        ),
        "lru_full_curve": lambda: [lru_faults(trace, c) for c in full],
        "opt_full_curve": lambda: [opt_faults(trace, c) for c in full],
    }


def _engine_tasks(
    prepared: PreparedTrace,
    capacities: list[int],
    candidate: Candidate,
) -> dict[str, Callable[[], Any]]:
    full = list(range(1, prepared.unique_pages + 1))
    mid = capacities[len(capacities) // 2]
    if candidate.mode == "python":
        return {
            "single_opt": lambda: prepared.opt_sweep([mid], backend="python", workers=1),
            "mixed_compare": lambda: prepared.sweep(capacities, backend="python", workers=1),
            "lru_full_curve": lambda: prepared.lru_curve(backend="python"),
            "opt_full_curve": lambda: prepared.opt_sweep(full, backend="python", workers=1),
        }
    return {
        "single_opt": lambda: prepared.opt_sweep(
            [mid], backend=candidate.backend, workers=1, heap_max=candidate.heap_max
        ),
        "mixed_compare": lambda: {
            "lru": prepared.lru_sweep(capacities, backend=candidate.backend),
            "opt": prepared.opt_sweep(
                capacities,
                backend=candidate.backend,
                workers=candidate.workers,
                heap_max=candidate.heap_max,
            ),
        },
        "lru_full_curve": lambda: prepared.lru_curve(backend=candidate.backend),
        "opt_full_curve": lambda: prepared.opt_sweep(
            full,
            backend=candidate.backend,
            workers=candidate.workers,
            heap_max=candidate.heap_max,
        ),
    }


def _candidates(max_loops: int, universe_hint: int) -> list[Candidate]:
    rows: list[Candidate] = [
        Candidate("reference_scalar", "python", 1, 0, 2, mode="reference"),
        Candidate("prepared_python", "python", 1, 0, 7, mode="python"),
        Candidate("native_scan_serial", "native", 1, 0, 9),
        Candidate("native_heap_serial", "native", 1, universe_hint + 1, 9),
    ]
    for workers in (1, 2, 4):
        for heap_max in (8, 16, 24, 28, 32, 36, 40, 48, 64, 96):
            rows.append(
                Candidate(
                    f"hybrid_h{heap_max}_w{workers}",
                    "native",
                    workers,
                    heap_max,
                    10 if workers > 1 else 9,
                )
            )
    # Historical search candidate: auto still used the pre-confirmatory h8 default.
    rows.append(Candidate("auto_default", "auto", 4, 8, 11))
    # Fine search only after all coarse serial/2-thread/4-thread regions exist.
    for heap_max in (18, 20, 22, 26, 30):
        rows.append(Candidate(f"refine_h{heap_max}_w2", "native", 2, heap_max, 11))
    for heap_max in (12, 18, 20, 22, 24, 26, 30, 34, 38, 42):
        rows.append(Candidate(f"refine_h{heap_max}_w4", "native", 4, heap_max, 11))
    return rows[:max_loops]


def _geom_mean(values: list[float]) -> float:
    return math.exp(sum(math.log(max(v, 1e-12)) for v in values) / len(values))


def run_search(
    *,
    max_loops: int = 50,
    min_loops: int = 35,
    stale_limit: int = 8,
    improvement_threshold: float = 0.01,
    length: int = 6000,
    universe: int = 129,
    capacity: int = 31,
    seed: int = 20261012,
) -> dict[str, Any]:
    traces: dict[str, list[int]] = {}
    prepared: dict[str, PreparedTrace] = {}
    capacities = [1, 3, 7, 17, capacity, 47, 79, min(113, universe - 1)]
    capacities = sorted(set(c for c in capacities if 0 < c <= universe))
    for i, family in enumerate(FAMILIES):
        trace = generate_trace(
            family,
            random.Random(seed + i * 1009),
            length,
            universe,
            capacity,
        )
        traces[family] = trace
        prepared[family] = prepare_trace(trace)

    # Parity gate before any performance search.
    parity_cases = 0
    for family in FAMILIES:
        tr = traces[family]
        pr = prepared[family]
        for c in capacities:
            if pr.faults("lru", c, backend="auto") != lru_faults(tr, c):
                raise RuntimeError(f"LRU parity failure: {family} cap={c}")
            if pr.faults("opt", c, backend="auto") != opt_faults(tr, c):
                raise RuntimeError(f"OPT parity failure: {family} cap={c}")
            parity_cases += 2

    baseline: dict[str, float] | None = None
    records: list[dict[str, Any]] = []
    best_score = float("inf")
    best_capability = -1
    stale = 0
    best_name = None

    for loop_no, candidate in enumerate(_candidates(max_loops, universe), start=1):
        task_times: dict[str, list[float]] = {
            "single_opt": [],
            "mixed_compare": [],
            "lru_full_curve": [],
            "opt_full_curve": [],
        }
        outputs_ok = True
        for family in FAMILIES:
            tr = traces[family]
            pr = prepared[family]
            if candidate.mode == "reference":
                tasks = _reference_tasks(tr, capacities)
                repeats = {"single_opt": 3, "mixed_compare": 1, "lru_full_curve": 1, "opt_full_curve": 1}
            else:
                # Avoid cross-candidate cache contamination for LRU first-build timing.
                pr._lru_curve_cache = None
                tasks = _engine_tasks(pr, capacities, candidate)
                repeats = {"single_opt": 5, "mixed_compare": 3, "lru_full_curve": 3, "opt_full_curve": 2}

            for name, fn in tasks.items():
                try:
                    task_times[name].append(_median_ms(fn, repeats[name]))
                except Exception:
                    outputs_ok = False
                    task_times[name].append(float("inf"))

        medians = {name: float(statistics.median(vals)) for name, vals in task_times.items()}
        if baseline is None:
            baseline = dict(medians)
        ratios = {
            name: medians[name] / baseline[name] if baseline[name] > 0 else 1.0
            for name in medians
        }
        perf_score = _geom_mean(list(ratios.values()))

        is_pareto_update = False
        reason: list[str] = []
        if outputs_ok:
            capability_gain = candidate.capability_level > best_capability
            perf_gain = perf_score < best_score * (1.0 - improvement_threshold)
            nonregressive_perf = perf_score <= best_score * 1.05
            if capability_gain and nonregressive_perf:
                is_pareto_update = True
                reason.append("capability")
            if perf_gain and candidate.capability_level >= best_capability:
                is_pareto_update = True
                reason.append("performance")
        if is_pareto_update:
            best_score = perf_score
            best_capability = max(best_capability, candidate.capability_level)
            best_name = candidate.name
            stale = 0
        else:
            stale += 1

        records.append(
            {
                "loop": loop_no,
                "candidate": candidate.name,
                "backend": candidate.backend,
                "workers": candidate.workers,
                "heap_max": candidate.heap_max,
                "capability_level": candidate.capability_level,
                "task_median_ms": medians,
                "normalized_ratios": ratios,
                "performance_score": perf_score,
                "outputs_ok": outputs_ok,
                "pareto_update": is_pareto_update,
                "update_reason": reason,
                "stale_loops": stale,
            }
        )

        if loop_no >= min_loops and stale >= stale_limit:
            break

    return {
        "experiment_id": "FRL-REINSTALL-007-CAPABILITY-PERFORMANCE-SEARCH-v1",
        "max_loops": max_loops,
        "loops_executed": len(records),
        "converged": len(records) < max_loops and records[-1]["stale_loops"] >= stale_limit,
        "convergence_rule": {
            "min_loops": min_loops,
            "stale_limit": stale_limit,
            "performance_improvement_threshold": improvement_threshold,
        },
        "parity_cases": parity_cases,
        "native": native_status(),
        "corpus": {
            "families": list(FAMILIES),
            "length": length,
            "universe": universe,
            "capacity_anchor": capacity,
            "query_capacities": capacities,
        },
        "baseline_ms": baseline,
        "best_candidate": best_name,
        "best_performance_score": best_score,
        "best_capability_level": best_capability,
        "records": records,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True)
    p.add_argument("--max-loops", type=int, default=50)
    p.add_argument("--min-loops", type=int, default=35)
    p.add_argument("--stale-limit", type=int, default=8)
    args = p.parse_args()
    result = run_search(
        max_loops=args.max_loops,
        min_loops=args.min_loops,
        stale_limit=args.stale_limit,
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
