from __future__ import annotations

import argparse
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path
from typing import Any, Mapping


class RiskMode(str, Enum):
    MEDIAN = "median"
    OBSERVED_UPPER = "observed_upper"


@dataclass(frozen=True)
class QPoint:
    q: int
    peak_bytes: int
    median_latency_seconds: float
    semantic_exact_count: int
    samples: int


def _validate_source(result: Mapping[str, Any]) -> None:
    if result.get("schema") != "finite-ram-lab.b469-result/v0.1":
        raise RuntimeError("b469_schema_invalid")
    if result.get("status") != "PASS":
        raise RuntimeError("b469_status_invalid")
    if result.get("pareto_q") != [1, 2, 4, 7]:
        raise RuntimeError("unexpected_q_frontier")


def points_for_mode(
    result: Mapping[str, Any],
    mode: RiskMode,
) -> tuple[QPoint, ...]:
    _validate_source(result)
    points = []
    for row in result["summary_rows"]:
        q = int(row["q"])
        samples = int(row.get("samples", 4))
        exact = int(row.get("semantic_exact_count", result["semantic_exact_count_per_q"]))
        if exact != samples:
            raise RuntimeError(f"semantic_gate_incomplete:q={q}")

        if mode is RiskMode.MEDIAN:
            peak = int(row["median_peak_bytes"])
        elif mode is RiskMode.OBSERVED_UPPER:
            if "max_peak_bytes" not in row:
                raise RuntimeError("observed_upper_peak_missing")
            peak = int(row["max_peak_bytes"])
        else:
            raise AssertionError("unreachable_risk_mode")

        points.append(
            QPoint(
                q=q,
                peak_bytes=peak,
                median_latency_seconds=float(row["median_work_seconds"]),
                semantic_exact_count=exact,
                samples=samples,
            )
        )

    return tuple(sorted(points, key=lambda item: item.q))


def select_q(
    result: Mapping[str, Any],
    *,
    peak_budget_bytes: int,
    mode: RiskMode,
) -> dict[str, Any]:
    if type(peak_budget_bytes) is not int or peak_budget_bytes < 0:
        raise ValueError("peak_budget_invalid")

    points = points_for_mode(result, mode)
    feasible = [point for point in points if point.peak_bytes <= peak_budget_bytes]
    if not feasible:
        raise RuntimeError("no_q_fits_peak_budget")

    selected = min(
        feasible,
        key=lambda point: (
            point.median_latency_seconds,
            point.peak_bytes,
            point.q,
        ),
    )
    return {
        "schema": "finite-ram-lab.q-budget-decision/v0.1",
        "claim_ceiling": "OBSERVED_FRONTIER_CONSTRAINT_GOVERNOR_V0",
        "risk_mode": mode.value,
        "peak_budget_bytes": peak_budget_bytes,
        "selected_q": selected.q,
        "selected_peak_model_bytes": selected.peak_bytes,
        "selected_median_latency_seconds": selected.median_latency_seconds,
        "selection_rule": (
            "minimum_observed_median_latency_subject_to_peak_budget_and_exactness"
        ),
        "source_workflow_run_id": result["workflow_run_id"],
        "source_sweep_sha256": result["sweep_sha256"],
    }


def policy_breakpoints(
    result: Mapping[str, Any],
    *,
    mode: RiskMode,
) -> dict[str, Any]:
    points = points_for_mode(result, mode)
    baseline = next(point for point in points if point.q == 1)

    breakpoints = []
    last_selected = None
    for budget in sorted({point.peak_bytes for point in points}):
        decision = select_q(
            result,
            peak_budget_bytes=budget,
            mode=mode,
        )
        selected = int(decision["selected_q"])
        if selected != last_selected:
            point = next(item for item in points if item.q == selected)
            breakpoints.append(
                {
                    "minimum_peak_budget_bytes": budget,
                    "extra_headroom_vs_q1_bytes": budget - baseline.peak_bytes,
                    "selected_q": selected,
                    "observed_peak_model_bytes": point.peak_bytes,
                    "median_latency_seconds": point.median_latency_seconds,
                    "latency_ratio_vs_q1": (
                        point.median_latency_seconds
                        / baseline.median_latency_seconds
                    ),
                }
            )
            last_selected = selected

    return {
        "risk_mode": mode.value,
        "baseline_q1_peak_bytes": baseline.peak_bytes,
        "breakpoints": breakpoints,
    }


def build_governor(result: Mapping[str, Any]) -> dict[str, Any]:
    _validate_source(result)
    return {
        "schema": "finite-ram-lab.q-budget-governor/v0.1",
        "status": "SOFTWARE_GOVERNOR",
        "claim_ceiling": "OBSERVED_FRONTIER_CONSTRAINT_GOVERNOR_V0",
        "source_workflow_run_id": result["workflow_run_id"],
        "source_sweep_sha256": result["sweep_sha256"],
        "policy": {
            RiskMode.MEDIAN.value: policy_breakpoints(
                result,
                mode=RiskMode.MEDIAN,
            ),
            RiskMode.OBSERVED_UPPER.value: policy_breakpoints(
                result,
                mode=RiskMode.OBSERVED_UPPER,
            ),
        },
        "principle": (
            "Choose the lowest observed median latency among exact q candidates "
            "that fit the selected peak-risk budget. Do not collapse memory and "
            "latency into one weighted score."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--risk-mode", choices=[item.value for item in RiskMode])
    parser.add_argument("--peak-budget-bytes", type=int)
    args = parser.parse_args()

    result = json.loads(args.source.read_text())

    if args.risk_mode is None:
        payload = build_governor(result)
    else:
        if args.peak_budget_bytes is None:
            parser.error("--peak-budget-bytes required with --risk-mode")
        payload = select_q(
            result,
            peak_budget_bytes=args.peak_budget_bytes,
            mode=RiskMode(args.risk_mode),
        )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
