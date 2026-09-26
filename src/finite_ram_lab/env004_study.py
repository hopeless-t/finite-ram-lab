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
    r"trial-(?P<order>\d+)-(?P<arm>pageout_only|pageout_plus_reclaim)-rep(?P<rep>\d+)\.json$"
)
BLOCK_RE = re.compile(r"(?:env004-)?block-(?P<block>\d+)$")


def load_spec(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def schedule_rows(spec: dict[str, Any], block: int) -> list[dict[str, Any]]:
    rows = [
        {"arm": arm, "repeat": rep}
        for arm in spec["arms"]
        for rep in range(int(spec["repeats_per_arm_per_block"]))
    ]
    rng = random.Random(int(spec["base_seed"]) + block * 1009)
    rng.shuffle(rows)
    return [{"order": i, **row} for i, row in enumerate(rows)]


def write_schedule(spec: dict[str, Any], block: int, out: str | Path) -> None:
    rows = schedule_rows(spec, block)
    path = Path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(
            fh,
            fieldnames=["order", "arm", "repeat"],
            lineterminator="\n",
        )
        w.writeheader()
        w.writerows(rows)


def trial_row(path: Path, block: int) -> dict[str, Any]:
    m = FILE_RE.search(path.name)
    if not m:
        raise ValueError(f"unexpected filename {path.name}")
    data = json.loads(path.read_text())
    return {
        "block": block,
        "order": int(m.group("order")),
        "arm": m.group("arm"),
        "repeat": int(m.group("rep")),
        "status": data["status"],
        "pageout_success": bool(data["pageout"]["success"]),
        "reclaim_success": data["reclaim"]["success"],
        "target_drop": float(data["derived"]["target_residency_drop"]),
        "control_drop": float(data["derived"]["control_residency_drop"]),
        "target_minus_control_drop": float(data["derived"]["target_minus_control_drop"]),
        "swap_growth_pageout_mib": float(data["derived"]["swap_growth_after_pageout_bytes"]) / (1024 * 1024),
        "swap_growth_reclaim_mib": float(data["derived"]["swap_growth_after_reclaim_bytes"]) / (1024 * 1024),
        "target_retouch_ms": float(data["retouch"]["target_ns"]) / 1e6,
        "control_retouch_ms": float(data["retouch"]["control_ns"]) / 1e6,
        "content_ok": bool(
            data["checks"]["target_content_match"]
            and data["checks"]["control_content_match"]
        ),
        "oom": not bool(data["checks"]["no_oom"]),
    }


def collect(root: Path) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    dirs = sorted(root.glob("block-*")) + sorted(root.glob("env004-block-*"))
    for d in dirs:
        m = BLOCK_RE.search(d.name)
        if not m:
            continue
        block = int(m.group("block"))
        for path in sorted((d / "raw").glob("trial-*.json")):
            rows.append(trial_row(path, block))
    if not rows:
        raise ValueError("no ENV-004 evidence")
    return pd.DataFrame(rows)


def analyze(spec: dict[str, Any], root: str | Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    trials = collect(Path(root))
    expected = int(spec["runner_blocks"]) * len(spec["arms"]) * int(spec["repeats_per_arm_per_block"])

    checks = {
        "all_trials_complete": len(trials) == expected,
        "all_pageout_calls_succeed": bool(trials["pageout_success"].all()),
        "all_reclaim_calls_succeed_in_reclaim_arm": bool(
            trials[trials["arm"] == "pageout_plus_reclaim"]["reclaim_success"].eq(True).all()
        ),
        "no_oom": bool((~trials["oom"]).all()),
        "content_integrity": bool(trials["content_ok"].all()),
    }

    arm_summary = {}
    for arm in spec["arms"]:
        g = trials[trials["arm"] == arm]
        arm_summary[arm] = {
            "trials": len(g),
            "median_target_drop": float(np.median(g["target_drop"])),
            "median_control_drop": float(np.median(g["control_drop"])),
            "median_target_minus_control_drop": float(np.median(g["target_minus_control_drop"])),
            "median_target_retouch_ms": float(np.median(g["target_retouch_ms"])),
            "median_control_retouch_ms": float(np.median(g["control_retouch_ms"])),
            "median_swap_growth_reclaim_mib": float(np.median(g["swap_growth_reclaim_mib"])),
        }

    summary = {
        "experiment_id": "ENV-004",
        "execution_status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "runner_blocks": int(trials["block"].nunique()),
        "total_trials": len(trials),
        "arm_summary": arm_summary,
        "authority_boundary": (
            "This probe characterizes pageout + memcg proactive reclaim as an instrument. "
            "It does not establish a semantic performance mechanism."
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
