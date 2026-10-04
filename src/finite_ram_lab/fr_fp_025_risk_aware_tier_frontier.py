from __future__ import annotations

import json
import statistics
from pathlib import Path
from typing import Any

SCHEMA = "finite-ram-lab.fr-fp-025-risk-aware-tier-frontier/v0.1"

DATA_PATH = (
    Path(__file__).resolve()
    .parents[2]
    / "data"
    / "FR-FP-021-few-shot-restore.json"
)

STATE_MIB = 8.0

BASELINES_MS = (
    3.0,
    5.0,
    10.0,
    25.0,
    100.0,
)

REUSE_PROBABILITIES = (
    0.10,
    0.25,
    0.50,
    0.75,
    1.00,
)

DEADLINES_MS = (
    10.0,
    25.0,
    50.0,
    100.0,
)

MISS_TOLERANCES = (
    0.01,
    0.05,
    0.10,
    0.25,
)


def _load() -> dict[str, Any]:
    return json.loads(
        DATA_PATH.read_text(
            encoding="utf-8"
        )
    )


def _build_empirical_priors(
    rows: list[dict[str, Any]],
) -> dict[str, list[float]]:
    residuals = []
    warm = []

    for row in rows:
        cold = [
            float(value)
            for value in row[
                "cold8_ms"
            ]
        ]
        warm_values = [
            float(value)
            for value in row[
                "warm8_ms"
            ]
        ]

        baseline = min(
            cold[:2]
        )

        residuals.extend(
            value / baseline
            for value in cold[2:]
        )
        warm.extend(
            warm_values
        )

    return {
        "residual": residuals,
        "warm_ms": warm,
    }


def _expected_positive_penalty_ms(
    *,
    baseline_ms: float,
    residuals: list[float],
    warm_ms: list[float],
) -> float:
    penalties = [
        max(
            0.0,
            baseline_ms
            * residual
            - warm,
        )
        for residual in residuals
        for warm in warm_ms
    ]

    return statistics.fmean(
        penalties
    )


def _deadline_risk(
    *,
    baseline_ms: float,
    residuals: list[float],
    deadline_ms: float,
) -> float:
    return (
        sum(
            baseline_ms
            * residual
            > deadline_ms
            for residual in residuals
        )
        / len(residuals)
    )


