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


FILE_RE = re.compile(
    r"trial-(?P<order>\d+)-high(?P<high>\d+)-hot(?P<hot>A|B)-rep(?P<rep>\d+)\.json$"
)
BLOCK_RE = re.compile(r"(?:obs003-)?block-(?P<block>\d+)$")


def load_spec(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def schedule_rows(spec: dict[str, Any], block: int) -> list[dict[str, Any]]:
    repeats = int(spec["repeats_per_level_per_block"])
    if repeats != 2:
        raise ValueError("OBS-003 frozen design requires exactly 2 repeats per level")

    rows: list[dict[str, Any]] = []
    for level in spec["memory_high_mib"]:
        # Exact A/B balance at every level in every runner block.
        rows.append({
            "memory_high_mib": int(level),
            "hot_identity": "A",
            "repeat": 0,
        })
        rows.append({
            "memory_high_mib": int(level),
            "hot_identity": "B",
            "repeat": 1,
        })

    rng = random.Random(int(spec["base_schedule_seed"]) + block * 1009)
    rng.shuffle(rows)
    return [{"order": i, **row} for i, row in enumerate(rows)]


def write_schedule(spec: dict[str, Any], block: int, out: str | Path) -> None:
    path = Path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(
            fh,
            fieldnames=["order", "memory_high_mib", "hot_identity", "repeat"],
            lineterminator="\n",
        )
        w.writeheader()
        w.writerows(schedule_rows(spec, block))


def collect(root: Path) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    dirs = sorted(root.glob("block-*")) + sorted(root.glob("obs003-block-*"))

    for d in dirs:
        bm = BLOCK_RE.search(d.name)
        if not bm:
            continue
        block = int(bm.group("block"))

        for path in sorted((d / "raw").glob("trial-*.json")):
            fm = FILE_RE.search(path.name)
            if not fm:
                raise ValueError(f"unexpected filename: {path.name}")

            z = json.loads(path.read_text())
            hot_fraction = float(
                z["residency_pre_retouch"]["hot"]["resident_fraction"]
            )
            rows.append({
                "block": block,
                "order": int(fm.group("order")),
                "memory_high_mib": int(fm.group("high")),
                "hot_identity": fm.group("hot"),
                "repeat": int(fm.group("rep")),
                "status": z["status"],
                "hot_fraction": hot_fraction,
                "cold_fraction": float(
                    z["residency_pre_retouch"]["cold"]["resident_fraction"]
                ),
                "misaligned": int(hot_fraction < 1.0),
                "hot_retouch_ms": float(z["hot_retouch_ns"]) / 1e6,
                "swap_mib_pre_retouch": float(z["swap_mib_pre_retouch"]),
                "pswpin": int(z["retouch_deltas"]["pswpin"]),
                "refault_anon": int(
                    z["retouch_deltas"]["workingset_refault_anon"]
                ),
                "pgmajfault": int(z["retouch_deltas"]["pgmajfault"]),
                "content_match": bool(z["content_match"]),
                "no_oom": bool(z["no_oom"]),
            })

    if not rows:
        raise ValueError("no OBS-003 evidence found")
    return pd.DataFrame(rows)


def cluster_bootstrap_curve(
    trials: pd.DataFrame,
    levels: list[int],
    resamples: int,
    seed: int,
) -> dict[str, Any]:
    block_level = (
        trials.groupby(["block", "memory_high_mib"], as_index=False)["misaligned"]
        .mean()
    )
    blocks = np.asarray(sorted(block_level["block"].unique()), dtype=int)

    matrix = np.empty((len(blocks), len(levels)), dtype=float)
    for i, block in enumerate(blocks):
        g = (
            block_level[block_level["block"] == block]
            .set_index("memory_high_mib")
        )
        matrix[i] = g.loc[levels, "misaligned"].to_numpy(dtype=float)

    rng = np.random.default_rng(seed)
    samples = np.empty((resamples, len(levels)), dtype=float)
    for i in range(resamples):
        chosen = rng.integers(0, len(blocks), size=len(blocks))
        samples[i] = matrix[chosen].mean(axis=0)

    return {
        str(level): {
            "median": float(np.median(samples[:, j])),
            "ci95": [
                float(np.quantile(samples[:, j], 0.025)),
                float(np.quantile(samples[:, j], 0.975)),
            ],
        }
        for j, level in enumerate(levels)
    }


def _median_or_none(values: pd.Series) -> float | None:
    if len(values) == 0:
        return None
    return float(np.median(values.to_numpy(dtype=float)))


def analyze(
    spec: dict[str, Any],
    root: str | Path,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    trials = collect(Path(root))

    blocks = int(spec["runner_blocks"])
    repeats = int(spec["repeats_per_level_per_block"])
    levels = [int(x) for x in spec["memory_high_mib"]]
    expected = blocks * repeats * len(levels)

    checks = {
        "thirty_two_blocks_present": int(trials["block"].nunique()) == blocks,
        "three_hundred_twenty_trials_present": len(trials) == expected,
        "all_trials_pass": bool((trials["status"] == "PASS").all()),
        "no_oom": bool(trials["no_oom"].all()),
        "content_integrity": bool(trials["content_match"].all()),
        "levels_balanced": all(
            all(
                g["memory_high_mib"].value_counts().get(level, 0) == repeats
                for level in levels
            )
            for _, g in trials.groupby("block")
        ),
        "hot_identity_balanced": all(
            set(level_g["hot_identity"]) == {"A", "B"}
            and len(level_g) == repeats
            for _, block_g in trials.groupby("block")
            for _, level_g in block_g.groupby("memory_high_mib")
        ),
    }

    block_level = (
        trials.groupby(["block", "memory_high_mib"], as_index=False)
        .agg(
            misalignment_rate=("misaligned", "mean"),
            mean_hot_fraction=("hot_fraction", "mean"),
            mean_latency_ms=("hot_retouch_ms", "mean"),
        )
        .sort_values(["block", "memory_high_mib"])
    )

    boot = cluster_bootstrap_curve(
        trials,
        levels,
        int(spec["cluster_bootstrap_resamples"]),
        int(spec["cluster_bootstrap_seed"]),
    )

    level_summary: dict[str, Any] = {}
    for level in levels:
        g = trials[trials["memory_high_mib"] == level]
        mis = g[g["misaligned"] == 1]
        resident = g[g["misaligned"] == 0]
        block_rates = block_level[
            block_level["memory_high_mib"] == level
        ]["misalignment_rate"]

        level_summary[str(level)] = {
            "trials": len(g),
            "misaligned_trials": int(g["misaligned"].sum()),
            "raw_misalignment_rate": float(g["misaligned"].mean()),
            "mean_runner_block_misalignment_rate": float(block_rates.mean()),
            "cluster_bootstrap": boot[str(level)],
            "median_hot_fraction": float(np.median(g["hot_fraction"])),
            "min_hot_fraction": float(g["hot_fraction"].min()),
            "median_latency_ms": float(np.median(g["hot_retouch_ms"])),
            "p90_latency_ms": float(np.quantile(g["hot_retouch_ms"], 0.90)),
            "median_latency_misaligned_ms": _median_or_none(
                mis["hot_retouch_ms"]
            ),
            "median_latency_fully_resident_ms": _median_or_none(
                resident["hot_retouch_ms"]
            ),
            "catastrophic_ge_500ms": int(
                (g["hot_retouch_ms"] >= 500.0).sum()
            ),
            "catastrophic_ge_500ms_among_misaligned": int(
                ((g["hot_retouch_ms"] >= 500.0) & (g["misaligned"] == 1)).sum()
            ),
        }

    summary = {
        "experiment_id": "OBS-003",
        "execution_status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "runner_blocks": int(trials["block"].nunique()),
        "total_trials": len(trials),
        "levels_mib": levels,
        "misalignment_rule": spec["misalignment_rule"],
        "level_summary": level_summary,
        "authority_boundary": (
            "OBS-003 estimates natural residency-misalignment opportunity under "
            "the declared NO_HINT hosted memcg workload. It does not estimate "
            "the benefit of an ideal or proposed mechanism."
        ),
    }
    return trials, block_level, summary


def main() -> None:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("schedule")
    s.add_argument("--spec", required=True)
    s.add_argument("--block", type=int, required=True)
    s.add_argument("--out", required=True)

    a = sub.add_parser("aggregate")
    a.add_argument("--spec", required=True)
    a.add_argument("--input-root", required=True)
    a.add_argument("--out-dir", required=True)

    args = p.parse_args()
    spec = load_spec(args.spec)

    if args.command == "schedule":
        write_schedule(spec, args.block, args.out)
        return

    trials, block_level, summary = analyze(spec, args.input_root)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    trials.sort_values(["block", "order"]).to_csv(out / "trials.csv", index=False)
    block_level.to_csv(out / "block-level.csv", index=False)
    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))

    if summary["execution_status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
