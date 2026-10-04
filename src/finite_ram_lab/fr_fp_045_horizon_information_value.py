from __future__ import annotations

import json
from typing import Any

from finite_ram_lab.fr_fp_044_break_even_horizon_gate import (
    HORIZON_GRID,
    _build_contexts,
    classify_interval,
)

SCHEMA = "finite-ram-lab.fr-fp-045-horizon-information-value/v0.1"

MEASUREMENT_COSTS_MS = (
    0.0,
    1.0,
    5.0,
    10.0,
    15.0,
    20.0,
    50.0,
)


def _regret_at_horizon(
    context: dict[str, Any],
    *,
    horizon_rounds: float,
    action: str,
) -> float:
    benefit = context[
        "benefit_ms_per_round"
    ]
    migration = context[
        "predicted_migration_ms"
    ]

    if action == "HOLD":
        return max(
            0.0,
            benefit
            * horizon_rounds
            - migration,
        )

    if action == "MIGRATE":
        return max(
            0.0,
            migration
            - benefit
            * horizon_rounds,
        )

    raise ValueError(
        "unknown_action"
    )


def robust_information_ceiling(
    context: dict[str, Any],
    *,
    lower_horizon: float,
    upper_horizon: float,
) -> dict[str, Any]:
    classified = classify_interval(
        context,
        lower_horizon=lower_horizon,
        upper_horizon=upper_horizon,
    )

    if not classified[
        "horizon_measurement_relevant"
    ]:
        action = (
            "MIGRATE"
            if classified[
                "action"
            ].startswith(
                "MIGRATE"
            )
            else "HOLD"
        )

        return {
            **classified,
            "robust_action": (
                action
            ),
            "hold_worst_case_regret_ms": (
                0.0
            ),
            "migrate_worst_case_regret_ms": (
                0.0
            ),
            "perfect_information_value_ceiling_ms": (
                0.0
            ),
        }

    hold_regret = (
        _regret_at_horizon(
            context,
            horizon_rounds=(
                upper_horizon
            ),
            action="HOLD",
        )
    )
    migrate_regret = (
        _regret_at_horizon(
            context,
            horizon_rounds=(
                lower_horizon
            ),
            action="MIGRATE",
        )
    )

    if hold_regret <= migrate_regret:
        robust_action = "HOLD"
        ceiling = hold_regret
    else:
        robust_action = "MIGRATE"
        ceiling = migrate_regret

    return {
        **classified,
        "robust_action": (
            robust_action
        ),
        "hold_worst_case_regret_ms": (
            hold_regret
        ),
        "migrate_worst_case_regret_ms": (
            migrate_regret
        ),
        "perfect_information_value_ceiling_ms": (
            ceiling
        ),
    }


def measurement_decision(
    context: dict[str, Any],
    *,
    lower_horizon: float,
    upper_horizon: float,
    measurement_cost_ms: float,
) -> dict[str, Any]:
    if measurement_cost_ms < 0.0:
        raise ValueError(
            "negative_measurement_cost"
        )

    result = robust_information_ceiling(
        context,
        lower_horizon=lower_horizon,
        upper_horizon=upper_horizon,
    )

    if not result[
        "horizon_measurement_relevant"
    ]:
        decision = (
            "STOP_ALREADY_CERTIFIED"
        )

    elif (
        measurement_cost_ms
        >= result[
            "perfect_information_value_ceiling_ms"
        ]
    ):
        decision = (
            "STOP_MEASUREMENT_TAKE_ROBUST_ACTION"
        )

    else:
        decision = (
            "MEASURE_MORE"
        )

    return {
        **result,
        "measurement_cost_ms": (
            measurement_cost_ms
        ),
        "measurement_decision": (
            decision
        ),
    }


