from __future__ import annotations

import json
import math
import statistics
import tempfile
import time
from pathlib import Path
from typing import Any

from finite_ram_lab.fr_fp_016_restore_size_scaling import (
    _fadvise_dontneed,
    _file_residency,
    _prepare_tier,
    _restore,
    _size_bytes,
)

SCHEMA = "finite-ram-lab.fr-fp-017-cold-latency-trace/v0.1"

STATE_MIB = 8
BLOCKS = 48
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


def _quantile(
    values: list[float],
    q: float,
) -> float:
    if not values:
        raise ValueError("empty_values")
    if not 0.0 <= q <= 1.0:
        raise ValueError("invalid_quantile")

    ordered = sorted(values)
    index = max(
        0,
        min(
            len(ordered) - 1,
            math.ceil(
                q * len(ordered)
            ) - 1,
        ),
    )
    return ordered[index]


def _autocorr(
    values: list[float],
    lag: int,
) -> float | None:
    if lag <= 0 or len(values) <= lag:
        return None

    left = values[:-lag]
    right = values[lag:]

    left_mean = statistics.fmean(left)
    right_mean = statistics.fmean(right)

    numerator = sum(
        (a - left_mean)
        * (b - right_mean)
        for a, b
        in zip(left, right)
    )
    left_ss = sum(
        (a - left_mean) ** 2
        for a in left
    )
    right_ss = sum(
        (b - right_mean) ** 2
        for b in right
    )

    if left_ss <= 0.0 or right_ss <= 0.0:
        return None

    return (
        numerator
        / math.sqrt(
            left_ss * right_ss
        )
    )


def _burst_stats(
    values_ms: list[float],
    threshold_ms: float,
) -> dict[str, Any]:
    flags = [
        value > threshold_ms
        for value in values_ms
    ]

    runs = []
    current = 0

    for flag in flags:
        if flag:
            current += 1
        elif current:
            runs.append(current)
            current = 0

    if current:
        runs.append(current)

    slow_to_slow_num = 0
    slow_to_slow_den = 0
    fast_to_slow_num = 0
    fast_to_slow_den = 0

    for first, second in zip(
        flags[:-1],
        flags[1:],
    ):
        if first:
            slow_to_slow_den += 1
            if second:
                slow_to_slow_num += 1
        else:
            fast_to_slow_den += 1
            if second:
                fast_to_slow_num += 1

    return {
        "threshold_ms": threshold_ms,
        "misses": sum(flags),
        "miss_rate": (
            sum(flags) / len(flags)
        ),
        "run_count": len(runs),
        "max_run": (
            max(runs)
            if runs
            else 0
        ),
        "mean_run": (
            statistics.fmean(runs)
            if runs
            else 0.0
        ),
        "p_slow_next_given_slow": (
            None
            if slow_to_slow_den == 0
            else (
                slow_to_slow_num
                / slow_to_slow_den
            )
        ),
        "p_slow_next_given_fast": (
            None
            if fast_to_slow_den == 0
            else (
                fast_to_slow_num
                / fast_to_slow_den
            )
        ),
    }


def _summary(
    values_ns: list[int],
) -> dict[str, Any]:
    values_ms = [
        value / 1_000_000.0
        for value in values_ns
    ]

    mean = statistics.fmean(values_ms)
    stdev = (
        statistics.stdev(values_ms)
        if len(values_ms) >= 2
        else 0.0
    )

    return {
        "count": len(values_ms),
        "min_ms": min(values_ms),
        "p50_ms": _quantile(
            values_ms,
            0.50,
        ),
        "p90_ms": _quantile(
            values_ms,
            0.90,
        ),
        "p95_ms": _quantile(
            values_ms,
            0.95,
        ),
        "p99_ms": _quantile(
            values_ms,
            0.99,
        ),
        "max_ms": max(values_ms),
        "mean_ms": mean,
        "stdev_ms": stdev,
        "cv": (
            0.0
            if mean == 0.0
            else stdev / mean
        ),
        "lag1_autocorr": _autocorr(
            values_ms,
            1,
        ),
        "lag2_autocorr": _autocorr(
            values_ms,
            2,
        ),
        "lag4_autocorr": _autocorr(
            values_ms,
            4,
        ),
        "deadline_miss_rates": {
            str(deadline): (
                sum(
                    value > deadline
                    for value in values_ms
                )
                / len(values_ms)
            )
            for deadline
            in DEADLINES_MS
        },
        "burst_25ms": _burst_stats(
            values_ms,
            25.0,
        ),
        "burst_50ms": _burst_stats(
            values_ms,
            50.0,
        ),
        "burst_100ms": _burst_stats(
            values_ms,
            100.0,
        ),
    }


