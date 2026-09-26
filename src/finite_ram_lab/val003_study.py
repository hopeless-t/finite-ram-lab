from __future__ import annotations

import argparse
import csv
import json
import math
import random
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


FILE_RE = re.compile(
    r"trial-(?P<order>\d+)-(?P<arm>correct_pageout|no_hint)-hot(?P<hot>A|B)-rep(?P<rep>\d+)\.json$"
)
BLOCK_RE = re.compile(r"(?:val003-)?block-(?P<block>\d+)$")


def load_spec(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def schedule_rows(spec: dict[str, Any], block: int) -> list[dict[str, Any]]:
    reps = int(spec["repeats_per_arm_per_block"])
    if reps % 2:
        raise ValueError("repeats per arm must be even for hot-identity balance")

    rows: list[dict[str, Any]] = []
    per_identity = reps // 2
    for arm in spec["arms"]:
        for hot in ("A", "B"):
            for rep in range(per_identity):
                rows.append({
                    "arm": arm,
                    "hot_identity": hot,
                    "repeat": rep,
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
            fieldnames=["order", "arm", "hot_identity", "repeat"],
            lineterminator="\n",
        )
        w.writeheader()
        w.writerows(schedule_rows(spec, block))


def collect(root: Path, threshold_ms: float) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    dirs = sorted(root.glob("block-*")) + sorted(root.glob("val003-block-*"))

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
            latency_ms = float(z["hot_retouch_ns"]) / 1e6
            rows.append({
                "block": block,
                "order": int(fm.group("order")),
                "arm": fm.group("arm"),
                "hot_identity": fm.group("hot"),
                "repeat": int(fm.group("rep")),
                "status": z["status"],
                "hot_retouch_ms": latency_ms,
                "catastrophic": int(latency_ms >= threshold_ms),
                "hot_fraction": z["residency_pre_retouch"]["hot"]["resident_fraction"],
                "cold_fraction": z["residency_pre_retouch"]["cold"]["resident_fraction"],
                "swap_mib_pre_retouch": z["swap_mib_pre_retouch"],
                "pswpin": z["retouch_deltas"]["pswpin"],
                "refault_anon": z["retouch_deltas"]["workingset_refault_anon"],
                "pgmajfault": z["retouch_deltas"]["pgmajfault"],
                "content_match": bool(z["content_match"]),
                "no_oom": bool(z["no_oom"]),
            })

    if not rows:
        raise ValueError("no VAL-003 evidence found")
    return pd.DataFrame(rows)


def block_risk_differences(trials: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for block, g in trials.groupby("block", sort=True):
        correct = g[g["arm"] == "correct_pageout"]["catastrophic"].to_numpy(dtype=float)
        nohint = g[g["arm"] == "no_hint"]["catastrophic"].to_numpy(dtype=float)
        if len(correct) == 0 or len(nohint) == 0:
            raise ValueError(f"block {block} missing arm")
        rows.append({
            "block": int(block),
            "correct_rate": float(correct.mean()),
            "no_hint_rate": float(nohint.mean()),
            "risk_difference_correct_minus_nohint": float(correct.mean() - nohint.mean()),
        })
    return pd.DataFrame(rows)


def monte_carlo_signflip(
    values: np.ndarray,
    draws: int,
    seed: int,
) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    observed = float(values.mean())
    n = len(values)

    lower_or_equal = 0
    abs_ge = 0
    done = 0
    chunk = 100_000

    while done < draws:
        m = min(chunk, draws - done)
        signs = rng.integers(0, 2, size=(m, n), dtype=np.int8) * 2 - 1
        perm = (signs @ values) / n
        lower_or_equal += int(np.count_nonzero(perm <= observed + 1e-15))
        abs_ge += int(np.count_nonzero(np.abs(perm) >= abs(observed) - 1e-15))
        done += m

    one_sided = (lower_or_equal + 1) / (draws + 1)
    two_sided = (abs_ge + 1) / (draws + 1)
    mcse_one = math.sqrt(one_sided * (1.0 - one_sided) / (draws + 1))
    mcse_two = math.sqrt(two_sided * (1.0 - two_sided) / (draws + 1))

    return {
        "blocks": n,
        "draws": draws,
        "seed": seed,
        "observed_mean_risk_difference": observed,
        "direction": "CORRECT_PAGEOUT < NO_HINT",
        "one_sided_p": one_sided,
        "one_sided_mcse": mcse_one,
        "two_sided_p_diagnostic": two_sided,
        "two_sided_mcse": mcse_two,
    }


def cluster_bootstrap(
    values: np.ndarray,
    resamples: int,
    seed: int,
) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    n = len(values)
    estimates = np.empty(resamples, dtype=float)
    for i in range(resamples):
        sample = values[rng.integers(0, n, size=n)]
        estimates[i] = float(sample.mean())
    return {
        "resamples": resamples,
        "seed": seed,
        "median_risk_difference": float(np.median(estimates)),
        "ci95": [
            float(np.quantile(estimates, 0.025)),
            float(np.quantile(estimates, 0.975)),
        ],
    }


def analyze(spec: dict[str, Any], root: str | Path) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    threshold = float(spec["catastrophic_threshold_ms"])
    trials = collect(Path(root), threshold)

    blocks = int(spec["runner_blocks"])
    reps = int(spec["repeats_per_arm_per_block"])
    expected = blocks * len(spec["arms"]) * reps

    checks = {
        "forty_blocks_present": int(trials["block"].nunique()) == blocks,
        "eight_hundred_trials_present": len(trials) == expected,
        "all_trials_pass": bool((trials["status"] == "PASS").all()),
        "no_oom": bool(trials["no_oom"].all()),
        "content_integrity": bool(trials["content_match"].all()),
        "arms_balanced": all(
            all(g["arm"].value_counts().get(arm, 0) == reps for arm in spec["arms"])
            for _, g in trials.groupby("block")
        ),
        "hot_identity_balanced": all(
            all(
                armg["hot_identity"].value_counts().get(k, 0) == reps // 2
                for k in ("A", "B")
            )
            for _, g in trials.groupby("block")
            for _, armg in g.groupby("arm")
        ),
    }

    block_rates = block_risk_differences(trials)
    diffs = block_rates["risk_difference_correct_minus_nohint"].to_numpy(dtype=float)

    randomization = monte_carlo_signflip(
        diffs,
        int(spec["randomization_draws"]),
        int(spec["randomization_seed"]),
    )
    bootstrap = cluster_bootstrap(
        diffs,
        int(spec["cluster_bootstrap_resamples"]),
        int(spec["cluster_bootstrap_seed"]),
    )

    arm_summary = {}
    for arm in spec["arms"]:
        g = trials[trials["arm"] == arm]
        arm_summary[arm] = {
            "trials": len(g),
            "catastrophic_events": int(g["catastrophic"].sum()),
            "catastrophic_rate": float(g["catastrophic"].mean()),
            "median_latency_ms": float(np.median(g["hot_retouch_ms"])),
            "p90_latency_ms": float(np.quantile(g["hot_retouch_ms"], 0.90)),
            "p95_latency_ms": float(np.quantile(g["hot_retouch_ms"], 0.95)),
            "p99_latency_ms": float(np.quantile(g["hot_retouch_ms"], 0.99)),
            "max_latency_ms": float(g["hot_retouch_ms"].max()),
        }

    summary = {
        "experiment_id": "VAL-003",
        "execution_status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "runner_blocks": int(trials["block"].nunique()),
        "total_trials": len(trials),
        "catastrophic_threshold_ms": threshold,
        "arm_summary": arm_summary,
        "primary_inference": {
            "estimand": "mean runner-block absolute risk difference CORRECT_PAGEOUT - NO_HINT",
            "randomization_test": randomization,
            "cluster_bootstrap": bootstrap,
        },
        "authority_boundary": (
            "Confirmatory evidence concerns the pre-registered >=500 ms catastrophic tail "
            "for CORRECT_PAGEOUT versus NO_HINT under this hosted memcg workload."
        ),
    }
    return trials, block_rates, summary


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

    trials, block_rates, summary = analyze(spec, args.input_root)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    trials.sort_values(["block", "order"]).to_csv(out / "trials.csv", index=False)
    block_rates.to_csv(out / "block-rates.csv", index=False)
    (out / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))

    if summary["execution_status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
