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
    r"trial-(?P<order>\d+)-high(?P<high>\d+)-(?P<arm>mmap|buffered_pread|direct_pread)\.json$"
)
BLOCK_RE = re.compile(r"(?:strata001-)?block-(?P<block>\d+)$")


def load_spec(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def schedule_rows(spec: dict[str, Any], block: int) -> list[dict[str, Any]]:
    if int(spec["trials_per_cell_per_block"]) != 1:
        raise ValueError("STRATA-001-PILOT-v1 requires one trial per cell per block")

    rows = [
        {"memory_high_mib": int(level), "arm": str(arm)}
        for level in spec["memory_high_mib"]
        for arm in spec["arms"]
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
            fieldnames=["order", "memory_high_mib", "arm"],
            lineterminator="\n",
        )
        w.writeheader()
        w.writerows(schedule_rows(spec, block))


def collect(root: Path) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    dirs = sorted(root.glob("block-*")) + sorted(root.glob("strata001-block-*"))

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
            pre = z["cgroup"]["pre_retouch"]
            rows.append({
                "block": block,
                "order": int(fm.group("order")),
                "memory_high_mib": int(fm.group("high")),
                "arm": fm.group("arm"),
                "status": z["status"],
                "hot_resident_fraction": float(
                    z["hot"]["pre_retouch_residency"]["resident_fraction"]
                ),
                "file_pre_fraction": float(
                    z["file"]["pre_scan_residency"]["resident_fraction"]
                ),
                "file_post_fraction": float(
                    z["file"]["post_scan_residency"]["resident_fraction"]
                ),
                "hot_retouch_ms": float(z["hot"]["retouch_ns"]) / 1e6,
                "scan_ms": float(z["scan"]["elapsed_ns"]) / 1e6,
                "work_ms": float(z["work_interval_ns"]) / 1e6,
                "cgroup_anon_mib": float(pre["memory_stat"]["anon"]) / (1024 * 1024),
                "cgroup_file_mib": float(pre["memory_stat"]["file"]) / (1024 * 1024),
                "swap_mib": float(pre["memory_swap_current"]) / (1024 * 1024),
                "pswpin": int(z["retouch_deltas"]["pswpin"]),
                "refault_anon": int(z["retouch_deltas"]["workingset_refault_anon"]),
                "pgmajfault": int(z["retouch_deltas"]["pgmajfault"]),
                "pgscan": int(z["retouch_deltas"]["pgscan"]),
                "pgsteal": int(z["retouch_deltas"]["pgsteal"]),
                "direct_io": bool(z["scan"]["direct_io"]),
                "scan_error": z["scan"]["error"],
                "content_integrity": bool(z["checks"]["content_integrity"]),
                "no_oom": bool(z["checks"]["no_oom"]),
            })
    if not rows:
        raise ValueError("no STRATA-001 pilot evidence found")
    return pd.DataFrame(rows)


def paired_effects(trials: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (block, level), g in trials.groupby(["block", "memory_high_mib"]):
        by_arm = g.set_index("arm")
        direct = by_arm.loc["direct_pread"]
        buffered = by_arm.loc["buffered_pread"]
        rows.append({
            "block": int(block),
            "memory_high_mib": int(level),
            "hot_residency_diff_direct_minus_buffered": float(
                direct["hot_resident_fraction"] - buffered["hot_resident_fraction"]
            ),
            "log_hot_retouch_ratio_direct_over_buffered": float(
                math.log(max(float(direct["hot_retouch_ms"]), 1e-12))
                - math.log(max(float(buffered["hot_retouch_ms"]), 1e-12))
            ),
            "work_ratio_direct_over_buffered": float(
                direct["work_ms"] / max(float(buffered["work_ms"]), 1e-12)
            ),
            "file_cache_diff_direct_minus_buffered": float(
                direct["file_post_fraction"] - buffered["file_post_fraction"]
            ),
        })
    return pd.DataFrame(rows).sort_values(["block", "memory_high_mib"])


def analyze(spec: dict[str, Any], root: str | Path) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    trials = collect(Path(root))
    blocks = int(spec["runner_blocks"])
    levels = [int(x) for x in spec["memory_high_mib"]]
    arms = [str(x) for x in spec["arms"]]

    expected_cells = {(level, arm) for level in levels for arm in arms}
    cells_ok = True
    for _, g in trials.groupby("block"):
        got = list(zip(g["memory_high_mib"], g["arm"]))
        if len(got) != len(expected_cells) or set(got) != expected_cells:
            cells_ok = False
            break

    checks = {
        "six_runner_blocks_present": int(trials["block"].nunique()) == blocks,
        "thirty_six_trials_present": len(trials) == int(spec["expected_trials"]),
        "all_trials_valid": bool((trials["status"] == "PASS").all()),
        "no_oom": bool(trials["no_oom"].all()),
        "all_cells_present_once_per_block": cells_ok,
        "direct_io_no_fallback": bool(
            trials.loc[trials["arm"] == "direct_pread", "direct_io"].all()
        ),
        "file_cold_before_each_scan": bool(
            (
                trials["file_pre_fraction"]
                <= float(spec["file_prepare"]["require_precache_fraction_le"])
            ).all()
        ),
        "content_integrity": bool(trials["content_integrity"].all()),
    }

    pairs = paired_effects(trials)

    cells: dict[str, Any] = {}
    for level in levels:
        for arm in arms:
            g = trials[
                (trials["memory_high_mib"] == level)
                & (trials["arm"] == arm)
            ]
            cells[f"{level}:{arm}"] = {
                "trials": int(len(g)),
                "median_hot_resident_fraction": float(np.median(g["hot_resident_fraction"])),
                "median_file_post_fraction": float(np.median(g["file_post_fraction"])),
                "median_hot_retouch_ms": float(np.median(g["hot_retouch_ms"])),
                "median_scan_ms": float(np.median(g["scan_ms"])),
                "median_work_ms": float(np.median(g["work_ms"])),
                "median_cgroup_anon_mib": float(np.median(g["cgroup_anon_mib"])),
                "median_cgroup_file_mib": float(np.median(g["cgroup_file_mib"])),
                "median_swap_mib": float(np.median(g["swap_mib"])),
            }

    paired_summary: dict[str, Any] = {}
    for level in levels:
        g = pairs[pairs["memory_high_mib"] == level]
        paired_summary[str(level)] = {
            "blocks": int(len(g)),
            "hot_residency_diff_direct_minus_buffered": {
                "median": float(np.median(g["hot_residency_diff_direct_minus_buffered"])),
                "values": [
                    float(x)
                    for x in g["hot_residency_diff_direct_minus_buffered"].to_numpy()
                ],
            },
            "log_hot_retouch_ratio_direct_over_buffered": {
                "median": float(np.median(g["log_hot_retouch_ratio_direct_over_buffered"])),
                "values": [
                    float(x)
                    for x in g["log_hot_retouch_ratio_direct_over_buffered"].to_numpy()
                ],
            },
            "work_ratio_direct_over_buffered": {
                "median": float(np.median(g["work_ratio_direct_over_buffered"])),
                "values": [
                    float(x)
                    for x in g["work_ratio_direct_over_buffered"].to_numpy()
                ],
            },
        }

    summary = {
        "experiment_id": spec["experiment_id"],
        "execution_status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "runner_blocks": int(trials["block"].nunique()),
        "total_trials": int(len(trials)),
        "cells": cells,
        "paired_primary": paired_summary,
        "inference_boundary": (
            "Pilot only: estimates effect direction and block-level variance. "
            "No hypothesis-support decision is authorized."
        ),
        "next_step": spec["next_step"],
    }
    return trials, pairs, summary


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

    trials, pairs, summary = analyze(spec, args.input_root)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    trials.sort_values(["block", "order"]).to_csv(out / "trials.csv", index=False)
    pairs.to_csv(out / "block-pairs.csv", index=False)
    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    if summary["execution_status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
