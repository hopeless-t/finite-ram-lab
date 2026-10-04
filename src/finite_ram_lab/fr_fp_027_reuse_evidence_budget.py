from __future__ import annotations

import json
from typing import Any

from scipy.stats import beta

SCHEMA = "finite-ram-lab.fr-fp-027-reuse-evidence-budget/v0.1"

CONFIDENCE_LEVELS = (
    0.95,
    0.99,
)

REPRESENTATIVE_CEILINGS = {
    "FAST_LOOSE": (
        0.8444807779047618
    ),
    "MID_TIGHT": (
        0.30
    ),
    "SLOW_STRICT": (
        0.08333333333333334
    ),
    "REFERENCE_10PCT": (
        0.10
    ),
    "REFERENCE_25PCT": (
        0.25
    ),
    "REFERENCE_50PCT": (
        0.50
    ),
}

MAX_SUCCESSES = 2
MAX_N = 10_000


def clopper_pearson_upper(
    *,
    reused: int,
    observations: int,
    confidence: float,
) -> float:
    if observations <= 0:
        raise ValueError(
            "observations_must_be_positive"
        )

    if not (
        0
        <= reused
        <= observations
    ):
        raise ValueError(
            "invalid_reuse_count"
        )

    if not (
        0.0
        < confidence
        < 1.0
    ):
        raise ValueError(
            "invalid_confidence"
        )

    if reused == observations:
        return 1.0

    return float(
        beta.ppf(
            confidence,
            reused + 1,
            observations - reused,
        )
    )


def minimum_observations(
    *,
    reuse_ceiling: float,
    reused: int,
    confidence: float,
) -> dict[str, Any]:
    if not (
        0.0
        < reuse_ceiling
        <= 1.0
    ):
        raise ValueError(
            "invalid_reuse_ceiling"
        )

    for observations in range(
        max(
            1,
            reused + 1,
        ),
        MAX_N + 1,
    ):
        upper = (
            clopper_pearson_upper(
                reused=reused,
                observations=observations,
                confidence=confidence,
            )
        )

        if upper <= reuse_ceiling:
            return {
                "observations": (
                    observations
                ),
                "reused": reused,
                "non_reused": (
                    observations
                    - reused
                ),
                "upper_bound": upper,
                "reuse_ceiling": (
                    reuse_ceiling
                ),
                "confidence": (
                    confidence
                ),
            }

    raise RuntimeError(
        "observation_budget_not_found"
    )


def zero_reuse_closed_form(
    *,
    observations: int,
    confidence: float,
) -> float:
    alpha = 1.0 - confidence

    return (
        1.0
        - alpha
        ** (
            1.0
            / observations
        )
    )


def run_panel() -> dict[str, Any]:
    table = {}

    for label, ceiling in (
        REPRESENTATIVE_CEILINGS.items()
    ):
        table[label] = {}

        for confidence in (
            CONFIDENCE_LEVELS
        ):
            ckey = (
                f"{confidence:.2f}"
            )
            table[label][ckey] = {
                str(reused): (
                    minimum_observations(
                        reuse_ceiling=ceiling,
                        reused=reused,
                        confidence=confidence,
                    )
                )
                for reused in range(
                    MAX_SUCCESSES + 1
                )
            }

    zero_reuse_exact_matches = []

    for observations in (
        2,
        5,
        11,
        29,
        35,
        53,
        100,
    ):
        for confidence in (
            CONFIDENCE_LEVELS
        ):
            exact = (
                clopper_pearson_upper(
                    reused=0,
                    observations=observations,
                    confidence=confidence,
                )
            )
            closed = (
                zero_reuse_closed_form(
                    observations=observations,
                    confidence=confidence,
                )
            )
            zero_reuse_exact_matches.append(
                abs(
                    exact
                    - closed
                )
                < 1e-12
            )

    checks = {
        "zero_reuse_closed_form_matches_exact_beta_bound": (
            all(
                zero_reuse_exact_matches
            )
        ),
        "95pct_10pct_ceiling_needs_29_zero_reuse_observations": (
            table[
                "REFERENCE_10PCT"
            ][
                "0.95"
            ][
                "0"
            ][
                "observations"
            ]
            == 29
        ),
        "95pct_25pct_ceiling_needs_11_zero_reuse_observations": (
            table[
                "REFERENCE_25PCT"
            ][
                "0.95"
            ][
                "0"
            ][
                "observations"
            ]
            == 11
        ),
        "95pct_50pct_ceiling_needs_5_zero_reuse_observations": (
            table[
                "REFERENCE_50PCT"
            ][
                "0.95"
            ][
                "0"
            ][
                "observations"
            ]
            == 5
        ),
        "95pct_slow_strict_needs_35_zero_reuse_observations": (
            table[
                "SLOW_STRICT"
            ][
                "0.95"
            ][
                "0"
            ][
                "observations"
            ]
            == 35
        ),
        "99pct_requires_no_less_evidence_than_95pct": all(
            table[label][
                "0.99"
            ][str(reused)][
                "observations"
            ]
            >= table[label][
                "0.95"
            ][str(reused)][
                "observations"
            ]
            for label
            in REPRESENTATIVE_CEILINGS
            for reused in range(
                MAX_SUCCESSES + 1
            )
        ),
        "observed_reuse_requires_more_evidence_than_zero_reuse": all(
            table[label][
                confidence
            ]["1"][
                "observations"
            ]
            >= table[label][
                confidence
            ]["0"][
                "observations"
            ]
            and table[label][
                confidence
            ]["2"][
                "observations"
            ]
            >= table[label][
                confidence
            ]["1"][
                "observations"
            ]
            for label
            in REPRESENTATIVE_CEILINGS
            for confidence
            in (
                "0.95",
                "0.99",
            )
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
            "EXACT_BINOMIAL_REUSE_EVIDENCE_BUDGET"
        ),
        "assumptions": [
            "reuse observations are Bernoulli under a stable decision window",
            "the one-sided Clopper-Pearson upper bound is used",
            "a reused event is counted as a Bernoulli success",
            "the result is an evidence budget, not a workload-validity proof",
        ],
        "confidence_levels": list(
            CONFIDENCE_LEVELS
        ),
        "representative_reuse_ceilings": (
            REPRESENTATIVE_CEILINGS
        ),
        "table": table,
        "checks": checks,
        "law": {
            "zero_reuse_upper": (
                "p_U = 1 - (1-confidence)^(1/n)"
            ),
            "general_upper": (
                "p_U = BetaQuantile(confidence, reused+1, observations-reused)"
            ),
            "decision": (
                "CERTIFY_COLD_ONLY_IF_P_UPPER_LE_REUSE_CEILING"
            ),
        },
        "decision": (
            "CONVERT_REUSE_CEILING_INTO_A_DECISION_SPECIFIC_OBSERVATION_BUDGET"
        ),
        "governor_direction": {
            "input": (
                "reuse ceiling from FR-FP-026"
            ),
            "output": (
                "minimum observations needed for a conservative reuse upper bound"
            ),
            "stop_rule": (
                "stop observing once p_upper <= reuse_ceiling"
            ),
            "fallback": (
                "if evidence budget is not met, keep WARM or use another policy"
            ),
        },
        "claim_ceiling": (
            "EXACT_BINOMIAL_EVIDENCE_BUDGET_UNDER_STABLE_BERNOULLI_REUSE_ASSUMPTION_ONLY"
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
