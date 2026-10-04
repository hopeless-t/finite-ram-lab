from __future__ import annotations

import itertools
import json
import math
import statistics
from pathlib import Path
from typing import Any

from finite_ram_lab.fr_fp_046_variable_size_knapsack import (
    _cold_penalty,
    _mandatory_ids,
    _used_mib,
)
from finite_ram_lab.fr_fp_049_joint_migration_aware_knapsack import (
    EVICT_INTERCEPT_MS,
    EVICT_SLOPE_MS_PER_MIB,
    PROMOTE_INTERCEPT_MS,
    PROMOTE_SLOPE_MS_PER_MIB,
)
from finite_ram_lab.fr_fp_051_online_joint_variable_size import (
    PHASE_HORIZON_ROUNDS,
    run_panel as _fp051_panel,
)

SCHEMA = "finite-ram-lab.fr-fp-053-current-run-migration-calibration/v0.1"

DATA_PATH = (
    Path(__file__).resolve()
    .parents[2]
    / "data"
    / "FR-FP-053-current-run-migration-calibration.json"
)


def _load() -> dict[str, Any]:
    return json.loads(
        DATA_PATH.read_text(
            encoding="utf-8"
        )
    )


def _base_promote(
    size_mib: float,
) -> float:
    return (
        PROMOTE_INTERCEPT_MS
        + PROMOTE_SLOPE_MS_PER_MIB
        * size_mib
    )


def _base_evict(
    size_mib: float,
) -> float:
    return (
        EVICT_INTERCEPT_MS
        + EVICT_SLOPE_MS_PER_MIB
        * size_mib
    )


def _direction_scales(
    rows: list[dict[str, Any]],
) -> dict[str, float]:
    promote_predicted = sum(
        float(row["predicted_ms"])
        for row in rows
        if row["direction"]
        == "PROMOTE"
    )
    promote_observed = sum(
        float(row["observed_ms"])
        for row in rows
        if row["direction"]
        == "PROMOTE"
    )
    evict_predicted = sum(
        float(row["predicted_ms"])
        for row in rows
        if row["direction"]
        == "EVICT"
    )
    evict_observed = sum(
        float(row["observed_ms"])
        for row in rows
        if row["direction"]
        == "EVICT"
    )

    return {
        "promote_scale": (
            promote_observed
            / promote_predicted
        ),
        "evict_scale": (
            evict_observed
            / evict_predicted
        ),
    }


def _predict_transition(
    row: dict[str, Any],
    *,
    promote_scale: float,
    evict_scale: float,
) -> float:
    return (
        sum(
            promote_scale
            * _base_promote(
                float(size_mib)
            )
            for size_mib in row[
                "promote_mib"
            ]
        )
        + sum(
            evict_scale
            * _base_evict(
                float(size_mib)
            )
            for size_mib in row[
                "evict_mib"
            ]
        )
    )


def _error_summary(
    rows: list[dict[str, Any]],
    *,
    promote_scale: float,
    evict_scale: float,
) -> dict[str, Any]:
    out = []
    errors = []

    for row in rows:
        predicted = (
            _predict_transition(
                row,
                promote_scale=(
                    promote_scale
                ),
                evict_scale=(
                    evict_scale
                ),
            )
        )
        observed = float(
            row["observed_ms"]
        )
        error = (
            predicted
            - observed
        )
        errors.append(
            error
        )
        out.append(
            {
                **row,
                "predicted_ms": (
                    predicted
                ),
                "error_ms": error,
                "absolute_error_ms": (
                    abs(error)
                ),
                "relative_error": (
                    abs(error)
                    / observed
                ),
            }
        )

    return {
        "rows": out,
        "mae_ms": statistics.fmean(
            abs(value)
            for value in errors
        ),
        "rmse_ms": math.sqrt(
            statistics.fmean(
                value ** 2
                for value in errors
            )
        ),
        "max_relative_error": max(
            row[
                "relative_error"
            ]
            for row in out
        ),
    }


def _state_map(
    states: list[dict[str, Any]],
) -> dict[int, dict[str, Any]]:
    return {
        int(row["state_id"]): row
        for row in states
    }


def _scaled_migration(
    states: list[dict[str, Any]],
    *,
    current_warm: set[int],
    candidate_warm: set[int],
    promote_scale: float,
    evict_scale: float,
) -> float:
    by_id = _state_map(
        states
    )

    return (
        sum(
            promote_scale
            * _base_promote(
                float(
                    by_id[
                        state_id
                    ][
                        "state_mib"
                    ]
                )
            )
            for state_id
            in (
                candidate_warm
                - current_warm
            )
        )
        + sum(
            evict_scale
            * _base_evict(
                float(
                    by_id[
                        state_id
                    ][
                        "state_mib"
                    ]
                )
            )
            for state_id
            in (
                current_warm
                - candidate_warm
            )
        )
    )


def _scaled_exhaustive(
    states: list[dict[str, Any]],
    *,
    current_warm: set[int],
    budget_mib: int,
    promote_scale: float,
    evict_scale: float,
) -> dict[str, Any]:
    mandatory = _mandatory_ids(
        states
    )
    ids = [
        int(row["state_id"])
        for row in states
    ]
    optional = [
        state_id
        for state_id in ids
        if state_id
        not in mandatory
    ]
    candidates = []

    for count in range(
        len(optional)
        + 1
    ):
        for subset in itertools.combinations(
            optional,
            count,
        ):
            warm = (
                mandatory
                | set(subset)
            )
            used = _used_mib(
                states,
                warm,
            )

            if used > budget_mib:
                continue

            service = (
                PHASE_HORIZON_ROUNDS
                * _cold_penalty(
                    states,
                    warm,
                )
            )
            migration = (
                _scaled_migration(
                    states,
                    current_warm=(
                        current_warm
                    ),
                    candidate_warm=warm,
                    promote_scale=(
                        promote_scale
                    ),
                    evict_scale=(
                        evict_scale
                    ),
                )
            )

            candidates.append(
                {
                    "warm_ids": sorted(
                        warm
                    ),
                    "used_mib": used,
                    "service_ms": (
                        service
                    ),
                    "migration_ms": (
                        migration
                    ),
                    "total_ms": (
                        service
                        + migration
                    ),
                }
            )

    if not candidates:
        raise RuntimeError(
            "no_scaled_candidate"
        )

    return min(
        candidates,
        key=lambda row: (
            row[
                "total_ms"
            ],
            -row[
                "used_mib"
            ],
            row[
                "warm_ids"
            ],
        ),
    )


