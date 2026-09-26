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
BLOCK_RE = re.compile(r"(?:exp003-)?block-(?P<block>\d+)$")


def load_spec(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def schedule_rows(spec: dict[str, Any], block: int) -> list[dict[str, Any]]:
    rows = [
        {
            "memory_high_mib": int(level),
            "fault_order": fault,
            "hot_position": hot,
            "arm": arm,
        }
        for level in spec["memory_high_mib"]
        for fault in spec["fault_orders"]
        for hot in spec["hot_positions"]
        for arm in spec["arms"]
    ]
    expected = 24 * int(spec["complete_repeats_per_block"])
    if int(spec["complete_repeats_per_block"]) != 1:
        raise ValueError("EXP-003 frozen design requires one complete repeat")
    if len(rows) != expected:
        raise ValueError("unexpected EXP-003 factorial size")

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
                "arm",
            ],
            lineterminator="\n",
        )
        w.writeheader()
        w.writerows(schedule_rows(spec, block))


def collect(root: Path) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    dirs = sorted(root.glob("block-*")) + sorted(root.glob("exp003-block-*"))

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
            checks = z["checks"]
            os_pre = z["os_pre_retouch"]

            rows.append({
                "block": block,
                "order": int(tm.group("order")),
                "memory_high_mib": (
                    int(os_pre["memory_high"]) // (1024 * 1024)
                ),
                "fault_order": str(z["fault_order"]),
                "hot_position": str(z["hot_position"]),
                "aligned": bool(z["aligned"]),
                "arm": str(z["arm"]),
                "status": str(z["status"]),
                "advice_ms": float(z["advice"]["duration_ns"]) / 1e6,
                "burst_ms": float(z["burst_touch_ns"]) / 1e6,
                "hot_retouch_ms": float(z["hot_retouch_ns"]) / 1e6,
                "work_interval_ms": float(z["work_interval_ns"]) / 1e6,
                "hot_fraction": float(
                    z["residency_pre_retouch"]["hot"]["resident_fraction"]
                ),
                "cold_fraction": float(
                    z["residency_pre_retouch"]["cold"]["resident_fraction"]
                ),
                "hot_first16_fraction": float(
                    z["residency_pre_retouch"]["hot_first16"][
                        "resident_fraction"
                    ]
                ),
                "cold_first16_fraction": float(
                    z["residency_pre_retouch"]["cold_first16"][
                        "resident_fraction"
                    ]
                ),
                "swap_mib_pre_retouch": float(z["swap_mib_pre_retouch"]),
                "pswpin": int(z["retouch_deltas"]["pswpin"]),
                "refault_anon": int(
                    z["retouch_deltas"]["workingset_refault_anon"]
                ),
                "pgmajfault": int(z["retouch_deltas"]["pgmajfault"]),
                "pgfault": int(z["retouch_deltas"]["pgfault"]),
                "pgscan": int(z["retouch_deltas"]["pgscan"]),
                "pgsteal": int(z["retouch_deltas"]["pgsteal"]),
                "content_match": bool(z["content_match"]),
                "no_oom": bool(z["no_oom"]),
                "memory_high_matches": bool(
                    checks["memory_high_matches"]
                ),
                "memory_max_matches": bool(
                    checks["memory_max_matches"]
                ),
                "shared_halves_contiguous": bool(
                    checks["shared_halves_contiguous"]
                ),
                "addresses_page_aligned": bool(
                    checks["addresses_page_aligned"]
                ),
                "pageout_target_exactly_sixteen_mib": bool(
                    checks["pageout_target_exactly_sixteen_mib"]
                ),
                "advice_success_when_required": bool(
                    checks["advice_success_when_required"]
                ),
                "no_advice_in_no_hint": bool(
                    checks["no_advice_in_no_hint"]
                ),
            })

    if not rows:
        raise ValueError("no EXP-003 evidence found")
    return pd.DataFrame(rows)


def exact_signflip_one_sided(
    values: np.ndarray,
    alternative: str,
) -> dict[str, Any]:
    n = len(values)
    if n > 20:
        raise ValueError("exact sign-flip capped at 20 blocks")

    observed = float(values.mean())
    total = 1 << n
    shifts = np.arange(n, dtype=np.uint32)
    extreme = 0
    chunk = 65536

    for start in range(0, total, chunk):
        stop = min(start + chunk, total)
        masks = np.arange(start, stop, dtype=np.uint32)[:, None]
        signs = (
            ((masks >> shifts[None, :]) & 1).astype(np.int8) * 2 - 1
        )
        perm = (signs @ values) / n

        if alternative == "less":
            extreme += int(
                np.count_nonzero(perm <= observed + 1e-15)
            )
        elif alternative == "greater":
            extreme += int(
                np.count_nonzero(perm >= observed - 1e-15)
            )
        else:
            raise ValueError("alternative must be less or greater")

    return {
        "blocks": n,
        "observed_mean_log_difference": observed,
        "geometric_mean_ratio": math.exp(observed),
        "alternative": alternative,
        "exact_permutations": total,
        "one_sided_p": extreme / total,
    }


