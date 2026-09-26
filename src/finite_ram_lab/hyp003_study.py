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


TRIAL_RE = re.compile(r"trial-(?P<order>\d+)\.json$")
BLOCK_RE = re.compile(r"(?:hyp003-)?block-(?P<block>\d+)$")


def load_spec(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def schedule_rows(spec: dict[str, Any], block: int) -> list[dict[str, Any]]:
    rows = [
        {
            "memory_high_mib": int(level),
            "fault_order": fault,
            "hot_position": hot,
        }
        for level in spec["memory_high_mib"]
        for fault in spec["fault_orders"]
        for hot in spec["hot_positions"]
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
                "fault_order",
                "hot_position",
            ],
            lineterminator="\n",
        )
        w.writeheader()
        w.writerows(schedule_rows(spec, block))


def exact_signflip_one_sided(
    values: np.ndarray,
    direction: str,
) -> dict[str, Any]:
    n = len(values)
    if n > 20:
        raise ValueError("exact sign-flip capped at 20 blocks")

    observed = float(values.mean())
    total = 1 << n
    extreme = 0

    for bits in range(total):
        signs = np.fromiter(
            (1.0 if (bits >> i) & 1 else -1.0 for i in range(n)),
            dtype=float,
            count=n,
        )
        estimate = float(np.mean(values * signs))
        if direction == "greater":
            if estimate >= observed - 1e-15:
                extreme += 1
        elif direction == "less":
            if estimate <= observed + 1e-15:
                extreme += 1
        else:
            raise ValueError("direction must be greater or less")

    return {
        "blocks": n,
        "observed_mean": observed,
        "direction": direction,
        "exact_permutations": total,
        "one_sided_p": extreme / total,
    }


def bootstrap_mean(
    values: np.ndarray,
    resamples: int,
    seed: int,
) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    n = len(values)
    estimates = np.empty(resamples, dtype=float)
    for i in range(resamples):
        estimates[i] = float(
            values[rng.integers(0, n, size=n)].mean()
        )
    return {
        "resamples": resamples,
        "seed": seed,
        "median": float(np.median(estimates)),
        "ci95": [
            float(np.quantile(estimates, 0.025)),
            float(np.quantile(estimates, 0.975)),
        ],
    }


def collect(root: Path) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    dirs = sorted(root.glob("block-*")) + sorted(root.glob("hyp003-block-*"))

    for d in dirs:
        bm = BLOCK_RE.search(d.name)
        if not bm:
            continue
        block = int(bm.group("block"))

        for path in sorted((d / "raw").glob("trial-*.json")):
            tm = TRIAL_RE.search(path.name)
            if not tm:
                raise ValueError(f"unexpected filename: {path.name}")

            z = json.loads(path.read_text())
            fault_order = str(z["fault_order"])
            first_faulted, second_faulted = fault_order.split("_")
            hot = str(z["hot_position"])
            hot_fraction = float(
                z["residency_pre_retouch"][hot]["resident_fraction"]
            )
            first_fraction = float(
                z["residency_pre_retouch"][first_faulted][
                    "resident_fraction"
                ]
            )
            second_fraction = float(
                z["residency_pre_retouch"][second_faulted][
                    "resident_fraction"
                ]
            )
            os_pre = z["os_pre_retouch"]

            rows.append({
                "block": block,
                "order": int(tm.group("order")),
                "memory_high_mib": (
                    int(os_pre["memory_high"]) // (1024 * 1024)
                ),
                "fault_order": fault_order,
                "first_faulted": first_faulted,
                "second_faulted": second_faulted,
                "hot_position": hot,
                "aligned": bool(z["aligned"]),
                "status": str(z["status"]),
                "hot_fraction": hot_fraction,
                "first_fraction": first_fraction,
                "second_fraction": second_fraction,
                "fault_order_contrast": (
                    second_fraction - first_fraction
                ),
                "hot_retouch_ms": float(z["hot_retouch_ns"]) / 1e6,
                "misaligned": not bool(z["aligned"]),
                "hot_not_fully_resident": int(hot_fraction < 1.0),
                "swap_mib_pre_retouch": float(z["swap_mib_pre_retouch"]),
                "pswpin": int(z["retouch_deltas"]["pswpin"]),
                "refault_anon": int(
                    z["retouch_deltas"]["workingset_refault_anon"]
                ),
                "pgmajfault": int(z["retouch_deltas"]["pgmajfault"]),
                "content_match": bool(z["content_match"]),
                "no_oom": bool(z["no_oom"]),
                "hot_unused_before_snapshot": bool(
                    z["checks"][
                        "hot_unused_before_residency_snapshot"
                    ]
                ),
            })

    if not rows:
        raise ValueError("no HYP-003 evidence found")
    return pd.DataFrame(rows)


def _block_primary(trials: pd.DataFrame) -> np.ndarray:
    values = []
    for _, g in trials.groupby("block", sort=True):
        aligned = g[g["aligned"]]["hot_fraction"].to_numpy(dtype=float)
        misaligned = g[~g["aligned"]]["hot_fraction"].to_numpy(dtype=float)
        values.append(float(aligned.mean() - misaligned.mean()))
    return np.asarray(values)


def _block_fault_check(trials: pd.DataFrame) -> np.ndarray:
    return (
        trials.groupby("block")["fault_order_contrast"]
        .mean()
        .sort_index()
        .to_numpy(dtype=float)
    )


