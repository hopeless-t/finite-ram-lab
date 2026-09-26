from __future__ import annotations

import argparse
import csv
import itertools
import json
import random
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


FILE_RE = re.compile(r"trial-(?P<order>\d+)-target(?P<target>A|B)\.json$")
BLOCK_RE = re.compile(r"(?:env006-)?block-(?P<block>\d+)$")


def load_spec(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def schedule_rows(spec: dict[str, Any], block: int) -> list[dict[str, Any]]:
    rows = [{"target_identity": x} for x in spec["target_identities"]]
    rng = random.Random(int(spec["base_schedule_seed"]) + block * 1009)
    rng.shuffle(rows)
    return [{"order": i, **r} for i, r in enumerate(rows)]


def write_schedule(spec: dict[str, Any], block: int, out: str | Path) -> None:
    path = Path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["order", "target_identity"], lineterminator="\n")
        w.writeheader()
        w.writerows(schedule_rows(spec, block))


def collect(root: Path) -> pd.DataFrame:
    rows = []
    dirs = sorted(root.glob("block-*")) + sorted(root.glob("env006-block-*"))
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
                "target_identity": fm.group("target"),
                "call_success": bool(z["pageout"]["success"]),
                "target_after_pageout": z["residency_after_pageout"]["target"]["resident_fraction"],
                "control_after_pageout": z["residency_after_pageout"]["control"]["resident_fraction"],
                "target_after_burst": z["residency_after_burst"]["target"]["resident_fraction"],
                "control_after_burst": z["residency_after_burst"]["control"]["resident_fraction"],
                "difference": z["derived"]["target_minus_control_fraction"],
                "swap_after_pageout_mib": z["derived"]["swap_growth_after_pageout_mib"],
                "swap_after_burst_mib": z["derived"]["swap_growth_after_burst_mib"],
                "content_match": bool(z["content_match"]),
                "no_oom": bool(z["no_oom"]),
            })
    if not rows:
        raise ValueError("no ENV-006 evidence")
    return pd.DataFrame(rows)


def exact_signflip(values: np.ndarray) -> dict[str, Any]:
    observed = float(np.mean(values))
    perm = []
    for signs in itertools.product((-1.0, 1.0), repeat=len(values)):
        perm.append(float(np.mean(values * np.asarray(signs))))
    arr = np.asarray(perm)
    return {
        "blocks": len(values),
        "observed_mean_difference": observed,
        "exact_permutations": len(arr),
        "two_sided_p": float(np.mean(np.abs(arr) >= abs(observed) - 1e-15)),
    }


def analyze(spec: dict[str, Any], root: str | Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    trials = collect(Path(root))
    block = trials.groupby("block", as_index=False)["difference"].mean()
    inf = exact_signflip(block["difference"].to_numpy(dtype=float))
    med = float(np.median(trials["difference"]))
    all_calls = bool(trials["call_success"].all())
    checks = {
        "eight_blocks_present": int(trials["block"].nunique()) == int(spec["runner_blocks"]),
        "sixteen_trials_present": len(trials) == int(spec["runner_blocks"]) * int(spec["trials_per_block"]),
        "all_calls_succeeded": all_calls,
        "all_content_match": bool(trials["content_match"].all()),
        "no_oom": bool(trials["no_oom"].all()),
        "target_identity_balanced": all(set(g["target_identity"]) == {"A", "B"} for _, g in trials.groupby("block")),
    }
    if not all_calls:
        classification = "UNAVAILABLE"
    elif med <= -0.10 and inf["two_sided_p"] <= 0.05:
        classification = "EFFECTIVE"
    elif med < 0:
        classification = "PARTIAL"
    else:
        classification = "INEFFECTIVE"
    summary = {
        "experiment_id": "ENV-006",
        "execution_status": "PASS" if all(checks.values()) else "FAIL",
        "classification": classification,
        "checks": checks,
        "runner_blocks": int(trials["block"].nunique()),
        "trials": len(trials),
        "median_target_after_pageout": float(np.median(trials["target_after_pageout"])),
        "median_target_after_burst": float(np.median(trials["target_after_burst"])),
        "median_control_after_burst": float(np.median(trials["control_after_burst"])),
        "median_target_minus_control_after_burst": med,
        "min_difference": float(trials["difference"].min()),
        "max_difference": float(trials["difference"].max()),
        "median_swap_after_pageout_mib": float(np.median(trials["swap_after_pageout_mib"])),
        "median_swap_after_burst_mib": float(np.median(trials["swap_after_burst_mib"])),
        "inference": inf,
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
