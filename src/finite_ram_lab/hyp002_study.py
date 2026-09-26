from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
import random
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


FILE_RE = re.compile(
    r"trial-(?P<order>\d+)-high(?P<high>\d+)-recent(?P<recent>A|B)-hot(?P<hot>A|B)\.json$"
)
BLOCK_RE = re.compile(r"(?:hyp002-)?block-(?P<block>\d+)$")


def load_spec(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def schedule_rows(spec: dict[str, Any], block: int) -> list[dict[str, Any]]:
    rows = [
        {
            "memory_high_mib": int(level),
            "recent_identity": recent,
            "hot_identity": hot,
        }
        for level in spec["memory_high_mib"]
        for recent in spec["recent_identities"]
        for hot in spec["hot_identities"]
    ]
    rng = random.Random(int(spec["base_schedule_seed"]) + block * 1009)
    rng.shuffle(rows)
    return [{"order": i, **row} for i, row in enumerate(rows)]


def write_schedule(spec: dict[str, Any], block: int, out: str | Path) -> None:
    path = Path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(
            fh,
            fieldnames=[
                "order",
                "memory_high_mib",
                "recent_identity",
                "hot_identity",
            ],
            lineterminator="\n",
        )
        w.writeheader()
        w.writerows(schedule_rows(spec, block))


def collect(root: Path) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    dirs = sorted(root.glob("block-*")) + sorted(root.glob("hyp002-block-*"))

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
            recent = fm.group("recent")
            hot = fm.group("hot")
            older = "B" if recent == "A" else "A"
            recent_fraction = float(
                z["residency_pre_retouch"][recent]["resident_fraction"]
            )
            older_fraction = float(
                z["residency_pre_retouch"][older]["resident_fraction"]
            )
            hot_fraction = float(
                z["residency_pre_retouch"][hot]["resident_fraction"]
            )

            rows.append({
                "block": block,
                "order": int(fm.group("order")),
                "memory_high_mib": int(fm.group("high")),
                "recent_identity": recent,
                "older_identity": older,
                "hot_identity": hot,
                "aligned": hot == recent,
                "status": z["status"],
                "recent_fraction": recent_fraction,
                "older_fraction": older_fraction,
                "recent_minus_older": recent_fraction - older_fraction,
                "hot_fraction": hot_fraction,
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
        raise ValueError("no HYP-002 evidence found")
    return pd.DataFrame(rows)


def exact_signflip(values: np.ndarray, direction: str) -> dict[str, Any]:
    n = len(values)
    if n > 20:
        raise ValueError("exact sign-flip capped at 20 blocks")

    observed = float(values.mean())
    total = 1 << n
    upper = 0
    lower = 0
    abs_ge = 0

    for bits in range(total):
        signs = np.fromiter(
            (1.0 if (bits >> i) & 1 else -1.0 for i in range(n)),
            dtype=float,
            count=n,
        )
        value = float(np.mean(values * signs))
        if value >= observed - 1e-15:
            upper += 1
        if value <= observed + 1e-15:
            lower += 1
        if abs(value) >= abs(observed) - 1e-15:
            abs_ge += 1

    if direction == "greater":
        one_sided = upper / total
    elif direction == "less":
        one_sided = lower / total
    else:
        raise ValueError("direction must be greater or less")

    return {
        "blocks": n,
        "observed_mean": observed,
        "exact_permutations": total,
        "direction": direction,
        "one_sided_p": one_sided,
        "two_sided_p_diagnostic": abs_ge / total,
    }


def bootstrap_mean(
    values: np.ndarray,
    resamples: int,
    seed: int,
) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    n = len(values)
    estimates = np.empty(resamples)
    for i in range(resamples):
        estimates[i] = float(
            values[rng.integers(0, n, size=n)].mean()
        )
    return {
        "resamples": resamples,
        "median": float(np.median(estimates)),
        "ci95": [
            float(np.quantile(estimates, 0.025)),
            float(np.quantile(estimates, 0.975)),
        ],
    }


def bootstrap_ratio(
    log_diffs: np.ndarray,
    resamples: int,
    seed: int,
) -> dict[str, Any]:
    boot = bootstrap_mean(log_diffs, resamples, seed)
    return {
        "resamples": resamples,
        "median_ratio": math.exp(boot["median"]),
        "ci95_ratio": [
            math.exp(boot["ci95"][0]),
            math.exp(boot["ci95"][1]),
        ],
    }


def analyze(
    spec: dict[str, Any],
    root: str | Path,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    trials = collect(Path(root))
    blocks = int(spec["runner_blocks"])
    expected = (
        blocks
        * len(spec["memory_high_mib"])
        * len(spec["recent_identities"])
        * len(spec["hot_identities"])
    )

    expected_cells = {
        (
            int(level),
            recent,
            hot,
        )
        for level in spec["memory_high_mib"]
        for recent in spec["recent_identities"]
        for hot in spec["hot_identities"]
    }

    checks = {
        "sixteen_blocks_present": int(trials["block"].nunique()) == blocks,
        "one_hundred_twenty_eight_trials_present": len(trials) == expected,
        "all_trials_pass": bool((trials["status"] == "PASS").all()),
        "no_oom": bool(trials["no_oom"].all()),
        "content_integrity": bool(trials["content_match"].all()),
        "factorial_cells_complete": all(
            {
                (
                    int(row.memory_high_mib),
                    str(row.recent_identity),
                    str(row.hot_identity),
                )
                for row in g.itertuples()
            }
            == expected_cells
            for _, g in trials.groupby("block")
        ),
    }

    block_primary = (
        trials.groupby("block", as_index=False)["recent_minus_older"]
        .mean()
        .rename(columns={"recent_minus_older": "primary_contrast"})
    )
    primary_values = block_primary["primary_contrast"].to_numpy(dtype=float)

    primary = {
        "estimand": "mean runner-block recent_fraction - older_fraction",
        "exact_signflip": exact_signflip(primary_values, "greater"),
        "cluster_bootstrap": bootstrap_mean(
            primary_values,
            int(spec["cluster_bootstrap_resamples"]),
            int(spec["cluster_bootstrap_seed"]),
        ),
    }

    latency_rows = []
    for block, g in trials.groupby("block", sort=True):
        aligned = np.log(
            np.maximum(
                g[g["aligned"]]["hot_retouch_ms"].to_numpy(dtype=float),
                1e-9,
            )
        )
        misaligned = np.log(
            np.maximum(
                g[~g["aligned"]]["hot_retouch_ms"].to_numpy(dtype=float),
                1e-9,
            )
        )
        latency_rows.append({
            "block": int(block),
            "log_misaligned_minus_aligned": float(
                misaligned.mean() - aligned.mean()
            ),
        })

    latency_blocks = pd.DataFrame(latency_rows)
    latency_values = latency_blocks[
        "log_misaligned_minus_aligned"
    ].to_numpy(dtype=float)

    secondary = {
        "estimand": (
            "mean runner-block log latency difference "
            "HOT=older minus HOT=recent"
        ),
        "exact_signflip": exact_signflip(latency_values, "greater"),
        "cluster_bootstrap_ratio": bootstrap_ratio(
            latency_values,
            int(spec["cluster_bootstrap_resamples"]),
            int(spec["cluster_bootstrap_seed"]) + 1,
        ),
        "geometric_mean_ratio_misaligned_over_aligned": math.exp(
            float(latency_values.mean())
        ),
    }

    level_summary = {}
    for level in spec["memory_high_mib"]:
        g = trials[trials["memory_high_mib"] == int(level)]
        level_summary[str(level)] = {
            "trials": len(g),
            "mean_recent_minus_older": float(
                g["recent_minus_older"].mean()
            ),
            "median_recent_minus_older": float(
                np.median(g["recent_minus_older"])
            ),
            "recent_greater_rate": float(
                (g["recent_minus_older"] > 0).mean()
            ),
            "median_hot_latency_aligned_ms": float(
                np.median(g[g["aligned"]]["hot_retouch_ms"])
            ),
            "median_hot_latency_misaligned_ms": float(
                np.median(g[~g["aligned"]]["hot_retouch_ms"])
            ),
        }

    mapping_check = {}
    for recent in spec["recent_identities"]:
        g = trials[trials["recent_identity"] == recent]
        mapping_check[str(recent)] = {
            "trials": len(g),
            "mean_recent_minus_older": float(
                g["recent_minus_older"].mean()
            ),
            "positive_rate": float(
                (g["recent_minus_older"] > 0).mean()
            ),
        }

    arm_summary = {
        "aligned": {
            "trials": int(trials["aligned"].sum()),
            "median_latency_ms": float(
                np.median(trials[trials["aligned"]]["hot_retouch_ms"])
            ),
            "p90_latency_ms": float(
                np.quantile(
                    trials[trials["aligned"]]["hot_retouch_ms"],
                    0.90,
                )
            ),
        },
        "misaligned": {
            "trials": int((~trials["aligned"]).sum()),
            "median_latency_ms": float(
                np.median(trials[~trials["aligned"]]["hot_retouch_ms"])
            ),
            "p90_latency_ms": float(
                np.quantile(
                    trials[~trials["aligned"]]["hot_retouch_ms"],
                    0.90,
                )
            ),
        },
    }

    summary = {
        "experiment_id": "HYP-002",
        "execution_status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "runner_blocks": int(trials["block"].nunique()),
        "total_trials": len(trials),
        "primary_recency_residency": primary,
        "secondary_semantic_latency": secondary,
        "level_summary": level_summary,
        "mapping_identity_check": mapping_check,
        "semantic_alignment_summary": arm_summary,
        "authority_boundary": (
            "HYP-002 tests a bounded separation between randomized past recency "
            "and independently randomized future semantic need under hosted "
            "memcg pressure. It does not test a production hint."
        ),
    }

    block_outputs = block_primary.merge(latency_blocks, on="block")
    return trials, block_outputs, summary


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

    trials, blocks, summary = analyze(spec, args.input_root)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    trials.sort_values(["block", "order"]).to_csv(out / "trials.csv", index=False)
    blocks.to_csv(out / "block-contrasts.csv", index=False)
    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))

    if summary["execution_status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