def _block_latency(trials: pd.DataFrame) -> np.ndarray:
    values = []
    for _, g in trials.groupby("block", sort=True):
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
        values.append(float(misaligned.mean() - aligned.mean()))
    return np.asarray(values)


def analyze(
    spec: dict[str, Any],
    root: str | Path,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    trials = collect(Path(root))

    blocks = int(spec["runner_blocks"])
    expected_cells = {
        (int(level), fault, hot)
        for level in spec["memory_high_mib"]
        for fault in spec["fault_orders"]
        for hot in spec["hot_positions"]
    }
    expected_trials = blocks * len(expected_cells)

    checks = {
        "sixteen_blocks_present": int(trials["block"].nunique()) == blocks,
        "one_hundred_twenty_eight_trials_present": (
            len(trials) == expected_trials
        ),
        "all_trials_pass": bool((trials["status"] == "PASS").all()),
        "no_oom": bool(trials["no_oom"].all()),
        "content_integrity": bool(trials["content_match"].all()),
        "factorial_cells_complete": all(
            {
                (
                    int(row.memory_high_mib),
                    str(row.fault_order),
                    str(row.hot_position),
                )
                for row in g.itertuples()
            } == expected_cells
            for _, g in trials.groupby("block")
        ),
        "hot_assignment_does_not_change_pre_reuse_operations": bool(
            trials["hot_unused_before_snapshot"].all()
        ),
    }

    primary_values = _block_primary(trials)
    fault_values = _block_fault_check(trials)
    latency_values = _block_latency(trials)

    primary = {
        "estimand": (
            "mean runner-block HOT resident fraction aligned "
            "minus misaligned"
        ),
        "exact_signflip": exact_signflip_one_sided(
            primary_values, "greater"
        ),
        "cluster_bootstrap": bootstrap_mean(
            primary_values,
            int(spec["cluster_bootstrap_resamples"]),
            int(spec["cluster_bootstrap_seed"]),
        ),
    }

    manipulation = {
        "estimand": (
            "mean runner-block second-faulted resident fraction "
            "minus first-faulted"
        ),
        "exact_signflip": exact_signflip_one_sided(
            fault_values, "greater"
        ),
        "cluster_bootstrap": bootstrap_mean(
            fault_values,
            int(spec["cluster_bootstrap_resamples"]),
            int(spec["cluster_bootstrap_seed"]) + 1,
        ),
    }

    latency_boot = bootstrap_mean(
        latency_values,
        int(spec["cluster_bootstrap_resamples"]),
        int(spec["cluster_bootstrap_seed"]) + 2,
    )
    secondary = {
        "estimand": (
            "mean runner-block log HOT-retouch latency "
            "misaligned minus aligned"
        ),
        "exact_signflip": exact_signflip_one_sided(
            latency_values, "greater"
        ),
        "geometric_mean_ratio_misaligned_over_aligned": math.exp(
            float(latency_values.mean())
        ),
        "cluster_bootstrap_ratio": {
            "resamples": latency_boot["resamples"],
            "median_ratio": math.exp(latency_boot["median"]),
            "ci95_ratio": [
                math.exp(latency_boot["ci95"][0]),
                math.exp(latency_boot["ci95"][1]),
            ],
        },
    }

    block_outputs = pd.DataFrame({
        "block": sorted(trials["block"].unique()),
        "primary_aligned_minus_misaligned_residency": primary_values,
        "manipulation_second_minus_first_residency": fault_values,
        "secondary_log_latency_misaligned_minus_aligned": latency_values,
    })

    level_summary: dict[str, Any] = {}
    for level in spec["memory_high_mib"]:
        level = int(level)
        g = trials[trials["memory_high_mib"] == level]
        aligned = g[g["aligned"]]
        misaligned = g[~g["aligned"]]
        level_summary[str(level)] = {
            "trials": len(g),
            "mean_fault_order_contrast": float(
                g["fault_order_contrast"].mean()
            ),
            "mean_hot_fraction_aligned": float(
                aligned["hot_fraction"].mean()
            ),
            "mean_hot_fraction_misaligned": float(
                misaligned["hot_fraction"].mean()
            ),
            "misalignment_rate_aligned": float(
                aligned["hot_not_fully_resident"].mean()
            ),
            "misalignment_rate_misaligned": float(
                misaligned["hot_not_fully_resident"].mean()
            ),
            "median_latency_aligned_ms": float(
                np.median(aligned["hot_retouch_ms"])
            ),
            "median_latency_misaligned_ms": float(
                np.median(misaligned["hot_retouch_ms"])
            ),
        }

    summary = {
        "experiment_id": "HYP-003",
        "execution_status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "runner_blocks": int(trials["block"].nunique()),
        "total_trials": len(trials),
        "primary_semantic_residency_gap": primary,
        "manipulation_check_fault_order": manipulation,
        "secondary_semantic_latency_cost": secondary,
        "level_summary": level_summary,
        "authority_boundary": (
            "HYP-003 tests a bounded separation between past fault/touch "
            "order and independently assigned future semantic demand. "
            "It does not test a coordination mechanism."
        ),
    }
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
    trials.sort_values(["block", "order"]).to_csv(
        out / "trials.csv",
        index=False,
    )
    blocks.to_csv(out / "block-contrasts.csv", index=False)
    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))

    if summary["execution_status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
