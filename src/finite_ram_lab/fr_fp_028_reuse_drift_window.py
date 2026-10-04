from __future__ import annotations

import json
import math
import random
import statistics
from functools import lru_cache
from typing import Any

from finite_ram_lab.fr_fp_027_reuse_evidence_budget import (
    clopper_pearson_upper,
)

SCHEMA = "finite-ram-lab.fr-fp-028-reuse-drift-window/v0.1"

CONFIDENCE = 0.95
REUSE_CEILING = 0.10
PRE_REUSE_P = 0.02
PRE_OBSERVATIONS = 60
POST_OBSERVATIONS = 60
ROLLING_WINDOW = 35
REPLICATES = 5_000
POST_REUSE_PROBABILITIES = (
    0.15,
    0.25,
    0.50,
)
SEED = 20261004


@lru_cache(maxsize=None)
def _upper(
    reused: int,
    observations: int,
) -> float:
    return clopper_pearson_upper(
        reused=reused,
        observations=observations,
        confidence=CONFIDENCE,
    )


def _series(
    observations: list[bool],
    *,
    window: int | None,
) -> list[float]:
    prefix = [0]

    for value in observations:
        prefix.append(
            prefix[-1]
            + int(value)
        )

    out = []

    for end in range(
        1,
        len(observations) + 1,
    ):
        start = (
            0
            if window is None
            else max(
                0,
                end - window,
            )
        )
        n = end - start
        reused = (
            prefix[end]
            - prefix[start]
        )
        out.append(
            _upper(
                reused,
                n,
            )
        )

    return out


def _delay(
    upper: list[float],
) -> int | None | float:
    anchor = (
        PRE_OBSERVATIONS
        - 1
    )

    if upper[anchor] > REUSE_CEILING:
        return None

    for index in range(
        PRE_OBSERVATIONS,
        len(upper),
    ):
        if upper[index] > REUSE_CEILING:
            return (
                index
                - PRE_OBSERVATIONS
                + 1
            )

    return math.inf


def _drift_trial(
    *,
    seed: int,
    post_reuse_p: float,
) -> dict[str, Any]:
    rng = random.Random(seed)

    observations = [
        rng.random()
        < PRE_REUSE_P
        for _ in range(
            PRE_OBSERVATIONS
        )
    ] + [
        rng.random()
        < post_reuse_p
        for _ in range(
            POST_OBSERVATIONS
        )
    ]

    cumulative = _series(
        observations,
        window=None,
    )
    rolling = _series(
        observations,
        window=ROLLING_WINDOW,
    )

    return {
        "cumulative_delay": (
            _delay(cumulative)
        ),
        "rolling_delay": (
            _delay(rolling)
        ),
    }


def _stable_trial(
    *,
    seed: int,
) -> dict[str, Any]:
    rng = random.Random(seed)
    observations = [
        rng.random()
        < PRE_REUSE_P
        for _ in range(
            PRE_OBSERVATIONS
            + POST_OBSERVATIONS
        )
    ]

    result = {}

    for name, window in (
        (
            "cumulative",
            None,
        ),
        (
            "rolling",
            ROLLING_WINDOW,
        ),
    ):
        upper = _series(
            observations,
            window=window,
        )
        anchor = (
            PRE_OBSERVATIONS
            - 1
        )
        certified = (
            upper[anchor]
            <= REUSE_CEILING
        )
        later_revoked = (
            certified
            and any(
                value
                > REUSE_CEILING
                for value
                in upper[
                    PRE_OBSERVATIONS:
                ]
            )
        )
        result[name] = {
            "certified": (
                certified
            ),
            "later_revoked": (
                later_revoked
            ),
        }

    return result


def _finite(
    values: list[
        int | float | None
    ],
) -> list[float]:
    return [
        float(value)
        for value in values
        if value is not None
        and math.isfinite(
            value
        )
    ]


def _summarize_drift(
    post_reuse_p: float,
) -> dict[str, Any]:
    rows = [
        _drift_trial(
            seed=(
                SEED
                + int(
                    post_reuse_p
                    * 10_000
                )
                * REPLICATES
                + index
            ),
            post_reuse_p=(
                post_reuse_p
            ),
        )
        for index in range(
            REPLICATES
        )
    ]

    jointly_qualified = [
        row
        for row in rows
        if row[
            "cumulative_delay"
        ]
        is not None
        and row[
            "rolling_delay"
        ]
        is not None
    ]

    cumulative = _finite(
        [
            row[
                "cumulative_delay"
            ]
            for row
            in jointly_qualified
        ]
    )
    rolling = _finite(
        [
            row[
                "rolling_delay"
            ]
            for row
            in jointly_qualified
        ]
    )

    return {
        "post_reuse_probability": (
            post_reuse_p
        ),
        "jointly_qualified": (
            len(
                jointly_qualified
            )
        ),
        "cumulative": {
            "median_invalidation_delay": (
                statistics.median(
                    cumulative
                )
            ),
            "mean_invalidation_delay": (
                statistics.fmean(
                    cumulative
                )
            ),
            "not_invalidated_within_horizon_rate": (
                sum(
                    row[
                        "cumulative_delay"
                    ]
                    is not None
                    and not math.isfinite(
                        row[
                            "cumulative_delay"
                        ]
                    )
                    for row
                    in jointly_qualified
                )
                / len(
                    jointly_qualified
                )
            ),
        },
        "rolling": {
            "median_invalidation_delay": (
                statistics.median(
                    rolling
                )
            ),
            "mean_invalidation_delay": (
                statistics.fmean(
                    rolling
                )
            ),
            "not_invalidated_within_horizon_rate": (
                sum(
                    row[
                        "rolling_delay"
                    ]
                    is not None
                    and not math.isfinite(
                        row[
                            "rolling_delay"
                        ]
                    )
                    for row
                    in jointly_qualified
                )
                / len(
                    jointly_qualified
                )
            ),
        },
    }


