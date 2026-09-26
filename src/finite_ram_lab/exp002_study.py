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


FILE_RE = re.compile(r"trial-(?P<order>\d+)-(?P<arm>correct_pageout|wrong_pageout|no_hint)-hot(?P<hot>A|B)-rep(?P<rep>\d+)\.json$")
BLOCK_RE = re.compile(r"(?:exp002-)?block-(?P<block>\d+)$")


def load_spec(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def schedule_rows(spec: dict[str, Any], block: int) -> list[dict[str, Any]]:
    reps = int(spec["repeats_per_arm_per_block"])
    if reps % 2:
        raise ValueError("repeats per arm must be even for identity balance")
    rows = []
    per_identity = reps // 2
    for arm in spec["arms"]:
        for hot in ("A", "B"):
            for rep in range(per_identity):
                rows.append({"arm": arm, "hot_identity": hot, "repeat": rep})
    rng = random.Random(int(spec["base_schedule_seed"]) + block * 1009)
    rng.shuffle(rows)
    return [{"order": i, **r} for i, r in enumerate(rows)]


def write_schedule(spec: dict[str, Any], block: int, out: str | Path) -> None:
    path = Path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["order", "arm", "hot_identity", "repeat"], lineterminator="\n")
        w.writeheader()
        w.writerows(schedule_rows(spec, block))


def collect(root: Path) -> pd.DataFrame:
    rows = []
    dirs = sorted(root.glob("block-*")) + sorted(root.glob("exp002-block-*"))
    for d in dirs:
        m = BLOCK_RE.search(d.name)
        if not m:
            continue
        block = int(m.group("block"))
        for p in sorted((d / "raw").glob("trial-*.json")):
            fm = FILE_RE.search(p.name)
            if not fm:
                raise ValueError(f"unexpected filename: {p.name}")
            z = json.loads(p.read_text())
            rows.append({
                "block": block,
                "order": int(fm.group("order")),
                "arm": fm.group("arm"),
                "hot_identity": fm.group("hot"),
                "repeat": int(fm.group("rep")),
                "status": z["status"],
                "advice_ms": z["advice"]["duration_ns"] / 1e6,
                "burst_ms": z["burst_touch_ns"] / 1e6,
                "hot_retouch_ms": z["hot_retouch_ns"] / 1e6,
                "work_interval_ms": z["work_interval_ns"] / 1e6,
                "hot_fraction": z["residency_pre_retouch"]["hot"]["resident_fraction"],
                "cold_fraction": z["residency_pre_retouch"]["cold"]["resident_fraction"],
                "hot_first16_fraction": z["residency_pre_retouch"]["hot_first16"]["resident_fraction"],
                "cold_first16_fraction": z["residency_pre_retouch"]["cold_first16"]["resident_fraction"],
                "swap_mib_pre_retouch": z["swap_mib_pre_retouch"],
                "pswpin": z["retouch_deltas"]["pswpin"],
                "refault_anon": z["retouch_deltas"]["workingset_refault_anon"],
                "pgmajfault": z["retouch_deltas"]["pgmajfault"],
                "content_match": bool(z["content_match"]),
                "no_oom": bool(z["no_oom"]),
            })
    if not rows:
        raise ValueError("no EXP-002 evidence")
    return pd.DataFrame(rows)


def block_contrast(trials: pd.DataFrame, arm_a: str, arm_b: str, outcome: str, log_scale: bool = True) -> np.ndarray:
    values = []
    for _, g in trials.groupby("block", sort=True):
        a = g[g["arm"] == arm_a][outcome].to_numpy(dtype=float)
        b = g[g["arm"] == arm_b][outcome].to_numpy(dtype=float)
        if log_scale:
            a = np.log(np.maximum(a, 1e-9))
            b = np.log(np.maximum(b, 1e-9))
        values.append(float(a.mean() - b.mean()))
    return np.asarray(values)


def exact_signflip(values: np.ndarray) -> dict[str, Any]:
    n = len(values)
    if n > 20:
        raise ValueError("exact sign-flip capped at 20 blocks")
    observed = float(values.mean())
    total = 1 << n
    shifts = np.arange(n, dtype=np.uint32)
    exceed = 0
    chunk = 65536
    for start in range(0, total, chunk):
        stop = min(start + chunk, total)
        masks = np.arange(start, stop, dtype=np.uint32)[:, None]
        signs = (((masks >> shifts[None, :]) & 1).astype(np.int8) * 2 - 1)
        perm = (signs @ values) / n
        exceed += int(np.count_nonzero(np.abs(perm) >= abs(observed) - 1e-15))
    return {
        "blocks": n,
        "observed_mean_log_difference": observed,
        "geometric_mean_ratio": math.exp(observed),
        "exact_permutations": total,
        "two_sided_p": exceed / total,
    }


