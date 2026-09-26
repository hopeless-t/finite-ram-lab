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
from scipy.stats import rankdata, spearmanr


FILE_RE = re.compile(
    r"timeline-(?P<order>\d+)-high(?P<high>\d+)-rep(?P<rep>\d+)\.json$"
)
BLOCK_RE = re.compile(r"(?:obs002-)?block-(?P<block>\d+)$")


def load_spec(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def schedule_rows(spec: dict[str, Any], block: int) -> list[dict[str, int]]:
    rows: list[dict[str, int]] = []
    for condition in spec["conditions"]:
        level = int(condition["memory_high_mib"])
        for repeat in range(int(condition["repeats_per_block"])):
            rows.append({"memory_high_mib": level, "repeat": repeat})
    rng = random.Random(int(spec["base_schedule_seed"]) + block * 1009)
    rng.shuffle(rows)
    return [{"order": i, **row} for i, row in enumerate(rows)]


def write_schedule(spec: dict[str, Any], block: int, out: str | Path) -> None:
    path = Path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["order", "repeat", "memory_high_mib"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(schedule_rows(spec, block))


def _phase(data: dict[str, Any], name: str) -> dict[str, Any]:
    for event in data["timeline"]:
        if event["phase"] == name:
            return event
    raise ValueError(f"missing phase {name}")


def _delta_stat(a: dict[str, Any], b: dict[str, Any], key: str) -> int:
    return int(b["os"]["memory_stat"].get(key, 0) - a["os"]["memory_stat"].get(key, 0))


def _delta_event(a: dict[str, Any], b: dict[str, Any], key: str) -> int:
    return int(b["os"]["memory_events"].get(key, 0) - a["os"]["memory_events"].get(key, 0))


def trial_row(path: Path, block: int) -> dict[str, Any]:
    match = FILE_RE.search(path.name)
    if not match:
        raise ValueError(f"unexpected evidence filename: {path.name}")

    data = json.loads(path.read_text())
    baseline = _phase(data, "BASELINE")
    burst = _phase(data, "BURST_ALLOC")
    retouch = _phase(data, "HOTSET_RETOUCH")

    hot_before = burst["regions"]["hotset"]
    burst_before = burst["regions"]["burst"]
    hot_after = retouch["regions"]["hotset"]

    return {
        "block": block,
        "order": int(match.group("order")),
        "repeat": int(match.group("rep")),
        "memory_high_mib": int(match.group("high")),
        "status": data["status"],
        "mincore_supported": bool(data["checks"].get("mincore_supported")),
        "retouch_latency_ms": float(retouch.get("phase_latency_ns", 0)) / 1e6,
        "burst_alloc_latency_ms": float(burst.get("phase_latency_ns", 0)) / 1e6,
        "hotset_total_pages": int(hot_before["total_pages"]),
        "hotset_resident_pages_after_burst": int(hot_before["resident_pages"]),
        "hotset_missing_pages_after_burst": int(hot_before["missing_pages"]),
        "hotset_resident_fraction_after_burst": float(hot_before["resident_fraction"]),
        "burst_resident_fraction_after_burst": float(burst_before["resident_fraction"]),
        "hotset_resident_fraction_after_retouch": float(hot_after["resident_fraction"]),
        "hotset_mincore_ns_after_burst": int(hot_before["mincore_duration_ns"]),
        "burst_mincore_ns_after_burst": int(burst_before["mincore_duration_ns"]),
        "swap_mib_after_burst": float(burst["os"]["memory_swap_current"]) / (1024 * 1024),
        "retouch_pswpin_pages": _delta_stat(burst, retouch, "pswpin"),
        "retouch_pswpout_pages": _delta_stat(burst, retouch, "pswpout"),
        "retouch_refault_anon": _delta_stat(burst, retouch, "workingset_refault_anon"),
        "retouch_pgmajfault": _delta_stat(burst, retouch, "pgmajfault"),
        "retouch_pgfault": _delta_stat(burst, retouch, "pgfault"),
        "retouch_pgscan": _delta_stat(burst, retouch, "pgscan"),
        "retouch_pgsteal": _delta_stat(burst, retouch, "pgsteal"),
        "retouch_high_events": _delta_event(burst, retouch, "high"),
        "oom_delta": _delta_event(baseline, retouch, "oom"),
        "oom_kill_delta": _delta_event(baseline, retouch, "oom_kill"),
    }


def collect(root: Path) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    dirs = sorted(root.glob("block-*")) + sorted(root.glob("obs002-block-*"))
    for block_dir in dirs:
        match = BLOCK_RE.search(block_dir.name)
        if not match:
            continue
        block = int(match.group("block"))
        for path in sorted((block_dir / "raw").glob("timeline-*.json")):
            rows.append(trial_row(path, block))
    if not rows:
        raise ValueError("no OBS-002 evidence found")
    return pd.DataFrame(rows)


def _within_block_permutation_p(
    transition: pd.DataFrame,
    predictor: str,
    outcome: str,
    permutations: int,
    seed: int,
) -> dict[str, float]:
    rng = np.random.default_rng(seed)
    x = transition[predictor].to_numpy(dtype=float)
    y = transition[outcome].to_numpy(dtype=float)
    blocks = transition["block"].to_numpy(dtype=int)
    unique_blocks = np.unique(blocks)

    xr = rankdata(x)
    yr = rankdata(y)
    xc = xr - xr.mean()
    yc = yr - yr.mean()
    denom = float(np.sqrt(np.sum(xc * xc) * np.sum(yc * yc)))
    if denom == 0:
        raise ValueError("permutation correlation is undefined for a constant variable")
    obs = float(np.sum(xc * yc) / denom)

    block_indices = [np.flatnonzero(blocks == block) for block in unique_blocks]
    exceed = 0
    for _ in range(permutations):
        yp = yc.copy()
        for idx in block_indices:
            yp[idx] = yc[rng.permutation(idx)]
        rho = float(np.sum(xc * yp) / denom)
        if abs(rho) >= abs(obs):
            exceed += 1

    return {
        "spearman_rho": obs,
        "permutations": permutations,
        "two_sided_p": (exceed + 1) / (permutations + 1),
    }


def _cluster_bootstrap_rho(
    transition: pd.DataFrame,
    predictor: str,
    outcome: str,
    resamples: int,
    seed: int,
) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    blocks = np.array(sorted(transition["block"].unique()), dtype=int)
    values = np.empty(resamples, dtype=float)

    groups = {b: transition[transition["block"] == b] for b in blocks}
    for i in range(resamples):
        chosen = rng.choice(blocks, size=len(blocks), replace=True)
        sample = pd.concat([groups[int(b)] for b in chosen], ignore_index=True)
        values[i] = float(spearmanr(sample[predictor], sample[outcome]).statistic)

    return {
        "resamples": resamples,
        "seed": seed,
        "median_rho": float(np.nanmedian(values)),
        "ci95": [
            float(np.nanquantile(values, 0.025)),
            float(np.nanquantile(values, 0.975)),
        ],
    }


def analyze(spec: dict[str, Any], root: str | Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    trials = collect(Path(root))
    transition_level = next(
        int(c["memory_high_mib"])
        for c in spec["conditions"]
        if c["role"] == "transition_zone"
    )
    transition = trials[trials["memory_high_mib"] == transition_level].copy()

    blocks_expected = int(spec["runner_blocks"])
    expected_trials = blocks_expected * sum(
        int(c["repeats_per_block"]) for c in spec["conditions"]
    )

    checks = {
        "eight_blocks_present": int(trials["block"].nunique()) == blocks_expected,
        "48_trials_present": len(trials) == expected_trials,
        "all_trials_pass": bool((trials["status"] == "PASS").all()),
        "no_oom": bool(((trials["oom_delta"] + trials["oom_kill_delta"]) == 0).all()),
        "mincore_supported": bool(trials["mincore_supported"].all()),
        "controls_present_in_each_block": all(
            {160, 168}.issubset(set(group["memory_high_mib"].astype(int)))
            for _, group in trials.groupby("block")
        ),
    }

    primary_perm = _within_block_permutation_p(
        transition,
        "hotset_resident_fraction_after_burst",
        "retouch_latency_ms",
        100000,
        int(spec["base_schedule_seed"]) + 701,
    )
    primary_boot = _cluster_bootstrap_rho(
        transition,
        "hotset_resident_fraction_after_burst",
        "retouch_latency_ms",
        5000,
        int(spec["base_schedule_seed"]) + 1701,
    )

    missing_vs_swapin = _within_block_permutation_p(
        transition,
        "hotset_missing_pages_after_burst",
        "retouch_pswpin_pages",
        100000,
        int(spec["base_schedule_seed"]) + 2701,
    )

    controls: dict[str, Any] = {}
    for level in (160, 164, 168):
        g = trials[trials["memory_high_mib"] == level]
        controls[str(level)] = {
            "trials": len(g),
            "median_retouch_latency_ms": float(np.median(g["retouch_latency_ms"])),
            "median_hotset_resident_fraction_after_burst": float(
                np.median(g["hotset_resident_fraction_after_burst"])
            ),
            "median_hotset_missing_pages_after_burst": float(
                np.median(g["hotset_missing_pages_after_burst"])
            ),
            "median_swap_mib_after_burst": float(np.median(g["swap_mib_after_burst"])),
            "median_retouch_pswpin_pages": float(np.median(g["retouch_pswpin_pages"])),
        }

    mincore_ns = pd.concat(
        [
            trials["hotset_mincore_ns_after_burst"],
            trials["burst_mincore_ns_after_burst"],
        ],
        ignore_index=True,
    ).to_numpy(dtype=float)

    summary = {
        "experiment_id": "OBS-002",
        "execution_status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "total_trials": len(trials),
        "runner_blocks": int(trials["block"].nunique()),
        "transition_trials": len(transition),
        "controls": controls,
        "primary_relationship": {
            "predictor": "hotset_resident_fraction_after_burst",
            "outcome": "retouch_latency_ms",
            "within_block_permutation": primary_perm,
            "cluster_bootstrap": primary_boot,
        },
        "supporting_relationship": {
            "predictor": "hotset_missing_pages_after_burst",
            "outcome": "retouch_pswpin_pages",
            "within_block_permutation": missing_vs_swapin,
        },
        "mincore_call_duration_ns": {
            "median": float(np.median(mincore_ns)),
            "p95": float(np.quantile(mincore_ns, 0.95)),
            "max": float(np.max(mincore_ns)),
        },
        "interpretation_boundary": (
            "Association between semantic-region residency and latency does not by itself "
            "prove that an application hint or coordination mechanism would improve Linux."
        ),
    }
    return trials, summary


def write_outputs(spec: dict[str, Any], root: str | Path, out_dir: str | Path) -> dict[str, Any]:
    trials, summary = analyze(spec, root)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    trials.sort_values(["block", "order"]).to_csv(out / "trials.csv", index=False)
    trials[trials["memory_high_mib"] == 164].sort_values(["block", "order"]).to_csv(
        out / "transition-164.csv", index=False
    )
    (out / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    return summary


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
        write_schedule(spec, args.block, args.out)
        return

    summary = write_outputs(spec, args.input_root, args.out_dir)
    print(json.dumps(summary, indent=2, sort_keys=True))
    if summary["execution_status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
