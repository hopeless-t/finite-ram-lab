from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics
from typing import Any, Mapping

from finite_ram_lab.lane_concurrency_sweep import _run_fresh_child
from finite_ram_lab.q_budget_governor import RiskMode, select_q


PROFILES = (
    ("upper_q1_boundary", RiskMode.OBSERVED_UPPER, 67_022_848),
    ("upper_q2_boundary", RiskMode.OBSERVED_UPPER, 67_108_864),
    ("upper_q4_boundary", RiskMode.OBSERVED_UPPER, 71_303_168),
    ("upper_q7_boundary", RiskMode.OBSERVED_UPPER, 71_507_968),
)

BALANCED_PROFILE_ORDERS = (
    (0, 1, 2, 3),
    (3, 2, 1, 0),
    (1, 0, 3, 2),
    (2, 3, 0, 1),
)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _decision_for_profile(
    source: Mapping[str, Any],
    *,
    name: str,
    risk_mode: RiskMode,
    peak_budget_bytes: int,
) -> dict[str, Any]:
    decision = select_q(
        source,
        peak_budget_bytes=peak_budget_bytes,
        mode=risk_mode,
    )
    return {
        "profile_name": name,
        "risk_mode": risk_mode.value,
        "peak_budget_bytes": peak_budget_bytes,
        "selected_q": int(decision["selected_q"]),
        "selected_peak_model_bytes": int(decision["selected_peak_model_bytes"]),
        "selected_median_latency_seconds": float(
            decision["selected_median_latency_seconds"]
        ),
        "source_sweep_sha256": decision["source_sweep_sha256"],
    }


def run_governor_dogfood(
    source: Mapping[str, Any],
    *,
    repetitions: int = 4,
    size: int = 2048,
    lane_count: int = 7,
    seed: int = 471,
    value_limit: int = 50,
    tile_rows: int = 64,
) -> dict[str, Any]:
    if repetitions != 4:
        raise ValueError("b471_requires_four_repetitions")

    decisions = [
        _decision_for_profile(
            source,
            name=name,
            risk_mode=risk_mode,
            peak_budget_bytes=budget,
        )
        for name, risk_mode, budget in PROFILES
    ]

    expected_qs = [1, 2, 4, 7]
    actual_qs = [decision["selected_q"] for decision in decisions]
    if actual_qs != expected_qs:
        raise RuntimeError(
            f"frozen_profile_selection_changed:{actual_qs!r}"
        )

    observations: dict[str, list[dict[str, Any]]] = {
        decision["profile_name"]: [] for decision in decisions
    }
    execution_rows = []

    for repetition, order in enumerate(BALANCED_PROFILE_ORDERS):
        row = {
            "repetition": repetition,
            "profile_order": [
                decisions[index]["profile_name"] for index in order
            ],
            "results": [],
        }
        for index in order:
            decision = decisions[index]
            observed = _run_fresh_child(
                q=int(decision["selected_q"]),
                size=size,
                lane_count=lane_count,
                seed=seed,
                value_limit=value_limit,
                tile_rows=tile_rows,
            )
            if not observed["semantic_exact"]:
                raise RuntimeError(
                    f"semantic_gate_failed:{decision['profile_name']}"
                )

            peak = int(observed["normalized_peak_growth_bytes"])
            budget = int(decision["peak_budget_bytes"])
            compliance = peak <= budget
            item = {
                "profile_name": decision["profile_name"],
                "risk_mode": decision["risk_mode"],
                "peak_budget_bytes": budget,
                "selected_q": decision["selected_q"],
                "selected_peak_model_bytes": decision[
                    "selected_peak_model_bytes"
                ],
                "semantic_exact": True,
                "observed_peak_bytes": peak,
                "budget_margin_bytes": budget - peak,
                "budget_compliant": compliance,
                "work_seconds": float(observed["work_seconds"]),
                "output_sha256": observed["output_sha256"],
            }
            observations[decision["profile_name"]].append(item)
            row["results"].append(item)
        execution_rows.append(row)

    digests = {
        item["output_sha256"]
        for values in observations.values()
        for item in values
    }
    if len(digests) != 1:
        raise RuntimeError("cross_profile_output_digest_mismatch")

    summaries = []
    for decision in decisions:
        name = decision["profile_name"]
        values = observations[name]
        peaks = [int(item["observed_peak_bytes"]) for item in values]
        margins = [int(item["budget_margin_bytes"]) for item in values]
        times = [float(item["work_seconds"]) for item in values]
        compliant_count = sum(bool(item["budget_compliant"]) for item in values)
        miss_count = len(values) - compliant_count

        summaries.append(
            {
                **decision,
                "samples": len(values),
                "semantic_exact_count": sum(
                    bool(item["semantic_exact"]) for item in values
                ),
                "budget_compliant_count": compliant_count,
                "budget_miss_count": miss_count,
                "observed_peak_bytes": peaks,
                "median_observed_peak_bytes": statistics.median(peaks),
                "max_observed_peak_bytes": max(peaks),
                "min_budget_margin_bytes": min(margins),
                "max_budget_overrun_bytes": max(
                    [max(0, -margin) for margin in margins],
                    default=0,
                ),
                "median_work_seconds": statistics.median(times),
            }
        )

    total_samples = sum(row["samples"] for row in summaries)
    total_misses = sum(row["budget_miss_count"] for row in summaries)

    return {
        "schema": "finite-ram-lab.governor-dogfood/v0.1",
        "claim_ceiling": "HOSTED_OBSERVED_FRONTIER_GOVERNOR_CALIBRATION",
        "source_sweep_sha256": source["sweep_sha256"],
        "profiles": decisions,
        "balanced_profile_orders": [
            [decisions[index]["profile_name"] for index in order]
            for order in BALANCED_PROFILE_ORDERS
        ],
        "repetitions": repetitions,
        "size": size,
        "lane_count": lane_count,
        "seed": seed,
        "value_limit": value_limit,
        "tile_rows": tile_rows,
        "output_sha256": next(iter(digests)),
        "execution_rows": execution_rows,
        "summary_rows": summaries,
        "overall": {
            "samples": total_samples,
            "budget_miss_count": total_misses,
            "budget_compliant_count": total_samples - total_misses,
            "classification": (
                "BOUNDARY_BUDGETS_ALL_COMPLIANT"
                if total_misses == 0
                else "BOUNDARY_BUDGET_CALIBRATION_REQUIRED"
            ),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--repetitions", type=int, default=4)
    parser.add_argument("--size", type=int, default=2048)
    parser.add_argument("--seed", type=int, default=471)
    args = parser.parse_args()

    source = _load(args.source)
    payload = run_governor_dogfood(
        source,
        repetitions=args.repetitions,
        size=args.size,
        seed=args.seed,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "overall": payload["overall"],
                "summary_rows": payload["summary_rows"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
