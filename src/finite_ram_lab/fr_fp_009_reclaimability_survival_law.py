from __future__ import annotations

import json
from typing import Any

from finite_ram_lab.fr_fp_002_semantic_oom import (
    _episodes,
    _first_safe_step,
)

SCHEMA = "finite-ram-lab.fr-fp-009-reclaimability-survival-law/v0.1"

LEADS = (1, 2, 3, 4, 5, 6)
BUDGETS = (2, 3, 4, 5, 6, 8, 10)
SAFE_SHIFTS = (0, 2, 4, 6, 8, 10)


def shifted_safe_time(
    rows: list[float],
    *,
    safe_shift: int,
) -> int | None:
    safe = _first_safe_step(
        rows
    )

    if safe is None:
        return None

    return max(
        1,
        safe - safe_shift,
    )


def survival_probability(
    trajectories: list[list[float]],
    *,
    deadline: int,
    safe_shift: int,
) -> float:
    at_risk = 0

    for rows in trajectories:
        safe = shifted_safe_time(
            rows,
            safe_shift=safe_shift,
        )

        if (
            safe is None
            or safe > deadline
        ):
            at_risk += 1

    return (
        at_risk
        / len(trajectories)
    )


def survival_curve(
    trajectories: list[list[float]],
    *,
    safe_shift: int = 0,
) -> dict[str, Any]:
    max_step = max(
        len(rows)
        for rows in trajectories
    ) - 1

    curve = {}

    for step in range(
        1,
        max_step + 1,
    ):
        events = 0
        risk = 0

        for rows in trajectories:
            safe = shifted_safe_time(
                rows,
                safe_shift=safe_shift,
            )

            if (
                safe is None
                or safe >= step
            ):
                risk += 1

            if safe == step:
                events += 1

        hazard = (
            0.0
            if risk == 0
            else events / risk
        )

        curve[str(step)] = {
            "at_risk": risk,
            "events": events,
            "hazard": hazard,
            "survival": (
                survival_probability(
                    trajectories,
                    deadline=step,
                    safe_shift=safe_shift,
                )
            ),
        }

    return curve


def analytic_oom_rate(
    trajectories: list[list[float]],
    *,
    transfer_lead: int,
    hot_budget: int,
    safe_shift: int,
) -> float:
    if hot_budget > transfer_lead:
        return 0.0

    return survival_probability(
        trajectories,
        deadline=hot_budget,
        safe_shift=safe_shift,
    )


def simulate_always_preemptive(
    rows: list[float],
    *,
    transfer_lead: int,
    hot_budget: int,
    safe_shift: int,
) -> bool:
    safe_step = shifted_safe_time(
        rows,
        safe_shift=safe_shift,
    )

    hot = 1
    pending: list[int] = []

    for step in range(
        1,
        len(rows),
    ):
        next_pending = []

        for remaining in pending:
            remaining -= 1

            if remaining <= 0:
                hot -= 1
            else:
                next_pending.append(
                    remaining
                )

        pending = next_pending
        hot += 1

        if (
            safe_step is not None
            and step >= safe_step
        ):
            hot = 1
            pending = []
        else:
            available = (
                hot
                - 1
                - len(pending)
            )

            if available > 0:
                pending.append(
                    transfer_lead
                )

        if hot > hot_budget:
            return True

    return False


def simulated_oom_rate(
    trajectories: list[list[float]],
    *,
    transfer_lead: int,
    hot_budget: int,
    safe_shift: int,
) -> float:
    return (
        sum(
            simulate_always_preemptive(
                rows,
                transfer_lead=transfer_lead,
                hot_budget=hot_budget,
                safe_shift=safe_shift,
            )
            for rows in trajectories
        )
        / len(trajectories)
    )


