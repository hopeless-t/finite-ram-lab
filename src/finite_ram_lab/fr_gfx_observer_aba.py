from __future__ import annotations

import hashlib
import json
import math
from statistics import mean, pstdev


SCHEMA = "finite-ram-lab.fr-gfx-005-observer-perturbation-aba/v0.1"
SEED = "FR-GFX-005-v0.1"

EPISODES = 8192
FRAMES_PER_SEGMENT = 120
BLOCKS_PER_DECISION = 8
EQUIVALENCE_MARGIN_MS = 1.0

ARMS = {
    "NULL_OBSERVER": {
        "constant_overhead_ms": 0.0,
        "tail_overhead_ms": 0.0,
    },
    "LIGHT_OBSERVER": {
        "constant_overhead_ms": 0.5,
        "tail_overhead_ms": 2.0,
    },
    "HEAVY_OBSERVER": {
        "constant_overhead_ms": 2.0,
        "tail_overhead_ms": 12.0,
    },
}


def _u(
    episode: int,
    segment: int,
    frame: int,
    domain: str,
) -> float:
    value = int.from_bytes(
        hashlib.sha256(
            (
                f"{SEED}|{episode}|{segment}|"
                f"{frame}|{domain}"
            ).encode("utf-8")
        ).digest()[:8],
        "big",
    )

    return value / float(
        (1 << 64) - 1
    )


def _noise(
    episode: int,
    segment: int,
    frame: int,
    amplitude: float,
) -> float:
    return (
        _u(
            episode,
            segment,
            frame,
            "noise",
        )
        - 0.5
    ) * 2.0 * amplitude


def _segment(
    episode: int,
    segment: int,
    *,
    observer_constant_ms: float = 0.0,
    observer_tail_ms: float = 0.0,
) -> list[float]:
    base = (
        100.0
        + (
            episode % 17
            - 8
        ) * 0.15
    )

    drift = (
        _u(
            episode,
            0,
            0,
            "drift",
        )
        - 0.5
    ) * 8.0

    position = (
        0.0
        if segment == 0
        else (
            0.5
            if segment == 1
            else 1.0
        )
    )

    rows = []

    for frame in range(
        FRAMES_PER_SEGMENT
    ):
        value = (
            base
            + drift * position
            + _noise(
                episode,
                segment,
                frame,
                4.0,
            )
        )

        if (
            _u(
                episode,
                segment,
                frame,
                "tail",
            )
            < 0.05
        ):
            value += (
                25.0
                + 15.0
                * _u(
                    episode,
                    segment,
                    frame,
                    "tailamp",
                )
            )

        if segment == 1:
            value += (
                observer_constant_ms
            )

            if (
                _u(
                    episode,
                    segment,
                    frame,
                    "obstail",
                )
                < 0.03
            ):
                value += (
                    observer_tail_ms
                )

        rows.append(value)

    return rows


def _mean_effects(
    *,
    constant_ms: float,
    tail_ms: float,
) -> tuple[
    list[float],
    list[float],
]:
    naive = []
    aba = []

    for episode in range(
        EPISODES
    ):
        a1 = mean(
            _segment(
                episode,
                0,
            )
        )

        b = mean(
            _segment(
                episode,
                1,
                observer_constant_ms=(
                    constant_ms
                ),
                observer_tail_ms=(
                    tail_ms
                ),
            )
        )

        a2 = mean(
            _segment(
                episode,
                2,
            )
        )

        naive.append(
            b - a1
        )

        aba.append(
            b
            - (
                a1 + a2
            ) / 2.0
        )

    return naive, aba


def _grouped(
    rows: list[float],
    group_size: int,
) -> list[float]:
    if (
        len(rows)
        % group_size
        != 0
    ):
        raise ValueError(
            "rows_not_divisible"
        )

    return [
        mean(
            rows[
                start :
                start + group_size
            ]
        )
        for start in range(
            0,
            len(rows),
            group_size,
        )
    ]


def _mae(
    rows: list[float],
    truth: float,
) -> float:
    return mean(
        abs(
            value - truth
        )
        for value in rows
    )


