from __future__ import annotations

import itertools
import json
import statistics
from typing import Any

from finite_ram_lab.fr_fp_025_risk_aware_tier_frontier import (
    _build_empirical_priors,
    _deadline_risk,
    _expected_positive_penalty_ms,
    _load,
)
from finite_ram_lab.fr_fp_027_reuse_evidence_budget import (
    clopper_pearson_upper,
)

SCHEMA = "finite-ram-lab.fr-fp-034-multistate-budget-allocation/v0.1"

STATE_MIB = 8.0
HOSTED_BASELINE_MS = 3.299338
CONFIDENCE = 0.95
DEADLINE_MS = 10.0
MISS_TOLERANCE = 0.05

STATE_REUSE_COUNTS = tuple(
    range(10)
)
OBSERVATIONS_PER_STATE = 35

WARM_SLOT_SWEEP = tuple(
    range(3, 11)
)


def _state_rows() -> list[dict[str, Any]]:
    data = _load()
    priors = _build_empirical_priors(
        data["rows"]
    )
    residuals = priors[
        "residual"
    ]
    warm_ms = priors[
        "warm_ms"
    ]

    conditional_penalty = (
        _expected_positive_penalty_ms(
            baseline_ms=HOSTED_BASELINE_MS,
            residuals=residuals,
            warm_ms=warm_ms,
        )
    )
    conditional_deadline_risk = (
        _deadline_risk(
            baseline_ms=HOSTED_BASELINE_MS,
            residuals=residuals,
            deadline_ms=DEADLINE_MS,
        )
    )

    rows = []

    for state_id, reused in enumerate(
        STATE_REUSE_COUNTS
    ):
        p_upper = (
            clopper_pearson_upper(
                reused=reused,
                observations=(
                    OBSERVATIONS_PER_STATE
                ),
                confidence=CONFIDENCE,
            )
        )
        expected_cold_penalty = (
            p_upper
            * conditional_penalty
        )
        deadline_risk = (
            p_upper
            * conditional_deadline_risk
        )

        rows.append(
            {
                "state_id": state_id,
                "state_mib": STATE_MIB,
                "reuse_count": reused,
                "observations": (
                    OBSERVATIONS_PER_STATE
                ),
                "reuse_upper": p_upper,
                "conditional_cold_minus_warm_penalty_ms": (
                    conditional_penalty
                ),
                "expected_cold_penalty_ms": (
                    expected_cold_penalty
                ),
                "value_density_ms_per_mib": (
                    expected_cold_penalty
                    / STATE_MIB
                ),
                "conditional_deadline_risk": (
                    conditional_deadline_risk
                ),
                "unconditional_deadline_risk": (
                    deadline_risk
                ),
                "mandatory_warm": (
                    deadline_risk
                    > MISS_TOLERANCE
                ),
            }
        )

    return rows