def bootstrap_ratio(
    values: np.ndarray,
    resamples: int,
    seed: int,
) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    n = len(values)
    est = np.empty(resamples, dtype=float)
    for i in range(resamples):
        sample = values[rng.integers(0, n, size=n)]
        est[i] = math.exp(float(sample.mean()))
    return {
        "resamples": resamples,
        "seed": seed,
        "median_ratio": float(np.median(est)),
        "ci95": [
            float(np.quantile(est, 0.025)),
            float(np.quantile(est, 0.975)),
        ],
    }


def block_log_contrast(
    trials: pd.DataFrame,
    stratum: str,
    arm_a: str,
    arm_b: str,
    outcome: str,
) -> np.ndarray:
    if stratum not in {"aligned", "misaligned"}:
        raise ValueError("invalid stratum")
    want_aligned = stratum == "aligned"
    subset = trials[trials["aligned"] == want_aligned]

    values = []
    for block, g in subset.groupby("block", sort=True):
        a = g[g["arm"] == arm_a][outcome].to_numpy(dtype=float)
        b = g[g["arm"] == arm_b][outcome].to_numpy(dtype=float)
        if len(a) != 4 or len(b) != 4:
            raise ValueError(
                f"block {block} stratum {stratum} missing balanced arm cells"
            )
        a = np.log(np.maximum(a, 1e-9))
        b = np.log(np.maximum(b, 1e-9))
        values.append(float(a.mean() - b.mean()))
    return np.asarray(values, dtype=float)


def contrast_result(
    spec: dict[str, Any],
    trials: pd.DataFrame,
    *,
    name: str,
    stratum: str,
    arm_a: str,
    arm_b: str,
    outcome: str,
    alternative: str,
    seed_offset: int,
) -> dict[str, Any]:
    values = block_log_contrast(
        trials, stratum, arm_a, arm_b, outcome
    )
    return {
        "name": name,
        "stratum": stratum,
        "arm_a": arm_a,
        "arm_b": arm_b,
        "outcome": outcome,
        "estimand": (
            f"runner-block mean log({outcome}) "
            f"{arm_a} - {arm_b}"
        ),
        "exact_signflip": exact_signflip_one_sided(
            values, alternative
        ),
        "cluster_bootstrap_ratio": bootstrap_ratio(
            values,
            int(spec["cluster_bootstrap_resamples"]),
            int(spec["cluster_bootstrap_seed"]) + seed_offset,
        ),
    }


def _arm_descriptive(g: pd.DataFrame) -> dict[str, Any]:
    return {
        "trials": len(g),
        "median_advice_ms": float(np.median(g["advice_ms"])),
        "median_hot_retouch_ms": float(
            np.median(g["hot_retouch_ms"])
        ),
        "p90_hot_retouch_ms": float(
            np.quantile(g["hot_retouch_ms"], 0.90)
        ),
        "median_work_interval_ms": float(
            np.median(g["work_interval_ms"])
        ),
        "p90_work_interval_ms": float(
            np.quantile(g["work_interval_ms"], 0.90)
        ),
        "median_hot_fraction": float(np.median(g["hot_fraction"])),
        "median_cold_fraction": float(
            np.median(g["cold_fraction"])
        ),
        "median_hot_first16_fraction": float(
            np.median(g["hot_first16_fraction"])
        ),
        "median_cold_first16_fraction": float(
            np.median(g["cold_first16_fraction"])
        ),
        "median_swap_mib_pre_retouch": float(
            np.median(g["swap_mib_pre_retouch"])
        ),
        "median_pswpin": float(np.median(g["pswpin"])),
        "median_refault_anon": float(
            np.median(g["refault_anon"])
        ),
        "median_pgmajfault": float(
            np.median(g["pgmajfault"])
        ),
    }