def _rmse(
    rows: list[float],
    truth: float,
) -> float:
    return math.sqrt(
        mean(
            (
                value - truth
            ) ** 2
            for value in rows
        )
    )


def _quantile(
    rows: list[float],
    q: float,
) -> float:
    ordered = sorted(
        rows
    )

    position = q * (
        len(ordered) - 1
    )

    lower = int(
        math.floor(position)
    )

    upper = int(
        math.ceil(position)
    )

    if lower == upper:
        return ordered[
            lower
        ]

    fraction = (
        position - lower
    )

    return (
        ordered[lower]
        * (
            1.0 - fraction
        )
        + ordered[upper]
        * fraction
    )


def _arm(
    name: str,
) -> dict:
    settings = ARMS[name]

    truth = (
        settings[
            "constant_overhead_ms"
        ]
        + 0.03
        * settings[
            "tail_overhead_ms"
        ]
    )

    naive, aba = (
        _mean_effects(
            constant_ms=settings[
                "constant_overhead_ms"
            ],
            tail_ms=settings[
                "tail_overhead_ms"
            ],
        )
    )

    grouped_naive = (
        _grouped(
            naive,
            BLOCKS_PER_DECISION,
        )
    )

    grouped_aba = (
        _grouped(
            aba,
            BLOCKS_PER_DECISION,
        )
    )

    return {
        "true_expected_mean_overhead_ms": (
            truth
        ),
        "single_block": {
            "naive_mean_ms": (
                mean(naive)
            ),
            "aba_mean_ms": (
                mean(aba)
            ),
            "naive_mae_ms": (
                _mae(
                    naive,
                    truth,
                )
            ),
            "aba_mae_ms": (
                _mae(
                    aba,
                    truth,
                )
            ),
            "naive_rmse_ms": (
                _rmse(
                    naive,
                    truth,
                )
            ),
            "aba_rmse_ms": (
                _rmse(
                    aba,
                    truth,
                )
            ),
            "naive_sd_ms": (
                pstdev(naive)
            ),
            "aba_sd_ms": (
                pstdev(aba)
            ),
        },
        "eight_block_decision": {
            "mean_estimate_ms": (
                mean(
                    grouped_aba
                )
            ),
            "sd_ms": (
                pstdev(
                    grouped_aba
                )
            ),
            "q05_ms": (
                _quantile(
                    grouped_aba,
                    0.05,
                )
            ),
            "q95_ms": (
                _quantile(
                    grouped_aba,
                    0.95,
                )
            ),
            "equivalence_pass_rate": (
                sum(
                    abs(value)
                    <= EQUIVALENCE_MARGIN_MS
                    for value
                    in grouped_aba
                )
                / len(
                    grouped_aba
                )
            ),
        },
    }


