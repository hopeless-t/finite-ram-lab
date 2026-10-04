from __future__ import annotations

import json
import math
import statistics
from pathlib import Path
from typing import Any

SCHEMA = "finite-ram-lab.fr-fp-022-baseline-estimator-frontier/v0.1"

DATA_PATH = (
    Path(__file__).resolve()
    .parents[2]
    / "data"
    / "FR-FP-021-few-shot-restore.json"
)

BASELINE_DEADLINE_MS = 25.0


def _load() -> dict[str, Any]:
    return json.loads(
        DATA_PATH.read_text(
            encoding="utf-8"
        )
    )


def _full_run_median(
    row: dict[str, Any],
) -> float:
    return statistics.median(
        float(value)
        for value in row["cold8_ms"]
    )


def _loo_prior(
    rows: list[dict[str, Any]],
    run_id: int,
) -> float:
    return statistics.median(
        _full_run_median(row)
        for row in rows
        if int(row["run_id"])
        != run_id
    )


def _estimate(
    values: list[float],
    *,
    probes: int,
    method: str,
) -> float:
    if probes == 0:
        raise ValueError(
            "zero_probe_requires_prior"
        )

    sample = values[:probes]

    if method == "FIRST":
        if probes != 1:
            raise ValueError(
                "FIRST_requires_one_probe"
            )
        return sample[0]

    if method == "MEDIAN":
        return statistics.median(
            sample
        )

    if method == "MIN":
        return min(sample)

    if method == "GEOMEAN":
        return math.exp(
            statistics.fmean(
                math.log(value)
                for value in sample
            )
        )

    raise ValueError(
        f"unknown_method:{method}"
    )


def _summary(
    rows: list[dict[str, Any]],
    *,
    probes: int,
    method: str,
) -> dict[str, Any]:
    errors = []
    costs = []
    high_errors = 0
    per_run = []

    for row in rows:
        values = [
            float(value)
            for value in row[
                "cold8_ms"
            ]
        ]

        # Fixed future target for every estimator:
        # the final three restores.
        future = values[3:]
        target = statistics.median(
            future
        )

        if probes == 0:
            prediction = _loo_prior(
                rows,
                int(row["run_id"]),
            )
            cost = 0.0
        else:
            prediction = _estimate(
                values,
                probes=probes,
                method=method,
            )
            cost = sum(
                values[:probes]
            )

        error = abs(
            math.log(
                prediction / target
            )
        )

        predicted_high = (
            prediction
            > BASELINE_DEADLINE_MS
        )
        actual_high = (
            target
            > BASELINE_DEADLINE_MS
        )

        if predicted_high != actual_high:
            high_errors += 1

        errors.append(error)
        costs.append(cost)

        per_run.append(
            {
                "run_id": row[
                    "run_id"
                ],
                "prediction_ms": (
                    prediction
                ),
                "future_median_ms": (
                    target
                ),
                "abs_log_error": (
                    error
                ),
                "calibration_cost_ms": (
                    cost
                ),
                "predicted_high": (
                    predicted_high
                ),
                "actual_high": (
                    actual_high
                ),
            }
        )

    ordered = sorted(
        errors
    )

    return {
        "probes": probes,
        "method": method,
        "mean_abs_log_error": (
            statistics.fmean(
                errors
            )
        ),
        "median_abs_log_error": (
            statistics.median(
                errors
            )
        ),
        "p90_abs_log_error": (
            ordered[
                math.ceil(
                    0.90
                    * len(ordered)
                )
                - 1
            ]
        ),
        "max_abs_log_error": (
            max(errors)
        ),
        "baseline_classification_errors": (
            high_errors
        ),
        "calibration_cost_ms": {
            "p50": statistics.median(
                costs
            ),
            "max": max(costs),
        },
        "per_run": per_run,
    }


def _dominates(
    left: dict[str, Any],
    right: dict[str, Any],
) -> bool:
    # Conservative Pareto comparison uses startup cost,
    # mean error, p90 error, worst-case error, and
    # high-baseline classification errors.
    left_values = (
        left[
            "calibration_cost_ms"
        ][
            "p50"
        ],
        left[
            "mean_abs_log_error"
        ],
        left[
            "p90_abs_log_error"
        ],
        left[
            "max_abs_log_error"
        ],
        left[
            "baseline_classification_errors"
        ],
    )
    right_values = (
        right[
            "calibration_cost_ms"
        ][
            "p50"
        ],
        right[
            "mean_abs_log_error"
        ],
        right[
            "p90_abs_log_error"
        ],
        right[
            "max_abs_log_error"
        ],
        right[
            "baseline_classification_errors"
        ],
    )

    return (
        all(
            a <= b
            for a, b
            in zip(
                left_values,
                right_values,
            )
        )
        and any(
            a < b
            for a, b
            in zip(
                left_values,
                right_values,
            )
        )
    )


