from __future__ import annotations

import json
from typing import Any

from finite_ram_lab.fr_fp_004_predictive_phase_map import (
    run_panel as run_phase_map,
)

SCHEMA = "finite-ram-lab.fr-fp-005-feasibility-oracle/v0.1"

PHASE_TO_ROUTE = {
    "PREDICTION_SAVES_IO": {
        "classification": "POLICY_VALUE_REGION",
        "next_step": "OPTIMIZE_PREDICTIVE_POLICY",
        "stop_policy_search": False,
        "northstar_gap": "MODEL_OR_POLICY_GAP",
    },
    "PREDICTION_HAS_NO_MATERIAL_IO_ADVANTAGE": {
        "classification": "SIMPLE_POLICY_SUFFICIENT",
        "next_step": "STOP_PREDICTOR_TUNING_USE_SIMPLE_POLICY",
        "stop_policy_search": True,
        "northstar_gap": "NO_NEW_POLICY_RESEARCH",
    },
    "NO_ZERO_OOM_PREDICTIVE_CANDIDATE": {
        "classification": "PREDICTOR_MODEL_GAP",
        "next_step": "IMPROVE_PREDICTOR_OR_POLICY_FAMILY",
        "stop_policy_search": False,
        "northstar_gap": "MODEL_GAP",
    },
    "DEADLINE_INFEASIBLE": {
        "classification": "TRANSFER_SURFACE_CAPABILITY_GAP",
        "next_step": "CHANGE_CAPACITY_BANDWIDTH_STATE_SIZE_OR_RECLAIM_TIMING",
        "stop_policy_search": True,
        "northstar_gap": "CAPABILITY_GAP",
    },
}


def classify_cell(
    cell: dict[str, Any],
) -> dict[str, Any]:
    phase = cell["phase"]

    if phase not in PHASE_TO_ROUTE:
        raise ValueError(
            f"unknown_phase:{phase}"
        )

    route = dict(
        PHASE_TO_ROUTE[phase]
    )

    best = cell.get(
        "best_zero_oom_predictive"
    )

    return {
        "phase": phase,
        **route,
        "always_semantic_oom_rate": (
            cell[
                "always_preemptive"
            ][
                "semantic_oom_rate"
            ]
        ),
        "best_predictive_margin": (
            None
            if best is None
            else best["margin"]
        ),
        "best_predictive_io_saving_fraction": (
            None
            if best is None
            else best[
                "io_saving_fraction"
            ]
        ),
    }


def build_oracle() -> dict[str, Any]:
    phase_map = run_phase_map()

    if phase_map["status"] != "PASS":
        raise RuntimeError(
            "phase_map_not_qualified"
        )

    table: dict[str, Any] = {}

    for lead, budgets in (
        phase_map["matrix"].items()
    ):
        table[lead] = {}

        for budget, cell in (
            budgets.items()
        ):
            table[lead][budget] = (
                classify_cell(
                    cell
                )
            )

    return {
        "schema": SCHEMA,
        "source_schema": (
            phase_map["schema"]
        ),
        "table": table,
        "phase_counts": (
            phase_map[
                "phase_counts"
            ]
        ),
    }


def route(
    *,
    transfer_lead: int,
    hot_budget: int,
) -> dict[str, Any]:
    oracle = build_oracle()

    lead_key = str(
        transfer_lead
    )
    budget_key = str(
        hot_budget
    )

    if (
        lead_key
        not in oracle[
            "table"
        ]
    ):
        return {
            "classification": (
                "OUT_OF_CALIBRATION"
            ),
            "next_step": (
                "MEASURE_NEW_TRANSFER_LEAD"
            ),
            "stop_policy_search": True,
            "reason": (
                "Transfer lead is outside the frozen phase-map grid."
            ),
        }

    if (
        budget_key
        not in oracle[
            "table"
        ][
            lead_key
        ]
    ):
        return {
            "classification": (
                "OUT_OF_CALIBRATION"
            ),
            "next_step": (
                "MEASURE_NEW_HOT_BUDGET"
            ),
            "stop_policy_search": True,
            "reason": (
                "Hot budget is outside the frozen phase-map grid."
            ),
        }

    return dict(
        oracle[
            "table"
        ][
            lead_key
        ][
            budget_key
        ]
    )


def run_panel() -> dict[str, Any]:
    cases = {
        "policy_value": route(
            transfer_lead=2,
            hot_budget=8,
        ),
        "simple_sufficient": route(
            transfer_lead=3,
            hot_budget=4,
        ),
        "capability_gap": route(
            transfer_lead=4,
            hot_budget=4,
        ),
        "out_of_calibration": route(
            transfer_lead=5,
            hot_budget=8,
        ),
    }

    checks = {
        "lead2_budget8_routes_policy_value": (
            cases[
                "policy_value"
            ][
                "classification"
            ]
            == "POLICY_VALUE_REGION"
        ),
        "lead2_budget8_keeps_policy_search_open": (
            not cases[
                "policy_value"
            ][
                "stop_policy_search"
            ]
        ),
        "lead3_budget4_stops_predictor_tuning": (
            cases[
                "simple_sufficient"
            ][
                "classification"
            ]
            == "SIMPLE_POLICY_SUFFICIENT"
            and cases[
                "simple_sufficient"
            ][
                "stop_policy_search"
            ]
        ),
        "lead4_budget4_routes_capability_gap": (
            cases[
                "capability_gap"
            ][
                "classification"
            ]
            == "TRANSFER_SURFACE_CAPABILITY_GAP"
            and cases[
                "capability_gap"
            ][
                "northstar_gap"
            ]
            == "CAPABILITY_GAP"
        ),
        "capability_gap_stops_policy_search": (
            cases[
                "capability_gap"
            ][
                "stop_policy_search"
            ]
        ),
        "unknown_grid_fails_closed": (
            cases[
                "out_of_calibration"
            ][
                "classification"
            ]
            == "OUT_OF_CALIBRATION"
            and cases[
                "out_of_calibration"
            ][
                "stop_policy_search"
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
        "checks": checks,
        "cases": cases,
        "policy": PHASE_TO_ROUTE,
        "decision": (
            "ROUTE_POLICY_RESEARCH_ONLY_INSIDE_THE_FEASIBLE_VALUE_REGION"
        ),
        "primary_findings": [
            "POLICY_VALUE_AND_CAPABILITY_GAPS_REQUIRE_DIFFERENT_NEXT_STEPS",
            "DEADLINE_INFEASIBILITY_IS_A_STOP_RULE_FOR_POLICY_SEARCH",
            "SIMPLE_POLICY_SUFFICIENCY_IS_ALSO_A_STOP_RULE",
            "OUT_OF_CALIBRATION_INPUTS_FAIL_CLOSED_TO_NEW_MEASUREMENT",
            "PHASE_MAPS_CAN_BE_COMPILED_INTO_SMALL_RESEARCH_ROUTING_ORACLES",
        ],
        "claim_ceiling": (
            "SYNTHETIC_PHASE_MAP_ROUTING_ORACLE_ONLY"
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
