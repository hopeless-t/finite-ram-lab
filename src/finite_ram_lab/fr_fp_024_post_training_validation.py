from __future__ import annotations

import json
import statistics
from pathlib import Path
from typing import Any

SCHEMA = "finite-ram-lab.fr-fp-024-post-training-validation/v0.1"

TRAIN_PATH = (
    Path(__file__).resolve()
    .parents[2]
    / "data"
    / "FR-FP-021-few-shot-restore.json"
)

VALIDATION_PATH = (
    Path(__file__).resolve()
    .parents[2]
    / "data"
    / "FR-FP-024-post-training-validation.json"
)

DEADLINES_MS = (
    10.0,
    25.0,
    50.0,
    100.0,
)


def _load(
    path: Path,
) -> dict[str, Any]:
    return json.loads(
        path.read_text(
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


def _build_prior(
    rows: list[dict[str, Any]],
    *,
    probes: int,
    baseline_mode: str,
) -> dict[str, Any]:
    raw = []
    residual = []

    for row in rows:
        values = [
            float(value)
            for value
            in row["cold8_ms"]
        ]

        if baseline_mode == "FIRST":
            baseline = values[0]
        elif baseline_mode == "MIN":
            baseline = min(
                values[:probes]
            )
        else:
            raise ValueError(
                f"unknown_baseline_mode:{baseline_mode}"
            )

        future = values[
            probes:
        ]

        raw.extend(future)
        residual.extend(
            value / baseline
            for value in future
        )

    return {
        "raw": raw,
        "residual": residual,
    }


def _evaluate(
    training: list[dict[str, Any]],
    validation: list[dict[str, Any]],
    *,
    probes: int,
    baseline_mode: str,
) -> dict[str, Any]:
    prior = _build_prior(
        training,
        probes=probes,
        baseline_mode=(
            baseline_mode
        ),
    )

    scores = {
        str(int(deadline)): {
            "raw": [],
            "normalized": [],
        }
        for deadline
        in DEADLINES_MS
    }

    per_run = []

    for row in validation:
        values = [
            float(value)
            for value
            in row["cold8_ms"]
        ]

        if baseline_mode == "FIRST":
            baseline = values[0]
        else:
            baseline = min(
                values[:probes]
            )

        future = values[
            probes:
        ]

        deadline_rows = {}

        for deadline in DEADLINES_MS:
            key = str(
                int(deadline)
            )

            raw_probability = (
                sum(
                    value > deadline
                    for value
                    in prior["raw"]
                )
                / len(prior["raw"])
            )

            residual_threshold = (
                deadline / baseline
            )

            normalized_probability = (
                sum(
                    value
                    > residual_threshold
                    for value
                    in prior["residual"]
                )
                / len(
                    prior["residual"]
                )
            )

            outcomes = [
                value > deadline
                for value
                in future
            ]

            for outcome in outcomes:
                scores[key][
                    "raw"
                ].append(
                    _brier(
                        raw_probability,
                        outcome,
                    )
                )
                scores[key][
                    "normalized"
                ].append(
                    _brier(
                        normalized_probability,
                        outcome,
                    )
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
                "run_id": row["run_id"],
                "baseline_ms": baseline,
                "future_median_ms": (
                    statistics.median(
                        future
                    )
                ),
                "deadlines": deadline_rows,
            }
        )

    summary = {}

    for deadline in DEADLINES_MS:
        key = str(
            int(deadline)
        )
        raw = statistics.fmean(
            scores[key]["raw"]
        )
        normalized = (
            statistics.fmean(
                scores[key][
                    "normalized"
                ]
            )
        )

        summary[key] = {
            "raw_brier": raw,
            "normalized_brier": (
                normalized
            ),
            "relative_improvement": (
                1.0
                - normalized / raw
            ),
        }

    return {
        "probes": probes,
        "baseline_mode": (
            baseline_mode
        ),
        "deadline_brier": summary,
        "improves_every_deadline": (
            all(
                row[
                    "normalized_brier"
                ]
                < row[
                    "raw_brier"
                ]
                for row
                in summary.values()
            )
        ),
        "per_run": per_run,
    }


def run_panel() -> dict[str, Any]:
    training_data = _load(
        TRAIN_PATH
    )
    validation_data = _load(
        VALIDATION_PATH
    )

    training = training_data[
        "rows"
    ]
    validation = (
        validation_data[
            "rows"
        ]
    )

    one_probe = _evaluate(
        training,
        validation,
        probes=1,
        baseline_mode="FIRST",
    )
    two_probe_min = _evaluate(
        training,
        validation,
        probes=2,
        baseline_mode="MIN",
    )

    checks = {
        "training_set_is_frozen_fifteen_runs": (
            len(training)
            == 15
        ),
        "validation_has_eight_unique_head_runs": (
            len(validation)
            == 8
            and validation_data[
                "unique_head_runs"
            ]
            == 8
        ),
        "validation_runs_are_after_training_cutoff": all(
            int(row["run_id"])
            > int(
                validation_data[
                    "training_cutoff_run_id"
                ]
            )
            for row in validation
        ),
        "one_probe_reproduces_partial_but_not_universal_gain": (
            not one_probe[
                "improves_every_deadline"
            ]
            and one_probe[
                "deadline_brier"
            ][
                "10"
            ][
                "relative_improvement"
            ]
            > 0.20
            and one_probe[
                "deadline_brier"
            ][
                "50"
            ][
                "relative_improvement"
            ]
            > 0.20
        ),
        "one_probe_25ms_does_not_improve": (
            one_probe[
                "deadline_brier"
            ][
                "25"
            ][
                "relative_improvement"
            ]
            <= 0.0
        ),
        "two_probe_min_improves_every_deadline": (
            two_probe_min[
                "improves_every_deadline"
            ]
        ),
        "two_probe_min_repairs_25ms": (
            two_probe_min[
                "deadline_brier"
            ][
                "25"
            ][
                "relative_improvement"
            ]
            > 0.0
        ),
        "two_probe_min_keeps_material_50ms_gain": (
            two_probe_min[
                "deadline_brier"
            ][
                "50"
            ][
                "relative_improvement"
            ]
            > 0.30
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
            "POST_TRAINING_UNIQUE_HEAD_RESIDUAL_PRIOR_VALIDATION"
        ),
        "source": {
            "new_physical_runs_scheduled_by_this_lane": 0,
            "training_runs": len(
                training
            ),
            "validation_unique_head_runs": (
                len(validation)
            ),
            "state_mib": (
                validation_data[
                    "state_mib"
                ]
            ),
        },
        "one_probe_first": (
            one_probe
        ),
        "two_probe_min": (
            two_probe_min
        ),
        "checks": checks,
        "decision": (
            "RETAIN_RESIDUAL_TAIL_FACTORIZATION_BUT_PROMOTE_TWO_PROBE_MIN_AS_THE_MORE_ROBUST_VALIDATED_BASELINE_FOR_DEADLINE_RISK"
        ),
        "theory_update": {
            "fr_fp_023_one_probe_all_deadlines_claim": (
                "NOT_EXTERNALLY_REPLICATED_AT_25MS"
            ),
            "fr_fp_022_two_probe_min_repair": (
                "SUPPORTED_ON_POST_TRAINING_VALIDATION"
            ),
            "tail_prior": (
                "RETAIN"
            ),
        },
        "claim_ceiling": (
            "EIGHT_POST_TRAINING_UNIQUE_HEAD_GITHUB_HOSTED_CI_RUNS_ONLY"
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