def _trial(
    root: Path,
    *,
    block: int,
    arm: str,
) -> dict[str, Any]:
    size_bytes = _size_bytes(
        STATE_MIB
    )
    marker = (
        block * 3
        + (
            1
            if arm
            == "WARM_PAGECACHE"
            else 2
        )
    )
    path = root / (
        f"b{block:03d}-"
        + arm.lower()
        + ".bin"
    )

    started_ns = (
        time.monotonic_ns()
    )

    prepared = _prepare_tier(
        path,
        size_bytes=size_bytes,
        marker=marker,
        cold=(
            arm
            == "COLD_DONTNEED"
        ),
    )
    pre = _file_residency(
        path
    )
    restored = _restore(
        path,
        size_bytes=size_bytes,
        marker=marker,
    )

    _fadvise_dontneed(
        path
    )
    path.unlink()
    time.sleep(
        0.002
    )

    return {
        "block": block,
        "arm": arm,
        "started_ns": started_ns,
        "prepare_verified": (
            prepared[
                "verified"
            ]
        ),
        "pre_resident_fraction": (
            pre[
                "resident_fraction"
            ]
        ),
        "read_ns": (
            restored[
                "read_ns"
            ]
        ),
        "restore_verified": (
            restored[
                "verified"
            ]
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
                    _trial(
                        root,
                        block=block,
                        arm=arm,
                    )
                )

    warm = sorted(
        (
            row
            for row in rows
            if row["arm"]
            == "WARM_PAGECACHE"
        ),
        key=lambda row: row["block"],
    )
    cold = sorted(
        (
            row
            for row in rows
            if row["arm"]
            == "COLD_DONTNEED"
        ),
        key=lambda row: row["block"],
    )

    warm_ns = [
        int(row["read_ns"])
        for row in warm
    ]
    cold_ns = [
        int(row["read_ns"])
        for row in cold
    ]

    warm_summary = _summary(
        warm_ns
    )
    cold_summary = _summary(
        cold_ns
    )

    paired_ratios = [
        cold_row["read_ns"]
        / warm_row["read_ns"]
        for warm_row, cold_row
        in zip(warm, cold)
    ]

    epoch_size = 12
    cold_epochs = []

    for start in range(
        0,
        BLOCKS,
        epoch_size,
    ):
        selected = cold_ns[
            start:
            start + epoch_size
        ]
        cold_epochs.append(
            {
                "start_block": start,
                "end_block": (
                    start
                    + len(selected)
                    - 1
                ),
                "p50_ms": (
                    _quantile(
                        [
                            value
                            / 1_000_000.0
                            for value
                            in selected
                        ],
                        0.50,
                    )
                ),
                "p95_ms": (
                    _quantile(
                        [
                            value
                            / 1_000_000.0
                            for value
                            in selected
                        ],
                        0.95,
                    )
                ),
            }
        )

    checks = {
        "full_trace_collected": (
            len(warm)
            == BLOCKS
            and len(cold)
            == BLOCKS
        ),
        "all_trials_verify": all(
            row["prepare_verified"]
            and row["restore_verified"]
            for row in rows
        ),
        "warm_residency_separated": all(
            row[
                "pre_resident_fraction"
            ]
            >= 0.95
            for row in warm
        ),
        "cold_residency_separated": all(
            row[
                "pre_resident_fraction"
            ]
            <= 0.10
            for row in cold
        ),
        "cold_median_slower_than_warm": (
            cold_summary[
                "p50_ms"
            ]
            > warm_summary[
                "p50_ms"
            ]
        ),
        "tail_quantiles_ordered": (
            cold_summary["p50_ms"]
            <= cold_summary["p90_ms"]
            <= cold_summary["p95_ms"]
            <= cold_summary["p99_ms"]
            <= cold_summary["max_ms"]
        ),
        "four_epochs_present": (
            len(cold_epochs)
            == 4
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
            "HOSTED_COLD_RESTORE_LONG_TEMPORAL_TRACE"
        ),
        "fixture": {
            "state_mib": STATE_MIB,
            "blocks": BLOCKS,
            "deadline_ms": list(
                DEADLINES_MS
            ),
        },
        "warm": (
            warm_summary
        ),
        "cold": (
            cold_summary
        ),
        "paired": {
            "median_cold_over_warm_ratio": (
                statistics.median(
                    paired_ratios
                )
            ),
            "min_ratio": min(
                paired_ratios
            ),
            "max_ratio": max(
                paired_ratios
            ),
            "cold_slower_pairs": sum(
                ratio > 1.0
                for ratio
                in paired_ratios
            ),
        },
        "cold_epochs": (
            cold_epochs
        ),
        "rows": rows,
        "checks": checks,
        "decision": (
            "MEASURE_COLD_RESTORE_AS_A_TEMPORAL_DISTRIBUTION_BEFORE_BUILDING_A_LATENT_IO_STATE_MODEL"
        ),
        "next_analysis": [
            "compare deadline miss clustering against iid Bernoulli baseline",
            "compare lag correlations to shuffled traces",
            "test whether epoch medians imply within-run regime drift",
            "retain WARM as environmental control",
        ],
        "claim_ceiling": (
            "HOSTED_8MIB_COLD_RESTORE_TEMPORAL_TRACE_PILOT_ONLY"
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
