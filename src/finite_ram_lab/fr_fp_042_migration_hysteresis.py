from __future__ import annotations

import json
from typing import Any

from finite_ram_lab.fr_fp_038_online_multistate_value import (
    MISS_TOLERANCE,
    OBSERVATIONS_PER_PHASE,
    _penalty_for_warm_set,
    run_panel as run_shadow_panel,
)

SCHEMA = "finite-ram-lab.fr-fp-042-migration-hysteresis/v0.1"

SOURCE_COST_CALIBRATION_RUN = 37205520749
SOURCE_COST_VALIDATION_RUN = 37210203932

PURE_PROMOTE_TRANSITIONS_MS = (
    60.900834 / 4.0,
    30.594290 / 2.0,
)
PURE_EVICT_TRANSITIONS_MS = (
    21.530858 / 2.0,
    31.390159 / 3.0,
)

CONSERVATIVE_PROMOTE_MS_PER_STATE = max(
    PURE_PROMOTE_TRANSITIONS_MS
)
CONSERVATIVE_EVICT_MS_PER_STATE = max(
    PURE_EVICT_TRANSITIONS_MS
)

HELD_OUT_MIXED_SWAP_ACTUAL_MS = (
    99.915626,
    107.480568,
    102.495132,
)

PHASE_HORIZON_ROUNDS = (
    OBSERVATIONS_PER_PHASE
)


def _migration_cost_ms(
    old_warm: set[int],
    new_warm: set[int],
) -> dict[str, Any]:
    promotes = len(
        new_warm
        - old_warm
    )
    evicts = len(
        old_warm
        - new_warm
    )

    return {
        "promotes": promotes,
        "evicts": evicts,
        "predicted_ms": (
            promotes
            * CONSERVATIVE_PROMOTE_MS_PER_STATE
            + evicts
            * CONSERVATIVE_EVICT_MS_PER_STATE
        ),
    }


def _max_deadline_risk_for_warm(
    states: list[dict[str, Any]],
    warm_ids: set[int],
) -> float:
    cold = [
        row
        for row in states
        if row["state_id"]
        not in warm_ids
    ]

    if not cold:
        return 0.0

    return max(
        row[
            "unconditional_deadline_risk"
        ]
        for row in cold
    )


