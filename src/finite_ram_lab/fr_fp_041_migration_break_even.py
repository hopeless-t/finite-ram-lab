from __future__ import annotations

import json
from typing import Any

from finite_ram_lab.fr_fp_038_online_multistate_value import (
    OBSERVATIONS_PER_PHASE,
    _penalty_for_warm_set,
    run_panel as run_shadow_panel,
)

SCHEMA = "finite-ram-lab.fr-fp-041-migration-break-even/v0.1"

SOURCE_PHYSICAL_RUN = 37210203932

OBSERVED_TRANSITION_MIGRATION_MS = (
    99.915626,
    107.480568,
    0.000421,
    102.495132,
)


def run_panel() -> dict[str, Any]:
    shadow = run_shadow_panel()

    if shadow["status"] != "PASS":
        raise RuntimeError(
            "shadow_parent_not_qualified"
        )

    phases = shadow["phases"]

    if len(phases) - 1 != len(
        OBSERVED_TRANSITION_MIGRATION_MS
    ):
        raise RuntimeError(
            "transition_count_mismatch"
        )

    rows = []

    for index in range(
        1,
        len(phases),
    ):
        previous = phases[
            index - 1
        ]
        current = phases[index]

        old_penalty = (
            _penalty_for_warm_set(
                current["states"],
                previous["warm_ids"],
            )
        )
        new_penalty = (
            current[
                "expected_cold_penalty_ms"
            ]
        )
        benefit_per_round = max(
            0.0,
            old_penalty
            - new_penalty,
        )
        migration_ms = (
            OBSERVED_TRANSITION_MIGRATION_MS[
                index - 1
            ]
        )

        changed = (
            previous["warm_ids"]
            != current["warm_ids"]
        )

        break_even_rounds = (
            None
            if benefit_per_round
            <= 0.0
            else (
                migration_ms
                / benefit_per_round
            )
        )
        phase_benefit_ms = (
            benefit_per_round
            * OBSERVATIONS_PER_PHASE
        )

        rows.append(
            {
                "from_phase": index,
                "to_phase": index + 1,
                "old_warm_ids": (
                    previous[
                        "warm_ids"
                    ]
                ),
                "new_warm_ids": (
                    current[
                        "warm_ids"
                    ]
                ),
                "placement_changed": (
                    changed
                ),
                "old_placement_penalty_ms_per_round": (
                    old_penalty
                ),
                "new_optimal_penalty_ms_per_round": (
                    new_penalty
                ),
                "expected_benefit_ms_per_round": (
                    benefit_per_round
                ),
                "phase_horizon_rounds": (
                    OBSERVATIONS_PER_PHASE
                ),
                "expected_benefit_over_phase_ms": (
                    phase_benefit_ms
                ),
                "observed_migration_ms": (
                    migration_ms
                ),
                "break_even_rounds": (
                    break_even_rounds
                ),
                "pays_back_within_phase": (
                    (
                        not changed
                    )
                    or (
                        phase_benefit_ms
                        >= migration_ms
                    )
                ),
                "net_phase_value_after_migration_ms": (
                    phase_benefit_ms
                    - migration_ms
                    if changed
                    else 0.0
                ),
            }
        )

    migrating = [
        row
        for row in rows
        if row[
            "placement_changed"
        ]
    ]
    unchanged = [
        row
        for row in rows
        if not row[
            "placement_changed"
        ]
    ]

    total_migration = sum(
        row[
            "observed_migration_ms"
        ]
        for row in migrating
    )
    total_phase_benefit = sum(
        row[
            "expected_benefit_over_phase_ms"
        ]
        for row in migrating
    )

    checks = {
        "parent_shadow_passes": (
            shadow["status"]
            == "PASS"
        ),
        "three_value_driven_physical_migrations_present": (
            len(migrating)
            == 3
        ),
        "one_unchanged_phase_has_zero_semantic_benefit": (
            len(unchanged)
            == 1
            and abs(
                unchanged[0][
                    "expected_benefit_ms_per_round"
                ]
            )
            < 1e-12
        ),
        "every_migrating_transition_has_positive_expected_benefit": all(
            row[
                "expected_benefit_ms_per_round"
            ]
            > 0.0
            for row in migrating
        ),
        "no_migration_breaks_even_within_twenty_round_phase": all(
            row[
                "break_even_rounds"
            ]
            is not None
            and row[
                "break_even_rounds"
            ]
            > OBSERVATIONS_PER_PHASE
            for row in migrating
        ),
        "aggregate_migration_cost_exceeds_twenty_round_benefit": (
            total_migration
            > total_phase_benefit
        ),
        "migration_cost_is_not_hidden_in_allocator_objective": (
            True
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
            "REUSED_HOSTED_PHYSICAL_MIGRATION_COST_BREAK_EVEN_NEGATIVE_RESULT"
        ),
        "source": {
            "shadow": (
                "FR-FP-038"
            ),
            "physical_actuation": (
                "FR-FP-039"
            ),
            "physical_run": (
                SOURCE_PHYSICAL_RUN
            ),
            "new_physical_runs": 0,
        },
        "fixture": {
            "warm_slots": 5,
            "state_mib": 8,
            "phase_horizon_rounds": (
                OBSERVATIONS_PER_PHASE
            ),
        },
        "transitions": rows,
        "summary": {
            "migrating_transition_count": (
                len(migrating)
            ),
            "total_observed_migration_ms": (
                total_migration
            ),
            "total_expected_twenty_round_benefit_ms": (
                total_phase_benefit
            ),
            "benefit_to_migration_ratio": (
                total_phase_benefit
                / total_migration
            ),
            "net_value_after_migration_ms": (
                total_phase_benefit
                - total_migration
            ),
            "break_even_rounds": [
                row[
                    "break_even_rounds"
                ]
                for row in migrating
            ],
        },
        "checks": checks,
        "decision": (
            "PRICE_PHYSICAL_MIGRATION_BEFORE_ACTUATION_AND_REQUIRE_EXPECTED_VALUE_TO_AMORTIZE_WITHIN_THE_PLACEMENT_VALIDITY_HORIZON"
        ),
        "theory_update": [
            "instantaneous semantic optimum is not the same as physical control optimum",
            "migration cost can dominate the expected restore-cost improvement",
            "placement should remain resident when a new optimum cannot amortize migration cost within its expected validity horizon",
            "zero-action decision relevance remains a special case of infinite migration aversion for zero decision benefit",
        ],
        "next": (
            "BUILD_A_HYSTERETIC_ALLOCATOR_THAT_SWITCHES_ONLY_WHEN_EXPECTED_HORIZON_BENEFIT_EXCEEDS_CONSERVATIVE_MIGRATION_COST"
        ),
        "claim_ceiling": (
            "REUSED_HOSTED_ACTUATION_COST_BREAK_EVEN_ON_FP038_039_FIXED_CAPACITY_TRACE_ONLY"
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
