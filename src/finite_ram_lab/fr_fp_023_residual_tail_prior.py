from __future__ import annotations

import json
import math
import statistics
from pathlib import Path
from typing import Any

SCHEMA = "finite-ram-lab.fr-fp-023-residual-tail-prior/v0.1"

DATA_PATH = (
    Path(__file__).resolve()
    .parents[2]
    / "data"
    / "FR-FP-021-few-shot-restore.json"
)

DEADLINES_MS = (
    10.0,
    25.0,
    50.0,
    100.0,
)


def _load() -> dict[str, Any]:
    return json.loads(
        DATA_PATH.read_text(
            encoding="utf-8"
        )
    )


def _brier(
    probability: float,
    outcome: bool,
) -> float:
    observed = (
        1.0
        if outcome
        else 0.0
    )
    return (
        probability
        - observed
    ) ** 2


def _quantile(
    values: list[float],
    q: float,
) -> float:
    ordered = sorted(values)
    index = max(
        0,
        min(
            len(ordered) - 1,
            math.ceil(
                q * len(ordered)
            ) - 1,
        ),
    )
    return ordered[index]


def run_panel() -> dict[str, Any]:
    data = _load()
    rows = data["rows"]

    per_deadline = {
        str(int(deadline)): {
            "raw_scores": [],
            "normalized_scores": [],
        }
        for deadline
        in DEADLINES_MS
    }

    raw_future_medians = []
    normalized_future_medians = []
    all_residuals = []
    per_run = []

    for index, current in enumerate(
        rows
    ):
        current_values = [
            float(value)
            for value
            in current["cold8_ms"]
        ]
        current_baseline = (
            current_values[0]
        )
        current_future = (
            current_values[1:]
        )

        training_raw = []
        training_residual = []

        for cursor, other in enumerate(
            rows
        ):
            if cursor == index:
                continue

            other_values = [
                float(value)
                for value
                in other["cold8_ms"]
            ]
            other_baseline = (
                other_values[0]
            )

            training_raw.extend(
                other_values[1:]
            )
            training_residual.extend(
                value
                / other_baseline
                for value
                in other_values[1:]
            )

        residuals = [
            value
            / current_baseline
            for value
            in current_future
        ]
        all_residuals.extend(
            residuals
        )

        raw_future_median = (
            statistics.median(
                current_future
            )
        )
        normalized_future_median = (
            statistics.median(
                residuals
            )
        )

        raw_future_medians.append(
            raw_future_median
        )
        normalized_future_medians.append(
            normalized_future_median
        )

        deadline_rows = {}

        for deadline in DEADLINES_MS:
            key = str(
                int(deadline)
            )

            raw_probability = (
                sum(
                    value > deadline
                    for value in training_raw
                )
                / len(training_raw)
            )

            residual_threshold = (
                deadline
                / current_baseline
            )

            normalized_probability = (
                sum(
                    value
                    > residual_threshold
                    for value
                    in training_residual
                )
                / len(
                    training_residual
                )
            )

            outcomes = [
                value > deadline
                for value in current_future
            ]

            raw_scores = [
                _brier(
                    raw_probability,
                    outcome,
                )
                for outcome in outcomes
            ]
            normalized_scores = [
                _brier(
                    normalized_probability,
                    outcome,
                )
                for outcome in outcomes
            ]

            per_deadline[key][
                "raw_scores"
            ].extend(
                raw_scores
            )
            per_deadline[key][
                "normalized_scores"
            ].extend(
                normalized_scores
            )

            deadline_rows[key] = {
                "raw_probability": (
                    raw_probability
                ),
                "normalized_probability": (
                    normalized_probability
                ),
                "actual_miss_rate": (
                    sum(outcomes)
                    / len(outcomes)
                ),
            }

        per_run.append(
            {
                "run_id": current[
                    "run_id"
                ],
                "baseline_ms": (
                    current_baseline
                ),
                "future_median_ms": (
                    raw_future_median
                ),
                "future_residual_median": (
                    normalized_future_median
                ),
                "future_residual_max": (
                    max(residuals)
                ),
                "deadlines": (
                    deadline_rows
                ),
            }
        )

    raw_log_stdev = (
        statistics.stdev(
            math.log(value)
            for value
            in raw_future_medians
        )
    )
    normalized_log_stdev = (
        statistics.stdev(
            math.log(value)
            for value
            in normalized_future_medians
        )
    )

    deadline_summary = {}

    for deadline in DEADLINES_MS:
        key = str(
            int(deadline)
        )
        raw = statistics.fmean(
            per_deadline[key][
                "raw_scores"
            ]
        )
        normalized = (
            statistics.fmean(
                per_deadline[key][
                    "normalized_scores"
                ]
            )
        )

        deadline_summary[key] = {
            "raw_brier": raw,
            "normalized_brier": (
                normalized
            ),
            "relative_improvement": (
                1.0
                - normalized / raw
            ),
        }

    residual_summary = {
        "count": len(
            all_residuals
        ),
        "p25": _quantile(
            all_residuals,
            0.25,
        ),
        "p50": _quantile(
            all_residuals,
            0.50,
        ),
        "p75": _quantile(
            all_residuals,
            0.75,
        ),
        "p90": _quantile(
            all_residuals,
            0.90,
        ),
        "p95": _quantile(
            all_residuals,
            0.95,
        ),
        "p99": _quantile(
            all_residuals,
            0.99,
        ),
        "max": max(
            all_residuals
        ),
        "gt_2x_rate": (
            sum(
                value > 2.0
                for value in all_residuals
            )
            / len(all_residuals)
        ),
        "gt_5x_rate": (
            sum(
                value > 5.0
                for value in all_residuals
            )
            / len(all_residuals)
        ),
    }

    checks = {
        "fifteen_runs_reused": (
            len(rows) == 15
        ),
        "seventy_five_future_samples": (
            len(all_residuals)
            == 75
        ),
        "normalization_reduces_cross_run_median_log_dispersion_by_over_50pct": (
            normalized_log_stdev
            < 0.50
            * raw_log_stdev
        ),
        "normalized_prior_improves_every_deadline_brier": all(
            row[
                "normalized_brier"
            ]
            < row[
                "raw_brier"
            ]
            for row
            in deadline_summary.values()
        ),
        "normalized_25ms_brier_improves_over_50pct": (
            deadline_summary[
                "25"
            ][
                "relative_improvement"
            ]
            > 0.50
        ),
        "normalized_50ms_brier_improves_over_80pct": (
            deadline_summary[
                "50"
            ][
                "relative_improvement"
            ]
            > 0.80
        ),
        "residual_tail_remains_material": (
            residual_summary[
                "gt_2x_rate"
            ]
            > 0.10
            and residual_summary[
                "gt_5x_rate"
            ]
            > 0.05
        ),
    }

    return {
        "schema": SCHEMA,
        "status": (
            "PASS"
            if all(
                checks.values()
            )
            else "FAIL"
        ),
        "classification": (
            "BASELINE_NORMALIZED_RESIDUAL_TAIL_PRIOR"
        ),
        "source": {
            "new_physical_runs": 0,
            "runs": len(rows),
            "state_mib": (
                data[
                    "state_mib"
                ]
            ),
            "future_samples": (
                len(all_residuals)
            ),
        },
        "model": {
            "baseline": (
                "first current-run COLD restore"
            ),
            "residual": (
                "future restore latency / current-run baseline"
            ),
            "raw_prior": (
                "leave-one-run-out pooled future latency"
            ),
            "normalized_prior": (
                "leave-one-run-out pooled residual multiplier"
            ),
        },
        "cross_run_dispersion": {
            "raw_future_median_log_stdev": (
                raw_log_stdev
            ),
            "normalized_future_median_log_stdev": (
                normalized_log_stdev
            ),
            "relative_reduction": (
                1.0
                - normalized_log_stdev
                / raw_log_stdev
            ),
        },
        "residual": (
            residual_summary
        ),
        "deadline_brier": (
            deadline_summary
        ),
        "per_run": per_run,
        "checks": checks,
        "decision": (
            "MODEL_COLD_RESTORE_AS_CURRENT_RUN_BASELINE_TIMES_A_RESIDUAL_MULTIPLIER_TAIL_PRIOR"
        ),
        "governor_direction": {
            "baseline_state": (
                "CURRENT_RUN_ONE_PROBE"
            ),
            "tail_state": (
                "CROSS_RUN_RESIDUAL_MULTIPLIER_PRIOR"
            ),
            "absolute_deadline_risk": (
                "P_RESIDUAL_GREATER_THAN_DEADLINE_OVER_CURRENT_BASELINE"
            ),
        },
        "claim_ceiling": (
            "LEAVE_ONE_RUN_OUT_RESIDUAL_TAIL_MODEL_ON_FIFTEEN_REUSED_8MIB_COLD_RUNS_ONLY"
        ),
    }


def main() -> int:
    print(
        json.dumps(
            run_panel(),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
