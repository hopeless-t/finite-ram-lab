from __future__ import annotations

import json
import math
import statistics
from pathlib import Path
from typing import Any

SCHEMA = "finite-ram-lab.fr-fp-021-few-shot-calibration/v0.1"

PROBE_COUNTS = (1, 2, 3)
BASELINE_DEADLINE_MS = 25.0

DATA_PATH = (
    Path(__file__).resolve()
    .parents[2]
    / "data"
    / "FR-FP-021-few-shot-restore.json"
)


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
        for value in row[
            "cold8_ms"
        ]
    )


def _loo_prior(
    rows: list[
        dict[str, Any]
    ],
    run_id: int,
) -> float:
    return statistics.median(
        _full_run_median(row)
        for row in rows
        if row[
            "run_id"
        ]
        != run_id
    )


def _confusion(
    predictions: list[bool],
    actual: list[bool],
) -> dict[str, int]:
    out = {
        "tp": 0,
        "tn": 0,
        "fp": 0,
        "fn": 0,
    }

    for predicted, truth in zip(
        predictions,
        actual,
    ):
        if predicted and truth:
            out["tp"] += 1
        elif predicted:
            out["fp"] += 1
        elif truth:
            out["fn"] += 1
        else:
            out["tn"] += 1

    return out


def _evaluate(
    rows: list[
        dict[str, Any]
    ],
    probe_count: int,
) -> dict[str, Any]:
    few_errors = []
    prior_errors = []
    costs = []
    baseline_predictions = []
    baseline_truth = []
    any_tail_predictions = []
    any_tail_truth = []
    per_run = []

    for row in rows:
        values = [
            float(value)
            for value in row[
                "cold8_ms"
            ]
        ]

        calibration = values[
            :probe_count
        ]
        future = values[
            probe_count:
        ]

        prediction = (
            statistics.median(
                calibration
            )
        )
        future_median = (
            statistics.median(
                future
            )
        )
        prior = _loo_prior(
            rows,
            int(
                row[
                    "run_id"
                ]
            ),
        )

        few_error = abs(
            math.log(
                prediction
                / future_median
            )
        )
        prior_error = abs(
            math.log(
                prior
                / future_median
            )
        )

        predicted_high = (
            prediction
            > BASELINE_DEADLINE_MS
        )
        future_high = (
            future_median
            > BASELINE_DEADLINE_MS
        )
        future_any_tail = any(
            value
            > BASELINE_DEADLINE_MS
            for value in future
        )

        few_errors.append(
            few_error
        )
        prior_errors.append(
            prior_error
        )
        costs.append(
            sum(
                calibration
            )
        )
        baseline_predictions.append(
            predicted_high
        )
        baseline_truth.append(
            future_high
        )
        any_tail_predictions.append(
            predicted_high
        )
        any_tail_truth.append(
            future_any_tail
        )

        per_run.append(
            {
                "run_id": (
                    row[
                        "run_id"
                    ]
                ),
                "calibration_median_ms": (
                    prediction
                ),
                "future_median_ms": (
                    future_median
                ),
                "loo_prior_median_ms": (
                    prior
                ),
                "few_shot_abs_log_error": (
                    few_error
                ),
                "prior_abs_log_error": (
                    prior_error
                ),
                "calibration_cost_ms": (
                    sum(
                        calibration
                    )
                ),
                "predicted_high_baseline": (
                    predicted_high
                ),
                "future_high_baseline": (
                    future_high
                ),
                "future_any_25ms_tail": (
                    future_any_tail
                ),
            }
        )

    few_mean = statistics.fmean(
        few_errors
    )
    prior_mean = statistics.fmean(
        prior_errors
    )

    return {
        "probe_count": (
            probe_count
        ),
        "few_shot": {
            "median_abs_log_error": (
                statistics.median(
                    few_errors
                )
            ),
            "mean_abs_log_error": (
                few_mean
            ),
            "mean_error_reduction_vs_loo_prior": (
                1.0
                - few_mean
                / prior_mean
            ),
        },
        "loo_prior": {
            "median_abs_log_error": (
                statistics.median(
                    prior_errors
                )
            ),
            "mean_abs_log_error": (
                prior_mean
            ),
        },
        "calibration_cost_ms": {
            "p50": (
                statistics.median(
                    costs
                )
            ),
            "max": max(
                costs
            ),
        },
        "future_baseline_over_25ms": (
            _confusion(
                baseline_predictions,
                baseline_truth,
            )
        ),
        "future_any_25ms_tail": (
            _confusion(
                any_tail_predictions,
                any_tail_truth,
            )
        ),
        "per_run": per_run,
    }


def run_panel() -> dict[str, Any]:
    data = _load()
    rows = data["rows"]

    evaluations = {
        str(probe_count): (
            _evaluate(
                rows,
                probe_count,
            )
        )
        for probe_count
        in PROBE_COUNTS
    }

    three = evaluations[
        "3"
    ]

    baseline_conf = (
        three[
            "future_baseline_over_25ms"
        ]
    )
    tail_conf = (
        three[
            "future_any_25ms_tail"
        ]
    )

    checks = {
        "fifteen_runs_with_six_trials": (
            len(rows)
            == 15
            and all(
                len(
                    row[
                        "cold8_ms"
                    ]
                )
                == 6
                for row in rows
            )
        ),
        "one_to_three_probe_evaluations_present": (
            set(
                evaluations
            )
            == {
                "1",
                "2",
                "3",
            }
        ),
        "three_probe_median_reduces_mean_log_error_over_80pct": (
            three[
                "few_shot"
            ][
                "mean_error_reduction_vs_loo_prior"
            ]
            > 0.80
        ),
        "three_probe_baseline_classification_is_perfect_on_frozen_runs": (
            baseline_conf[
                "tp"
            ]
            + baseline_conf[
                "tn"
            ]
            == 15
            and baseline_conf[
                "fp"
            ]
            == 0
            and baseline_conf[
                "fn"
            ]
            == 0
        ),
        "tail_risk_is_not_eliminated_by_baseline_calibration": (
            tail_conf[
                "fn"
            ]
            > 0
        ),
        "three_probe_calibration_has_nonzero_cost": (
            three[
                "calibration_cost_ms"
            ][
                "p50"
            ]
            > 0.0
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
            "REUSED_HOSTED_CI_FEW_SHOT_CURRENT_RUN_CALIBRATION"
        ),
        "source": {
            "new_physical_runs": 0,
            "runs": len(
                rows
            ),
            "trials_per_run": 6,
            "state_mib": (
                data[
                    "state_mib"
                ]
            ),
        },
        "evaluations": evaluations,
        "checks": checks,
        "decision": (
            "SEPARATE_FEW_SHOT_RUN_BASELINE_CALIBRATION_FROM_RESIDUAL_WITHIN_RUN_TAIL_RISK"
        ),
        "governor_direction": {
            "run_baseline": (
                "CALIBRATE_FROM_EARLY_CURRENT_RUN_RESTORES"
            ),
            "tail_risk": (
                "RETAIN_SEPARATE_DEADLINE_MISS_PRIOR"
            ),
            "probe_count": (
                "THREE_PROBE_MEDIAN_IS_A_QUALIFIED_CANDIDATE_NOT_A_UNIVERSAL_DEFAULT"
            ),
        },
        "claim_ceiling": (
            "FIFTEEN_REUSED_RUNS_SIX_TRIALS_EACH_FOR_8MIB_FEW_SHOT_CALIBRATION_ONLY"
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