def run_panel() -> dict[str, Any]:
    data = _load()
    rows = data["rows"]

    candidates = [
        _summary(
            rows,
            probes=0,
            method="LOO_PRIOR",
        ),
        _summary(
            rows,
            probes=1,
            method="FIRST",
        ),
        _summary(
            rows,
            probes=2,
            method="MEDIAN",
        ),
        _summary(
            rows,
            probes=2,
            method="MIN",
        ),
        _summary(
            rows,
            probes=2,
            method="GEOMEAN",
        ),
        _summary(
            rows,
            probes=3,
            method="MEDIAN",
        ),
        _summary(
            rows,
            probes=3,
            method="MIN",
        ),
        _summary(
            rows,
            probes=3,
            method="GEOMEAN",
        ),
    ]

    by_id = {
        (
            f"{row['probes']}:"
            f"{row['method']}"
        ): row
        for row in candidates
    }

    pareto = []

    for candidate in candidates:
        dominated = any(
            _dominates(
                other,
                candidate,
            )
            for other in candidates
            if other is not candidate
        )

        if not dominated:
            pareto.append(
                (
                    f"{candidate['probes']}:"
                    f"{candidate['method']}"
                )
            )

    one = by_id["1:FIRST"]
    two_median = by_id[
        "2:MEDIAN"
    ]
    two_min = by_id[
        "2:MIN"
    ]
    three_median = by_id[
        "3:MEDIAN"
    ]
    three_min = by_id[
        "3:MIN"
    ]

    checks = {
        "fifteen_frozen_runs": (
            len(rows) == 15
        ),
        "fixed_future_target_has_three_samples": all(
            len(
                row[
                    "cold8_ms"
                ][3:]
            )
            == 3
            for row in rows
        ),
        "one_probe_classifies_baseline_regime_perfectly": (
            one[
                "baseline_classification_errors"
            ]
            == 0
        ),
        "two_probe_median_is_hurt_by_positive_tail_contamination": (
            two_median[
                "mean_abs_log_error"
            ]
            > one[
                "mean_abs_log_error"
            ]
            * 2.0
        ),
        "two_probe_min_improves_mean_error_over_one_probe": (
            two_min[
                "mean_abs_log_error"
            ]
            < one[
                "mean_abs_log_error"
            ]
        ),
        "two_probe_min_preserves_zero_baseline_classification_errors": (
            two_min[
                "baseline_classification_errors"
            ]
            == 0
        ),
        "three_probe_min_is_dominated_by_two_probe_min": (
            _dominates(
                two_min,
                three_min,
            )
        ),
        "two_probe_median_is_dominated_by_one_probe": (
            _dominates(
                one,
                two_median,
            )
        ),
        "three_probe_median_has_lower_median_error_but_higher_worst_case_than_one_probe": (
            three_median[
                "median_abs_log_error"
            ]
            < one[
                "median_abs_log_error"
            ]
            and three_median[
                "max_abs_log_error"
            ]
            > one[
                "max_abs_log_error"
            ]
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
            "REUSED_EVIDENCE_BASELINE_ESTIMATOR_FRONTIER"
        ),
        "source": {
            "new_physical_runs": 0,
            "runs": len(rows),
            "state_mib": (
                data[
                    "state_mib"
                ]
            ),
        },
        "target": (
            "median of final three COLD restores for every estimator"
        ),
        "candidates": by_id,
        "pareto_candidates": (
            pareto
        ),
        "checks": checks,
        "decision": (
            "USE_ONE_PROBE_FOR_CHEAP_REGIME_CLASSIFICATION_AND_CONSIDER_TWO_PROBE_LOWER_ENVELOPE_ONLY_WHEN_EXTRA_BASELINE_PRECISION_JUSTIFIES_THE_COST"
        ),
        "governor_direction": {
            "cheap_default_candidate": (
                "ONE_PROBE_FIRST"
            ),
            "optional_precision_candidate": (
                "TWO_PROBE_MIN"
            ),
            "two_probe_median": (
                "REJECT_ON_FROZEN_EVIDENCE"
            ),
            "three_probe_more_is_better_assumption": (
                "REJECT"
            ),
            "tail_risk": (
                "RETAIN_SEPARATELY"
            ),
        },
        "claim_ceiling": (
            "ESTIMATOR_FRONTIER_ON_FIFTEEN_REUSED_8MIB_COLD_RESTORE_RUNS_ONLY"
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