def run_panel() -> dict[str, Any]:
    trajectories = [
        trajectory
        for _family, trajectory
        in _episodes()
    ]

    curve = survival_curve(
        trajectories
    )

    comparisons = []
    max_abs_error = 0.0

    for lead in LEADS:
        for budget in BUDGETS:
            for shift in SAFE_SHIFTS:
                analytic = (
                    analytic_oom_rate(
                        trajectories,
                        transfer_lead=lead,
                        hot_budget=budget,
                        safe_shift=shift,
                    )
                )
                simulated = (
                    simulated_oom_rate(
                        trajectories,
                        transfer_lead=lead,
                        hot_budget=budget,
                        safe_shift=shift,
                    )
                )
                error = abs(
                    analytic - simulated
                )
                max_abs_error = max(
                    max_abs_error,
                    error,
                )

                comparisons.append(
                    {
                        "lead": lead,
                        "budget": budget,
                        "safe_shift": shift,
                        "analytic_oom_rate": analytic,
                        "simulated_oom_rate": simulated,
                        "abs_error": error,
                    }
                )

    checks = {
        "expanded_grid_has_252_cells": (
            len(comparisons)
            == 252
        ),
        "analytic_matches_simulation_exactly": (
            max_abs_error == 0.0
        ),
        "baseline_survival_before_first_safe_is_one": (
            curve["4"][
                "survival"
            ]
            == 1.0
        ),
        "horizon_survival_matches_never_safe_mass": (
            abs(
                curve["13"][
                    "survival"
                ]
                - 0.194
            )
            < 1e-12
        ),
        "budget_gt_lead_is_pipeline_feasible": all(
            row[
                "analytic_oom_rate"
            ]
            == 0.0
            for row in comparisons
            if row["budget"]
            > row["lead"]
        ),
        "lead4_budget4_matches_survival_law": (
            analytic_oom_rate(
                trajectories,
                transfer_lead=4,
                hot_budget=4,
                safe_shift=0,
            )
            == 1.0
            and analytic_oom_rate(
                trajectories,
                transfer_lead=4,
                hot_budget=4,
                safe_shift=10,
            )
            == 0.194
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
            "ANALYTIC_RECLAIMABILITY_SURVIVAL_LAW_VALIDATED_ON_FROZEN_TOY"
        ),
        "assumptions": [
            "one new hot state per step",
            "always-preemptive transfer initiation",
            "at most one new transfer initiated per step",
            "integer fixed transfer lead",
            "transfer completions remove one hot state",
            "safe reclaimability collapses retained hot history to one state",
            "no transfer failure",
        ],
        "law": {
            "if_hot_budget_gt_transfer_lead": (
                "semantic_oom_rate = 0"
            ),
            "otherwise": (
                "semantic_oom_rate = S_T(hot_budget)"
            ),
            "safe_time": (
                "T = first safe-reclaimability step; never-safe trajectories are right-censored beyond the horizon"
            ),
        },
        "survival_curve": curve,
        "grid": {
            "leads": list(
                LEADS
            ),
            "budgets": list(
                BUDGETS
            ),
            "safe_shifts": list(
                SAFE_SHIFTS
            ),
            "cells": len(
                comparisons
            ),
            "max_abs_error": (
                max_abs_error
            ),
        },
        "checks": checks,
        "decision": (
            "USE_SURVIVAL_LAW_INSTEAD_OF_MONTE_CARLO_WHEN_THE_FROZEN_TRANSFER_ASSUMPTIONS_HOLD"
        ),
        "skill_candidate": {
            "id": (
                "SEMANTIC_OOM_SURVIVAL_LAW"
            ),
            "mc_policy": "SKIP",
            "invalidate_on": [
                "state_arrival_rate_changes",
                "transfer_throughput_changes",
                "transfer_lead_is_not_fixed",
                "transfer_failures_exist",
                "safe_reclaimability_does_not_collapse_history",
            ],
        },
        "claim_ceiling": (
            "ANALYTIC_LAW_FOR_FROZEN_SYNTHETIC_TRANSFER_MODEL_ONLY"
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
