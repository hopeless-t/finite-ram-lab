from __future__ import annotations

import json
import math
from typing import Any

from finite_ram_lab.fr_fp_025_risk_aware_tier_frontier import (
    BASELINES_MS,
    DEADLINES_MS,
    MISS_TOLERANCES,
    REUSE_PROBABILITIES,
    STATE_MIB,
    _build_empirical_priors,
    _deadline_risk,
    _expected_positive_penalty_ms,
    _load,
)

SCHEMA = "finite-ram-lab.fr-fp-026-reuse-ceiling/v0.1"

MEMORY_SHADOW_PRICES = (
    0.05,
    0.10,
    0.25,
    0.50,
    1.00,
    2.00,
    5.00,
    10.00,
    25.00,
)

REUSE_GRID = tuple(
    value / 20.0
    for value in range(
        1,
        21,
    )
)


def _safe_div(
    numerator: float,
    denominator: float,
) -> float:
    if denominator <= 0.0:
        return math.inf

    return numerator / denominator


def reuse_ceiling(
    *,
    baseline_ms: float,
    memory_shadow_price_ms_per_mib: float,
    deadline_ms: float,
    miss_tolerance: float,
    residuals: list[float],
    warm_ms: list[float],
) -> dict[str, Any]:
    conditional_penalty = (
        _expected_positive_penalty_ms(
            baseline_ms=baseline_ms,
            residuals=residuals,
            warm_ms=warm_ms,
        )
    )
    conditional_deadline_risk = (
        _deadline_risk(
            baseline_ms=baseline_ms,
            residuals=residuals,
            deadline_ms=deadline_ms,
        )
    )

    p_cost = min(
        1.0,
        _safe_div(
            memory_shadow_price_ms_per_mib
            * STATE_MIB,
            conditional_penalty,
        ),
    )

    p_deadline = min(
        1.0,
        _safe_div(
            miss_tolerance,
            conditional_deadline_risk,
        ),
    )

    ceiling = min(
        1.0,
        p_cost,
        p_deadline,
    )

    binding = []

    if abs(
        ceiling - p_cost
    ) < 1e-12:
        binding.append(
            "EXPECTED_COST"
        )

    if abs(
        ceiling - p_deadline
    ) < 1e-12:
        binding.append(
            "DEADLINE_RISK"
        )

    if ceiling == 1.0:
        binding.append(
            "NO_REUSE_RESTRICTION"
        )

    return {
        "baseline_ms": baseline_ms,
        "memory_shadow_price_ms_per_mib": (
            memory_shadow_price_ms_per_mib
        ),
        "deadline_ms": deadline_ms,
        "miss_tolerance": miss_tolerance,
        "conditional_expected_penalty_ms": (
            conditional_penalty
        ),
        "conditional_deadline_risk": (
            conditional_deadline_risk
        ),
        "cost_reuse_ceiling": p_cost,
        "deadline_reuse_ceiling": (
            p_deadline
        ),
        "reuse_probability_ceiling": (
            ceiling
        ),
        "binding_constraints": (
            binding
        ),
    }


def direct_eligible(
    *,
    reuse_probability: float,
    baseline_ms: float,
    memory_shadow_price_ms_per_mib: float,
    deadline_ms: float,
    miss_tolerance: float,
    residuals: list[float],
    warm_ms: list[float],
) -> bool:
    conditional_penalty = (
        _expected_positive_penalty_ms(
            baseline_ms=baseline_ms,
            residuals=residuals,
            warm_ms=warm_ms,
        )
    )
    conditional_deadline_risk = (
        _deadline_risk(
            baseline_ms=baseline_ms,
            residuals=residuals,
            deadline_ms=deadline_ms,
        )
    )

    lambda_star = (
        reuse_probability
        * conditional_penalty
        / STATE_MIB
    )
    q_deadline = (
        reuse_probability
        * conditional_deadline_risk
    )

    return (
        memory_shadow_price_ms_per_mib
        >= lambda_star
        and q_deadline
        <= miss_tolerance
    )


