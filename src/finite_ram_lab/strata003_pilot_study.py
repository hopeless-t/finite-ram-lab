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


ARMS = [
    "buffered",
    "dontneed_4m",
    "dontneed_8m",
    "dontneed_16m",
    "dontneed_32m",
    "dontneed_96m",
    "direct",
]

FILE_RE = re.compile(
    r"trial-(?P<order>\d+)-(?P<arm>buffered|dontneed_4m|dontneed_8m|dontneed_16m|dontneed_32m|dontneed_96m|direct)\.json$"
)
BLOCK_RE = re.compile(r"(?:(?:strata003(?:-pilot)?-)?block)-(?P<block>\d+)$")


def load_spec(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def schedule_rows(spec: dict[str, Any], block: int) -> list[dict[str, Any]]:
    if int(spec["trials_per_arm_per_block"]) != 1:
        raise ValueError("STRATA-003-PILOT-v1 requires one trial per arm per block")
    rows = [{"arm": str(arm)} for arm in spec["arms"]]
    rng = random.Random(int(spec["base_schedule_seed"]) + block * 1009)
    rng.shuffle(rows)
    return [{"order": i, **row} for i, row in enumerate(rows)]


def write_schedule(spec: dict[str, Any], block: int, out: str | Path) -> None:
    path = Path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["order", "arm"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(schedule_rows(spec, block))


def collect(root: Path) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    dirs = (
        sorted(root.glob("block-*"))
        + sorted(root.glob("strata003-block-*"))
        + sorted(root.glob("strata003-pilot-block-*"))
    )
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
            post = z["cgroup"]["post_scan"]
            rows.append({
                "block": block,
                "order": int(fm.group("order")),
                "arm": fm.group("arm"),
                "status": z["status"],
                "release_interval_mib": z["parameters"]["release_interval_mib"],
                "advice_success": bool(z["scan"]["advice"]["success"]),
                "advice_calls": int(z["scan"]["advice"]["calls"]),
                "direct_io": bool(z["scan"]["direct_io"]),
                "file_pre_fraction": float(z["file"]["pre_scan_residency"]["resident_fraction"]),
                "file_post_fraction": float(z["file"]["post_scan_residency"]["resident_fraction"]),
                "memory_high_events": int(z["scan_deltas"]["memory_high_events"]),
                "max_scan_memory_mib": float(z["scan_deltas"]["max_memory_current"]) / (1024 * 1024),
                "max_scan_file_mib": float(z["scan_deltas"]["max_cgroup_file"]) / (1024 * 1024),
                "post_scan_memory_mib": float(post["memory_current"]) / (1024 * 1024),
                "post_scan_file_mib": float(post["memory_stat"]["file"]) / (1024 * 1024),
                "scan_ms": float(z["scan"]["elapsed_ns"]) / 1e6,
                "throughput_mib_s": float(z["parameters"]["cold_file_mib"]) / max(float(z["scan"]["elapsed_ns"]) / 1e9, 1e-12),
                "hot_resident_fraction": float(z["hot"]["pre_retouch_residency"]["resident_fraction"]),
                "hot_retouch_ms": float(z["hot"]["retouch_ns"]) / 1e6,
                "swap_mib": float(post["memory_swap_current"]) / (1024 * 1024),
                "content_integrity": bool(z["checks"]["content_integrity"]),
                "no_oom": bool(z["checks"]["no_oom"]),
                "release_ranges_page_aligned": bool(z["checks"]["release_ranges_page_aligned"]),
            })
    if not rows:
        raise ValueError("no STRATA-003 pilot evidence found")
    return pd.DataFrame(rows)


def paired_effects(trials: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for block, g in trials.groupby("block"):
        by = g.set_index("arm")
        base = by.loc["buffered"]
        for arm in [a for a in ARMS if a != "buffered"]:
            x = by.loc[arm]
            base_events = float(base["memory_high_events"])
            pae = (
                1.0 - float(x["memory_high_events"]) / base_events
                if base_events > 0
                else np.nan
            )
            rows.append({
                "block": int(block),
                "arm": arm,
                "pressure_avoidance_efficiency": pae,
                "high_events_diff_vs_buffered": float(
                    x["memory_high_events"] - base["memory_high_events"]
                ),
                "transient_footprint_reduction": float(
                    1.0 - x["max_scan_memory_mib"] / max(float(base["max_scan_memory_mib"]), 1e-12)
                ),
                "final_footprint_reduction": float(
                    1.0 - x["post_scan_memory_mib"] / max(float(base["post_scan_memory_mib"]), 1e-12)
                ),
                "scan_ratio_vs_buffered": float(
                    x["scan_ms"] / max(float(base["scan_ms"]), 1e-12)
                ),
                "advice_density_calls_per_gib": float(
                    x["advice_calls"] / (96.0 / 1024.0)
                ),
            })
    return pd.DataFrame(rows).sort_values(["arm", "block"])


def analyze(spec: dict[str, Any], root: str | Path) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    trials = collect(Path(root))
    blocks = int(spec["runner_blocks"])
    arms = [str(x) for x in spec["arms"]]

    cells_ok = True
    for _, g in trials.groupby("block"):
        got = list(g["arm"])
        if len(got) != len(arms) or set(got) != set(arms):
            cells_ok = False
            break

    advice_rows = trials[trials["arm"].str.startswith("dontneed_")]
    direct_rows = trials[trials["arm"] == "direct"]

    checks = {
        "eight_runner_blocks_present": int(trials["block"].nunique()) == blocks,
        "fifty_six_trials_present": len(trials) == int(spec["expected_trials"]),
        "all_trials_valid": bool((trials["status"] == "PASS").all()),
        "all_arms_once_per_block": cells_ok,
        "file_cold_before_each_scan": bool(
            (trials["file_pre_fraction"] <= float(spec["file_prepare"]["require_precache_fraction_le"])).all()
        ),
        "release_ranges_page_aligned": bool(advice_rows["release_ranges_page_aligned"].all()),
        "advice_success": bool(advice_rows["advice_success"].all()),
        "direct_no_fallback": bool(direct_rows["direct_io"].all()),
        "content_integrity": bool(trials["content_integrity"].all()),
        "no_oom": bool(trials["no_oom"].all()),
    }

    pairs = paired_effects(trials)

    cells: dict[str, Any] = {}
    for arm in arms:
        g = trials[trials["arm"] == arm]
        cells[arm] = {
            "trials": int(len(g)),
            "release_interval_mib": (
                None if g["release_interval_mib"].isna().all()
                else float(g["release_interval_mib"].dropna().iloc[0])
            ),
            "median_advice_calls": float(np.median(g["advice_calls"])),
            "median_memory_high_events": float(np.median(g["memory_high_events"])),
            "median_max_scan_memory_mib": float(np.median(g["max_scan_memory_mib"])),
            "median_post_scan_memory_mib": float(np.median(g["post_scan_memory_mib"])),
            "median_file_post_fraction": float(np.median(g["file_post_fraction"])),
            "median_max_scan_file_mib": float(np.median(g["max_scan_file_mib"])),
            "median_post_scan_file_mib": float(np.median(g["post_scan_file_mib"])),
            "median_scan_ms": float(np.median(g["scan_ms"])),
            "median_throughput_mib_s": float(np.median(g["throughput_mib_s"])),
            "median_hot_resident_fraction": float(np.median(g["hot_resident_fraction"])),
            "median_hot_retouch_ms": float(np.median(g["hot_retouch_ms"])),
            "median_swap_mib": float(np.median(g["swap_mib"])),
        }

    response: dict[str, Any] = {}
    for arm in [a for a in arms if a != "buffered"]:
        g = pairs[pairs["arm"] == arm]
        response[arm] = {
            "blocks": int(len(g)),
            "median_pressure_avoidance_efficiency": (
                None if g["pressure_avoidance_efficiency"].isna().all()
                else float(np.nanmedian(g["pressure_avoidance_efficiency"]))
            ),
            "median_transient_footprint_reduction": float(
                np.median(g["transient_footprint_reduction"])
            ),
            "median_final_footprint_reduction": float(
                np.median(g["final_footprint_reduction"])
            ),
            "median_scan_ratio_vs_buffered": float(
                np.median(g["scan_ratio_vs_buffered"])
            ),
            "median_advice_density_calls_per_gib": float(
                np.median(g["advice_density_calls_per_gib"])
            ),
            "high_events_diff_values": [
                float(x) for x in g["high_events_diff_vs_buffered"].to_numpy()
            ],
            "scan_ratio_values": [
                float(x) for x in g["scan_ratio_vs_buffered"].to_numpy()
            ],
        }

    summary = {
        "experiment_id": spec["experiment_id"],
        "execution_status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "runner_blocks": int(trials["block"].nunique()),
        "total_trials": int(len(trials)),
        "cells": cells,
        "response_surface": response,
        "selection": "NONE_PILOT_RESPONSE_SURFACE_ONLY",
        "inference_boundary": "Pilot only; do not freeze an OSS default cadence from this result alone.",
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