def _greedy_allocate(
    states: list[dict[str, Any]],
    *,
    warm_slots: int,
) -> dict[str, Any]:
    mandatory = [
        row
        for row in states
        if row[
            "mandatory_warm"
        ]
    ]

    if len(mandatory) > warm_slots:
        return {
            "feasible": False,
            "reason": (
                "MANDATORY_WARM_EXCEEDS_BUDGET"
            ),
            "warm_slots": warm_slots,
            "mandatory_count": len(
                mandatory
            ),
        }

    mandatory_ids = {
        row[
            "state_id"
        ]
        for row in mandatory
    }
    optional = [
        row
        for row in states
        if row[
            "state_id"
        ]
        not in mandatory_ids
    ]
    optional.sort(
        key=lambda row: (
            -row[
                "value_density_ms_per_mib"
            ],
            row[
                "state_id"
            ],
        )
    )

    remaining = (
        warm_slots
        - len(mandatory)
    )
    selected_optional = (
        optional[:remaining]
    )
    warm_ids = (
        mandatory_ids
        | {
            row[
                "state_id"
            ]
            for row
            in selected_optional
        }
    )
    cold_rows = [
        row
        for row in states
        if row[
            "state_id"
        ]
        not in warm_ids
    ]

    optional_cold = [
        row
        for row in optional
        if row[
            "state_id"
        ]
        not in warm_ids
    ]

    selected_densities = [
        row[
            "value_density_ms_per_mib"
        ]
        for row
        in selected_optional
    ]
    cold_densities = [
        row[
            "value_density_ms_per_mib"
        ]
        for row
        in optional_cold
    ]

    lambda_lower = (
        0.0
        if not cold_densities
        else max(
            cold_densities
        )
    )
    lambda_upper = (
        None
        if not selected_densities
        else min(
            selected_densities
        )
    )

    return {
        "feasible": True,
        "warm_slots": warm_slots,
        "warm_mib": (
            warm_slots
            * STATE_MIB
        ),
        "mandatory_warm_ids": sorted(
            mandatory_ids
        ),
        "optional_warm_ids": sorted(
            row[
                "state_id"
            ]
            for row
            in selected_optional
        ),
        "warm_ids": sorted(
            warm_ids
        ),
        "cold_ids": sorted(
            row[
                "state_id"
            ]
            for row
            in cold_rows
        ),
        "expected_cold_penalty_ms": sum(
            row[
                "expected_cold_penalty_ms"
            ]
            for row
            in cold_rows
        ),
        "max_cold_deadline_risk": (
            0.0
            if not cold_rows
            else max(
                row[
                    "unconditional_deadline_risk"
                ]
                for row
                in cold_rows
            )
        ),
        "lambda_interval_ms_per_mib": {
            "lower": lambda_lower,
            "upper": lambda_upper,
        },
    }


def _exhaustive_allocate(
    states: list[dict[str, Any]],
    *,
    warm_slots: int,
) -> dict[str, Any]:
    ids = [
        row[
            "state_id"
        ]
        for row in states
    ]
    mandatory_ids = {
        row[
            "state_id"
        ]
        for row in states
        if row[
            "mandatory_warm"
        ]
    }

    candidates = []

    for subset in itertools.combinations(
        ids,
        warm_slots,
    ):
        warm_ids = set(
            subset
        )

        if not mandatory_ids.issubset(
            warm_ids
        ):
            continue

        cold_rows = [
            row
            for row in states
            if row[
                "state_id"
            ]
            not in warm_ids
        ]
        candidates.append(
            {
                "warm_ids": sorted(
                    warm_ids
                ),
                "expected_cold_penalty_ms": sum(
                    row[
                        "expected_cold_penalty_ms"
                    ]
                    for row
                    in cold_rows
                ),
            }
        )

    if not candidates:
        return {
            "feasible": False,
        }

    best = min(
        candidates,
        key=lambda row: (
            row[
                "expected_cold_penalty_ms"
            ],
            row[
                "warm_ids"
            ],
        )
    )

    return {
        "feasible": True,
        "warm_ids": best[
            "warm_ids"
        ],
        "expected_cold_penalty_ms": (
            best[
                "expected_cold_penalty_ms"
            ]
        ),
        "candidate_count": len(
            candidates
        ),
    }


