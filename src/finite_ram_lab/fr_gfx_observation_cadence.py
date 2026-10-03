from __future__ import annotations

import json


SCHEMA = "finite-ram-lab.fr-gfx-004-adaptive-observation-cadence/v0.1"

DURATION_PMF_MS = (
    (50.0, 0.25),
    (100.0, 0.35),
    (250.0, 0.25),
    (1000.0, 0.15),
)

FIXED_INTERVALS_MS = (
    50.0,
    100.0,
    250.0,
    500.0,
    1000.0,
)

BASE_INTERVAL_MS = 500.0
BURST_INTERVAL_MS = 50.0
BURST_WINDOW_MS = 500.0
ANOMALY_RATE_PER_SECOND = 0.2
CHEAP_TRIGGER_RECALL = 0.90


def periodic_detection_probability(
    interval_ms: float,
) -> float:
    if interval_ms <= 0.0:
        raise ValueError(
            "interval_must_be_positive"
        )

    return sum(
        probability
        * min(
            1.0,
            duration_ms
            / interval_ms,
        )
        for duration_ms, probability
        in DURATION_PMF_MS
    )


def samples_per_second(
    interval_ms: float,
) -> float:
    return 1000.0 / interval_ms


def adaptive_detection_probability(
    trigger_recall: float,
) -> float:
    slow = (
        periodic_detection_probability(
            BASE_INTERVAL_MS
        )
    )

    return (
        slow
        + trigger_recall
        * (
            1.0 - slow
        )
    )


def adaptive_samples_per_second(
    anomaly_rate_per_second: float,
) -> float:
    base_rate = samples_per_second(
        BASE_INTERVAL_MS
    )

    burst_rate = samples_per_second(
        BURST_INTERVAL_MS
    )

    burst_fraction = (
        anomaly_rate_per_second
        * (
            BURST_WINDOW_MS
            / 1000.0
        )
    )

    return (
        base_rate
        + burst_fraction
        * (
            burst_rate
            - base_rate
        )
    )


def trigger_recall_for_target(
    target_detection: float,
) -> float:
    slow = (
        periodic_detection_probability(
            BASE_INTERVAL_MS
        )
    )

    if target_detection <= slow:
        return 0.0

    if target_detection > 1.0:
        raise ValueError(
            "target_detection_above_one"
        )

    return (
        target_detection
        - slow
    ) / (
        1.0 - slow
    )


def event_rate_break_even_vs_fast() -> float:
    base_rate = samples_per_second(
        BASE_INTERVAL_MS
    )

    burst_rate = samples_per_second(
        BURST_INTERVAL_MS
    )

    fast_rate = burst_rate

    return (
        fast_rate
        - base_rate
    ) / (
        (
            BURST_WINDOW_MS
            / 1000.0
        )
        * (
            burst_rate
            - base_rate
        )
    )