def run_panel() -> dict:
    arms = {
        name: _arm(name)
        for name in ARMS
    }

    null_naive, null_aba = (
        _mean_effects(
            constant_ms=0.0,
            tail_ms=0.0,
        )
    )

    false_perturbation = {}

    for blocks in (
        1,
        2,
        4,
        8,
        16,
    ):
        grouped_naive = (
            _grouped(
                null_naive,
                blocks,
            )
        )

        grouped_aba = (
            _grouped(
                null_aba,
                blocks,
            )
        )

        false_perturbation[
            str(blocks)
        ] = {
            "naive_abs_gt_1ms": (
                sum(
                    abs(value)
                    > EQUIVALENCE_MARGIN_MS
                    for value
                    in grouped_naive
                )
                / len(
                    grouped_naive
                )
            ),
            "aba_abs_gt_1ms": (
                sum(
                    abs(value)
                    > EQUIVALENCE_MARGIN_MS
                    for value
                    in grouped_aba
                )
                / len(
                    grouped_aba
                )
            ),
        }

    frozen = {
        "null_aba_mae": (
            0.6702464188226963
        ),
        "null_naive_mae": (
            1.2329958296867667
        ),
        "null_single_false_naive": (
            0.5389404296875
        ),
        "null_single_false_aba": (
            0.2353515625
        ),
        "null_eight_false_aba": (
            0.0
        ),
        "light_pass_rate": (
            0.9326171875
        ),
        "heavy_pass_rate": (
            0.0
        ),
        "light_mean_estimate": (
            0.5451759225167098
        ),
        "heavy_mean_estimate": (
            2.3475746041573347
        ),
    }

    actual = {
        "null_aba_mae": (
            arms[
                "NULL_OBSERVER"
            ][
                "single_block"
            ][
                "aba_mae_ms"
            ]
        ),
        "null_naive_mae": (
            arms[
                "NULL_OBSERVER"
            ][
                "single_block"
            ][
                "naive_mae_ms"
            ]
        ),
        "null_single_false_naive": (
            false_perturbation[
                "1"
            ][
                "naive_abs_gt_1ms"
            ]
        ),
        "null_single_false_aba": (
            false_perturbation[
                "1"
            ][
                "aba_abs_gt_1ms"
            ]
        ),
        "null_eight_false_aba": (
            false_perturbation[
                "8"
            ][
                "aba_abs_gt_1ms"
            ]
        ),
        "light_pass_rate": (
            arms[
                "LIGHT_OBSERVER"
            ][
                "eight_block_decision"
            ][
                "equivalence_pass_rate"
            ]
        ),
        "heavy_pass_rate": (
            arms[
                "HEAVY_OBSERVER"
            ][
                "eight_block_decision"
            ][
                "equivalence_pass_rate"
            ]
        ),
        "light_mean_estimate": (
            arms[
                "LIGHT_OBSERVER"
            ][
                "eight_block_decision"
            ][
                "mean_estimate_ms"
            ]
        ),
        "heavy_mean_estimate": (
            arms[
                "HEAVY_OBSERVER"
            ][
                "eight_block_decision"
            ][
                "mean_estimate_ms"
            ]
        ),
    }

    if actual != frozen:
        raise RuntimeError(
            (
                "frozen_aba_panel_"
                f"changed:{actual}"
            )
        )

    return {
        "schema": SCHEMA,
        "status": "PASS",
        "classification": (
            "SYNTHETIC_OBSERVER_PERTURBATION_ABA_PROTOCOL_VALIDATED"
        ),
        "model": {
            "segment_positions": (
                "A1=t0, B=t1, A2=t2"
            ),
            "linear_drift_model": (
                "y(t)=mu+beta*t+delta*I_B+epsilon"
            ),
            "aba_estimator": (
                "delta_hat=B-(A1+A2)/2"
            ),
            "property": (
                "linear beta drift cancels exactly in expectation"
            ),
        },
        "fixture": {
            "episodes": EPISODES,
            "frames_per_segment": (
                FRAMES_PER_SEGMENT
            ),
            "blocks_per_decision": (
                BLOCKS_PER_DECISION
            ),
            "synthetic_baseline_ms": (
                100.0
            ),
            "equivalence_margin_ms": (
                EQUIVALENCE_MARGIN_MS
            ),
            "equivalence_margin_relative_to_100ms_baseline": (
                EQUIVALENCE_MARGIN_MS
                / 100.0
            ),
        },
        "arms": arms,
        "null_false_perturbation_by_blocks": (
            false_perturbation
        ),
        "protocol": [
            "freeze scene/map/backend/power-state identity",
            "run A1 without observer",
            "run B with observer",
            "run A2 without observer",
            "estimate B-(A1+A2)/2",
            "repeat multiple blocks",
            "pre-register equivalence margin before looking at B",
            "qualify observer only if mean/tail/RSS/CPU/logging budgets all pass",
        ],
        "primary_findings": [
            "A_B_A_INTERPOLATION_REDUCES_LINEAR_DRIFT_CONFOUNDING",
            "ONE_ABA_BLOCK_IS_STILL_TOO_NOISY_FOR_A_TIGHT_LOW_END_PERTURBATION_GATE",
            "REPEATED_MATCHED_BLOCKS_ARE_REQUIRED",
            "OBSERVER_EQUIVALENCE_MARGIN_MUST_BE_PRE_REGISTERED",
            "READ_ONLY_DOES_NOT_MEAN_ZERO_PERTURBATION",
        ],
        "claim_ceiling": (
            "SYNTHETIC_OBSERVER_PERTURBATION_PROTOCOL_ONLY"
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
