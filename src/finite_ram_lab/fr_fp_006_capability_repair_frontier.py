from __future__ import annotations

import json
from typing import Any

from finite_ram_lab.fr_fp_005_feasibility_oracle import (
    route,
)

SCHEMA = "finite-ram-lab.fr-fp-006-capability-repair-frontier/v0.1"

BASELINE_LEAD = 4
BASELINE_BUDGET = 4
GRID_LEADS = (1, 2, 3, 4)
GRID_BUDGETS = (4, 6, 8, 10)


def _is_capability_gap(
    *,
    lead: int,
    budget: int,
) -> bool:
    row = route(
        transfer_lead=lead,
        hot_budget=budget,
    )
    return (
        row[
            "classification"
        ]
        == "TRANSFER_SURFACE_CAPABILITY_GAP"
    )


def minimum_budget_repair() -> dict[str, Any]:
    for budget in GRID_BUDGETS:
        if budget <= BASELINE_BUDGET:
            continue

        if not _is_capability_gap(
            lead=BASELINE_LEAD,
            budget=budget,
        ):
            return {
                "lever": "HOT_CAPACITY",
                "baseline_budget_states": BASELINE_BUDGET,
                "required_budget_states": budget,
                "absolute_increase_states": (
                    budget - BASELINE_BUDGET
                ),
                "relative_capacity_increase": (
                    budget / BASELINE_BUDGET
                    - 1.0
                ),
                "result": route(
                    transfer_lead=BASELINE_LEAD,
                    hot_budget=budget,
                ),
            }

    return {
        "lever": "HOT_CAPACITY",
        "result": (
            "NO_REPAIR_INSIDE_FROZEN_GRID"
        ),
    }


def minimum_lead_repair() -> dict[str, Any]:
    for lead in sorted(
        (
            value
            for value
            in GRID_LEADS
            if value < BASELINE_LEAD
        ),
        reverse=True,
    ):
        if not _is_capability_gap(
            lead=lead,
            budget=BASELINE_BUDGET,
        ):
            return {
                "lever": "TRANSFER_LEAD",
                "baseline_lead_steps": BASELINE_LEAD,
                "required_lead_steps": lead,
                "absolute_reduction_steps": (
                    BASELINE_LEAD - lead
                ),
                "relative_lead_reduction": (
                    1.0
                    - lead / BASELINE_LEAD
                ),
                "result": route(
                    transfer_lead=lead,
                    hot_budget=BASELINE_BUDGET,
                ),
            }

    return {
        "lever": "TRANSFER_LEAD",
        "result": (
            "NO_REPAIR_INSIDE_FROZEN_GRID"
        ),
    }


def equivalent_state_size_repair(
    capacity_repair: dict[str, Any],
) -> dict[str, Any]:
    required_budget = (
        capacity_repair[
            "required_budget_states"
        ]
    )

    size_fraction = (
        BASELINE_BUDGET
        / required_budget
    )

    return {
        "lever": "STATE_SIZE",
        "mapping": (
            "fixed_hot_bytes / smaller_state_bytes -> larger_effective_state_budget"
        ),
        "baseline_effective_budget_states": BASELINE_BUDGET,
        "target_effective_budget_states": required_budget,
        "maximum_state_size_fraction_of_baseline": (
            size_fraction
        ),
        "minimum_state_size_reduction_fraction": (
            1.0 - size_fraction
        ),
        "evidence_class": (
            "GEOMETRIC_EQUIVALENCE_ONLY"
        ),
        "note": (
            "This maps state-size reduction onto the frozen state-count budget; "
            "it does not claim a physical codec or representation can achieve it."
        ),
    }


def reclaimability_timing_gap() -> dict[str, Any]:
    return {
        "lever": "RECLAIMABILITY_TIMING",
        "classification": "MODEL_GAP",
        "next_step": (
            "QUALIFY_EFFECT_OF_EARLIER_SAFE_RECLAIMABILITY_ON_DEADLINE_FEASIBILITY"
        ),
        "reason": (
            "FR-FP-004 varies budget, transfer lead, and predictor margin, but "
            "does not vary the underlying safe-reclaimability arrival time."
        ),
        "minimum_shift_steps": None,
        "unknown_is_not_zero": True,
    }


def run_panel() -> dict[str, Any]:
    baseline = route(
        transfer_lead=BASELINE_LEAD,
        hot_budget=BASELINE_BUDGET,
    )

    capacity = minimum_budget_repair()
    lead = minimum_lead_repair()
    state_size = (
        equivalent_state_size_repair(
            capacity
        )
    )
    reclaimability = (
        reclaimability_timing_gap()
    )

    checks = {
        "baseline_is_capability_gap": (
            baseline[
                "classification"
            ]
            == "TRANSFER_SURFACE_CAPABILITY_GAP"
        ),
        "one_step_lead_reduction_repairs": (
            lead[
                "absolute_reduction_steps"
            ]
            == 1
            and lead[
                "required_lead_steps"
            ]
            == 3
            and lead[
                "result"
            ][
                "classification"
            ]
            != "TRANSFER_SURFACE_CAPABILITY_GAP"
        ),
        "two_state_capacity_increase_repairs": (
            capacity[
                "absolute_increase_states"
            ]
            == 2
            and capacity[
                "required_budget_states"
            ]
            == 6
            and capacity[
                "result"
            ][
                "classification"
            ]
            != "TRANSFER_SURFACE_CAPABILITY_GAP"
        ),
        "state_size_equivalence_is_one_third_reduction": (
            abs(
                state_size[
                    "minimum_state_size_reduction_fraction"
                ]
                - 1.0 / 3.0
            )
            < 1e-12
        ),
        "reclaimability_shift_remains_unknown": (
            reclaimability[
                "classification"
            ]
            == "MODEL_GAP"
            and reclaimability[
                "minimum_shift_steps"
            ]
            is None
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
        "baseline": {
            "transfer_lead": BASELINE_LEAD,
            "hot_budget": BASELINE_BUDGET,
            "oracle": baseline,
        },
        "repair_frontier": {
            "transfer_lead": lead,
            "hot_capacity": capacity,
            "state_size": state_size,
            "reclaimability_timing": reclaimability,
        },
        "checks": checks,
        "comparison_policy": (
            "DO_NOT_RANK_HETEROGENEOUS_LEVERS_WITHOUT_A_FROZEN_COMMON_COST_MODEL"
        ),
        "decision": (
            "DECOMPOSE_CAPABILITY_GAP_INTO_MINIMAL_MEASURED_REPAIRS_AND_EXPLICIT_MODEL_GAPS"
        ),
        "primary_findings": [
            "LEAD4_BUDGET4_CAPABILITY_GAP_CAN_BE_ESCAPED_BY_ONE_STEP_LEAD_REDUCTION",
            "THE_SAME_GAP_CAN_BE_ESCAPED_BY_TWO_MORE_HOT_STATE_SLOTS",
            "AT_FIXED_HOT_BYTES_THAT_CAPACITY_CHANGE_IS_GEOMETRICALLY_EQUIVALENT_TO_AT_LEAST_ONE_THIRD_STATE_SIZE_REDUCTION",
            "RECLAIMABILITY_TIMING_EFFECT_IS_NOT_IDENTIFIED_BY_THE_CURRENT_PHASE_MAP",
            "HETEROGENEOUS_RESOURCE_LEVERS_MUST_NOT_BE_RANKED_WITHOUT_A_COMMON_COST_MODEL",
        ],
        "claim_ceiling": (
            "SYNTHETIC_CAPABILITY_REPAIR_FRONTIER_AND_GEOMETRIC_EQUIVALENCE_ONLY"
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
