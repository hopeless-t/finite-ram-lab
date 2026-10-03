from __future__ import annotations

import json
import statistics
from typing import Any

from finite_ram_lab.fr_fp_002_semantic_oom import (
    _episodes,
    _first_safe_step,
)
from finite_ram_lab.fr_fp_003_predictive_cold_tier import (
    estimate_safe_eta,
)

SCHEMA = "finite-ram-lab.fr-fp-004-predictive-phase-map/v0.1"

LEADS = (1, 2, 3, 4)
BUDGETS = (4, 6, 8, 10)
MARGINS = (-1, 0, 1, 2, 3, 4)


def simulate(
    rows: list[float],
    *,
    policy: str,
    budget: int,
    lead: int,
    margin: int = 0,
) -> dict[str, Any]:
    if lead < 1:
        raise ValueError("lead_must_be_positive")

    safe_step = _first_safe_step(rows)
    hot = 1
    cold = 0
    pending: list[int] = []
    semantic_oom = False
    cold_writes = 0
    requests = 0
    peak_hot = 1

    for step in range(1, len(rows)):
        next_pending = []

        for remaining in pending:
            remaining -= 1

            if remaining <= 0:
                hot -= 1
                cold += 1
                cold_writes += 1
            else:
                next_pending.append(remaining)

        pending = next_pending
        hot += 1

        if safe_step is not None and step >= safe_step:
            hot = 1
            cold = 0
            pending = []
        else:
            available = hot - 1 - len(pending)

            request = False

            if available > 0:
                if policy == "ALWAYS_PREEMPTIVE":
                    request = True

                elif policy == "PREDICTIVE_TRANSFER":
                    eta = estimate_safe_eta(rows, step)
                    slots = budget - hot

                    request = (
                        eta
                        > (
                            slots
                            - lead
                            + margin
                        )
                    )
                else:
                    raise ValueError(
                        f"unknown_policy:{policy}"
                    )

            if request:
                pending.append(lead)
                requests += 1

        if hot > budget:
            semantic_oom = True

        peak_hot = max(peak_hot, hot)

    return {
        "semantic_oom": semantic_oom,
        "cold_writes": cold_writes,
        "requests": requests,
        "peak_hot": peak_hot,
    }


def _summarize(
    rows: list[dict[str, Any]],
) -> dict[str, float]:
    return {
        "semantic_oom_rate": (
            sum(row["semantic_oom"] for row in rows)
            / len(rows)
        ),
        "mean_cold_writes": statistics.fmean(
            row["cold_writes"]
            for row in rows
        ),
        "mean_requests": statistics.fmean(
            row["requests"]
            for row in rows
        ),
        "mean_peak_hot": statistics.fmean(
            row["peak_hot"]
            for row in rows
        ),
    }


def _phase(
    *,
    always: dict[str, float],
    best: dict[str, Any] | None,
) -> str:
    if always["semantic_oom_rate"] > 0.0:
        return "DEADLINE_INFEASIBLE"

    if best is None:
        return "NO_ZERO_OOM_PREDICTIVE_CANDIDATE"

    if best["io_saving_fraction"] <= 0.05:
        return "PREDICTION_HAS_NO_MATERIAL_IO_ADVANTAGE"

    return "PREDICTION_SAVES_IO"


