from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping


PARETO_Q = (2, 4, 7)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def calibrated_points(b489: Mapping[str, Any]) -> list[dict[str, Any]]:
    if b489.get("schema") != "finite-ram-lab.b489-result/v0.1":
        raise RuntimeError("b489_schema_invalid")
    if b489.get("implementation") != "TILED_WHERE":
        raise RuntimeError("implementation_invalid")

    rows = []
    for q in PARETO_Q:
        row = next(item for item in b489["summary_rows"] if int(item["q"]) == q)
        rows.append(
            {
                "q": q,
                "empirical_max_peak_bytes": int(
                    row["pooled_empirical_max_peak_bytes"]
                ),
                "sample_count": int(row["pooled_sample_count"]),
                "rank_max_one_step_predictive_coverage_floor": float(
                    row["rank_max_one_step_predictive_coverage_floor"]
                ),
                "median_latency_seconds": float(row["median_new_work_seconds"]),
            }
        )
    return rows


def select_q(
    b489: Mapping[str, Any],
    *,
    peak_budget_bytes: int,
    minimum_rank_coverage: float = 0.95,
) -> dict[str, Any]:
    if peak_budget_bytes < 0:
        raise ValueError("peak_budget_invalid")
    if not (0.0 < minimum_rank_coverage < 1.0):
        raise ValueError("minimum_rank_coverage_invalid")

    points = calibrated_points(b489)
    eligible = [
        row
        for row in points
        if row["empirical_max_peak_bytes"] <= peak_budget_bytes
        and row["rank_max_one_step_predictive_coverage_floor"]
        >= minimum_rank_coverage
    ]
    if not eligible:
        raise RuntimeError("no_coverage_qualified_repaired_q_fits_budget")

    selected = min(
        eligible,
        key=lambda row: (
            row["median_latency_seconds"],
            row["empirical_max_peak_bytes"],
            row["q"],
        ),
    )
    return {
        "schema": "finite-ram-lab.repaired-coverage-aware-decision/v0.1",
        "implementation": "TILED_WHERE",
        "claim_ceiling": "EXCHANGEABILITY_CONDITIONAL_REPAIRED_GOVERNOR_V2",
        "peak_budget_bytes": peak_budget_bytes,
        "minimum_rank_coverage": minimum_rank_coverage,
        "selected_q": selected["q"],
        "selected_empirical_max_peak_bytes": selected["empirical_max_peak_bytes"],
        "selected_sample_count": selected["sample_count"],
        "selected_rank_max_one_step_predictive_coverage_floor": selected[
            "rank_max_one_step_predictive_coverage_floor"
        ],
        "selected_median_latency_seconds": selected["median_latency_seconds"],
        "selection_rule": (
            "minimum repaired-runtime median latency among Pareto q values whose "
            "19-runner pooled empirical maximum fits the declared peak budget and "
            "whose rank-max coverage floor meets the declared minimum"
        ),
        "assumption": (
            "future repaired-runtime execution is exchangeable with the pooled "
            "independent hosted-runner calibration population; not a worst-case guarantee"
        ),
    }


def build_policy(
    b489: Mapping[str, Any],
    *,
    minimum_rank_coverage: float = 0.95,
) -> dict[str, Any]:
    points = calibrated_points(b489)
    qualified = [
        row
        for row in points
        if row["rank_max_one_step_predictive_coverage_floor"]
        >= minimum_rank_coverage
    ]

    breakpoints = []
    last_q = None
    for budget in sorted({row["empirical_max_peak_bytes"] for row in qualified}):
        decision = select_q(
            b489,
            peak_budget_bytes=budget,
            minimum_rank_coverage=minimum_rank_coverage,
        )
        if decision["selected_q"] != last_q:
            breakpoints.append(
                {
                    "minimum_peak_budget_bytes": budget,
                    "selected_q": decision["selected_q"],
                    "sample_count": decision["selected_sample_count"],
                    "rank_max_one_step_predictive_coverage_floor": decision[
                        "selected_rank_max_one_step_predictive_coverage_floor"
                    ],
                    "median_latency_seconds": decision[
                        "selected_median_latency_seconds"
                    ],
                }
            )
            last_q = decision["selected_q"]

    return {
        "schema": "finite-ram-lab.repaired-coverage-aware-governor/v0.1",
        "status": "SOFTWARE_GOVERNOR",
        "implementation": "TILED_WHERE",
        "claim_ceiling": "EXCHANGEABILITY_CONDITIONAL_REPAIRED_GOVERNOR_V2",
        "minimum_rank_coverage": minimum_rank_coverage,
        "pareto_q": list(PARETO_Q),
        "dominated_q_excluded": [1],
        "points": points,
        "breakpoints": breakpoints,
        "assumption": (
            "future repaired-runtime execution is exchangeable with the pooled "
            "independent hosted-runner calibration population; sample-max coverage "
            "is not a worst-case guarantee"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--b489", type=Path, required=True)
    parser.add_argument("--minimum-rank-coverage", type=float, default=0.95)
    parser.add_argument("--peak-budget-bytes", type=int)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    b489 = _load(args.b489)
    if args.peak_budget_bytes is None:
        payload = build_policy(
            b489,
            minimum_rank_coverage=args.minimum_rank_coverage,
        )
    else:
        payload = select_q(
            b489,
            peak_budget_bytes=args.peak_budget_bytes,
            minimum_rank_coverage=args.minimum_rank_coverage,
        )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