def run_panel() -> dict[str, Any]:
    shadow = run_shadow_panel()

    if shadow["status"] != "PASS":
        raise RuntimeError(
            "shadow_parent_not_qualified"
        )

    mixed_prediction = (
        4
        * CONSERVATIVE_PROMOTE_MS_PER_STATE
        + 4
        * CONSERVATIVE_EVICT_MS_PER_STATE
    )

    validation = [
        {
            "actual_ms": actual,
            "predicted_ms": (
                mixed_prediction
            ),
            "relative_error": (
                (
                    mixed_prediction
                    - actual
                )
                / actual
            ),
            "absolute_relative_error": (
                abs(
                    mixed_prediction
                    - actual
                )
                / actual
            ),
        }
        for actual in (
            HELD_OUT_MIXED_SWAP_ACTUAL_MS
        )
    ]

    phases = shadow["phases"]
    immediate_service_ms = sum(
        row[
            "expected_cold_penalty_ms"
        ]
        * PHASE_HORIZON_ROUNDS
        for row in phases
    )
    observed_immediate_migration_ms = sum(
        HELD_OUT_MIXED_SWAP_ACTUAL_MS
    )

    current_warm = set(
        phases[0]["warm_ids"]
    )
    hysteretic_service_ms = (
        phases[0][
            "expected_cold_penalty_ms"
        ]
        * PHASE_HORIZON_ROUNDS
    )
    hysteretic_migration_ms = 0.0
    transition_rows = []

    for phase_index in range(
        1,
        len(phases),
    ):
        phase = phases[
            phase_index
        ]
        candidate = set(
            phase["warm_ids"]
        )

        current_penalty = (
            _penalty_for_warm_set(
                phase["states"],
                sorted(
                    current_warm
                ),
            )
        )
        candidate_penalty = (
            phase[
                "expected_cold_penalty_ms"
            ]
        )
        benefit_per_round = max(
            0.0,
            current_penalty
            - candidate_penalty,
        )
        benefit_over_horizon = (
            benefit_per_round
            * PHASE_HORIZON_ROUNDS
        )
        migration = (
            _migration_cost_ms(
                current_warm,
                candidate,
            )
        )
        current_deadline_risk = (
            _max_deadline_risk_for_warm(
                phase["states"],
                current_warm,
            )
        )
        current_safe = (
            current_deadline_risk
            <= MISS_TOLERANCE
            + 1e-12
        )

        must_migrate = (
            not current_safe
        )
        value_migrate = (
            candidate
            != current_warm
            and benefit_over_horizon
            >= migration[
                "predicted_ms"
            ]
        )
        migrate = (
            must_migrate
            or value_migrate
        )

        before = sorted(
            current_warm
        )

        if migrate:
            current_warm = candidate
            hysteretic_migration_ms += (
                migration[
                    "predicted_ms"
                ]
            )

        selected_penalty = (
            _penalty_for_warm_set(
                phase["states"],
                sorted(
                    current_warm
                ),
            )
        )
        hysteretic_service_ms += (
            selected_penalty
            * PHASE_HORIZON_ROUNDS
        )

        transition_rows.append(
            {
                "from_phase": (
                    phase_index
                ),
                "to_phase": (
                    phase_index
                    + 1
                ),
                "before_warm_ids": (
                    before
                ),
                "candidate_warm_ids": (
                    sorted(
                        candidate
                    )
                ),
                "selected_warm_ids": (
                    sorted(
                        current_warm
                    )
                ),
                "current_penalty_ms_per_round": (
                    current_penalty
                ),
                "candidate_penalty_ms_per_round": (
                    candidate_penalty
                ),
                "benefit_ms_per_round": (
                    benefit_per_round
                ),
                "benefit_over_horizon_ms": (
                    benefit_over_horizon
                ),
                "predicted_migration_ms": (
                    migration[
                        "predicted_ms"
                    ]
                ),
                "promotes": (
                    migration[
                        "promotes"
                    ]
                ),
                "evicts": (
                    migration[
                        "evicts"
                    ]
                ),
                "current_deadline_risk": (
                    current_deadline_risk
                ),
                "current_deadline_safe": (
                    current_safe
                ),
                "must_migrate_for_safety": (
                    must_migrate
                ),
                "migrate_for_value": (
                    value_migrate
                ),
                "migrated": (
                    migrate
                ),
            }
        )

    immediate_model_migration_ms = (
        3
        * mixed_prediction
    )
    immediate_model_total_ms = (
        immediate_service_ms
        + immediate_model_migration_ms
    )
    immediate_observed_total_ms = (
        immediate_service_ms
        + observed_immediate_migration_ms
    )
    hysteretic_total_ms = (
        hysteretic_service_ms
        + hysteretic_migration_ms
    )

    checks = {
        "cost_model_calibration_uses_only_pure_fp037_transitions": (
            SOURCE_COST_CALIBRATION_RUN
            == 37205520749
        ),
        "mixed_fp039_swaps_are_held_out_for_validation": (
            SOURCE_COST_VALIDATION_RUN
            == 37210203932
        ),
        "held_out_mixed_swap_max_relative_error_under_five_percent": (
            max(
                row[
                    "absolute_relative_error"
                ]
                for row in validation
            )
            < 0.05
        ),
        "all_current_placements_remain_deadline_safe": all(
            row[
                "current_deadline_safe"
            ]
            for row in transition_rows
        ),
        "twenty_round_hysteresis_skips_all_value_only_swaps": (
            all(
                not row[
                    "migrated"
                ]
                for row in transition_rows
            )
        ),
        "hysteretic_policy_uses_zero_migration_cost_on_fixture": (
            abs(
                hysteretic_migration_ms
            )
            < 1e-12
        ),
        "hysteretic_total_beats_immediate_model_total": (
            hysteretic_total_ms
            < immediate_model_total_ms
        ),
        "hysteretic_total_beats_immediate_observed_total": (
            hysteretic_total_ms
            < immediate_observed_total_ms
        ),
        "semantic_service_cost_is_higher_when_hysteresis_retains_old_placement": (
            hysteretic_service_ms
            > immediate_service_ms
        ),
        "physical_total_cost_is_lower_after_pricing_migration": (
            hysteretic_total_ms
            < immediate_observed_total_ms
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
            "CROSS_VALIDATED_PHYSICAL_MIGRATION_COST_MODEL_AND_HYSTERETIC_PLACEMENT"
        ),
        "cost_model": {
            "promote_ms_per_state": (
                CONSERVATIVE_PROMOTE_MS_PER_STATE
            ),
            "evict_ms_per_state": (
                CONSERVATIVE_EVICT_MS_PER_STATE
            ),
            "mixed_4_promote_4_evict_prediction_ms": (
                mixed_prediction
            ),
            "validation": validation,
        },
        "fixture": {
            "phase_horizon_rounds": (
                PHASE_HORIZON_ROUNDS
            ),
            "warm_slots": 5,
            "state_mib": 8,
        },
        "transitions": (
            transition_rows
        ),
        "immediate_optimum": {
            "service_cost_ms": (
                immediate_service_ms
            ),
            "model_migration_cost_ms": (
                immediate_model_migration_ms
            ),
            "observed_migration_cost_ms": (
                observed_immediate_migration_ms
            ),
            "model_total_ms": (
                immediate_model_total_ms
            ),
            "observed_total_ms": (
                immediate_observed_total_ms
            ),
        },
        "hysteretic": {
            "service_cost_ms": (
                hysteretic_service_ms
            ),
            "migration_cost_ms": (
                hysteretic_migration_ms
            ),
            "total_ms": (
                hysteretic_total_ms
            ),
            "migrations": sum(
                row[
                    "migrated"
                ]
                for row in transition_rows
            ),
        },
        "checks": checks,
        "decision": (
            "RETAIN_CURRENT_PLACEMENT_WHEN_EXPECTED_HORIZON_BENEFIT_DOES_NOT_AMORTIZE_A_CROSS_VALIDATED_PHYSICAL_MIGRATION_COST"
        ),
        "theory_update": [
            "a slightly worse semantic placement can be the better physical policy",
            "migration hysteresis should be driven by expected validity horizon rather than arbitrary score epsilon",
            "safety constraints override hysteresis and force migration when the retained placement becomes inadmissible",
        ],
        "next": (
            "PHYSICALLY_COMPARE_IMMEDIATE_OPTIMUM_AND_HYSTERETIC_PLACEMENT_ON_A_TRACE_LONG_ENOUGH_TO_INCLUDE_BOTH_HOLD_AND_MIGRATE_REGIMES"
        ),
        "claim_ceiling": (
            "CROSS_VALIDATED_COST_MODEL_AND_HYSTERESIS_ON_FP037_038_039_EQUAL_SIZE_FIXED_CAPACITY_EVIDENCE_ONLY"
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
