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


FILE_RE = re.compile(r"trial-(?P<order>\d+)-(?P<arm>hot_evict|cold_evict)-hot(?P<hot>A|B)-rep(?P<rep>\d+)\.json$")
BLOCK_RE = re.compile(r"(?:exp001-)?block-(?P<block>\d+)$")


def load_spec(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def schedule_rows(spec: dict[str, Any], block: int) -> list[dict[str, Any]]:
    reps = int(spec["repeats_per_arm_per_block"])
    if reps != 2:
        raise ValueError("current frozen design requires 2 repeats per arm")
    rows = []
    for arm in spec["arms"]:
        for rep, hot in enumerate(("A", "B")):
            rows.append({"arm": arm, "hot_identity": hot, "repeat": rep})
    rng = random.Random(int(spec["base_schedule_seed"]) + block * 1009)
    rng.shuffle(rows)
    return [{"order": i, **row} for i, row in enumerate(rows)]


def write_schedule(spec: dict[str, Any], block: int, out: str | Path) -> None:
    rows = schedule_rows(spec, block)
    path = Path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["order", "arm", "hot_identity", "repeat"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def collect(root: Path) -> pd.DataFrame:
    rows = []
    dirs = sorted(root.glob("block-*")) + sorted(root.glob("exp001-block-*"))
    for d in dirs:
        m = BLOCK_RE.search(d.name)
        if not m:
            continue
        block = int(m.group("block"))
        for p in sorted((d / "raw").glob("trial-*.json")):
            fm = FILE_RE.search(p.name)
            if not fm:
                raise ValueError(f"unexpected filename {p.name}")
            z = json.loads(p.read_text())
            rows.append({
                "block": block,
                "order": int(fm.group("order")),
                "arm": fm.group("arm"),
                "hot_identity": fm.group("hot"),
                "repeat": int(fm.group("rep")),
                "status": z["status"],
                "hot_retouch_ms": z["hot_retouch_ns"] / 1e6,
                "target_fraction": z["residency_pre_retouch"]["target"]["resident_fraction"],
                "nontarget_fraction": z["residency_pre_retouch"]["nontarget"]["resident_fraction"],
                "hot_fraction": z["residency_pre_retouch"]["hot"]["resident_fraction"],
                "pswpin": z["retouch_deltas"]["pswpin"],
                "refault_anon": z["retouch_deltas"]["workingset_refault_anon"],
                "pgmajfault": z["retouch_deltas"]["pgmajfault"],
                "pgfault": z["retouch_deltas"]["pgfault"],
                "swap_mib_pre_retouch": z["swap_mib_pre_retouch"],
                "content_match": z["content_match"],
                "no_oom": z["fidelity"]["no_oom"],
            })
    if not rows:
        raise ValueError("no EXP-001 evidence found")
    return pd.DataFrame(rows)


def exact_signflip(contrasts: np.ndarray) -> dict[str, Any]:
    observed = float(np.mean(contrasts))
    vals = []
    for signs in itertools.product((-1.0, 1.0), repeat=len(contrasts)):
        vals.append(float(np.mean(contrasts * np.asarray(signs))))
    vals = np.asarray(vals)
    p = float(np.mean(np.abs(vals) >= abs(observed) - 1e-15))
    return {
        "blocks": len(contrasts),
        "observed_mean_log_difference": observed,
        "geometric_mean_ratio_hot_evict_over_cold_evict": math.exp(observed),
        "exact_permutations": len(vals),
        "two_sided_p": p,
    }


def bootstrap_ratio(contrasts: np.ndarray, resamples: int, seed: int) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    n = len(contrasts)
    est = np.empty(resamples)
    for i in range(resamples):
        sample = contrasts[rng.integers(0, n, size=n)]
        est[i] = math.exp(float(np.mean(sample)))
    return {
        "resamples": resamples,
        "median_ratio": float(np.median(est)),
        "ci95": [float(np.quantile(est, 0.025)), float(np.quantile(est, 0.975))],
    }


def analyze(spec: dict[str, Any], root: str | Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    trials = collect(Path(root))
    blocks = int(spec["runner_blocks"])
    expected = blocks * len(spec["arms"]) * int(spec["repeats_per_arm_per_block"])
    checks = {
        "eight_blocks_present": int(trials["block"].nunique()) == blocks,
        "thirty_two_trials_present": len(trials) == expected,
        "all_trials_valid": bool((trials["status"] == "PASS").all()),
        "no_oom": bool(trials["no_oom"].all()),
        "arms_balanced": all(
            g["arm"].value_counts().get("hot_evict", 0) == g["arm"].value_counts().get("cold_evict", 0)
            for _, g in trials.groupby("block")
        ),
        "hot_mapping_identity_balanced": all(
            all(armg["hot_identity"].value_counts().get(k, 0) == 1 for k in ("A", "B"))
            for _, g in trials.groupby("block") for _, armg in g.groupby("arm")
        ),
    }

    block_rows = []
    for block, g in trials.groupby("block", sort=True):
        hot = np.log(np.maximum(g[g["arm"] == "hot_evict"]["hot_retouch_ms"].to_numpy(dtype=float), 1e-9))
        cold = np.log(np.maximum(g[g["arm"] == "cold_evict"]["hot_retouch_ms"].to_numpy(dtype=float), 1e-9))
        block_rows.append({"block": int(block), "log_difference": float(hot.mean() - cold.mean())})
    block_df = pd.DataFrame(block_rows)
    contrasts = block_df["log_difference"].to_numpy(dtype=float)

    inference = exact_signflip(contrasts)
    boot = bootstrap_ratio(
        contrasts, int(spec["cluster_bootstrap_resamples"]), int(spec["base_schedule_seed"]) + 7001
    )

    arm_summary = {}
    for arm in spec["arms"]:
        g = trials[trials["arm"] == arm]
        arm_summary[arm] = {
            "trials": len(g),
            "median_hot_retouch_ms": float(np.median(g["hot_retouch_ms"])),
            "p90_hot_retouch_ms": float(np.quantile(g["hot_retouch_ms"], 0.90)),
            "median_hot_fraction_pre_retouch": float(np.median(g["hot_fraction"])),
            "median_pswpin": float(np.median(g["pswpin"])),
            "median_refault_anon": float(np.median(g["refault_anon"])),
            "median_pgmajfault": float(np.median(g["pgmajfault"])),
        }

    summary = {
        "experiment_id": "EXP-001",
        "execution_status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "runner_blocks": int(trials["block"].nunique()),
        "total_trials": len(trials),
        "arm_summary": arm_summary,
        "primary_inference": {
            "exact_signflip": inference,
            "cluster_bootstrap_ratio": boot,
        },
        "fidelity": {
            "max_target_fraction": float(trials["target_fraction"].max()),
            "min_nontarget_fraction": float(trials["nontarget_fraction"].min()),
            "all_content_match": bool(trials["content_match"].all()),
        },
        "authority_boundary": "Causal residency-identity effect under bounded intervention; not a claim about natural Linux eviction optimality.",
    }
    return trials, summary


def write_outputs(spec: dict[str, Any], root: str | Path, out_dir: str | Path) -> dict[str, Any]:
    trials, summary = analyze(spec, root)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    trials.sort_values(["block", "order"]).to_csv(out / "trials.csv", index=False)
    (out / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    return summary


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
    summary = write_outputs(spec, args.input_root, args.out_dir)
    print(json.dumps(summary, indent=2, sort_keys=True))
    if summary["execution_status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
