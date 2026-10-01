from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping


Q_VALUES = (1, 2, 4, 7)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _latency_by_q(b469: Mapping[str, Any]) -> dict[int, float]:
    if b469.get("schema") != "finite-ram-lab.b469-result/v0.1":
        raise RuntimeError("b469_schema_invalid")
    return {
        int(row["q"]): float(row["median_work_seconds"])
        for row in b469["summary_rows"]
    }


def calibrated_points(
    b469: Mapping[str, Any],
    b472: Mapping[str, Any],
    b474: Mapping[str, Any],
) -> list[dict[str, Any]]:
    if b472.get("schema") != "finite-ram-lab.b472-result/v0.1":
        raise RuntimeError("b472_schema_invalid")
    if b474.get("schema") != "finite-ram-lab.b474-result/v0.1":
        raise RuntimeError("b474_schema_invalid")

    latency = _latency_by_q(b469)
    points = [
        {
            "q": 1,
            "empirical_max_peak_bytes": int(
                b472["union_empirical_max_peak_bytes"]
            ),
            "sample_count": int(b472["total_sample_count"]),
            "rank_max_one_step_predictive_coverage_floor": float(
                b472["rank_max_one_step_predictive_coverage_floor"]
            ),
            "median_latency_seconds": latency[1],
            "source": "B472",
        }
    ]
    for row in b474["summary_rows"]:
        q = int(row["q"])
        points.append(
            {
                "q": q,
                "empirical_max_peak_bytes": int(
                    row["union_empirical_max_peak_bytes"]
                ),
                "sample_count": int(row["union_sample_count"]),
                "rank_max_one_step_predictive_coverage_floor": float(
                    row["rank_max_one_step_predictive_coverage_floor"]
                ),
                "median_latency_seconds": latency[q],
                "source": "B474",
            }
        )
    return sorted(points, key=lambda row: row["q"])


def select_q(
    b469: Mapping[str, Any],
    b472: Mapping[str, Any],
    b474: Mapping[str, Any],
    *,
    peak_budget_bytes: int,
    minimum_rank_coverage: float = 0.95,
) -> dict[str, Any]:
    if peak_budget_bytes < 0:
        raise ValueError("peak_budget_invalid")
    if not (0.0 < minimum_rank_coverage < 1.0):
        raise ValueError("minimum_rank_coverage_invalid")

    points = calibrated_points(b469, b472, b474)
    eligible = [
        row
        for row in points
        if row["empirical_max_peak_bytes"] <= peak_budget_bytes
        and row["rank_max_one_step_predictive_coverage_floor"]
        >= minimum_rank_coverage
    ]
    if not eligible:
        raise RuntimeError("no_coverage_qualified_q_fits_budget")

    selected = min(
        eligible,
        key=lambda row: (
            row["median_latency_seconds"],
            row["empirical_max_peak_bytes"],
            row["q"],
        ),
    )
    return {
        "schema": "finite-ram-lab.coverage-aware-q-decision/v0.1",
        "claim_ceiling": "EXCHANGEABILITY_CONDITIONAL_COVERAGE_AWARE_GOVERNOR_V1",
        "peak_budget_bytes": peak_budget_bytes,
        "minimum_rank_coverage": minimum_rank_coverage,
        "selected_q": selected["q"],
        "selected_empirical_max_peak_bytes": selected[
            "empirical_max_peak_bytes"
        ],
        "selected_sample_count": selected["sample_count"],
        "selected_rank_max_one_step_predictive_coverage_floor": selected[
            "rank_max_one_step_predictive_coverage_floor"
        ],
        "selected_median_latency_seconds": selected[
            "median_latency_seconds"
        ],
        "selection_rule": (
            "minimum balanced-sweep median latency among q values whose pooled "
            "empirical maximum fits the peak budget and whose rank-max coverage "
            "floor meets the declared minimum"
        ),
        "assumption": (
            "future execution exchangeable with comparable pooled calibration "
            "observations; this is not a worst-case memory guarantee"
        ),
    }


def build_policy(
    b469: Mapping[str, Any],
    b472: Mapping[str, Any],
    b474: Mapping[str, Any],
    *,
    minimum_rank_coverage: float = 0.95,
) -> dict[str, Any]:
    points = calibrated_points(b469, b472, b474)
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
            b469,
            b472,
            b474,
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
        "schema": "finite-ram-lab.coverage-aware-q-governor/v0.1",
        "status": "SOFTWARE_GOVERNOR",
        "claim_ceiling": "EXCHANGEABILITY_CONDITIONAL_COVERAGE_AWARE_GOVERNOR_V1",
        "minimum_rank_coverage": minimum_rank_coverage,
        "points": points,
        "breakpoints": breakpoints,
        "assumption": (
            "future execution exchangeable with comparable pooled calibration "
            "observations; sample-max rank coverage is not a worst-case guarantee"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--b469", type=Path, required=True)
    parser.add_argument("--b472", type=Path, required=True)
    parser.add_argument("--b474", type=Path, required=True)
    parser.add_argument("--minimum-rank-coverage", type=float, default=0.95)
    parser.add_argument("--peak-budget-bytes", type=int)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    b469 = _load(args.b469)
    b472 = _load(args.b472)
    b474 = _load(args.b474)

    if args.peak_budget_bytes is None:
        payload = build_policy(
            b469,
            b472,
            b474,
            minimum_rank_coverage=args.minimum_rank_coverage,
        )
    else:
        payload = select_q(
            b469,
            b472,
            b474,
            peak_budget_bytes=args.peak_budget_bytes,
            minimum_rank_coverage=args.minimum_rank_coverage,
        )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