def run_panel() -> dict[str, Any]:
    data = _load()
    calibration = data[
        "joint_pure_direction_calibration"
    ]
    holdout = data[
        "semantic_mixed_holdout"
    ]
    scales = _direction_scales(
        calibration
    )

    unscaled = _error_summary(
        holdout,
        promote_scale=1.0,
        evict_scale=1.0,
    )
    scaled = _error_summary(
        holdout,
        promote_scale=(
            scales[
                "promote_scale"
            ]
        ),
        evict_scale=(
            scales[
                "evict_scale"
            ]
        ),
    )

    parent = _fp051_panel()
    phase_inputs = parent[
        "phase_inputs"
    ]
    original_rows = parent[
        "joint"
    ][
        "rows"
    ]

    current = set(
        original_rows[0][
            "joint_warm_ids"
        ]
    )
    scaled_rows = [
        {
            "phase": 1,
            "warm_ids": sorted(
                current
            ),
            "original_warm_ids": (
                original_rows[0][
                    "joint_warm_ids"
                ]
            ),
            "path_changed": False,
        }
    ]

    for phase, original in zip(
        phase_inputs[1:],
        original_rows[1:],
    ):
        result = _scaled_exhaustive(
            phase["states"],
            current_warm=current,
            budget_mib=int(
                phase[
                    "budget_mib"
                ]
            ),
            promote_scale=(
                scales[
                    "promote_scale"
                ]
            ),
            evict_scale=(
                scales[
                    "evict_scale"
                ]
            ),
        )
        changed = (
            result["warm_ids"]
            != original[
                "joint_warm_ids"
            ]
        )
        scaled_rows.append(
            {
                "phase": (
                    phase[
                        "phase"
                    ]
                ),
                **result,
                "original_warm_ids": (
                    original[
                        "joint_warm_ids"
                    ]
                ),
                "path_changed": (
                    changed
                ),
            }
        )
        current = set(
            result[
                "warm_ids"
            ]
        )

    path_changed = any(
        row[
            "path_changed"
        ]
        for row in scaled_rows
    )

    checks = {
        "calibration_uses_only_joint_pure_direction_transitions": all(
            row["direction"]
            in {
                "PROMOTE",
                "EVICT",
            }
            for row in calibration
        ),
        "holdout_has_four_mixed_semantic_transitions": (
            len(holdout) == 4
        ),
        "direction_scales_are_positive": (
            scales[
                "promote_scale"
            ]
            > 0.0
            and scales[
                "evict_scale"
            ]
            > 0.0
        ),
        "scaled_model_improves_unseen_mixed_transition_mae": (
            scaled[
                "mae_ms"
            ]
            < unscaled[
                "mae_ms"
            ]
        ),
        "scaled_model_improves_unseen_mixed_transition_rmse": (
            scaled[
                "rmse_ms"
            ]
            < unscaled[
                "rmse_ms"
            ]
        ),
        "current_run_scaling_does_not_change_the_five_phase_joint_path": (
            not path_changed
        ),
        "parent_shadow_still_passes": (
            parent[
                "status"
            ]
            == "PASS"
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
            "CURRENT_RUN_DIRECTION_SCALE_WITH_DECISION_RELEVANCE_GATE"
        ),
        "source": data[
            "source"
        ],
        "calibration": {
            "promote_scale": (
                scales[
                    "promote_scale"
                ]
            ),
            "evict_scale": (
                scales[
                    "evict_scale"
                ]
            ),
            "calibration_rows": (
                calibration
            ),
        },
        "holdout": {
            "unscaled": unscaled,
            "scaled": scaled,
            "mae_reduction_fraction": (
                1.0
                - scaled[
                    "mae_ms"
                ]
                / unscaled[
                    "mae_ms"
                ]
            ),
        },
        "scaled_optimizer": {
            "rows": scaled_rows,
            "path_changed": (
                path_changed
            ),
        },
        "checks": checks,
        "decision": (
            "KEEP_THE_STRUCTURAL_AFFINE_BYTE_MODEL_AND_SKIP_STRUCTURAL_REFIT_WHEN_LIGHTWEIGHT_CURRENT_RUN_DIRECTION_SCALING_RESTORES_HELDOUT_ERROR_WITHOUT_CHANGING_THE_OPTIMAL_PATH"
        ),
        "meta_transfer": (
            "model maintenance is decision-directed: prediction error alone does not justify structural retraining if a cheaper calibration repairs held-out error and the admissible decision is unchanged"
        ),
        "next": (
            "COMPILE_MODEL_MAINTENANCE_DECISION_RELEVANCE_ONLY_AFTER_AN_INDEPENDENT_MODEL_OR_DECISION_FAMILY_REPLICATES_THE_RULE"
        ),
        "claim_ceiling": (
            "CURRENT_RUN_DIRECTION_SCALING_AND_REFIT_SKIP_ON_ONE_FP052_HOSTED_TRACE_ONLY"
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