def _summarize_stable() -> dict[str, Any]:
    rows = [
        _stable_trial(
            seed=(
                SEED
                + 9_000_000
                + index
            )
        )
        for index in range(
            REPLICATES
        )
    ]

    out = {}

    for method in (
        "cumulative",
        "rolling",
    ):
        certified = sum(
            row[method][
                "certified"
            ]
            for row in rows
        )
        revoked = sum(
            row[method][
                "later_revoked"
            ]
            for row in rows
        )

        out[method] = {
            "certified_at_anchor_rate": (
                certified
                / REPLICATES
            ),
            "conditional_false_revocation_rate": (
                0.0
                if certified == 0
                else revoked
                / certified
            ),
        }

    return out


def run_panel() -> dict[str, Any]:
    drift = {
        str(
            post_reuse_p
        ): _summarize_drift(
            post_reuse_p
        )
        for post_reuse_p
        in POST_REUSE_PROBABILITIES
    }
    stable = _summarize_stable()

    checks = {
        "replicate_count_frozen": (
            REPLICATES
            == 5_000
        ),
        "rolling_window_is_large_enough_to_certify_zero_reuse_10pct": (
            _upper(
                0,
                ROLLING_WINDOW,
            )
            <= REUSE_CEILING
        ),
        "rolling_invalidates_faster_for_all_injected_drifts": all(
            row[
                "rolling"
            ][
                "median_invalidation_delay"
            ]
            < row[
                "cumulative"
            ][
                "median_invalidation_delay"
            ]
            for row in (
                drift.values()
            )
        ),
        "rolling_has_high_stable_false_revocation": (
            stable[
                "rolling"
            ][
                "conditional_false_revocation_rate"
            ]
            > 0.50
        ),
        "cumulative_stable_false_revocation_is_low": (
            stable[
                "cumulative"
            ][
                "conditional_false_revocation_rate"
            ]
            < 0.10
        ),
        "weak_drift_exposes_cumulative_staleness": (
            drift[
                "0.15"
            ][
                "cumulative"
            ][
                "median_invalidation_delay"
            ]
            >= 2.0
            * drift[
                "0.15"
            ][
                "rolling"
            ][
                "median_invalidation_delay"
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
            "SYNTHETIC_REUSE_EVIDENCE_STALENESS_AND_ROLLING_WINDOW_NEGATIVE_RESULT"
        ),
        "fixture": {
            "confidence": CONFIDENCE,
            "reuse_ceiling": (
                REUSE_CEILING
            ),
            "pre_reuse_probability": (
                PRE_REUSE_P
            ),
            "pre_observations": (
                PRE_OBSERVATIONS
            ),
            "post_observations": (
                POST_OBSERVATIONS
            ),
            "rolling_window": (
                ROLLING_WINDOW
            ),
            "replicates": (
                REPLICATES
            ),
            "post_reuse_probabilities": list(
                POST_REUSE_PROBABILITIES
            ),
        },
        "stable": stable,
        "drift": drift,
        "checks": checks,
        "decision": (
            "REJECT_NAIVE_ROLLING_WINDOW_UCB_AS_THE_DEFAULT_DRIFT_REPAIR"
        ),
        "theory_update": [
            "cumulative evidence can remain certified too long after reuse probability rises",
            "a rolling exact UCB invalidates faster",
            "but the same rolling rule revokes qualification too often under a stable low-reuse process",
            "old evidence needs explicit validity/lifecycle control rather than blind cumulative retention or blind fixed-window forgetting",
        ],
        "next": (
            "TEST_AN_EXPLICIT_CHANGE_DETECTOR_OR_HYSTERETIC_EVIDENCE_RESET_BEFORE_DISCARDING_QUALIFIED_HISTORY"
        ),
        "claim_ceiling": (
            "SYNTHETIC_BERNOULLI_DRIFT_INJECTION_FOR_ONE_10PCT_REUSE_CEILING_ONLY"
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
