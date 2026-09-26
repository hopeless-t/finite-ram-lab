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


TRIAL_RE = re.compile(r"trial-(?P<order>\d+)\.json$")
BLOCK_RE = re.compile(r"(?:char002-)?block-(?P<block>\d+)$")


def load_spec(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def schedule_rows(spec: dict[str, Any], block: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for level in spec["memory_high_mib"]:
        for creation in spec["families"]["separate"]["creation_orders"]:
            for fault in spec["families"]["separate"]["fault_orders"]:
                rows.append({
                    "family": "separate",
                    "memory_high_mib": int(level),
                    "creation_order": creation,
                    "fault_order": fault,
                })

        for fault in spec["families"]["shared"]["fault_orders"]:
            rows.append({
                "family": "shared",
                "memory_high_mib": int(level),
                "creation_order": "NA",
                "fault_order": fault,
            })

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
                "family",
                "memory_high_mib",
                "creation_order",
                "fault_order",
            ],
            lineterminator="\n",
        )
        w.writeheader()
        w.writerows(schedule_rows(spec, block))


def exact_signflip_two_sided(values: np.ndarray) -> dict[str, Any]:
    n = len(values)
    if n > 20:
        raise ValueError("exact sign-flip capped at 20 blocks")

    observed = float(values.mean())
    total = 1 << n
    exceed = 0

    for bits in range(total):
        signs = np.fromiter(
            (1.0 if (bits >> i) & 1 else -1.0 for i in range(n)),
            dtype=float,
            count=n,
        )
        estimate = float(np.mean(values * signs))
        if abs(estimate) >= abs(observed) - 1e-15:
            exceed += 1

    return {
        "blocks": n,
        "observed_mean": observed,
        "exact_permutations": total,
        "two_sided_p": exceed / total,
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
    dirs = sorted(root.glob("block-*")) + sorted(root.glob("char002-block-*"))

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
            family = str(z["family"])
            params = z["parameters"]
            os_after = z["os_after_burst"]

            row: dict[str, Any] = {
                "block": block,
                "order": int(tm.group("order")),
                "family": family,
                "memory_high_mib": int(os_after["memory_high"]) // (1024 * 1024),
                "creation_order": str(params["creation_order"]),
                "fault_order": str(params["fault_order"]),
                "status": str(z["status"]),
                "content_match": bool(z["content_match"]),
                "no_oom": bool(z["no_oom"]),
                "addresses_page_aligned": bool(z["checks"]["addresses_page_aligned"]),
                "memory_current_mib": float(os_after["memory_current"]) / (1024 * 1024),
                "swap_mib": float(os_after["memory_swap_current"]) / (1024 * 1024),
                "pgscan": int(os_after["memory_stat"].get("pgscan", 0)),
                "pgsteal": int(os_after["memory_stat"].get("pgsteal", 0)),
            }

            if family == "separate":
                a = float(z["residency_after_burst"]["A"]["resident_fraction"])
                b = float(z["residency_after_burst"]["B"]["resident_fraction"])
                addr_a = int(z["addresses"]["A"])
                addr_b = int(z["addresses"]["B"])
                lower = str(z["addresses"]["lower_identity"])
                higher = str(z["addresses"]["higher_identity"])
                first_created, second_created = list(params["creation_order"])
                first_faulted, second_faulted = list(params["fault_order"])
                fractions = {"A": a, "B": b}

                row.update({
                    "A_fraction": a,
                    "B_fraction": b,
                    "A_address": addr_a,
                    "B_address": addr_b,
                    "lower_identity": lower,
                    "higher_identity": higher,
                    "creation_contrast": fractions[second_created] - fractions[first_created],
                    "fault_contrast": fractions[second_faulted] - fractions[first_faulted],
                    "address_contrast": fractions[higher] - fractions[lower],
                    "second_created_is_higher": int(second_created == higher),
                })
            elif family == "shared":
                lower = float(z["residency_after_burst"]["lower"]["resident_fraction"])
                upper = float(z["residency_after_burst"]["upper"]["resident_fraction"])
                first_faulted, second_faulted = params["fault_order"].split("_")
                fractions = {"lower": lower, "upper": upper}

                row.update({
                    "lower_fraction": lower,
                    "upper_fraction": upper,
                    "lower_address": int(z["addresses"]["lower"]),
                    "upper_address": int(z["addresses"]["upper"]),
                    "address_contrast": upper - lower,
                    "fault_contrast": fractions[second_faulted] - fractions[first_faulted],
                })
            else:
                raise ValueError(f"unexpected family: {family}")

            rows.append(row)

    if not rows:
        raise ValueError("no CHAR-002 evidence found")
    return pd.DataFrame(rows)


def _block_contrast(
    trials: pd.DataFrame,
    family: str,
    column: str,
) -> pd.DataFrame:
    g = trials[trials["family"] == family]
    return (
        g.groupby("block", as_index=False)[column]
        .mean()
        .rename(columns={column: "contrast"})
        .sort_values("block")
    )


def _contrast_report(
    spec: dict[str, Any],
    trials: pd.DataFrame,
    family: str,
    column: str,
    seed_offset: int,
    estimand: str,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    blocks = _block_contrast(trials, family, column)
    values = blocks["contrast"].to_numpy(dtype=float)
    return blocks, {
        "estimand": estimand,
        "exact_signflip": exact_signflip_two_sided(values),
        "cluster_bootstrap": bootstrap_mean(
            values,
            int(spec["cluster_bootstrap_resamples"]),
            int(spec["cluster_bootstrap_seed"]) + seed_offset,
        ),
    }


def analyze(
    spec: dict[str, Any],
    root: str | Path,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    trials = collect(Path(root))
    blocks_expected = int(spec["runner_blocks"])
    expected_cells = {
        (
            "separate",
            int(level),
            creation,
            fault,
        )
        for level in spec["memory_high_mib"]
        for creation in spec["families"]["separate"]["creation_orders"]
        for fault in spec["families"]["separate"]["fault_orders"]
    } | {
        (
            "shared",
            int(level),
            "NA",
            fault,
        )
        for level in spec["memory_high_mib"]
        for fault in spec["families"]["shared"]["fault_orders"]
    }
    expected_trials = blocks_expected * len(expected_cells)

    checks = {
        "sixteen_blocks_present": int(trials["block"].nunique()) == blocks_expected,
        "one_hundred_ninety_two_trials_present": len(trials) == expected_trials,
        "all_trials_pass": bool((trials["status"] == "PASS").all()),
        "no_oom": bool(trials["no_oom"].all()),
        "content_integrity": bool(trials["content_match"].all()),
        "addresses_page_aligned": bool(trials["addresses_page_aligned"].all()),
        "factorial_cells_complete": all(
            {
                (
                    str(row.family),
                    int(row.memory_high_mib),
                    str(row.creation_order),
                    str(row.fault_order),
                )
                for row in g.itertuples()
            } == expected_cells
            for _, g in trials.groupby("block")
        ),
    }

    reports = {}
    block_tables = []

    definitions = [
        (
            "S1_creation_order",
            "separate",
            "creation_contrast",
            1,
            "resident fraction(second-created) - resident fraction(first-created)",
        ),
        (
            "S2_fault_order",
            "separate",
            "fault_contrast",
            2,
            "resident fraction(second-faulted) - resident fraction(first-faulted)",
        ),
        (
            "H1_address_position",
            "shared",
            "address_contrast",
            3,
            "resident fraction(upper) - resident fraction(lower)",
        ),
        (
            "H2_fault_order",
            "shared",
            "fault_contrast",
            4,
            "resident fraction(second-faulted) - resident fraction(first-faulted)",
        ),
    ]

    for name, family, column, offset, estimand in definitions:
        blocks, report = _contrast_report(
            spec,
            trials,
            family,
            column,
            offset,
            estimand,
        )
        blocks = blocks.rename(columns={"contrast": name})
        block_tables.append(blocks)
        reports[name] = report

    block_outputs = block_tables[0]
    for table in block_tables[1:]:
        block_outputs = block_outputs.merge(table, on="block")

    separate = trials[trials["family"] == "separate"].copy()
    relation_rate = float(separate["second_created_is_higher"].mean())
    confounding = {
        "trials": len(separate),
        "second_created_is_higher_rate": relation_rate,
        "second_created_is_lower_rate": 1.0 - relation_rate,
        "perfectly_collinear": relation_rate in {0.0, 1.0},
    }

    level_summary: dict[str, Any] = {}
    for level in spec["memory_high_mib"]:
        level = int(level)
        s = separate[separate["memory_high_mib"] == level]
        h = trials[
            (trials["family"] == "shared")
            & (trials["memory_high_mib"] == level)
        ]
        level_summary[str(level)] = {
            "separate_trials": len(s),
            "shared_trials": len(h),
            "mean_S_creation_contrast": float(s["creation_contrast"].mean()),
            "mean_S_fault_contrast": float(s["fault_contrast"].mean()),
            "mean_S_address_contrast": float(s["address_contrast"].mean()),
            "mean_H_address_contrast": float(h["address_contrast"].mean()),
            "mean_H_fault_contrast": float(h["fault_contrast"].mean()),
        }

    summary = {
        "experiment_id": "CHAR-002",
        "execution_status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "runner_blocks": int(trials["block"].nunique()),
        "total_trials": len(trials),
        "primary_mechanism_contrasts": reports,
        "separate_vma_creation_address_relation": confounding,
        "level_summary": level_summary,
        "authority_boundary": (
            "CHAR-002 characterizes mapping/fault/address associations under the "
            "declared hosted memcg workload. It does not establish a general Linux "
            "reclaim policy or authorize a semantic coordination mechanism."
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
    trials.sort_values(["block", "order"]).to_csv(out / "trials.csv", index=False)
    blocks.to_csv(out / "block-contrasts.csv", index=False)
    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))

    if summary["execution_status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
