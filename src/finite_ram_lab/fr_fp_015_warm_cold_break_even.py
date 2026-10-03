from __future__ import annotations

import json
from typing import Any

SCHEMA = "finite-ram-lab.fr-fp-015-warm-cold-break-even/v0.1"

WARM_READ_NS = 847_494.0
COLD_READ_NS = 3_102_932.5
RESTORE_PENALTY_NS = (
    COLD_READ_NS
    - WARM_READ_NS
)

WARM_RESIDENT_MIB = 8.0
COLD_RESIDENT_MIB = 0.0
MEMORY_SAVING_MIB = (
    WARM_RESIDENT_MIB
    - COLD_RESIDENT_MIB
)

REUSE_PROBABILITIES = (
    0.0,
    0.01,
    0.05,
    0.10,
    0.25,
    0.50,
    1.0,
)

SHADOW_PRICES_US_PER_MIB = (
    10.0,
    50.0,
    100.0,
    200.0,
    300.0,
)


def break_even_shadow_price_ns_per_mib(
    reuse_probability: float,
) -> float:
    if not (
        0.0
        <= reuse_probability
        <= 1.0
    ):
        raise ValueError(
            "reuse_probability_out_of_range"
        )

    return (
        reuse_probability
        * RESTORE_PENALTY_NS
        / MEMORY_SAVING_MIB
    )


def break_even_reuse_probability(
    shadow_price_ns_per_mib: float,
) -> float:
    if shadow_price_ns_per_mib < 0.0:
        raise ValueError(
            "negative_shadow_price"
        )

    return (
        shadow_price_ns_per_mib
        * MEMORY_SAVING_MIB
        / RESTORE_PENALTY_NS
    )


def choose_tier(
    *,
    reuse_probability: float,
    shadow_price_ns_per_mib: float,
) -> str:
    threshold = (
        break_even_shadow_price_ns_per_mib(
            reuse_probability
        )
    )

    if (
        shadow_price_ns_per_mib
        > threshold
    ):
        return "COLD"

    if (
        shadow_price_ns_per_mib
        < threshold
    ):
        return "WARM"

    return "INDIFFERENT"


def run_panel() -> dict[str, Any]:
    reuse_frontier = [
        {
            "reuse_probability": p,
            "break_even_shadow_price_ns_per_mib": (
                break_even_shadow_price_ns_per_mib(
                    p
                )
            ),
            "break_even_shadow_price_us_per_mib": (
                break_even_shadow_price_ns_per_mib(
                    p
                )
                / 1000.0
            ),
        }
        for p in REUSE_PROBABILITIES
    ]

    shadow_frontier = [
        {
            "shadow_price_us_per_mib": (
                value
            ),
            "break_even_reuse_probability": (
                break_even_reuse_probability(
                    value * 1000.0
                )
            ),
        }
        for value in SHADOW_PRICES_US_PER_MIB
    ]

    examples = {
        "low_reuse_moderate_memory_price": (
            choose_tier(
                reuse_probability=0.05,
                shadow_price_ns_per_mib=(
                    50_000.0
                ),
            )
        ),
        "high_reuse_moderate_memory_price": (
            choose_tier(
                reuse_probability=0.50,
                shadow_price_ns_per_mib=(
                    50_000.0
                ),
            )
        ),
        "high_memory_price_even_if_reused": (
            choose_tier(
                reuse_probability=1.0,
                shadow_price_ns_per_mib=(
                    300_000.0
                ),
            )
        ),
    }

    checks = {
        "restore_penalty_positive": (
            RESTORE_PENALTY_NS
            > 2_000_000.0
        ),
        "memory_saving_is_eight_mib": (
            MEMORY_SAVING_MIB
            == 8.0
        ),
        "frontier_is_linear_in_reuse_probability": all(
            abs(
                break_even_shadow_price_ns_per_mib(
                    p
                )
                - p
                * break_even_shadow_price_ns_per_mib(
                    1.0
                )
            )
            < 1e-9
            for p in REUSE_PROBABILITIES
        ),
        "zero_reuse_break_even_is_zero": (
            break_even_shadow_price_ns_per_mib(
                0.0
            )
            == 0.0
        ),
        "full_reuse_break_even_is_about_282us_per_mib": (
            abs(
                break_even_shadow_price_ns_per_mib(
                    1.0
                )
                / 1000.0
                - 281.9298125
            )
            < 1e-9
        ),
        "example_low_reuse_prefers_cold_under_declared_price": (
            examples[
                "low_reuse_moderate_memory_price"
            ]
            == "COLD"
        ),
        "example_high_reuse_prefers_warm_under_same_price": (
            examples[
                "high_reuse_moderate_memory_price"
            ]
            == "WARM"
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
            "ANALYTIC_WARM_COLD_BREAK_EVEN_FRONTIER_FROM_HOSTED_MEASUREMENTS"
        ),
        "evidence": {
            "source_pr": 133,
            "warm_read_ns": (
                WARM_READ_NS
            ),
            "cold_read_ns": (
                COLD_READ_NS
            ),
            "restore_penalty_ns": (
                RESTORE_PENALTY_NS
            ),
            "warm_resident_mib": (
                WARM_RESIDENT_MIB
            ),
            "cold_resident_mib": (
                COLD_RESIDENT_MIB
            ),
            "memory_saving_mib": (
                MEMORY_SAVING_MIB
            ),
        },
        "law": {
            "break_even_shadow_price": (
                "lambda_star(p) = p * (L_cold - L_warm) / (M_warm - M_cold)"
            ),
            "cold_condition": (
                "choose COLD when lambda > lambda_star(p)"
            ),
            "warm_condition": (
                "choose WARM when lambda < lambda_star(p)"
            ),
        },
        "reuse_frontier": (
            reuse_frontier
        ),
        "shadow_price_frontier": (
            shadow_frontier
        ),
        "examples": examples,
        "checks": checks,
        "decision": (
            "KEEP_MEMORY_SHADOW_PRICE_AND_REUSE_PROBABILITY_EXPLICIT_INSTEAD_OF_HIDING_THEM_IN_A_SINGLE_TIER_SCORE"
        ),
        "claim_ceiling": (
            "ANALYTIC_BREAK_EVEN_FRONTIER_FROM_SINGLE_HOSTED_RESTORE_PILOT_ONLY"
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
