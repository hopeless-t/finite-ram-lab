from __future__ import annotations

import argparse
import csv
import json
import random
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .char_sweep import trial_row


BLOCK_RE = re.compile(r"block-(?P<block>\d+)$")


def load_spec(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def make_block_schedule(spec: dict[str, Any], block: int) -> list[dict[str, int]]:
    levels = [int(x) for x in spec["memory_high_mib"]]
    repeats = int(spec["repeats_per_level"])
    seed = int(spec["base_schedule_seed"]) + block * 1009
    rng = random.Random(seed)

    rows = [
        {"repeat": repeat, "memory_high_mib": level}
        for level in levels
        for repeat in range(repeats)
    ]
    rng.shuffle(rows)
    return [{"order": i, **row} for i, row in enumerate(rows)]


def write_block_schedule(spec: dict[str, Any], block: int, out: str | Path) -> None:
    rows = make_block_schedule(spec, block)
    path = Path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["order", "repeat", "memory_high_mib"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def _estimate_breakpoint(levels: np.ndarray, values: np.ndarray) -> float:
    if len(levels) < 4:
        raise ValueError("at least four levels are required")
    order = np.argsort(levels)
    x = levels[order]
    y = values[order]
    scores: list[tuple[float, int]] = []
    for split in range(1, len(x)):
        left = y[:split]
        right = y[split:]
        if len(left) == 0 or len(right) == 0:
            continue
        sse = float(np.sum((left - left.mean()) ** 2) + np.sum((right - right.mean()) ** 2))
        scores.append((sse, split))
    _, best = min(scores, key=lambda z: z[0])
    return float((x[best - 1] + x[best]) / 2.0)


def _collect(root: Path) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    block_dirs = sorted(root.glob("block-*")) + sorted(root.glob("val001-block-*"))
    for block_dir in block_dirs:
        match = BLOCK_RE.search(block_dir.name)
        if not match:
            continue
        block = int(match.group("block"))
        for path in sorted((block_dir / "raw").glob("timeline-*.json")):
            row = trial_row(path)
            row["block"] = block
            rows.append(row)
    if not rows:
        raise ValueError("no VAL-001 trial evidence found")
    return pd.DataFrame(rows)


def _block_level_table(trials: pd.DataFrame) -> pd.DataFrame:
    metrics = [
        "retouch_latency_ms",
        "swap_growth_mib",
        "high_events_delta",
        "pgscan_delta",
        "pgsteal_delta",
        "pgfault_delta",
        "pgmajfault_delta",
        "psi_some_total_delta_us",
        "psi_full_total_delta_us",
    ]
    agg = (
        trials.groupby(["block", "memory_high_mib"], as_index=False)[metrics]
        .median()
        .sort_values(["block", "memory_high_mib"])
    )
    return agg


def _per_block_breakpoints(block_level: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for block, group in block_level.groupby("block", sort=True):
        levels = group["memory_high_mib"].to_numpy(dtype=float)
        latency = group["retouch_latency_ms"].to_numpy(dtype=float)
        log_latency = np.log(np.maximum(latency, 1e-9))
        bp = _estimate_breakpoint(levels, log_latency)
        low = float(group.loc[group["memory_high_mib"] == levels.min(), "retouch_latency_ms"].iloc[0])
        high = float(group.loc[group["memory_high_mib"] == levels.max(), "retouch_latency_ms"].iloc[0])
        rows.append(
            {
                "block": int(block),
                "breakpoint_mib": bp,
                "latency_at_160_ms": low,
                "latency_at_192_ms": high,
                "endpoint_ratio_160_over_192": low / high if high > 0 else float("inf"),
            }
        )
    return pd.DataFrame(rows)


def _level_summary(block_level: pd.DataFrame) -> pd.DataFrame:
    metrics = [c for c in block_level.columns if c not in {"block", "memory_high_mib"}]
    rows = []
    for level, group in block_level.groupby("memory_high_mib", sort=True):
        row: dict[str, Any] = {
            "memory_high_mib": int(level),
            "runner_blocks": int(group["block"].nunique()),
        }
        for metric in metrics:
            values = group[metric].to_numpy(dtype=float)
            row[f"median_{metric}"] = float(np.median(values))
            row[f"min_{metric}"] = float(np.min(values))
            row[f"max_{metric}"] = float(np.max(values))
        rows.append(row)
    return pd.DataFrame(rows)


def _cluster_bootstrap(
    block_level: pd.DataFrame,
    resamples: int,
    seed: int,
) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    blocks = np.array(sorted(block_level["block"].unique()), dtype=int)
    levels = np.array(sorted(block_level["memory_high_mib"].unique()), dtype=float)

    matrix = np.empty((len(blocks), len(levels)), dtype=float)
    for i, block in enumerate(blocks):
        g = block_level[block_level["block"] == block].set_index("memory_high_mib")
        matrix[i] = np.log(
            np.maximum(
                g.loc[levels, "retouch_latency_ms"].to_numpy(dtype=float),
                1e-9,
            )
        )

    estimates = np.empty(resamples, dtype=float)
    for i in range(resamples):
        chosen = rng.integers(0, len(blocks), size=len(blocks))
        curve = np.median(matrix[chosen], axis=0)
        estimates[i] = _estimate_breakpoint(levels, curve)

    unique, counts = np.unique(estimates, return_counts=True)
    order = np.argsort(counts)[::-1]
    modes = [
        {"breakpoint_mib": float(unique[j]), "count": int(counts[j]), "rate": float(counts[j] / resamples)}
        for j in order
    ]

    return {
        "resamples": resamples,
        "seed": seed,
        "median_breakpoint_mib": float(np.median(estimates)),
        "ci95_mib": [
            float(np.quantile(estimates, 0.025)),
            float(np.quantile(estimates, 0.975)),
        ],
        "modes": modes,
    }


def aggregate(
    spec: dict[str, Any],
    input_root: str | Path,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    trials = _collect(Path(input_root))
    block_level = _block_level_table(trials)
    per_block = _per_block_breakpoints(block_level)
    level_summary = _level_summary(block_level)

    blocks_expected = int(spec["runner_blocks"])
    repeats = int(spec["repeats_per_level"])
    levels = [int(x) for x in spec["memory_high_mib"]]
    expected_trials = blocks_expected * repeats * len(levels)

    checks = {
        "six_blocks_present": int(trials["block"].nunique()) == blocks_expected,
        "108_trials_present": len(trials) == expected_trials,
        "all_trials_pass": bool((trials["status"] == "PASS").all()),
        "no_oom": bool(((trials["oom_delta"] + trials["oom_kill_delta"]) == 0).all()),
        "all_levels_present_in_each_block": all(
            set(group["memory_high_mib"].astype(int)) == set(levels)
            and len(group) == repeats * len(levels)
            for _, group in trials.groupby("block")
        ),
    }

    bootstrap = _cluster_bootstrap(
        block_level,
        int(spec.get("cluster_bootstrap_resamples", 5000)),
        int(spec["base_schedule_seed"]) + 99991,
    )

    meta = {
        "experiment_id": "VAL-001",
        "execution_status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "runner_blocks": int(trials["block"].nunique()),
        "total_trials": len(trials),
        "levels_mib": levels,
        "repeats_per_level": repeats,
        "cluster_bootstrap": bootstrap,
        "interpretation_boundary": (
            "Execution PASS means the validation experiment was performed correctly. "
            "Replication support must be interpreted from the evidence separately."
        ),
    }
    return trials, block_level, per_block, level_summary, meta


def write_outputs(
    spec: dict[str, Any],
    input_root: str | Path,
    out_dir: str | Path,
) -> dict[str, Any]:
    trials, block_level, per_block, level_summary, meta = aggregate(spec, input_root)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    trials.sort_values(["block", "order"]).to_csv(out / "trials.csv", index=False)
    block_level.to_csv(out / "block-level.csv", index=False)
    per_block.to_csv(out / "per-block.csv", index=False)
    level_summary.to_csv(out / "level-summary.csv", index=False)
    (out / "meta.json").write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n")
    return meta


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("schedule")
    p.add_argument("--spec", required=True)
    p.add_argument("--block", type=int, required=True)
    p.add_argument("--out", required=True)

    p = sub.add_parser("aggregate")
    p.add_argument("--spec", required=True)
    p.add_argument("--input-root", required=True)
    p.add_argument("--out-dir", required=True)

    args = parser.parse_args()
    spec = load_spec(args.spec)

    if args.command == "schedule":
        write_block_schedule(spec, args.block, args.out)
        return

    meta = write_outputs(spec, args.input_root, args.out_dir)
    print(json.dumps(meta, indent=2, sort_keys=True))
    if meta["execution_status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
