from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from .sim import generate_trace, lru_faults, opt_faults


FAMILIES = ("stable_hotset", "sequential_scan", "shifting_hotset", "bursty")


def percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    xs = sorted(values)
    pos = (len(xs) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(xs) - 1)
    frac = pos - lo
    return xs[lo] * (1 - frac) + xs[hi] * frac


def run(family: str, seed: int, trials: int) -> dict:
    if family not in FAMILIES:
        raise ValueError(f"unknown family: {family}")
    if trials <= 0:
        raise ValueError("trials must be positive")

    root_rng = random.Random(seed)
    rows = []

    for trial in range(trials):
        trial_seed = root_rng.randrange(0, 2**63)
        rng = random.Random(trial_seed)
        universe = rng.randint(24, 96)
        capacity = rng.randint(4, min(24, universe - 1))
        length = rng.randint(400, 1000)
        trace = generate_trace(family, rng, length, universe, capacity)

        lru = lru_faults(trace, capacity)
        opt = opt_faults(trace, capacity)
        if opt > lru:
            raise AssertionError("OPT cannot fault more than LRU")

        rows.append({
            "trial": trial,
            "seed": trial_seed,
            "family": family,
            "length": length,
            "universe": universe,
            "capacity": capacity,
            "unique_pages": len(set(trace)),
            "lru_faults": lru,
            "opt_faults": opt,
            "lru_fault_rate": lru / length,
            "opt_fault_rate": opt / length,
            "fault_rate_gap": (lru - opt) / length,
        })

    gaps = [r["fault_rate_gap"] for r in rows]
    return {
        "experiment_id": "MC-001",
        "family": family,
        "seed": seed,
        "trials": trials,
        "summary": {
            "mean_fault_rate_gap": sum(gaps) / len(gaps),
            "p50_fault_rate_gap": percentile(gaps, 0.50),
            "p90_fault_rate_gap": percentile(gaps, 0.90),
            "p99_fault_rate_gap": percentile(gaps, 0.99),
            "max_fault_rate_gap": max(gaps),
        },
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--family", required=True, choices=FAMILIES)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--trials", type=int, default=1000)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    result = run(args.family, args.seed, args.trials)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
