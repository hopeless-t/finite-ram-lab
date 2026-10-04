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

SCHEMA = "finite-ram-lab.fr-fp-029-reuse-drift-alarm-frontier/v0.1"

CONFIDENCE = 0.95
REUSE_CEILING = 0.10
PRE_REUSE_P = 0.02
PRE_OBSERVATIONS = 60
POST_OBSERVATIONS = 60
ROLLING_WINDOW = 35
THRESHOLDS = (
    3,
    4,
    5,
    6,
    7,
    8,
)
POST_REUSE_PROBABILITIES = (
    0.15,
    0.25,
    0.50,
)
REPLICATES = 10_000
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


def _qualified(
    pre: list[bool],
) -> bool:
    return (
        _upper(
            sum(pre),
            len(pre),
        )
        <= REUSE_CEILING
    )


def _first_cumulative_revoke(
    pre: list[bool],
    post: list[bool],
) -> int | None:
    reused = sum(pre)
    n = len(pre)

    for delay, value in enumerate(
        post,
        start=1,
    ):
        n += 1
        reused += int(value)

        if (
            _upper(
                reused,
                n,
            )
            > REUSE_CEILING
        ):
            return delay

    return None


def _first_recency_alarms(
    pre: list[bool],
    post: list[bool],
) -> dict[int, int | None]:
    combined = (
        pre
        + post
    )
    prefix = [0]

    for value in combined:
        prefix.append(
            prefix[-1]
            + int(value)
        )

    alarms = {
        threshold: None
        for threshold
        in THRESHOLDS
    }

    for absolute_index in range(
        PRE_OBSERVATIONS,
        PRE_OBSERVATIONS
        + POST_OBSERVATIONS,
    ):
        end = (
            absolute_index
            + 1
        )
        start = max(
            0,
            end
            - ROLLING_WINDOW,
        )
        recent_reused = (
            prefix[end]
            - prefix[start]
        )
        delay = (
            absolute_index
            - PRE_OBSERVATIONS
            + 1
        )

        for threshold in (
            THRESHOLDS
        ):
            if (
                alarms[threshold]
                is None
                and recent_reused
                >= threshold
            ):
                alarms[
                    threshold
                ] = delay

    return alarms


def _scenario(
    *,
    post_reuse_p: float,
    seed_offset: int,
) -> dict[str, Any]:
    certified = 0
    cumulative_delays = []
    alarm_delays = {
        threshold: []
        for threshold
        in THRESHOLDS
    }

    for index in range(
        REPLICATES
    ):
        rng = random.Random(
            SEED
            + seed_offset
            + index
        )
        pre = [
            rng.random()
            < PRE_REUSE_P
            for _ in range(
                PRE_OBSERVATIONS
            )
        ]

        if not _qualified(
            pre
        ):
            continue

        certified += 1

        post = [
            rng.random()
            < post_reuse_p
            for _ in range(
                POST_OBSERVATIONS
            )
        ]

        cumulative_delays.append(
            _first_cumulative_revoke(
                pre,
                post,
            )
        )
        alarms = (
            _first_recency_alarms(
                pre,
                post,
            )
        )

        for threshold in (
            THRESHOLDS
        ):
            alarm_delays[
                threshold
            ].append(
                alarms[
                    threshold
                ]
            )

    def summarize(
        delays: list[
            int | None
        ],
    ) -> dict[str, Any]:
        detected = [
            delay
            for delay in delays
            if delay is not None
        ]

        return {
            "detection_rate": (
                len(detected)
                / len(delays)
            ),
            "median_delay": (
                None
                if not detected
                else statistics.median(
                    detected
                )
            ),
            "mean_delay": (
                None
                if not detected
                else statistics.fmean(
                    detected
                )
            ),
        }

    return {
        "post_reuse_probability": (
            post_reuse_p
        ),
        "certified": certified,
        "cumulative": summarize(
            cumulative_delays
        ),
        "alarms": {
            str(threshold): (
                summarize(
                    alarm_delays[
                        threshold
                    ]
                )
            )
            for threshold
            in THRESHOLDS
        },
    }


def _is_dominated(
    *,
    threshold: int,
    stable: dict[str, Any],
    weak: dict[str, Any],
) -> bool:
    own_false = stable[
        "alarms"
    ][
        str(threshold)
    ][
        "detection_rate"
    ]
    own_detect = weak[
        "alarms"
    ][
        str(threshold)
    ][
        "detection_rate"
    ]
    own_delay = weak[
        "alarms"
    ][
        str(threshold)
    ][
        "median_delay"
    ]

    for other in THRESHOLDS:
        if other == threshold:
            continue

        other_false = stable[
            "alarms"
        ][
            str(other)
        ][
            "detection_rate"
        ]
        other_detect = weak[
            "alarms"
        ][
            str(other)
        ][
            "detection_rate"
        ]
        other_delay = weak[
            "alarms"
        ][
            str(other)
        ][
            "median_delay"
        ]

        no_worse = (
            other_false
            <= own_false
            and other_detect
            >= own_detect
            and other_delay
            <= own_delay
        )
        strictly_better = (
            other_false
            < own_false
            or other_detect
            > own_detect
            or other_delay
            < own_delay
        )

        if (
            no_worse
            and strictly_better
        ):
            return True

    return False


