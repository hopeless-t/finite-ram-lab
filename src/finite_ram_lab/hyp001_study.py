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
    r"timeline-(?P<order>\d+)-high(?P<high>\d+)-(?P<arm>aligned|misaligned|control)-(?P<recent>A|B)-rep(?P<rep>\d+)\.json$"
)
BLOCK_RE = re.compile(r"(?:hyp001-)?block-(?P<block>\d+)$")


def load_spec(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def schedule_rows(spec: dict[str, Any], block: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    primary = int(spec["primary_level_mib"])
    reps = int(spec["primary_repeats_per_arm_per_block"])

    # Exact balance: 3 A-recent and 3 B-recent within each primary arm.
    if reps % 2:
        raise ValueError("primary repeats per arm must be even")
    per_identity = reps // 2
    for arm in spec["primary_arms"]:
        for recent in ("A", "B"):
            for rep in range(per_identity):
                rows.append(
                    {
                        "memory_high_mib": primary,
                        "arm": arm,
                        "recent_identity": recent,
                        "repeat": rep,
                    }
                )

    for i, level in enumerate(spec["control_levels_mib"]):
        rows.append(
            {
                "memory_high_mib": int(level),
                "arm": "control",
                "recent_identity": "A" if (block + i) % 2 == 0 else "B",
                "repeat": 0,
            }
        )

    rng = random.Random(int(spec["base_schedule_seed"]) + block * 1009)
    rng.shuffle(rows)
    return [{"order": i, **row} for i, row in enumerate(rows)]


def write_schedule(spec: dict[str, Any], block: int, out: str | Path) -> None:
    rows = schedule_rows(spec, block)
    path = Path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["order", "memory_high_mib", "arm", "recent_identity", "repeat"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def _phase(data: dict[str, Any], name: str) -> dict[str, Any]:
    return next(e for e in data["timeline"] if e["phase"] == name)


def _delta_stat(a: dict[str, Any], b: dict[str, Any], key: str) -> int:
    return int(b["os"]["memory_stat"].get(key, 0) - a["os"]["memory_stat"].get(key, 0))


def _delta_event(a: dict[str, Any], b: dict[str, Any], key: str) -> int:
    return int(b["os"]["memory_events"].get(key, 0) - a["os"]["memory_events"].get(key, 0))


def trial_row(path: Path, block: int) -> dict[str, Any]:
    m = FILE_RE.search(path.name)
    if not m:
        raise ValueError(f"unexpected filename: {path.name}")
    data = json.loads(path.read_text())
    base = _phase(data, "BASELINE")
    burst = _phase(data, "BURST_ALLOC")
    retouch = _phase(data, "TARGET_RETOUCH")

    return {
        "block": block,
        "order": int(m.group("order")),
        "memory_high_mib": int(m.group("high")),
        "arm": m.group("arm"),
        "recent_identity": m.group("recent"),
        "repeat": int(m.group("rep")),
        "status": data["status"],
        "target_identity": retouch["target_identity"],
        "retouch_latency_ms": float(retouch["phase_latency_ns"]) / 1e6,
        "swap_mib_after_burst": float(burst["os"]["memory_swap_current"]) / (1024 * 1024),
        "retouch_pswpin_pages": _delta_stat(burst, retouch, "pswpin"),
        "retouch_refault_anon": _delta_stat(burst, retouch, "workingset_refault_anon"),
        "retouch_pgmajfault": _delta_stat(burst, retouch, "pgmajfault"),
        "retouch_pgfault": _delta_stat(burst, retouch, "pgfault"),
        "retouch_pgscan": _delta_stat(burst, retouch, "pgscan"),
        "retouch_pgsteal": _delta_stat(burst, retouch, "pgsteal"),
        "retouch_high_events": _delta_event(burst, retouch, "high"),
        "oom_delta": _delta_event(base, retouch, "oom"),
        "oom_kill_delta": _delta_event(base, retouch, "oom_kill"),
    }


def collect(root: Path) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    dirs = sorted(root.glob("block-*")) + sorted(root.glob("hyp001-block-*"))
    for d in dirs:
        m = BLOCK_RE.search(d.name)
        if not m:
            continue
        block = int(m.group("block"))
        for path in sorted((d / "raw").glob("timeline-*.json")):
            rows.append(trial_row(path, block))
    if not rows:
        raise ValueError("no HYP-001 evidence found")
    return pd.DataFrame(rows)


def _block_contrasts(primary: pd.DataFrame, outcome: str) -> pd.DataFrame:
    rows = []
    for block, g in primary.groupby("block", sort=True):
        aligned = g[g["arm"] == "aligned"][outcome].to_numpy(dtype=float)
        misaligned = g[g["arm"] == "misaligned"][outcome].to_numpy(dtype=float)
        if len(aligned) == 0 or len(misaligned) == 0:
            raise ValueError(f"block {block} lacks an arm")
        if outcome == "retouch_latency_ms":
            aligned = np.log(np.maximum(aligned, 1e-9))
            misaligned = np.log(np.maximum(misaligned, 1e-9))
        diff = float(misaligned.mean() - aligned.mean())
        rows.append({"block": int(block), "difference": diff})
    return pd.DataFrame(rows)


def _exact_signflip(contrasts: np.ndarray) -> dict[str, Any]:
    n = len(contrasts)
    if n > 22:
        raise ValueError("exact sign-flip is intentionally capped at 22 blocks")
    observed = float(np.mean(contrasts))
    exceed = 0
    total = 1 << n
    for mask in range(total):
        signs = np.fromiter(
            (1.0 if (mask >> i) & 1 else -1.0 for i in range(n)),
            dtype=float,
            count=n,
        )
        value = float(np.mean(contrasts * signs))
        if abs(value) >= abs(observed) - 1e-15:
            exceed += 1
    return {
        "blocks": n,
        "observed_mean_log_difference": observed,
        "geometric_mean_ratio_misaligned_over_aligned": math.exp(observed),
        "exact_permutations": total,
        "two_sided_p": exceed / total,
    }


def _bootstrap_ratio(contrasts: np.ndarray, resamples: int, seed: int) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    estimates = np.empty(resamples)
    n = len(contrasts)
    for i in range(resamples):
        sample = contrasts[rng.integers(0, n, size=n)]
        estimates[i] = math.exp(float(np.mean(sample)))
    return {
        "resamples": resamples,
        "median_ratio": float(np.median(estimates)),
        "ci95": [
            float(np.quantile(estimates, 0.025)),
            float(np.quantile(estimates, 0.975)),
        ],
    }


def analyze(spec: dict[str, Any], root: str | Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    trials = collect(Path(root))
    primary_level = int(spec["primary_level_mib"])
    primary = trials[
        (trials["memory_high_mib"] == primary_level)
        & trials["arm"].isin(spec["primary_arms"])
    ].copy()

    expected_blocks = int(spec["runner_blocks"])
    expected_trials = expected_blocks * (
        2 * int(spec["primary_repeats_per_arm_per_block"])
        + len(spec["control_levels_mib"]) * int(spec["control_trials_per_level_per_block"])
    )

    checks = {
        "twenty_blocks_present": int(trials["block"].nunique()) == expected_blocks,
        "280_trials_present": len(trials) == expected_trials,
        "all_trials_pass": bool((trials["status"] == "PASS").all()),
        "no_oom": bool(((trials["oom_delta"] + trials["oom_kill_delta"]) == 0).all()),
        "primary_arms_balanced": all(
            (g["arm"].value_counts().get("aligned", 0) == g["arm"].value_counts().get("misaligned", 0))
            for _, g in primary.groupby("block")
        ),
        "recent_identity_balanced": all(
            all(
                armg["recent_identity"].value_counts().get(k, 0)
                == len(armg) // 2
                for k in ("A", "B")
            )
            for _, g in primary.groupby("block")
            for _, armg in g.groupby("arm")
        ),
    }

    latency_contrasts = _block_contrasts(primary, "retouch_latency_ms")
    exact = _exact_signflip(latency_contrasts["difference"].to_numpy(dtype=float))
    boot = _bootstrap_ratio(
        latency_contrasts["difference"].to_numpy(dtype=float),
        int(spec["cluster_bootstrap_resamples"]),
        int(spec["base_schedule_seed"]) + 8001,
    )

    secondary = {}
    for metric in ("retouch_pswpin_pages", "retouch_refault_anon", "retouch_pgmajfault"):
        c = _block_contrasts(primary, metric)
        secondary[metric] = {
            "mean_misaligned_minus_aligned": float(c["difference"].mean()),
            "median_block_difference": float(c["difference"].median()),
        }

    controls = {}
    for level in spec["control_levels_mib"]:
        g = trials[trials["memory_high_mib"] == int(level)]
        controls[str(level)] = {
            "trials": len(g),
            "median_latency_ms": float(np.median(g["retouch_latency_ms"])),
            "median_swap_mib_after_burst": float(np.median(g["swap_mib_after_burst"])),
            "median_high_events": float(np.median(g["retouch_high_events"])),
        }

    arm_summary = {}
    for arm in spec["primary_arms"]:
        g = primary[primary["arm"] == arm]
        arm_summary[arm] = {
            "trials": len(g),
            "median_latency_ms": float(np.median(g["retouch_latency_ms"])),
            "p90_latency_ms": float(np.quantile(g["retouch_latency_ms"], 0.90)),
            "median_pswpin_pages": float(np.median(g["retouch_pswpin_pages"])),
            "median_refault_anon": float(np.median(g["retouch_refault_anon"])),
            "median_pgmajfault": float(np.median(g["retouch_pgmajfault"])),
        }

    summary = {
        "experiment_id": "HYP-001",
        "execution_status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "runner_blocks": int(trials["block"].nunique()),
        "total_trials": len(trials),
        "primary_trials": len(primary),
        "primary_level_mib": primary_level,
        "arm_summary": arm_summary,
        "primary_inference": {
            "outcome": "log TARGET_RETOUCH latency",
            "block_contrast": "mean(misaligned)-mean(aligned) within runner",
            "exact_signflip": exact,
            "cluster_bootstrap_ratio": boot,
        },
        "secondary_descriptive": secondary,
        "controls": controls,
        "authority_boundary": (
            "HYP-001 tests matched future-reuse alignment under memcg pressure. "
            "It does not test an application hint or prove a kernel defect."
        ),
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
