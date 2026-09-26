from __future__ import annotations

import argparse
import json
import math
import random
from collections import defaultdict
from pathlib import Path
from typing import Iterable


def quantile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    xs = sorted(values)
    pos = (len(xs) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(xs) - 1)
    frac = pos - lo
    return xs[lo] * (1 - frac) + xs[hi] * frac


def mean(values: Iterable[float]) -> float:
    xs = list(values)
    return sum(xs) / len(xs) if xs else 0.0


def bootstrap_ci(values: list[float], statistic: str, resamples: int, seed: int) -> tuple[float, float]:
    if not values:
        return (0.0, 0.0)
    rng = random.Random(seed)
    n = len(values)
    estimates: list[float] = []
    for _ in range(resamples):
        sample = [values[rng.randrange(n)] for _ in range(n)]
        if statistic == "mean":
            estimates.append(mean(sample))
        elif statistic == "p90":
            estimates.append(quantile(sample, 0.90))
        elif statistic == "p99":
            estimates.append(quantile(sample, 0.99))
        else:
            raise ValueError(statistic)
    return (quantile(estimates, 0.025), quantile(estimates, 0.975))


def wilson_interval(successes: int, total: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if total <= 0:
        return (0.0, 0.0)
    p = successes / total
    denom = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denom
    half = z * math.sqrt((p * (1 - p) / total) + (z * z / (4 * total * total))) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def convergence(values: list[float], seed: int) -> list[dict]:
    rng = random.Random(seed)
    shuffled = values[:]
    rng.shuffle(shuffled)
    checkpoints = [100, 250, 500, 1000, 2000, 4000, 8000, 16000, len(shuffled)]
    checkpoints = sorted({n for n in checkpoints if 0 < n <= len(shuffled)})
    out = []
    running = 0.0
    next_idx = 0
    for i, value in enumerate(shuffled, start=1):
        running += value
        if next_idx < len(checkpoints) and i == checkpoints[next_idx]:
            out.append({"n": i, "mean_fault_rate_gap": running / i})
            next_idx += 1
    return out


def capacity_ratio_bins(rows: list[dict]) -> list[dict]:
    edges = [0.0, 0.15, 0.25, 0.40, 0.60, 1.01]
    bins: list[list[float]] = [[] for _ in range(len(edges) - 1)]
    for row in rows:
        ratio = row["capacity"] / row["universe"]
        for i in range(len(edges) - 1):
            if edges[i] <= ratio < edges[i + 1]:
                bins[i].append(float(row["fault_rate_gap"]))
                break
    out = []
    for i, vals in enumerate(bins):
        out.append({
            "capacity_ratio_min": edges[i],
            "capacity_ratio_max": edges[i + 1],
            "trials": len(vals),
            "mean_fault_rate_gap": mean(vals),
            "p90_fault_rate_gap": quantile(vals, 0.90),
        })
    return out


def load_rows(root: Path) -> dict[str, list[dict]]:
    by_family: dict[str, list[dict]] = defaultdict(list)
    for path in sorted(root.rglob("mc-*.json")):
        data = json.loads(path.read_text())
        by_family[data["family"]].extend(data["rows"])
    if not by_family:
        raise SystemExit("no MC shard files found")
    return by_family


def analyze(root: Path, resamples: int, seed: int, rare_threshold: float) -> dict:
    by_family = load_rows(root)
    families = {}
    for family, rows in sorted(by_family.items()):
        gaps = [float(r["fault_rate_gap"]) for r in rows]
        rare = sum(v >= rare_threshold for v in gaps)
        rare_ci = wilson_interval(rare, len(gaps))
        mean_ci = bootstrap_ci(gaps, "mean", resamples, seed + 11)
        p90_ci = bootstrap_ci(gaps, "p90", resamples, seed + 23)
        p99_ci = bootstrap_ci(gaps, "p99", resamples, seed + 37)
        families[family] = {
            "trials": len(rows),
            "mean_fault_rate_gap": mean(gaps),
            "mean_ci95": list(mean_ci),
            "mean_ci95_width": mean_ci[1] - mean_ci[0],
            "p90_fault_rate_gap": quantile(gaps, 0.90),
            "p90_ci95": list(p90_ci),
            "p99_fault_rate_gap": quantile(gaps, 0.99),
            "p99_ci95": list(p99_ci),
            "rare_gap_threshold": rare_threshold,
            "rare_gap_count": rare,
            "rare_gap_rate": rare / len(gaps),
            "rare_gap_rate_ci95": list(rare_ci),
            "convergence": convergence(gaps, seed + 101),
            "capacity_ratio_bins": capacity_ratio_bins(rows),
        }
    return {
        "analysis_id": "MC-QUALITY-001",
        "bootstrap_resamples": resamples,
        "analysis_seed": seed,
        "rare_gap_threshold": rare_threshold,
        "total_trials": sum(v["trials"] for v in families.values()),
        "families": families,
    }


def to_markdown(result: dict) -> str:
    lines = [
        "# MC-QUALITY-001",
        "",
        f"Total trials: **{result['total_trials']}**",
        f"Bootstrap resamples per statistic: **{result['bootstrap_resamples']}**",
        "",
        "| Family | Trials | Mean gap | Mean 95% CI | P90 | P99 | Rare gap rate |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for family, s in result["families"].items():
        ci = s["mean_ci95"]
        rci = s["rare_gap_rate_ci95"]
        lines.append(
            f"| {family} | {s['trials']} | {s['mean_fault_rate_gap']:.5f} | "
            f"[{ci[0]:.5f}, {ci[1]:.5f}] | {s['p90_fault_rate_gap']:.5f} | "
            f"{s['p99_fault_rate_gap']:.5f} | {s['rare_gap_rate']:.4f} "
            f"([{rci[0]:.4f}, {rci[1]:.4f}]) |"
        )
    lines += [
        "",
        "Interval widths quantify sampling uncertainty under the declared synthetic generator.",
        "More trials should narrow them, with diminishing returns close to the usual 1/sqrt(n) rate.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--markdown")
    parser.add_argument("--bootstrap-resamples", type=int, default=500)
    parser.add_argument("--seed", type=int, default=2026092601)
    parser.add_argument("--rare-threshold", type=float, default=0.20)
    args = parser.parse_args()

    result = analyze(Path(args.input), args.bootstrap_resamples, args.seed, args.rare_threshold)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    if args.markdown:
        Path(args.markdown).write_text(to_markdown(result))


if __name__ == "__main__":
    main()