def run_panel() -> dict:
    fixed = {
        str(
            int(interval)
        ): {
            "interval_ms": interval,
            "detection_probability": (
                periodic_detection_probability(
                    interval
                )
            ),
            "samples_per_second": (
                samples_per_second(
                    interval
                )
            ),
        }
        for interval in (
            FIXED_INTERVALS_MS
        )
    }

    adaptive_detection = (
        adaptive_detection_probability(
            CHEAP_TRIGGER_RECALL
        )
    )

    adaptive_rate = (
        adaptive_samples_per_second(
            ANOMALY_RATE_PER_SECOND
        )
    )

    fast_rate = samples_per_second(
        BURST_INTERVAL_MS
    )

    frozen = {
        "fixed_detection": {
            "50": 1.0,
            "100": 0.875,
            "250": 0.59,
            "500": 0.37,
            "1000": 0.26,
        },
        "adaptive_detection": (
            0.937
        ),
        "adaptive_rate": 3.8,
        "sampling_reduction_vs_fast": (
            0.81
        ),
        "target_90_trigger_recall": (
            0.8412698412698413
        ),
        "event_rate_break_even": 2.0,
    }

    for key, expected in (
        frozen[
            "fixed_detection"
        ].items()
    ):
        actual = fixed[key][
            "detection_probability"
        ]

        if actual != expected:
            raise RuntimeError(
                (
                    "fixed_detection_"
                    f"changed:{key}:{actual}"
                )
            )

    sampling_reduction = (
        1.0
        - adaptive_rate
        / fast_rate
    )

    target_90 = (
        trigger_recall_for_target(
            0.90
        )
    )

    break_even = (
        event_rate_break_even_vs_fast()
    )

    if (
        adaptive_detection
        != frozen[
            "adaptive_detection"
        ]
    ):
        raise RuntimeError(
            "adaptive_detection_changed"
        )

    if (
        adaptive_rate
        != frozen[
            "adaptive_rate"
        ]
    ):
        raise RuntimeError(
            "adaptive_rate_changed"
        )

    if (
        sampling_reduction
        != frozen[
            "sampling_reduction_vs_fast"
        ]
    ):
        raise RuntimeError(
            "sampling_reduction_changed"
        )

    if abs(
        target_90
        - frozen[
            "target_90_trigger_recall"
        ]
    ) > 1e-15:
        raise RuntimeError(
            "trigger_recall_threshold_changed"
        )

    if (
        break_even
        != frozen[
            "event_rate_break_even"
        ]
    ):
        raise RuntimeError(
            "event_rate_break_even_changed"
        )

    adaptive = {
        "base_interval_ms": (
            BASE_INTERVAL_MS
        ),
        "burst_interval_ms": (
            BURST_INTERVAL_MS
        ),
        "burst_window_ms": (
            BURST_WINDOW_MS
        ),
        "cheap_trigger_recall": (
            CHEAP_TRIGGER_RECALL
        ),
        "anomaly_rate_per_second": (
            ANOMALY_RATE_PER_SECOND
        ),
        "detection_probability": (
            adaptive_detection
        ),
        "samples_per_second": (
            adaptive_rate
        ),
        "sampling_reduction_vs_always_fast": (
            sampling_reduction
        ),
    }

    if not (
        adaptive[
            "detection_probability"
        ]
        > fixed["100"][
            "detection_probability"
        ]
        and adaptive[
            "samples_per_second"
        ]
        < fixed["100"][
            "samples_per_second"
        ]
    ):
        raise RuntimeError(
            "adaptive_does_not_dominate_100ms"
        )

    if not (
        adaptive[
            "detection_probability"
        ]
        > fixed["250"][
            "detection_probability"
        ]
        and adaptive[
            "samples_per_second"
        ]
        < fixed["250"][
            "samples_per_second"
        ]
    ):
        raise RuntimeError(
            "adaptive_does_not_dominate_250ms"
        )

    return {
        "schema": SCHEMA,
        "status": "PASS",
        "classification": (
            "SYNTHETIC_ADAPTIVE_OBSERVATION_CADENCE_VALIDATED"
        ),
        "event_duration_pmf_ms": [
            {
                "duration_ms": duration,
                "probability": probability,
            }
            for duration, probability
            in DURATION_PMF_MS
        ],
        "fixed_sampling": fixed,
        "adaptive_sampling": (
            adaptive
        ),
        "derived": {
            "trigger_recall_required_for_90pct_detection": (
                target_90
            ),
            "event_rate_break_even_vs_always_50ms_per_second": (
                break_even
            ),
            "efficiency_gain_detection_per_sample_vs_always_fast": (
                (
                    adaptive_detection
                    / adaptive_rate
                )
                / (
                    fixed["50"][
                        "detection_probability"
                    ]
                    / fixed["50"][
                        "samples_per_second"
                    ]
                )
            ),
        },
        "assumptions": [
            "event onset phase is uniform relative to periodic sampling",
            "cheap frame anomaly trigger is independent enough to use a frozen recall scalar",
            "a triggered burst obtains an immediate first expensive sample",
            "sampling cost is proportional to sample count",
            "duration distribution is synthetic and must be replaced by measured traces",
        ],
        "primary_findings": [
            "SAMPLING_CADENCE_IS_A_RESOURCE_CONTROL_VARIABLE",
            "ALWAYS_FAST_TELEMETRY_IS_NOT_REQUIRED_WHEN_CHEAP_TRIGGERS_ARE_RELIABLE",
            "ADAPTIVE_BURST_SAMPLING_CAN_DOMINATE_FIXED_INTERMEDIATE_CADENCES",
            "TRIGGER_RECALL_HAS_A_CALCULABLE_MINIMUM_FOR_A_DETECTION_SLO",
            "OBSERVER_ESCALATION_HAS_ITS_OWN_PRESSURE_KNEE",
        ],
        "claim_ceiling": (
            "SYNTHETIC_OBSERVATION_CADENCE_MODEL_ONLY"
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