def run_panel() -> dict[str, Any]:
    states = _state_rows()
    mandatory_count = sum(
        row[
            "mandatory_warm"
        ]
        for row in states
    )

    frontier = {}

    for warm_slots in (
        WARM_SLOT_SWEEP
    ):
        greedy = _greedy_allocate(
            states,
            warm_slots=warm_slots,
        )
        exact = _exhaustive_allocate(
            states,
            warm_slots=warm_slots,
        )

        frontier[
            str(warm_slots)
        ] = {
            "greedy": greedy,
            "exact": exact,
            "matches_exact": (
                greedy[
                    "feasible"
                ]
                == exact[
                    "feasible"
                ]
                and (
                    not greedy[
                        "feasible"
                    ]
                    or (
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
                    )
                )
            ),
        }

    feasible_rows = [
        frontier[
            str(slot)
        ][
            "greedy"
        ]
        for slot in WARM_SLOT_SWEEP
        if frontier[
            str(slot)
        ][
            "greedy"
        ][
            "feasible"
        ]
    ]

    penalties = [
        row[
            "expected_cold_penalty_ms"
        ]
        for row
        in feasible_rows
    ]

    budget5 = frontier[
        "5"
    ][
        "greedy"
    ]

    checks = {
        "ten_states_present": (
            len(states) == 10
        ),
        "at_least_one_deadline_mandatory_state": (
            mandatory_count > 0
        ),
        "budget5_is_feasible": (
            budget5[
                "feasible"
            ]
        ),
        "budget5_uses_exactly_five_warm_slots": (
            len(
                budget5[
                    "warm_ids"
                ]
            )
            == 5
        ),
        "every_feasible_greedy_solution_matches_exhaustive_optimum": all(
            frontier[
                str(slot)
            ][
                "matches_exact"
            ]
            for slot in WARM_SLOT_SWEEP
        ),
        "expected_cold_penalty_is_nonincreasing_with_more_warm_budget": all(
            left
            >= right
            for left, right
            in zip(
                penalties[:-1],
                penalties[1:],
            )
        ),
        "all_cold_states_meet_deadline_tolerance": all(
            row[
                "max_cold_deadline_risk"
            ]
            <= MISS_TOLERANCE
            + 1e-12
            for row
            in feasible_rows
        ),
        "budget5_has_endogenous_shadow_price_interval": (
            budget5[
                "lambda_interval_ms_per_mib"
            ][
                "upper"
            ]
            is not None
            and budget5[
                "lambda_interval_ms_per_mib"
            ][
                "lower"
            ]
            <= budget5[
                "lambda_interval_ms_per_mib"
            ][
                "upper"
            ]
        ),
    }

    marginal_savings = []

    for left, right in zip(
        feasible_rows[:-1],
        feasible_rows[1:],
    ):
        marginal_savings.append(
            (
                left[
                    "expected_cold_penalty_ms"
                ]
                - right[
                    "expected_cold_penalty_ms"
                ]
            )
            / STATE_MIB
        )

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
            "EQUAL_SIZE_MULTI_STATE_WARM_BUDGET_ALLOCATION_WITH_ENDOGENOUS_SHADOW_PRICE"
        ),
        "source": {
            "hosted_baseline_ms": (
                HOSTED_BASELINE_MS
            ),
            "reused_restore_runs": 15,
            "new_physical_runs": 0,
        },
        "fixture": {
            "state_count": len(
                states
            ),
            "state_mib": STATE_MIB,
            "reuse_observations_per_state": (
                OBSERVATIONS_PER_STATE
            ),
            "reuse_counts": list(
                STATE_REUSE_COUNTS
            ),
            "confidence": CONFIDENCE,
            "deadline_ms": DEADLINE_MS,
            "miss_tolerance": (
                MISS_TOLERANCE
            ),
            "warm_slot_sweep": list(
                WARM_SLOT_SWEEP
            ),
        },
        "states": states,
        "mandatory_warm_count": (
            mandatory_count
        ),
        "frontier": frontier,
        "marginal_expected_penalty_savings_ms_per_mib": (
            marginal_savings
        ),
        "checks": checks,
        "law": {
            "state_value": (
                "v_i = p_upper_i * E[(bR-W)+]"
            ),
            "deadline_guard": (
                "mandatory WARM if p_upper_i * P(bR>D) > epsilon"
            ),
            "equal_size_allocator": (
                "after mandatory WARM states, fill remaining slots by descending v_i / MiB"
            ),
            "endogenous_shadow_price": (
                "lambda lies between the highest optional COLD density and the lowest optional WARM density at the budget boundary"
            ),
        },
        "decision": (
            "ENDOGENIZE_MEMORY_SHADOW_PRICE_FROM_A_FINITE_MULTI_STATE_WARM_BUDGET"
        ),
        "next": (
            "PHYSICALLY_ACTUATE_MULTIPLE_8MIB_STATES_UNDER_A_SHARED_WARM_BUDGET_AND_COMPARE_WITH_STATIC_TIERING"
        ),
        "claim_ceiling": (
            "SYNTHETIC_TEN_STATE_EQUAL_SIZE_ALLOCATION_USING_ONE_HOSTED_BASELINE_AND_REUSED_RESTORE_PRIORS_ONLY"
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
