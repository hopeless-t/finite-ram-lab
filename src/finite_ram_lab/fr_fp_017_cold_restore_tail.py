from __future__ import annotations

import json
import math
import statistics
import tempfile
from pathlib import Path
from typing import Any

from finite_ram_lab.fr_fp_014_warm_cold_restore import (
    run_trial,
)

SCHEMA = "finite-ram-lab.fr-fp-017-cold-restore-tail/v0.1"

BLOCKS = 32
ARMS = (
    "WARM_PAGECACHE",
    "COLD_DONTNEED",
)
DEADLINES_MS = (
    5,
    10,
    25,
    50,
    100,
    200,
)

PRIOR_COLD_8MIB_MEDIANS_MS = (
    4.7503795,
    140.9070215,
    87.6428545,
)


def _percentile(
    values: list[float],
    q: float,
) -> float:
    if not values:
        raise ValueError(
            "empty_values"
        )

    if not (
        0.0
        <= q
        <= 1.0
    ):
        raise ValueError(
            "q_out_of_range"
        )

    ordered = sorted(
        values
    )
    position = (
        len(ordered)
        - 1
    ) * q
    lower = math.floor(
        position
    )
    upper = math.ceil(
        position
    )

    if lower == upper:
        return ordered[
            lower
        ]

    weight = (
        position
        - lower
    )

    return (
        ordered[
            lower
        ]
        * (
            1.0
            - weight
        )
        + ordered[
            upper
        ]
        * weight
    )


def _lag1_correlation(
    values: list[float],
) -> float | None:
    if len(values) < 3:
        return None

    xs = values[:-1]
    ys = values[1:]
    x_mean = statistics.fmean(
        xs
    )
    y_mean = statistics.fmean(
        ys
    )

    numerator = sum(
        (
            x
            - x_mean
        )
        * (
            y
            - y_mean
        )
        for x, y
        in zip(
            xs,
            ys,
        )
    )

    x_energy = sum(
        (
            x
            - x_mean
        ) ** 2
        for x in xs
    )
    y_energy = sum(
        (
            y
            - y_mean
        ) ** 2
        for y in ys
    )

    denominator = math.sqrt(
        x_energy
        * y_energy
    )

    if denominator == 0.0:
        return None

    return (
        numerator
        / denominator
    )


def _longest_true_run(
    flags: list[bool],
) -> int:
    best = 0
    current = 0

    for flag in flags:
        if flag:
            current += 1
            best = max(
                best,
                current,
            )
        else:
            current = 0

    return best


def _summary(
    values_ns: list[float],
) -> dict[str, Any]:
    mean = statistics.fmean(
        values_ns
    )
    stdev = statistics.stdev(
        values_ns
    )

    deadlines = {}

    for deadline_ms in (
        DEADLINES_MS
    ):
        threshold_ns = (
            deadline_ms
            * 1_000_000.0
        )
        flags = [
            value
            > threshold_ns
            for value
            in values_ns
        ]

        deadlines[
            str(
                deadline_ms
            )
        ] = {
            "miss_rate": (
                sum(
                    flags
                )
                / len(
                    flags
                )
            ),
            "miss_count": (
                sum(
                    flags
                )
            ),
            "longest_consecutive_miss_run": (
                _longest_true_run(
                    flags
                )
            ),
        }

    log_values = [
        math.log1p(
            value
        )
        for value
        in values_ns
    ]

    return {
        "count": len(
            values_ns
        ),
        "min_ns": min(
            values_ns
        ),
        "p50_ns": _percentile(
            values_ns,
            0.50,
        ),
        "p90_ns": _percentile(
            values_ns,
            0.90,
        ),
        "p95_ns": _percentile(
            values_ns,
            0.95,
        ),
        "max_ns": max(
            values_ns
        ),
        "mean_ns": mean,
        "stdev_ns": (
            stdev
        ),
        "coefficient_of_variation": (
            stdev
            / mean
        ),
        "p95_over_p50": (
            _percentile(
                values_ns,
                0.95,
            )
            / _percentile(
                values_ns,
                0.50,
            )
        ),
        "log_latency_lag1_correlation": (
            _lag1_correlation(
                log_values
            )
        ),
        "deadlines_ms": (
            deadlines
        ),
    }