def analyze(
    spec: dict[str, Any],
    root: str | Path,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    trials = collect(Path(root))
    blocks = int(spec["runner_blocks"])

    expected_cells = {
        (int(level), fault, hot, arm)
        for level in spec["memory_high_mib"]
        for fault in spec["fault_orders"]
        for hot in spec["hot_positions"]
        for arm in spec["arms"]
    }
    expected_trials = blocks * len(expected_cells)

    checks = {
        "sixteen_blocks_present": (
            int(trials["block"].nunique()) == blocks
        ),
        "three_hundred_eighty_four_trials_present": (
            len(trials) == expected_trials
        ),
        "all_trials_pass": bool(
            (trials["status"] == "PASS").all()
        ),
        "no_oom": bool(trials["no_oom"].all()),
        "content_integrity": bool(trials["content_match"].all()),
        "factorial_cells_complete": all(
            {
                (
                    int(row.memory_high_mib),
                    str(row.fault_order),
                    str(row.hot_position),
                    str(row.arm),
                )
                for row in g.itertuples()
            } == expected_cells
            for _, g in trials.groupby("block")
        ),
        "memory_high_matches": bool(
            trials["memory_high_matches"].all()
        ),
        "memory_max_matches": bool(
            trials["memory_max_matches"].all()
        ),
        "shared_halves_contiguous": bool(
            trials["shared_halves_contiguous"].all()
        ),
        "addresses_page_aligned": bool(
            trials["addresses_page_aligned"].all()
        ),
        "pageout_target_exactly_sixteen_mib": bool(
            trials["pageout_target_exactly_sixteen_mib"].all()
        ),
        "advice_success_when_required": bool(
            trials["advice_success_when_required"].all()
        ),
        "no_advice_in_no_hint": bool(
            trials["no_advice_in_no_hint"].all()
        ),
    }

    contrast_defs = [
        (
            "primary_hot_correct_vs_nohint_misaligned",
            "misaligned",
            "correct_pageout",
            "no_hint",
            "hot_retouch_ms",
            "less",
        ),
        (
            "net_correct_vs_nohint_misaligned",
            "misaligned",
            "correct_pageout",
            "no_hint",
            "work_interval_ms",
            "less",
        ),
        (
            "redteam_hot_wrong_vs_nohint_misaligned",
            "misaligned",
            "wrong_pageout",
            "no_hint",
            "hot_retouch_ms",
            "greater",
        ),
        (
            "redteam_hot_wrong_vs_correct_misaligned",
            "misaligned",
            "wrong_pageout",
            "correct_pageout",
            "hot_retouch_ms",
            "greater",
        ),
        (
            "redteam_total_wrong_vs_nohint_misaligned",
            "misaligned",
            "wrong_pageout",
            "no_hint",
            "work_interval_ms",
            "greater",
        ),
        (
            "redteam_total_wrong_vs_correct_misaligned",
            "misaligned",
            "wrong_pageout",
            "correct_pageout",
            "work_interval_ms",
            "greater",
        ),
        (
            "control_hot_correct_vs_nohint_aligned",
            "aligned",
            "correct_pageout",
            "no_hint",
            "hot_retouch_ms",
            "less",
        ),
        (
            "control_total_correct_vs_nohint_aligned",
            "aligned",
            "correct_pageout",
            "no_hint",
            "work_interval_ms",
            "less",
        ),
        (
            "control_hot_wrong_vs_nohint_aligned",
            "aligned",
            "wrong_pageout",
            "no_hint",
            "hot_retouch_ms",
            "greater",
        ),
        (
            "control_total_wrong_vs_nohint_aligned",
            "aligned",
            "wrong_pageout",
            "no_hint",
            "work_interval_ms",
            "greater",
        ),
    ]

    contrasts: dict[str, Any] = {}
    block_table = pd.DataFrame(
        {"block": sorted(trials["block"].unique())}
    )
    for i, (
        name,
        stratum,
        arm_a,
        arm_b,
        outcome,
        alternative,
    ) in enumerate(contrast_defs, start=1):
        result = contrast_result(
            spec,
            trials,
            name=name,
            stratum=stratum,
            arm_a=arm_a,
            arm_b=arm_b,
            outcome=outcome,
            alternative=alternative,
            seed_offset=i,
        )
        contrasts[name] = result
        values = block_log_contrast(
            trials, stratum, arm_a, arm_b, outcome
        )
        block_table[name] = values

    level_summary: dict[str, Any] = {}
    for level in spec["memory_high_mib"]:
        level = int(level)
        level_summary[str(level)] = {}
        for stratum, want_aligned in (
            ("misaligned", False),
            ("aligned", True),
        ):
            g = trials[
                (trials["memory_high_mib"] == level)
                & (trials["aligned"] == want_aligned)
            ]
            level_summary[str(level)][stratum] = {
                arm: _arm_descriptive(g[g["arm"] == arm])
                for arm in spec["arms"]
            }

    summary = {
        "experiment_id": "EXP-003",
        "execution_status": (
            "PASS" if all(checks.values()) else "FAIL"
        ),
        "checks": checks,
        "runner_blocks": int(trials["block"].nunique()),
        "total_trials": len(trials),
        "contrasts": contrasts,
        "level_summary": level_summary,
        "classification_rules": {
            "mechanism_sensitive_benefit": (
                "primary misaligned CORRECT vs NO_HINT HOT-retouch "
                "favors CORRECT under frozen inference"
            ),
            "net_benefit": (
                "mechanism-sensitive benefit plus misaligned total-work "
                "CORRECT vs NO_HINT favors CORRECT"
            ),
            "cost_shifting_only": (
                "HOT-retouch benefit without total-work benefit"
            ),
            "no_benefit": (
                "primary misaligned HOT-retouch endpoint does not "
                "support CORRECT"
            ),
            "unsafe_asymmetric_harm": (
                "wrong/stale harm is large relative to correct benefit "
                "or aligned controls show material unnecessary-action damage"
            ),
        },
        "authority_boundary": (
            "EXP-003 tests one existing MADV_PAGEOUT semantic action "
            "under bounded hosted memcg conditions. Diagnostics cannot "
            "rescue a negative primary endpoint."
        ),
    }
    return trials, block_table, summary


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
