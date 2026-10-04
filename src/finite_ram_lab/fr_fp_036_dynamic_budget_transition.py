from __future__ import annotations

import json
from typing import Any

from finite_ram_lab.fr_fp_034_multistate_budget_allocation import (
    STATE_MIB,
    _exhaustive_allocate,
    _greedy_allocate,
    _state_rows,
)

SCHEMA = "finite-ram-lab.fr-fp-036-dynamic-budget-transition/v0.1"

STATE_COUNT = 10
CAPACITY_SCHEDULE = (
    5,
    3,
    7,
    4,
    6,
)
INFEASIBLE_TEST_SLOTS = 2


def _transition(
    previous: set[int],
    current: set[int],
) -> dict[str, Any]:
    evict = sorted(
        previous
        - current
    )
    promote = sorted(
        current
        - previous
    )
    changed = sorted(
        previous
        ^ current
    )

    return {
        "previous_warm_ids": sorted(
            previous
        ),
        "current_warm_ids": sorted(
            current
        ),
        "evict_ids": evict,
        "promote_ids": promote,
        "changed_ids": changed,
        "minimal_actuation_count": (
            len(changed)
        ),
        "full_reenforcement_count": (
            STATE_COUNT
        ),
        "avoided_redundant_actuations": (
            STATE_COUNT
            - len(changed)
        ),
        "changed_state_mib": (
            len(changed)
            * STATE_MIB
        ),
    }


def run_panel() -> dict[str, Any]:
    states = _state_rows()

    phases = []
    previous: set[int] | None = None
    transitions = []

    for phase, warm_slots in enumerate(
        CAPACITY_SCHEDULE,
        start=1,
    ):
        greedy = _greedy_allocate(
            states,
            warm_slots=warm_slots,
        )
        exact = _exhaustive_allocate(
            states,
            warm_slots=warm_slots,
        )

        if not greedy[
            "feasible"
        ]:
            raise RuntimeError(
                f"unexpected_infeasible_phase:{phase}"
            )

        warm_ids = set(
            greedy[
                "warm_ids"
            ]
        )

        phases.append(
            {
                "phase": phase,
                "warm_slots": (
                    warm_slots
                ),
                "warm_mib": (
                    warm_slots
                    * STATE_MIB
                ),
                "warm_ids": sorted(
                    warm_ids
                ),
                "cold_ids": (
                    greedy[
                        "cold_ids"
                    ]
                ),
                "expected_cold_penalty_ms": (
                    greedy[
                        "expected_cold_penalty_ms"
                    ]
                ),
                "lambda_interval_ms_per_mib": (
                    greedy[
                        "lambda_interval_ms_per_mib"
                    ]
                ),
                "matches_exact": (
                    greedy[
                        "warm_ids"
                    ]
                    == exact[
                        "warm_ids"
                    ]
                    and abs(
                        greedy[
                            "expected_cold_penalty_ms"
                        ]
                        - exact[
                            "expected_cold_penalty_ms"
                        ]
                    )
                    < 1e-12
                ),
            }
        )

        if previous is not None:
            transitions.append(
                {
                    "from_phase": (
                        phase - 1
                    ),
                    "to_phase": phase,
                    "from_slots": (
                        CAPACITY_SCHEDULE[
                            phase - 2
                        ]
                    ),
                    "to_slots": (
                        warm_slots
                    ),
                    **_transition(
                        previous,
                        warm_ids,
                    ),
                }
            )

        previous = warm_ids

    infeasible_greedy = (
        _greedy_allocate(
            states,
            warm_slots=(
                INFEASIBLE_TEST_SLOTS
            ),
        )
    )
    infeasible_exact = (
        _exhaustive_allocate(
            states,
            warm_slots=(
                INFEASIBLE_TEST_SLOTS
            ),
        )
    )

    total_minimal = sum(
        row[
            "minimal_actuation_count"
        ]
        for row in transitions
    )
    total_full = sum(
        row[
            "full_reenforcement_count"
        ]
        for row in transitions
    )

    nested = []

    for row in transitions:
        previous_set = set(
            row[
                "previous_warm_ids"
            ]
        )
        current_set = set(
            row[
                "current_warm_ids"
            ]
        )

        if (
            row[
                "to_slots"
            ]
            < row[
                "from_slots"
            ]
        ):
            nested.append(
                current_set.issubset(
                    previous_set
                )
            )
        else:
            nested.append(
                previous_set.issubset(
                    current_set
                )
            )

    checks = {
        "all_dynamic_phases_match_exact_optimum": all(
            row[
                "matches_exact"
            ]
            for row in phases
        ),
        "capacity_changes_produce_nested_optimal_sets": (
            all(nested)
        ),
        "minimal_actuation_touches_only_changed_states": all(
            row[
                "minimal_actuation_count"
            ]
            == (
                len(
                    row[
                        "evict_ids"
                    ]
                )
                + len(
                    row[
                        "promote_ids"
                    ]
                )
            )
            for row in transitions
        ),
        "minimal_actuation_beats_full_reenforcement": (
            total_minimal
            < total_full
        ),
        "two_slot_budget_fails_closed": (
            not infeasible_greedy[
                "feasible"
            ]
            and not infeasible_exact[
                "feasible"
            ]
        ),
        "infeasible_reason_is_mandatory_warm_budget": (
            infeasible_greedy[
                "reason"
            ]
            == "MANDATORY_WARM_EXCEEDS_BUDGET"
        ),
        "mandatory_warm_count_is_three": (
            infeasible_greedy[
                "mandatory_count"
            ]
            == 3
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
            "DYNAMIC_WARM_BUDGET_OPTIMAL_SET_TRANSITION_AND_MINIMAL_ACTUATION"
        ),
        "capacity_schedule_slots": list(
            CAPACITY_SCHEDULE
        ),
        "capacity_schedule_mib": [
            value
            * STATE_MIB
            for value in (
                CAPACITY_SCHEDULE
            )
        ],
        "phases": phases,
        "transitions": transitions,
        "summary": {
            "transition_count": (
                len(
                    transitions
                )
            ),
            "minimal_actuations": (
                total_minimal
            ),
            "full_reenforcement_actuations": (
                total_full
            ),
            "actuation_reduction_fraction": (
                1.0
                - total_minimal
                / total_full
            ),
            "infeasible_test_slots": (
                INFEASIBLE_TEST_SLOTS
            ),
        },
        "infeasible": {
            "greedy": (
                infeasible_greedy
            ),
            "exact": (
                infeasible_exact
            ),
        },
        "checks": checks,
        "decision": (
            "ACTUATE_ONLY_THE_SYMMETRIC_DIFFERENCE_BETWEEN_OLD_AND_NEW_OPTIMAL_WARM_SETS_AND_FAIL_CLOSED_BELOW_MANDATORY_CAPACITY"
        ),
        "meta_transfer": (
            "unchanged state placements are decision-irrelevant actuation work and should not be reissued"
        ),
        "next": (
            "PHYSICALLY_APPLY_THE_DYNAMIC_5_TO_3_TO_7_TO_4_TO_6_SLOT_SCHEDULE_WITH_ONLY_DELTA_TIER_ACTIONS"
        ),
        "claim_ceiling": (
            "SYNTHETIC_DYNAMIC_CAPACITY_TRANSITIONS_ON_THE_FR_FP_034_EQUAL_SIZE_TEN_STATE_FIXTURE_ONLY"
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