def run_panel() -> dict[str, Any]:
    stable = _scenario(
        post_reuse_p=(
            PRE_REUSE_P
        ),
        seed_offset=(
            1_000_000
        ),
    )

    drift = {
        str(value): _scenario(
            post_reuse_p=value,
            seed_offset=(
                int(
                    value
                    * 1_000
                )
                * 20_000
            ),
        )
        for value
        in POST_REUSE_PROBABILITIES
    }

    weak = drift[
        "0.15"
    ]

    pareto = [
        threshold
        for threshold
        in THRESHOLDS
        if not _is_dominated(
            threshold=threshold,
            stable=stable,
            weak=weak,
        )
    ]

    stable_rates = [
        stable[
            "alarms"
        ][
            str(threshold)
        ][
            "detection_rate"
        ]
        for threshold
        in THRESHOLDS
    ]
    weak_rates = [
        weak[
            "alarms"
        ][
            str(threshold)
        ][
            "detection_rate"
        ]
        for threshold
        in THRESHOLDS
    ]
    weak_delays = [
        weak[
            "alarms"
        ][
            str(threshold)
        ][
            "median_delay"
        ]
        for threshold
        in THRESHOLDS
    ]

    cumulative_stable = (
        stable[
            "cumulative"
        ][
            "detection_rate"
        ]
    )
    cumulative_weak = (
        weak[
            "cumulative"
        ]
    )
    k4_stable = (
        stable[
            "alarms"
        ][
            "4"
        ][
            "detection_rate"
        ]
    )
    k4_weak = (
        weak[
            "alarms"
        ][
            "4"
        ]
    )
    k5_stable = (
        stable[
            "alarms"
        ][
            "5"
        ][
            "detection_rate"
        ]
    )

    checks = {
        "replicate_count_frozen": (
            REPLICATES
            == 10_000
        ),
        "stable_false_revocation_decreases_with_threshold": all(
            left
            >= right
            for left, right
            in zip(
                stable_rates[:-1],
                stable_rates[1:],
            )
        ),
        "weak_drift_detection_decreases_with_threshold": all(
            left
            >= right
            for left, right
            in zip(
                weak_rates[:-1],
                weak_rates[1:],
            )
        ),
        "weak_drift_delay_increases_with_threshold": all(
            left
            <= right
            for left, right
            in zip(
                weak_delays[:-1],
                weak_delays[1:],
            )
        ),
        "k4_reduces_false_revocation_vs_cumulative": (
            k4_stable
            < cumulative_stable
        ),
        "k4_improves_weak_drift_detection_coverage_vs_cumulative": (
            k4_weak[
                "detection_rate"
            ]
            > cumulative_weak[
                "detection_rate"
            ]
        ),
        "k4_pays_with_slower_weak_drift_median_delay": (
            k4_weak[
                "median_delay"
            ]
            > cumulative_weak[
                "median_delay"
            ]
        ),
        "k5_has_sub_one_percent_stable_false_revocation": (
            k5_stable
            < 0.01
        ),
        "multiple_thresholds_remain_pareto_candidates": (
            len(pareto)
            >= 3
        ),
        "strong_drift_is_detected_by_all_alarm_thresholds": all(
            drift[
                "0.5"
            ][
                "alarms"
            ][
                str(threshold)
            ][
                "detection_rate"
            ]
            == 1.0
            for threshold
            in THRESHOLDS
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
            "SYNTHETIC_REUSE_DRIFT_ALARM_PARETO_FRONTIER"
        ),
        "fixture": {
            "confidence": (
                CONFIDENCE
            ),
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
            "thresholds": list(
                THRESHOLDS
            ),
            "post_reuse_probabilities": list(
                POST_REUSE_PROBABILITIES
            ),
            "replicates": (
                REPLICATES
            ),
        },
        "stable": stable,
        "drift": drift,
        "pareto_thresholds": (
            pareto
        ),
        "checks": checks,
        "decision": (
            "EXPOSE_DRIFT_ALARM_AS_A_FALSE_REVOCATION_DETECTION_COVERAGE_DELAY_FRONTIER"
        ),
        "governor_direction": {
            "do_not": (
                "HARD_CODE_ONE_RECENCY_ALARM_THRESHOLD_AS_UNIVERSAL"
            ),
            "external_policy_axes": [
                "stable false-revocation tolerance",
                "drift detection coverage requirement",
                "drift detection delay budget",
            ],
            "reference": (
                "retain cumulative exact UCB as a baseline comparator"
            ),
        },
        "claim_ceiling": (
            "SYNTHETIC_DRIFT_ALARM_FRONTIER_FOR_ONE_REUSE_CEILING_AND_WINDOW_ONLY"
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