def run_panel() -> dict[str, Any]:
    rows = []

    with tempfile.TemporaryDirectory(
        prefix="fr-fp-017-"
    ) as tmp:
        root = Path(tmp)

        for block in range(
            BLOCKS
        ):
            order = (
                ARMS
                if block % 2 == 0
                else tuple(
                    reversed(
                        ARMS
                    )
                )
            )

            for arm in order:
                rows.append(
                    run_trial(
                        block=block,
                        arm=arm,
                        root=root,
                    )
                )

    by_arm = {
        arm: sorted(
            (
                row
                for row in rows
                if row[
                    "arm"
                ]
                == arm
            ),
            key=lambda row: (
                row[
                    "block"
                ]
            ),
        )
        for arm in ARMS
    }

    latency = {
        arm: [
            float(
                row[
                    "restore"
                ][
                    "read_ns"
                ]
            )
            for row in by_arm[
                arm
            ]
        ]
        for arm in ARMS
    }

    summaries = {
        arm: _summary(
            values
        )
        for arm, values
        in latency.items()
    }

    paired_ratios = [
        cold
        / warm
        for warm, cold
        in zip(
            latency[
                "WARM_PAGECACHE"
            ],
            latency[
                "COLD_DONTNEED"
            ],
        )
    ]

    current_cold_median_ms = (
        summaries[
            "COLD_DONTNEED"
        ][
            "p50_ns"
        ]
        / 1_000_000.0
    )

    prior_distance = [
        {
            "prior_median_ms": (
                prior
            ),
            "current_over_prior": (
                current_cold_median_ms
                / prior
            ),
        }
        for prior
        in PRIOR_COLD_8MIB_MEDIANS_MS
    ]

    checks = {
        "thirty_two_paired_blocks": (
            len(
                by_arm[
                    "WARM_PAGECACHE"
                ]
            )
            == BLOCKS
            and len(
                by_arm[
                    "COLD_DONTNEED"
                ]
            )
            == BLOCKS
        ),
        "all_spills_verify": all(
            row[
                "spill_verified"
            ]
            for row in rows
        ),
        "all_restores_verify": all(
            row[
                "restore"
            ][
                "verified"
            ]
            for row in rows
        ),
        "warm_is_resident": all(
            row[
                "pre_restore_residency"
            ][
                "resident_fraction"
            ]
            >= 0.95
            for row in by_arm[
                "WARM_PAGECACHE"
            ]
        ),
        "cold_is_nonresident": all(
            row[
                "pre_restore_residency"
            ][
                "resident_fraction"
            ]
            <= 0.10
            for row in by_arm[
                "COLD_DONTNEED"
            ]
        ),
        "cold_median_slower_than_warm": (
            summaries[
                "COLD_DONTNEED"
            ][
                "p50_ns"
            ]
            > summaries[
                "WARM_PAGECACHE"
            ][
                "p50_ns"
            ]
        ),
        "cold_p95_slower_than_warm_p95": (
            summaries[
                "COLD_DONTNEED"
            ][
                "p95_ns"
            ]
            > summaries[
                "WARM_PAGECACHE"
            ][
                "p95_ns"
            ]
        ),
        "deadline_curve_complete": all(
            str(
                value
            )
            in summaries[
                "COLD_DONTNEED"
            ][
                "deadlines_ms"
            ]
            for value
            in DEADLINES_MS
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
            "HOSTED_LINUX_FIXED_SIZE_RESTORE_TAIL_AND_TEMPORAL_TRACE"
        ),
        "blocks": (
            BLOCKS
        ),
        "state_mib": 8,
        "summaries": (
            summaries
        ),
        "paired_ratio_summary": (
            _summary(
                paired_ratios
            )
        ),
        "paired_cold_over_warm_ratios": (
            paired_ratios
        ),
        "current_cold_median_ms": (
            current_cold_median_ms
        ),
        "prior_cold_8mib_medians_ms": list(
            PRIOR_COLD_8MIB_MEDIANS_MS
        ),
        "prior_regime_distance": (
            prior_distance
        ),
        "cold_trace_ns": (
            latency[
                "COLD_DONTNEED"
            ]
        ),
        "warm_trace_ns": (
            latency[
                "WARM_PAGECACHE"
            ]
        ),
        "checks": checks,
        "decision": (
            "MODEL_COLD_RESTORE_AS_A_DEADLINE_RISK_DISTRIBUTION_WITH_RUN_LEVEL_AND_TEMPORAL_STATE"
        ),
        "claim_ceiling": (
            "HOSTED_LINUX_FIXED_8MIB_RESTORE_TAIL_TRACE_ONLY"
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