def _exhaustive_worst_regret(
    context: dict[str, Any],
    *,
    lower: int,
    upper: int,
    action: str,
) -> float:
    values = [
        value
        for value in HORIZON_GRID
        if lower
        <= value
        <= upper
    ]

    if not values:
        raise RuntimeError(
            "empty_horizon_grid_interval"
        )

    return max(
        _regret_at_horizon(
            context,
            horizon_rounds=float(
                value
            ),
            action=action,
        )
        for value in values
    )


def run_panel() -> dict[str, Any]:
    contexts = _build_contexts()
    comparisons = []
    mismatches = []
    monotonic_rows = []

    for context in contexts:
        for lower in HORIZON_GRID:
            for upper in HORIZON_GRID:
                if upper < lower:
                    continue

                result = (
                    robust_information_ceiling(
                        context,
                        lower_horizon=float(
                            lower
                        ),
                        upper_horizon=float(
                            upper
                        ),
                    )
                )

                if result[
                    "horizon_measurement_relevant"
                ]:
                    exhaustive = (
                        _exhaustive_worst_regret(
                            context,
                            lower=lower,
                            upper=upper,
                            action=result[
                                "robust_action"
                            ],
                        )
                    )
                    formula = result[
                        "perfect_information_value_ceiling_ms"
                    ]
                    valid = (
                        abs(
                            exhaustive
                            - formula
                        )
                        < 1e-9
                    )
                else:
                    exhaustive = 0.0
                    formula = 0.0
                    valid = True

                row = {
                    "context": (
                        context["label"]
                    ),
                    "lower": lower,
                    "upper": upper,
                    "robust_action": (
                        result[
                            "robust_action"
                        ]
                    ),
                    "formula_regret_ms": (
                        formula
                    ),
                    "exhaustive_regret_ms": (
                        exhaustive
                    ),
                    "valid": valid,
                }
                comparisons.append(
                    row
                )

                if not valid:
                    mismatches.append(
                        row
                    )

                decisions = [
                    measurement_decision(
                        context,
                        lower_horizon=float(
                            lower
                        ),
                        upper_horizon=float(
                            upper
                        ),
                        measurement_cost_ms=(
                            cost
                        ),
                    )[
                        "measurement_decision"
                    ]
                    for cost in (
                        MEASUREMENT_COSTS_MS
                    )
                ]
                measure_flags = [
                    decision
                    == "MEASURE_MORE"
                    for decision
                    in decisions
                ]
                monotonic_rows.append(
                    all(
                        not (
                            earlier is False
                            and later is True
                        )
                        for earlier, later
                        in zip(
                            measure_flags[:-1],
                            measure_flags[1:],
                        )
                    )
                )

    by_label = {
        row["label"]: row
        for row in contexts
    }
    phase2 = by_label[
        "PHASE2_A_TO_B"
    ]
    phase5 = by_label[
        "PHASE5_A_TO_B"
    ]

    representative = {
        "phase2_ambiguous": (
            robust_information_ceiling(
                phase2,
                lower_horizon=50.0,
                upper_horizon=70.0,
            )
        ),
        "phase2_cost5": (
            measurement_decision(
                phase2,
                lower_horizon=50.0,
                upper_horizon=70.0,
                measurement_cost_ms=5.0,
            )
        ),
        "phase2_cost20": (
            measurement_decision(
                phase2,
                lower_horizon=50.0,
                upper_horizon=70.0,
                measurement_cost_ms=20.0,
            )
        ),
        "phase5_ambiguous": (
            robust_information_ceiling(
                phase5,
                lower_horizon=200.0,
                upper_horizon=250.0,
            )
        ),
        "phase5_cost5": (
            measurement_decision(
                phase5,
                lower_horizon=200.0,
                upper_horizon=250.0,
                measurement_cost_ms=5.0,
            )
        ),
        "phase5_cost15": (
            measurement_decision(
                phase5,
                lower_horizon=200.0,
                upper_horizon=250.0,
                measurement_cost_ms=15.0,
            )
        ),
    }

    checks = {
        "regret_formula_matches_exhaustive_grid_everywhere": (
            not mismatches
        ),
        "comparison_grid_is_large": (
            len(comparisons)
            > 5_000
        ),
        "measurement_decision_is_monotonic_in_measurement_cost": (
            all(
                monotonic_rows
            )
        ),
        "phase2_ambiguous_robust_action_is_hold": (
            representative[
                "phase2_ambiguous"
            ][
                "robust_action"
            ]
            == "HOLD"
        ),
        "phase2_information_ceiling_is_about_16ms": (
            16.0
            < representative[
                "phase2_ambiguous"
            ][
                "perfect_information_value_ceiling_ms"
            ]
            < 17.0
        ),
        "phase2_cost5_keeps_measurement": (
            representative[
                "phase2_cost5"
            ][
                "measurement_decision"
            ]
            == "MEASURE_MORE"
        ),
        "phase2_cost20_stops_measurement": (
            representative[
                "phase2_cost20"
            ][
                "measurement_decision"
            ]
            == "STOP_MEASUREMENT_TAKE_ROBUST_ACTION"
        ),
        "phase5_ambiguous_robust_action_is_migrate": (
            representative[
                "phase5_ambiguous"
            ][
                "robust_action"
            ]
            == "MIGRATE"
        ),
        "phase5_information_ceiling_is_about_10ms": (
            10.0
            < representative[
                "phase5_ambiguous"
            ][
                "perfect_information_value_ceiling_ms"
            ]
            < 11.0
        ),
        "phase5_cost5_keeps_measurement": (
            representative[
                "phase5_cost5"
            ][
                "measurement_decision"
            ]
            == "MEASURE_MORE"
        ),
        "phase5_cost15_stops_measurement": (
            representative[
                "phase5_cost15"
            ][
                "measurement_decision"
            ]
            == "STOP_MEASUREMENT_TAKE_ROBUST_ACTION"
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
            "ROBUST_HORIZON_INFORMATION_VALUE_CEILING"
        ),
        "source": {
            "new_physical_runs": 0,
            "parent_gate": (
                "FR-FP-044"
            ),
            "measurement_cost_unit": (
                "milliseconds"
            ),
            "regret_unit": (
                "milliseconds"
            ),
        },
        "law": {
            "hold_worst_case_regret": (
                "max(0, benefit_per_round*H_upper - migration_cost)"
            ),
            "migrate_worst_case_regret": (
                "max(0, migration_cost - benefit_per_round*H_lower)"
            ),
            "robust_action": (
                "argmin(HOLD_regret, MIGRATE_regret)"
            ),
            "perfect_information_value_ceiling": (
                "min(HOLD_regret, MIGRATE_regret)"
            ),
            "measurement_stop": (
                "stop if measurement_cost >= perfect_information_value_ceiling"
            ),
        },
        "measurement_costs_ms": list(
            MEASUREMENT_COSTS_MS
        ),
        "representative": (
            representative
        ),
        "grid": {
            "comparisons": (
                len(comparisons)
            ),
            "mismatches": (
                len(mismatches)
            ),
        },
        "checks": checks,
        "decision": (
            "MEASURE_HORIZON_ONLY_WHEN_THE_MAXIMUM_ROBUST_VALUE_OF_PERFECT_INFORMATION_EXCEEDS_MEASUREMENT_COST"
        ),
        "meta_transfer": (
            "decision-relevant information can still be pruned when the maximum decision regret it could remove is smaller than the cost of acquiring it"
        ),
        "next": (
            "CALIBRATE_A_REAL_HORIZON_MEASUREMENT_COST_OR_PROXY_BEFORE_USING_THE_INFORMATION_VALUE_GATE_PHYSICALLY"
        ),
        "claim_ceiling": (
            "ANALYTIC_ROBUST_INFORMATION_VALUE_BOUND_ON_FP044_HORIZON_CONTEXTS_ONLY"
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
