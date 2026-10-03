from __future__ import annotations

import json
import math
import random
import statistics
from pathlib import Path
from typing import Any

SCHEMA = "finite-ram-lab.fr-fp-018-order-null/v0.1"

SHUFFLES = 20_000
SEED = 20261004
THRESHOLD_MS = 25.0
EPOCH_SIZE = 12
ALPHA = 0.05
METRIC_COUNT = 7
BONFERRONI_ALPHA = ALPHA / METRIC_COUNT

DATA_PATH = (
    Path(__file__).resolve()
    .parents[2]
    / "data"
    / "FR-FP-017-trace.json"
)


def _autocorr(
    values: list[float],
    lag: int,
) -> float:
    left = values[:-lag]
    right = values[lag:]
    left_mean = statistics.fmean(left)
    right_mean = statistics.fmean(right)

    numerator = sum(
        (a - left_mean)
        * (b - right_mean)
        for a, b in zip(left, right)
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
        return 0.0

    return (
        numerator
        / math.sqrt(
            left_ss * right_ss
        )
    )


def _max_run(
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


def _epoch_chunks(
    values: list[float],
) -> list[list[float]]:
    return [
        values[
            start:
            start + EPOCH_SIZE
        ]
        for start in range(
            0,
            len(values),
            EPOCH_SIZE,
        )
    ]


def _stats(
    values_ms: list[float],
) -> dict[str, float]:
    flags = [
        value > THRESHOLD_MS
        for value in values_ms
    ]
    epochs = _epoch_chunks(
        values_ms
    )
    epoch_medians = [
        statistics.median(epoch)
        for epoch in epochs
    ]
    epoch_misses = [
        sum(
            value > THRESHOLD_MS
            for value in epoch
        )
        for epoch in epochs
    ]

    return {
        "lag1": _autocorr(
            values_ms,
            1,
        ),
        "lag2": _autocorr(
            values_ms,
            2,
        ),
        "lag4": _autocorr(
            values_ms,
            4,
        ),
        "max_run_25ms": float(
            _max_run(flags)
        ),
        "epoch_miss_range_25ms": float(
            max(epoch_misses)
            - min(epoch_misses)
        ),
        "epoch_median_range_ms": (
            max(epoch_medians)
            - min(epoch_medians)
        ),
        "miss_count_25ms": float(
            sum(flags)
        ),
    }


def _pvalue_upper(
    observed: float,
    null: list[float],
) -> float:
    return (
        1
        + sum(
            value >= observed
            for value in null
        )
    ) / (
        len(null) + 1
    )


def _pvalue_lower(
    observed: float,
    null: list[float],
) -> float:
    return (
        1
        + sum(
            value <= observed
            for value in null
        )
    ) / (
        len(null) + 1
    )


def _pvalue_abs(
    observed: float,
    null: list[float],
) -> float:
    target = abs(
        observed
    )
    return (
        1
        + sum(
            abs(value) >= target
            for value in null
        )
    ) / (
        len(null) + 1
    )


def analyze_order(
    values_ns: list[int],
    *,
    seed: int,
) -> dict[str, Any]:
    values_ms = [
        value / 1_000_000.0
        for value in values_ns
    ]
    observed = _stats(
        values_ms
    )

    rng = random.Random(
        seed
    )
    null = {
        key: []
        for key in observed
    }

    for _ in range(
        SHUFFLES
    ):
        shuffled = list(
            values_ms
        )
        rng.shuffle(
            shuffled
        )
        row = _stats(
            shuffled
        )

        for key, value in row.items():
            null[key].append(
                value
            )

    pvalues = {
        "lag1_abs": _pvalue_abs(
            observed["lag1"],
            null["lag1"],
        ),
        "lag2_abs": _pvalue_abs(
            observed["lag2"],
            null["lag2"],
        ),
        "lag4_abs": _pvalue_abs(
            observed["lag4"],
            null["lag4"],
        ),
        "max_run_cluster_upper": _pvalue_upper(
            observed["max_run_25ms"],
            null["max_run_25ms"],
        ),
        "max_run_anticleuster_lower": _pvalue_lower(
            observed["max_run_25ms"],
            null["max_run_25ms"],
        ),
        "epoch_miss_range_upper": _pvalue_upper(
            observed[
                "epoch_miss_range_25ms"
            ],
            null[
                "epoch_miss_range_25ms"
            ],
        ),
        "epoch_median_range_upper": _pvalue_upper(
            observed[
                "epoch_median_range_ms"
            ],
            null[
                "epoch_median_range_ms"
            ],
        ),
    }

    significant = [
        key
        for key, value in pvalues.items()
        if value
        <= BONFERRONI_ALPHA
    ]

    return {
        "observed": observed,
        "pvalues": pvalues,
        "bonferroni_alpha": (
            BONFERRONI_ALPHA
        ),
        "significant_metrics": (
            significant
        ),
        "order_effect_detected": (
            bool(significant)
        ),
    }


def _load() -> dict[str, Any]:
    return json.loads(
        DATA_PATH.read_text(
            encoding="utf-8"
        )
    )


def run_panel() -> dict[str, Any]:
    data = _load()
    warm = analyze_order(
        data["warm_read_ns"],
        seed=SEED + 1,
    )
    cold = analyze_order(
        data["cold_read_ns"],
        seed=SEED + 2,
    )

    if (
        cold[
            "order_effect_detected"
        ]
        and not warm[
            "order_effect_detected"
        ]
    ):
        route = (
            "COLD_SPECIFIC_TEMPORAL_STRUCTURE_CANDIDATE"
        )
    elif warm[
        "order_effect_detected"
    ]:
        route = (
            "SHARED_ENVIRONMENT_OR_HARNESS_TEMPORAL_STRUCTURE_CANDIDATE"
        )
    else:
        route = (
            "NO_STRONG_WITHIN_RUN_ORDER_EFFECT_AT_CURRENT_POWER"
        )

    checks = {
        "frozen_trace_loaded": (
            data[
                "schema"
            ]
            == "finite-ram-lab.fr-fp-017-trace-data/v0.1"
        ),
        "warm_has_48_samples": (
            len(
                data[
                    "warm_read_ns"
                ]
            )
            == 48
        ),
        "cold_has_48_samples": (
            len(
                data[
                    "cold_read_ns"
                ]
            )
            == 48
        ),
        "twenty_thousand_shuffles": (
            SHUFFLES
            == 20_000
        ),
        "all_pvalues_valid": all(
            0.0 < value <= 1.0
            for result in (
                warm,
                cold,
            )
            for value in result[
                "pvalues"
            ].values()
        ),
        "miss_count_preserved_by_order_null": (
            cold[
                "observed"
            ][
                "miss_count_25ms"
            ]
            == 8.0
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
            "ORDER_ONLY_MONTE_CARLO_NULL_ON_FROZEN_HOSTED_TRACE"
        ),
        "source_run": data[
            "source_run"
        ],
        "shuffles": SHUFFLES,
        "seed": SEED,
        "threshold_ms": (
            THRESHOLD_MS
        ),
        "multiple_testing": {
            "alpha": ALPHA,
            "metric_count": (
                METRIC_COUNT
            ),
            "bonferroni_alpha": (
                BONFERRONI_ALPHA
            ),
        },
        "warm": warm,
        "cold": cold,
        "route": route,
        "checks": checks,
        "decision": (
            "ROUTE_LATENT_STATE_MODELING_ONLY_AFTER_ORDER_EFFECT_IS_TESTED_AGAINST_A_SHUFFLED_MARGINAL_NULL"
        ),
        "claim_ceiling": (
            "ORDER_STRUCTURE_TEST_ON_ONE_FROZEN_48_SAMPLE_HOSTED_TRACE_ONLY"
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