def bootstrap_ratio(values: np.ndarray, resamples: int, seed: int) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    n = len(values)
    est = np.empty(resamples)
    for i in range(resamples):
        sample = values[rng.integers(0, n, size=n)]
        est[i] = math.exp(float(sample.mean()))
    return {
        "resamples": resamples,
        "median_ratio": float(np.median(est)),
        "ci95": [float(np.quantile(est, 0.025)), float(np.quantile(est, 0.975))],
    }


def contrast_result(spec: dict[str, Any], trials: pd.DataFrame, a: str, b: str, outcome: str, seed_offset: int) -> dict[str, Any]:
    c = block_contrast(trials, a, b, outcome, True)
    return {
        "arm_a": a,
        "arm_b": b,
        "outcome": outcome,
        "exact_signflip": exact_signflip(c),
        "cluster_bootstrap_ratio": bootstrap_ratio(
            c, int(spec["cluster_bootstrap_resamples"]), int(spec["base_schedule_seed"]) + seed_offset
        ),
    }


def analyze(spec: dict[str, Any], root: str | Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    trials = collect(Path(root))
    blocks = int(spec["runner_blocks"])
    reps = int(spec["repeats_per_arm_per_block"])
    expected = blocks * len(spec["arms"]) * reps
    checks = {
        "twenty_blocks_present": int(trials["block"].nunique()) == blocks,
        "three_hundred_sixty_trials_present": len(trials) == expected,
        "all_trials_pass": bool((trials["status"] == "PASS").all()),
        "no_oom": bool(trials["no_oom"].all()),
        "arms_balanced": all(all(g["arm"].value_counts().get(a, 0) == reps for a in spec["arms"]) for _, g in trials.groupby("block")),
        "hot_identity_balanced": all(
            all(armg["hot_identity"].value_counts().get(k, 0) == reps // 2 for k in ("A", "B"))
            for _, g in trials.groupby("block") for _, armg in g.groupby("arm")
        ),
    }

    arm_summary = {}
    for arm in spec["arms"]:
        g = trials[trials["arm"] == arm]
        arm_summary[arm] = {
            "trials": len(g),
            "median_hot_retouch_ms": float(np.median(g["hot_retouch_ms"])),
            "p90_hot_retouch_ms": float(np.quantile(g["hot_retouch_ms"], 0.90)),
            "median_work_interval_ms": float(np.median(g["work_interval_ms"])),
            "p90_work_interval_ms": float(np.quantile(g["work_interval_ms"], 0.90)),
            "median_advice_ms": float(np.median(g["advice_ms"])),
            "median_hot_fraction": float(np.median(g["hot_fraction"])),
            "median_cold_fraction": float(np.median(g["cold_fraction"])),
            "median_swap_mib_pre_retouch": float(np.median(g["swap_mib_pre_retouch"])),
            "median_pswpin": float(np.median(g["pswpin"])),
            "median_refault_anon": float(np.median(g["refault_anon"])),
            "median_pgmajfault": float(np.median(g["pgmajfault"])),
        }

    primary = contrast_result(spec, trials, "correct_pageout", "no_hint", "hot_retouch_ms", 5001)
    redteam = contrast_result(spec, trials, "wrong_pageout", "correct_pageout", "hot_retouch_ms", 5002)
    net = contrast_result(spec, trials, "correct_pageout", "no_hint", "work_interval_ms", 5003)

    summary = {
        "experiment_id": "EXP-002",
        "execution_status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "runner_blocks": int(trials["block"].nunique()),
        "total_trials": len(trials),
        "arm_summary": arm_summary,
        "primary_correct_vs_nohint": primary,
        "redteam_wrong_vs_correct": redteam,
        "net_interval_correct_vs_nohint": net,
        "authority_boundary": (
            "Tests one semantic signal through MADV_PAGEOUT under the hosted memcg workload; "
            "not a generalized coordinator or kernel-policy result."
        ),
    }
    return trials, summary


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
    trials, summary = analyze(spec, args.input_root)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    trials.sort_values(["block", "order"]).to_csv(out / "trials.csv", index=False)
    (out / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))
    if summary["execution_status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