def _cell(
    *,
    baseline_ms: float,
    reuse_probability: float,
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

    expected_penalty = (
        reuse_probability
        * conditional_penalty
    )

    lambda_star_ms_per_mib = (
        expected_penalty
        / STATE_MIB
    )

    deadline = {}

    for value in DEADLINES_MS:
        conditional = _deadline_risk(
            baseline_ms=baseline_ms,
            residuals=residuals,
            deadline_ms=value,
        )
        unconditional = (
            reuse_probability
            * conditional
        )

        deadline[
            str(int(value))
        ] = {
            "conditional_on_reuse": (
                conditional
            ),
            "unconditional_per_state": (
                unconditional
            ),
            "eligible_tolerances": [
                tolerance
                for tolerance
                in MISS_TOLERANCES
                if unconditional
                <= tolerance
            ],
        }

    return {
        "baseline_ms": baseline_ms,
        "reuse_probability": (
            reuse_probability
        ),
        "conditional_expected_cold_minus_warm_penalty_ms": (
            conditional_penalty
        ),
        "expected_penalty_ms_per_state": (
            expected_penalty
        ),
        "lambda_star_ms_per_mib": (
            lambda_star_ms_per_mib
        ),
        "deadline_risk": deadline,
    }


def run_panel() -> dict[str, Any]:
    data = _load()
    rows = data["rows"]
    priors = _build_empirical_priors(
        rows
    )
    residuals = priors[
        "residual"
    ]
    warm_ms = priors[
        "warm_ms"
    ]

    cells = {}

    for baseline in BASELINES_MS:
        for reuse in (
            REUSE_PROBABILITIES
        ):
            key = (
                f"b{baseline:g}"
                f"_p{reuse:.2f}"
            )
            cells[key] = _cell(
                baseline_ms=baseline,
                reuse_probability=reuse,
                residuals=residuals,
                warm_ms=warm_ms,
            )

    lambda_monotonic_reuse = all(
        cells[
            f"b{baseline:g}_p{left:.2f}"
        ][
            "lambda_star_ms_per_mib"
        ]
        <= cells[
            f"b{baseline:g}_p{right:.2f}"
        ][
            "lambda_star_ms_per_mib"
        ]
        for baseline in BASELINES_MS
        for left, right
        in zip(
            REUSE_PROBABILITIES[:-1],
            REUSE_PROBABILITIES[1:],
        )
    )

    lambda_monotonic_baseline = all(
        cells[
            f"b{left:g}_p{reuse:.2f}"
        ][
            "lambda_star_ms_per_mib"
        ]
        <= cells[
            f"b{right:g}_p{reuse:.2f}"
        ][
            "lambda_star_ms_per_mib"
        ]
        for reuse in REUSE_PROBABILITIES
        for left, right
        in zip(
            BASELINES_MS[:-1],
            BASELINES_MS[1:],
        )
    )

    deadline_monotonic_baseline = all(
        cells[
            f"b{left:g}_p{reuse:.2f}"
        ][
            "deadline_risk"
        ][
            str(int(deadline))
        ][
            "unconditional_per_state"
        ]
        <= cells[
            f"b{right:g}_p{reuse:.2f}"
        ][
            "deadline_risk"
        ][
            str(int(deadline))
        ][
            "unconditional_per_state"
        ]
        for reuse in REUSE_PROBABILITIES
        for deadline in DEADLINES_MS
        for left, right
        in zip(
            BASELINES_MS[:-1],
            BASELINES_MS[1:],
        )
    )

    deadline_monotonic_deadline = all(
        cells[
            f"b{baseline:g}_p{reuse:.2f}"
        ][
            "deadline_risk"
        ][
            str(int(left))
        ][
            "unconditional_per_state"
        ]
        >= cells[
            f"b{baseline:g}_p{reuse:.2f}"
        ][
            "deadline_risk"
        ][
            str(int(right))
        ][
            "unconditional_per_state"
        ]
        for baseline in BASELINES_MS
        for reuse in REUSE_PROBABILITIES
        for left, right
        in zip(
            DEADLINES_MS[:-1],
            DEADLINES_MS[1:],
        )
    )

    representative = {
        "fast_low_reuse": cells[
            "b3_p0.10"
        ],
        "mid_reuse": cells[
            "b10_p0.50"
        ],
        "slow_high_reuse": cells[
            "b100_p1.00"
        ],
    }

    checks = {
        "fifteen_source_runs": (
            len(rows) == 15
        ),
        "sixty_residual_samples": (
            len(residuals) == 60
        ),
        "ninety_warm_samples": (
            len(warm_ms) == 90
        ),
        "lambda_star_monotonic_in_reuse": (
            lambda_monotonic_reuse
        ),
        "lambda_star_monotonic_in_baseline": (
            lambda_monotonic_baseline
        ),
        "deadline_risk_monotonic_in_baseline": (
            deadline_monotonic_baseline
        ),
        "deadline_risk_monotonic_in_deadline": (
            deadline_monotonic_deadline
        ),
        "slow_high_reuse_is_not_10ms_cold_eligible_at_25pct_tolerance": (
            0.25
            not in representative[
                "slow_high_reuse"
            ][
                "deadline_risk"
            ][
                "10"
            ][
                "eligible_tolerances"
            ]
        ),
        "fast_low_reuse_has_lower_shadow_price_than_slow_high_reuse": (
            representative[
                "fast_low_reuse"
            ][
                "lambda_star_ms_per_mib"
            ]
            < representative[
                "slow_high_reuse"
            ][
                "lambda_star_ms_per_mib"
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
            "EMPIRICAL_RISK_AWARE_WARM_COLD_TIER_FRONTIER"
        ),
        "source": {
            "new_physical_runs": 0,
            "runs": len(rows),
            "state_mib": STATE_MIB,
            "residual_samples": (
                len(residuals)
            ),
            "warm_samples": (
                len(warm_ms)
            ),
        },
        "law": {
            "expected_break_even_shadow_price": (
                "lambda_star = p * E[(b*R - W)_+] / 8MiB"
            ),
            "deadline_risk": (
                "q_D = p * P(b*R > D)"
            ),
            "cold_eligibility": (
                "external lambda >= lambda_star AND q_D <= external miss tolerance"
            ),
        },
        "grid": {
            "baselines_ms": list(
                BASELINES_MS
            ),
            "reuse_probabilities": list(
                REUSE_PROBABILITIES
            ),
            "deadlines_ms": list(
                DEADLINES_MS
            ),
            "miss_tolerances": list(
                MISS_TOLERANCES
            ),
            "cells": cells,
        },
        "representative": (
            representative
        ),
        "checks": checks,
        "decision": (
            "ROUTE_WARM_VS_COLD_WITH_SEPARATE_MEMORY_SHADOW_PRICE_AND_DEADLINE_RISK_CONSTRAINTS"
        ),
        "governor_direction": {
            "resident_state": [
                "calibrated current-run baseline b",
                "residual multiplier prior R",
                "warm restore prior W",
            ],
            "external_policy_inputs": [
                "reuse probability p",
                "memory shadow price lambda",
                "deadline D",
                "miss tolerance epsilon",
            ],
            "forbidden_collapse": (
                "DO_NOT_REPLACE_EXPECTED_COST_AND_DEADLINE_RISK_WITH_ONE_HIDDEN_UNIVERSAL_UTILITY"
            ),
        },
        "claim_ceiling": (
            "EMPIRICAL_FRONTIER_FROM_REUSED_8MIB_HOSTED_RESTORE_EVIDENCE_ONLY"
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
