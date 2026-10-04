from __future__ import annotations

import json
import math
from typing import Any

from finite_ram_lab.fr_fp_038_online_multistate_value import (
    MISS_TOLERANCE,
    _penalty_for_warm_set,
    run_panel as run_shadow_panel,
)
from finite_ram_lab.fr_fp_042_migration_hysteresis import (
    _max_deadline_risk_for_warm,
    _migration_cost_ms,
)

SCHEMA = "finite-ram-lab.fr-fp-044-break-even-horizon-gate/v0.1"

HORIZON_GRID = tuple(
    range(
        0,
        301,
        5,
    )
)


def _context(
    *,
    phase: dict[str, Any],
    current_warm: set[int],
    candidate_warm: set[int],
    label: str,
) -> dict[str, Any]:
    current_penalty = (
        _penalty_for_warm_set(
            phase["states"],
            sorted(current_warm),
        )
    )
    candidate_penalty = (
        _penalty_for_warm_set(
            phase["states"],
            sorted(candidate_warm),
        )
    )
    benefit_per_round = max(
        0.0,
        current_penalty
        - candidate_penalty,
    )
    migration = _migration_cost_ms(
        current_warm,
        candidate_warm,
    )
    deadline_risk = (
        _max_deadline_risk_for_warm(
            phase["states"],
            current_warm,
        )
    )
    deadline_safe = (
        deadline_risk
        <= MISS_TOLERANCE
        + 1e-12
    )

    if (
        candidate_warm
        == current_warm
    ):
        break_even = None
        break_even_reason = (
            "NO_PLACEMENT_CHANGE"
        )
    elif benefit_per_round <= 0.0:
        break_even = None
        break_even_reason = (
            "NO_POSITIVE_SERVICE_BENEFIT"
        )
    else:
        break_even = (
            migration["predicted_ms"]
            / benefit_per_round
        )
        break_even_reason = (
            "FINITE_THRESHOLD"
        )

    return {
        "label": label,
        "phase": phase["phase"],
        "current_warm_ids": sorted(
            current_warm
        ),
        "candidate_warm_ids": sorted(
            candidate_warm
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
        "predicted_migration_ms": (
            migration["predicted_ms"]
        ),
        "break_even_horizon_rounds": (
            break_even
        ),
        "break_even_reason": (
            break_even_reason
        ),
        "current_deadline_risk": (
            deadline_risk
        ),
        "current_deadline_safe": (
            deadline_safe
        ),
    }


def _direct_decision(
    context: dict[str, Any],
    *,
    horizon_rounds: float,
) -> str:
    if not context[
        "current_deadline_safe"
    ]:
        return "MIGRATE_SAFETY"

    if (
        context[
            "current_warm_ids"
        ]
        == context[
            "candidate_warm_ids"
        ]
    ):
        return "HOLD_NO_CHANGE"

    benefit = context[
        "benefit_ms_per_round"
    ]

    if benefit <= 0.0:
        return "HOLD_NO_VALUE"

    if (
        benefit
        * horizon_rounds
        >= context[
            "predicted_migration_ms"
        ]
    ):
        return "MIGRATE_VALUE"

    return "HOLD_NOT_AMORTIZED"


def classify_interval(
    context: dict[str, Any],
    *,
    lower_horizon: float,
    upper_horizon: float,
) -> dict[str, Any]:
    if (
        lower_horizon < 0.0
        or upper_horizon
        < lower_horizon
    ):
        raise ValueError(
            "invalid_horizon_interval"
        )

    if not context[
        "current_deadline_safe"
    ]:
        action = (
            "MIGRATE_CERTIFIED_BY_SAFETY"
        )
        relevant = False

    elif (
        context[
            "current_warm_ids"
        ]
        == context[
            "candidate_warm_ids"
        ]
    ):
        action = (
            "HOLD_CERTIFIED_NO_CHANGE"
        )
        relevant = False

    elif context[
        "benefit_ms_per_round"
    ] <= 0.0:
        action = (
            "HOLD_CERTIFIED_NO_VALUE"
        )
        relevant = False

    else:
        threshold = context[
            "break_even_horizon_rounds"
        ]

        if (
            lower_horizon
            >= threshold
        ):
            action = (
                "MIGRATE_CERTIFIED"
            )
            relevant = False

        elif (
            upper_horizon
            < threshold
        ):
            action = (
                "HOLD_CERTIFIED"
            )
            relevant = False

        else:
            action = (
                "NEED_MORE_HORIZON_EVIDENCE"
            )
            relevant = True

    return {
        "lower_horizon": (
            lower_horizon
        ),
        "upper_horizon": (
            upper_horizon
        ),
        "action": action,
        "horizon_measurement_relevant": (
            relevant
        ),
    }


def _build_contexts() -> list[
    dict[str, Any]
]:
    shadow = run_shadow_panel()

    if shadow["status"] != "PASS":
        raise RuntimeError(
            "shadow_parent_not_qualified"
        )

    phases = shadow["phases"]
    a = {
        4,
        6,
        7,
        8,
        9,
    }
    b = {
        0,
        1,
        2,
        3,
        4,
    }

    return [
        _context(
            phase=phases[1],
            current_warm=a,
            candidate_warm=b,
            label="PHASE2_A_TO_B",
        ),
        _context(
            phase=phases[2],
            current_warm=b,
            candidate_warm=a,
            label="PHASE3_B_TO_A",
        ),
        _context(
            phase=phases[3],
            current_warm=a,
            candidate_warm=a,
            label="PHASE4_A_TO_A",
        ),
        _context(
            phase=phases[4],
            current_warm=a,
            candidate_warm=b,
            label="PHASE5_A_TO_B",
        ),
    ]


def run_panel() -> dict[str, Any]:
    contexts = _build_contexts()
    comparisons = []
    mismatches = []

    for context in contexts:
        for lower in (
            HORIZON_GRID
        ):
            for upper in (
                HORIZON_GRID
            ):
                if upper < lower:
                    continue

                classified = (
                    classify_interval(
                        context,
                        lower_horizon=float(
                            lower
                        ),
                        upper_horizon=float(
                            upper
                        ),
                    )
                )
                low_direct = (
                    _direct_decision(
                        context,
                        horizon_rounds=float(
                            lower
                        ),
                    )
                )
                high_direct = (
                    _direct_decision(
                        context,
                        horizon_rounds=float(
                            upper
                        ),
                    )
                )

                action = classified[
                    "action"
                ]

                if action.startswith(
                    "MIGRATE_CERTIFIED"
                ):
                    valid = (
                        low_direct.startswith(
                            "MIGRATE"
                        )
                        and high_direct.startswith(
                            "MIGRATE"
                        )
                    )

                elif action.startswith(
                    "HOLD_CERTIFIED"
                ):
                    valid = (
                        low_direct.startswith(
                            "HOLD"
                        )
                        and high_direct.startswith(
                            "HOLD"
                        )
                    )

                else:
                    valid = (
                        low_direct.startswith(
                            "HOLD"
                        )
                        and high_direct.startswith(
                            "MIGRATE"
                        )
                    )

                row = {
                    "context": (
                        context["label"]
                    ),
                    "lower": lower,
                    "upper": upper,
                    "classification": (
                        action
                    ),
                    "low_direct": (
                        low_direct
                    ),
                    "high_direct": (
                        high_direct
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

    by_label = {
        row["label"]: row
        for row in contexts
    }

    thresholds = {
        label: row[
            "break_even_horizon_rounds"
        ]
        for label, row
        in by_label.items()
    }

    representative = {
        "phase2_hold": (
            classify_interval(
                by_label[
                    "PHASE2_A_TO_B"
                ],
                lower_horizon=20.0,
                upper_horizon=50.0,
            )
        ),
        "phase2_ambiguous": (
            classify_interval(
                by_label[
                    "PHASE2_A_TO_B"
                ],
                lower_horizon=50.0,
                upper_horizon=70.0,
            )
        ),
        "phase2_migrate": (
            classify_interval(
                by_label[
                    "PHASE2_A_TO_B"
                ],
                lower_horizon=80.0,
                upper_horizon=120.0,
            )
        ),
        "phase5_hold": (
            classify_interval(
                by_label[
                    "PHASE5_A_TO_B"
                ],
                lower_horizon=100.0,
                upper_horizon=200.0,
            )
        ),
        "phase5_ambiguous": (
            classify_interval(
                by_label[
                    "PHASE5_A_TO_B"
                ],
                lower_horizon=200.0,
                upper_horizon=250.0,
            )
        ),
    }

    checks = {
        "all_interval_classifications_match_direct_endpoint_decisions": (
            not mismatches
        ),
        "comparison_grid_is_large": (
            len(comparisons)
            > 5_000
        ),
        "phase2_break_even_matches_fp043_mixed_regime": (
            60.0
            < thresholds[
                "PHASE2_A_TO_B"
            ]
            < 61.0
        ),
        "phase3_break_even_matches_fp043_mixed_regime": (
            79.0
            < thresholds[
                "PHASE3_B_TO_A"
            ]
            < 81.0
        ),
        "phase5_break_even_is_above_h100": (
            thresholds[
                "PHASE5_A_TO_B"
            ]
            > 200.0
        ),
        "no_change_context_never_needs_horizon_measurement": (
            not classify_interval(
                by_label[
                    "PHASE4_A_TO_A"
                ],
                lower_horizon=0.0,
                upper_horizon=300.0,
            )[
                "horizon_measurement_relevant"
            ]
        ),
        "straddling_interval_keeps_measurement_relevant": (
            representative[
                "phase2_ambiguous"
            ][
                "horizon_measurement_relevant"
            ]
            and representative[
                "phase5_ambiguous"
            ][
                "horizon_measurement_relevant"
            ]
        ),
        "separated_intervals_prune_measurement": (
            not representative[
                "phase2_hold"
            ][
                "horizon_measurement_relevant"
            ]
            and not representative[
                "phase2_migrate"
            ][
                "horizon_measurement_relevant"
            ]
            and not representative[
                "phase5_hold"
            ][
                "horizon_measurement_relevant"
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
        "classification": (
            "ANALYTIC_BREAK_EVEN_HORIZON_INTERVAL_GATE"
        ),
        "source": {
            "new_physical_runs": 0,
            "migration_cost_model": (
                "FR-FP-042"
            ),
            "physical_mixed_regime": (
                "FR-FP-043"
            ),
        },
        "law": {
            "break_even": (
                "H_star = migration_cost / benefit_per_round"
            ),
            "migrate_certified": (
                "H_lower >= H_star"
            ),
            "hold_certified": (
                "H_upper < H_star"
            ),
            "continue_measuring": (
                "H_lower < H_star <= H_upper"
            ),
            "safety_override": (
                "unsafe retained placement migrates regardless of horizon"
            ),
        },
        "contexts": contexts,
        "thresholds": (
            thresholds
        ),
        "representative": (
            representative
        ),
        "grid": {
            "horizon_values": list(
                HORIZON_GRID
            ),
            "comparisons": (
                len(comparisons)
            ),
            "mismatches": (
                len(mismatches)
            ),
        },
        "checks": checks,
        "decision": (
            "STOP_HORIZON_MEASUREMENT_ONCE_THE_VALIDITY_INTERVAL_LIES_ENTIRELY_ON_ONE_SIDE_OF_BREAK_EVEN"
        ),
        "meta_transfer": (
            "decision-relevance pruning now applies to validity-horizon measurement: exact horizon estimation is unnecessary once all admissible values imply the same migration decision"
        ),
        "next": (
            "BUILD_A_SEQUENTIAL_HORIZON_EVIDENCE_PROCESS_THAT_SHRINKS_THE_INTERVAL_UNTIL_THE_BREAK_EVEN_GATE_RESOLVES"
        ),
        "claim_ceiling": (
            "ANALYTIC_HORIZON_INTERVAL_REDUCTION_ON_FP042_043_EQUAL_SIZE_MIGRATION_CONTEXTS_ONLY"
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