def run_panel() -> dict[str, Any]:
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

    comparisons = []
    mismatches = []

    for baseline in BASELINES_MS:
        for shadow_price in (
            MEMORY_SHADOW_PRICES
        ):
            for deadline in (
                DEADLINES_MS
            ):
                for tolerance in (
                    MISS_TOLERANCES
                ):
                    ceiling = reuse_ceiling(
                        baseline_ms=baseline,
                        memory_shadow_price_ms_per_mib=(
                            shadow_price
                        ),
                        deadline_ms=deadline,
                        miss_tolerance=tolerance,
                        residuals=residuals,
                        warm_ms=warm_ms,
                    )

                    for reuse in (
                        REUSE_GRID
                    ):
                        direct = direct_eligible(
                            reuse_probability=reuse,
                            baseline_ms=baseline,
                            memory_shadow_price_ms_per_mib=(
                                shadow_price
                            ),
                            deadline_ms=deadline,
                            miss_tolerance=tolerance,
                            residuals=residuals,
                            warm_ms=warm_ms,
                        )
                        reduced = (
                            reuse
                            <= ceiling[
                                "reuse_probability_ceiling"
                            ]
                            + 1e-12
                        )

                        row = {
                            "baseline_ms": (
                                baseline
                            ),
                            "memory_shadow_price_ms_per_mib": (
                                shadow_price
                            ),
                            "deadline_ms": (
                                deadline
                            ),
                            "miss_tolerance": (
                                tolerance
                            ),
                            "reuse_probability": (
                                reuse
                            ),
                            "direct_eligible": (
                                direct
                            ),
                            "ceiling_eligible": (
                                reduced
                            ),
                        }
                        comparisons.append(
                            row
                        )

                        if direct != reduced:
                            mismatches.append(
                                row
                            )

    representative = {
        "tight_deadline_mid_run": (
            reuse_ceiling(
                baseline_ms=10.0,
                memory_shadow_price_ms_per_mib=1.0,
                deadline_ms=25.0,
                miss_tolerance=0.05,
                residuals=residuals,
                warm_ms=warm_ms,
            )
        ),
        "loose_deadline_fast_run": (
            reuse_ceiling(
                baseline_ms=3.0,
                memory_shadow_price_ms_per_mib=0.5,
                deadline_ms=50.0,
                miss_tolerance=0.10,
                residuals=residuals,
                warm_ms=warm_ms,
            )
        ),
        "slow_run_strict_deadline": (
            reuse_ceiling(
                baseline_ms=100.0,
                memory_shadow_price_ms_per_mib=10.0,
                deadline_ms=100.0,
                miss_tolerance=0.05,
                residuals=residuals,
                warm_ms=warm_ms,
            )
        ),
    }

    checks = {
        "source_reused_without_new_physical_runs": (
            len(
                data["rows"]
            )
            == 15
        ),
        "comparison_grid_is_large": (
            len(comparisons)
            >= 10_000
        ),
        "analytic_ceiling_matches_direct_policy_everywhere": (
            not mismatches
        ),
        "reuse_ceiling_is_unit_interval": all(
            0.0
            <= row[
                "reuse_probability_ceiling"
            ]
            <= 1.0
            for row in (
                representative.values()
            )
        ),
        "strict_slow_case_is_restricted": (
            representative[
                "slow_run_strict_deadline"
            ][
                "reuse_probability_ceiling"
            ]
            < 0.10
        ),
        "fast_loose_case_is_less_restricted": (
            representative[
                "loose_deadline_fast_run"
            ][
                "reuse_probability_ceiling"
            ]
            > representative[
                "slow_run_strict_deadline"
            ][
                "reuse_probability_ceiling"
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
            "ANALYTIC_REUSE_PROBABILITY_CEILING_FOR_RISK_AWARE_TIERING"
        ),
        "source": {
            "new_physical_runs": 0,
            "reused_runs": len(
                data["rows"]
            ),
            "residual_samples": len(
                residuals
            ),
            "warm_samples": len(
                warm_ms
            ),
        },
        "law": {
            "cost_bound": (
                "p <= 8MiB*lambda/E[(bR-W)+]"
            ),
            "deadline_bound": (
                "p <= epsilon/P(bR>D)"
            ),
            "combined": (
                "p <= min(1, cost_bound, deadline_bound)"
            ),
        },
        "grid": {
            "baselines_ms": list(
                BASELINES_MS
            ),
            "memory_shadow_prices_ms_per_mib": list(
                MEMORY_SHADOW_PRICES
            ),
            "deadlines_ms": list(
                DEADLINES_MS
            ),
            "miss_tolerances": list(
                MISS_TOLERANCES
            ),
            "reuse_grid": list(
                REUSE_GRID
            ),
            "comparisons": len(
                comparisons
            ),
            "mismatches": len(
                mismatches
            ),
        },
        "representative": (
            representative
        ),
        "checks": checks,
        "decision": (
            "REPLACE_EXACT_REUSE_POINT_ESTIMATION_WITH_A_SAFE_REUSE_UPPER_BOUND_WHEN_ROUTING_WARM_VS_COLD"
        ),
        "governor_direction": {
            "needed_workload_signal": (
                "UPPER_CONFIDENCE_BOUND_ON_REUSE_PROBABILITY"
            ),
            "not_required": (
                "EXACT_REUSE_PROBABILITY_POINT_ESTIMATE"
            ),
            "cold_rule": (
                "COLD_IF_REUSE_UPPER_BOUND_LE_REUSE_CEILING"
            ),
        },
        "claim_ceiling": (
            "ANALYTIC_REDUCTION_OF_FR_FP_025_EMPIRICAL_8MIB_FRONTIER_ONLY"
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