def run_panel() -> dict[str, Any]:
    episodes = [
        trajectory
        for _family, trajectory
        in _episodes()
    ]

    matrix: dict[str, Any] = {}

    for lead in LEADS:
        matrix[str(lead)] = {}

        for budget in BUDGETS:
            always = _summarize(
                [
                    simulate(
                        trajectory,
                        policy="ALWAYS_PREEMPTIVE",
                        budget=budget,
                        lead=lead,
                    )
                    for trajectory
                    in episodes
                ]
            )

            candidates = []

            for margin in MARGINS:
                row = _summarize(
                    [
                        simulate(
                            trajectory,
                            policy="PREDICTIVE_TRANSFER",
                            budget=budget,
                            lead=lead,
                            margin=margin,
                        )
                        for trajectory
                        in episodes
                    ]
                )

                candidates.append(
                    {
                        "margin": margin,
                        **row,
                    }
                )

            zero_oom = [
                row
                for row in candidates
                if row["semantic_oom_rate"] == 0.0
            ]

            best = None

            if zero_oom:
                selected = min(
                    zero_oom,
                    key=lambda row: (
                        row["mean_cold_writes"],
                        row["mean_requests"],
                        abs(row["margin"]),
                        row["margin"],
                    ),
                )

                baseline_writes = (
                    always["mean_cold_writes"]
                )

                saving = (
                    0.0
                    if baseline_writes <= 0.0
                    else 1.0
                    - selected["mean_cold_writes"]
                    / baseline_writes
                )

                best = {
                    **selected,
                    "io_saving_fraction": saving,
                }

            matrix[str(lead)][str(budget)] = {
                "always_preemptive": always,
                "predictive_candidates": candidates,
                "best_zero_oom_predictive": best,
                "phase": _phase(
                    always=always,
                    best=best,
                ),
            }

    lead2 = matrix["2"]
    lead3 = matrix["3"]
    lead4 = matrix["4"]

    checks = {
        "lead4_budget4_is_infeasible": (
            lead4["4"]["phase"]
            == "DEADLINE_INFEASIBLE"
            and lead4["4"][
                "always_preemptive"
            ]["semantic_oom_rate"]
            > 0.99
        ),
        "lead2_budget8_prediction_saves_gt_40pct": (
            lead2["8"]["phase"]
            == "PREDICTION_SAVES_IO"
            and lead2["8"][
                "best_zero_oom_predictive"
            ]["io_saving_fraction"]
            > 0.40
        ),
        "lead2_io_value_increases_with_slack": (
            lead2["4"][
                "best_zero_oom_predictive"
            ]["io_saving_fraction"]
            < lead2["6"][
                "best_zero_oom_predictive"
            ]["io_saving_fraction"]
            < lead2["8"][
                "best_zero_oom_predictive"
            ]["io_saving_fraction"]
            < lead2["10"][
                "best_zero_oom_predictive"
            ]["io_saving_fraction"]
        ),
        "lead3_budget4_has_no_material_advantage": (
            lead3["4"]["phase"]
            == "PREDICTION_HAS_NO_MATERIAL_IO_ADVANTAGE"
        ),
        "feasible_region_has_zero_oom_candidate": all(
            cell["best_zero_oom_predictive"]
            is not None
            for lead, budgets
            in matrix.items()
            for budget, cell
            in budgets.items()
            if cell["phase"]
            != "DEADLINE_INFEASIBLE"
        ),
    }

    phase_counts: dict[str, int] = {}

    for budgets in matrix.values():
        for cell in budgets.values():
            phase = cell["phase"]
            phase_counts[phase] = (
                phase_counts.get(phase, 0)
                + 1
            )

    return {
        "schema": SCHEMA,
        "status": (
            "PASS"
            if all(checks.values())
            else "FAIL"
        ),
        "classification": (
            "SYNTHETIC_PREDICTIVE_RESIDENCY_PHASE_DIAGRAM"
        ),
        "leads": list(LEADS),
        "budgets": list(BUDGETS),
        "margins": list(MARGINS),
        "episodes": len(episodes),
        "matrix": matrix,
        "phase_counts": phase_counts,
        "checks": checks,
        "primary_findings": [
            "PREDICTION_VALUE_GROWS_WITH_HOT_BUDGET_SLACK",
            "LONGER_TRANSFER_LEAD_ERODES_PREDICTIVE_IO_ADVANTAGE",
            "A_DEADLINE_INFEASIBLE_REGION_EXISTS_WHERE_ALWAYS_PREEMPTIVE_IS_TOO_LATE",
            "POLICY_OPTIMIZATION_CANNOT_CROSS_A_PHYSICAL_TRANSFER_DEADLINE_FRONTIER",
            "THE_GOVERNOR_NEEDS_BUDGET_SLACK_TRANSFER_LEAD_AND_RECLAIMABILITY_ETA_IN_ONE_STATE",
        ],
        "claim_ceiling": (
            "SYNTHETIC_PREDICTIVE_RESIDENCY_PHASE_BOUNDARY_ONLY"
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
