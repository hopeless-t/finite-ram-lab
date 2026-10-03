from __future__ import annotations

import json
import math
import random
import statistics
from pathlib import Path
from typing import Any

SCHEMA = "finite-ram-lab.fr-fp-020-cross-run-prior/v0.1"

BOOTSTRAPS = 20_000
SEED = 20261004
DEADLINES_MS = (5.0, 10.0, 25.0, 50.0, 100.0)

DATA_PATH = (
    Path(__file__).resolve()
    .parents[2]
    / "data"
    / "FR-FP-020-cross-run-restore.json"
)


def _quantile(
    values: list[float],
    q: float,
) -> float:
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


def _cv(
    values: list[float],
) -> float:
    mean = statistics.fmean(values)
    return (
        statistics.stdev(values)
        / mean
    )


def _deadline_rate(
    values: list[float],
    deadline_ms: float,
) -> float:
    return (
        sum(
            value > deadline_ms
            for value in values
        )
        / len(values)
    )


def _bootstrap(
    values: list[float],
) -> dict[str, Any]:
    rng = random.Random(SEED)

    medians = []
    rates = {
        str(int(deadline)): []
        for deadline
        in DEADLINES_MS
    }

    for _ in range(BOOTSTRAPS):
        sample = [
            values[
                rng.randrange(
                    len(values)
                )
            ]
            for _ in values
        ]

        medians.append(
            statistics.median(
                sample
            )
        )

        for deadline in DEADLINES_MS:
            rates[
                str(
                    int(deadline)
                )
            ].append(
                _deadline_rate(
                    sample,
                    deadline,
                )
            )

    return {
        "median_ms_95pct": [
            _quantile(
                medians,
                0.025,
            ),
            _quantile(
                medians,
                0.975,
            ),
        ],
        "deadline_miss_95pct": {
            key: [
                _quantile(
                    samples,
                    0.025,
                ),
                _quantile(
                    samples,
                    0.975,
                ),
            ]
            for key, samples
            in rates.items()
        },
    }


def _largest_log_gap(
    values: list[float],
) -> dict[str, Any]:
    ordered = sorted(values)

    gaps = [
        math.log(
            right / left
        )
        for left, right
        in zip(
            ordered[:-1],
            ordered[1:],
        )
    ]
    index = max(
        range(
            len(gaps)
        ),
        key=lambda cursor: gaps[
            cursor
        ],
    )

    lower = ordered[index]
    upper = ordered[
        index + 1
    ]

    return {
        "lower_ms": lower,
        "upper_ms": upper,
        "ratio": (
            upper / lower
        ),
        "log_gap": gaps[index],
        "geometric_midpoint_ms": (
            math.sqrt(
                lower * upper
            )
        ),
        "high_count": sum(
            value >= upper
            for value in values
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
    rows = data["rows"]

    cold = [
        float(
            row[
                "cold8_ms"
            ]
        )
        for row in rows
    ]
    warm = [
        float(
            row[
                "warm8_ms"
            ]
        )
        for row in rows
    ]

    stable = all(
        row[
            "all_trials_verify"
        ]
        and row[
            "all_warm_pre_resident"
        ]
        and row[
            "all_cold_pre_nonresident"
        ]
        and row[
            "cold_slower_at_every_size"
        ]
        for row in rows
    )

    cold_summary = {
        "count": len(cold),
        "min_ms": min(cold),
        "p25_ms": _quantile(
            cold,
            0.25,
        ),
        "p50_ms": _quantile(
            cold,
            0.50,
        ),
        "p75_ms": _quantile(
            cold,
            0.75,
        ),
        "p90_ms": _quantile(
            cold,
            0.90,
        ),
        "p95_ms": _quantile(
            cold,
            0.95,
        ),
        "max_ms": max(cold),
        "max_over_min": (
            max(cold)
            / min(cold)
        ),
        "mean_ms": (
            statistics.fmean(
                cold
            )
        ),
        "cv": _cv(cold),
        "log_stdev": (
            statistics.stdev(
                math.log(
                    value
                )
                for value in cold
            )
        ),
        "deadline_miss_rates": {
            str(
                int(deadline)
            ): _deadline_rate(
                cold,
                deadline,
            )
            for deadline
            in DEADLINES_MS
        },
    }

    warm_summary = {
        "count": len(warm),
        "min_ms": min(warm),
        "p50_ms": _quantile(
            warm,
            0.50,
        ),
        "p90_ms": _quantile(
            warm,
            0.90,
        ),
        "p95_ms": _quantile(
            warm,
            0.95,
        ),
        "max_ms": max(warm),
        "max_over_min": (
            max(warm)
            / min(warm)
        ),
        "mean_ms": (
            statistics.fmean(
                warm
            )
        ),
        "cv": _cv(warm),
        "log_stdev": (
            statistics.stdev(
                math.log(
                    value
                )
                for value in warm
            )
        ),
    }

    gap = _largest_log_gap(
        cold
    )
    bootstrap = _bootstrap(
        cold
    )

    checks = {
        "fifteen_independent_ci_runs": (
            len(rows) == 15
        ),
        "all_source_runs_preserve_physical_tier_gates": (
            stable
        ),
        "cold_cross_run_range_exceeds_30x": (
            cold_summary[
                "max_over_min"
            ]
            > 30.0
        ),
        "cold_log_dispersion_exceeds_warm": (
            cold_summary[
                "log_stdev"
            ]
            > warm_summary[
                "log_stdev"
            ]
        ),
        "material_high_latency_gap_exists": (
            gap["ratio"]
            > 5.0
            and gap[
                "high_count"
            ]
            >= 2
        ),
        "bootstrap_count_frozen": (
            BOOTSTRAPS
            == 20_000
        ),
        "median_uncertainty_is_nonzero": (
            bootstrap[
                "median_ms_95pct"
            ][0]
            < bootstrap[
                "median_ms_95pct"
            ][1]
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
            "REUSED_HOSTED_CI_CROSS_RUN_RESTORE_PRIOR"
        ),
        "source": {
            "new_physical_runs": 0,
            "reused_ci_runs": (
                len(rows)
            ),
            "state_mib": (
                data[
                    "state_mib"
                ]
            ),
        },
        "cold": cold_summary,
        "warm": warm_summary,
        "cold_bootstrap": bootstrap,
        "largest_cold_log_gap": gap,
        "checks": checks,
        "decision": (
            "MODEL_COLD_RESTORE_WITH_A_RUN_LEVEL_UNCERTAINTY_PRIOR_NOT_A_SINGLE_POINT_LATENCY"
        ),
        "governor_direction": {
            "point_estimate": (
                "REJECT_AS_SOLE_INPUT"
            ),
            "recommended_state": [
                "empirical run-level restore distribution",
                "deadline-miss probability with uncertainty interval",
                "current-run calibration evidence when available",
            ],
            "high_latency_regime": (
                "CANDIDATE_ONLY_NOT_A_STABLE_DISCRETE_STATE"
            ),
        },
        "claim_ceiling": (
            "FIFTEEN_REUSED_GITHUB_HOSTED_CI_RUNS_FOR_8MIB_RESTORE_ONLY"
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
