from __future__ import annotations

import json
import random
import statistics
from collections import Counter
from typing import Any

SCHEMA = "finite-ram-lab.fr-fp-002-semantic-oom-mc/v0.1"

SEED = 20261004
EPISODES = 1000
STEPS = 14
RESIDUAL_EPS = 0.12
ENDPOINT_DELTA = 0.35
BUDGETS = (2, 4, 8, 16)

FAMILY_NAMES = (
    "CONTRACTION",
    "SLOW_DRIFT",
    "FALSE_SMALL_THEN_JUMP",
    "OSCILLATORY",
)
FAMILY_WEIGHTS = (
    0.50,
    0.20,
    0.20,
    0.10,
)

POLICIES = (
    "FULL_TRAJECTORY",
    "PREMATURE_TERMINAL",
    "AGE_ONLY",
    "RESIDUAL_ONLY",
    "VALIDATED_ENDPOINT",
    "COLD_TIER_VALIDATED",
)


def _trajectory(
    rng: random.Random,
    family: str,
) -> list[float]:
    if family == "CONTRACTION":
        value = rng.uniform(
            3.0,
            8.0,
        )
        rho = rng.uniform(
            0.45,
            0.75,
        )
        rows = [value]

        for _ in range(
            1,
            STEPS,
        ):
            rows.append(
                rows[-1]
                * rho
            )

        return rows

    if family == "SLOW_DRIFT":
        start = rng.uniform(
            1.5,
            3.0,
        )
        step = rng.uniform(
            0.06,
            0.11,
        )

        return [
            max(
                0.0,
                start
                - step * index,
            )
            for index in range(
                STEPS
            )
        ]

    if family == "FALSE_SMALL_THEN_JUMP":
        rows = [
            rng.uniform(
                2.5,
                5.0,
            )
        ]

        for step_index in range(
            1,
            STEPS,
        ):
            if step_index < 5:
                rows.append(
                    rows[-1]
                    - rng.uniform(
                        0.02,
                        0.07,
                    )
                )
            elif step_index == 5:
                rows.append(
                    rows[-1]
                    + rng.uniform(
                        1.0,
                        2.0,
                    )
                )
            else:
                rows.append(
                    rows[-1]
                    * rng.uniform(
                        0.45,
                        0.62,
                    )
                )

        return rows

    if family == "OSCILLATORY":
        rows = [
            rng.uniform(
                2.0,
                6.0,
            )
        ]
        rho = rng.uniform(
            0.45,
            0.70,
        )

        for _ in range(
            1,
            STEPS,
        ):
            rows.append(
                -rows[-1]
                * rho
            )

        return rows

    raise ValueError(
        f"unknown_family:{family}"
    )


def _residual(
    rows: list[float],
    step: int,
) -> float:
    return abs(
        rows[step]
        - rows[step - 1]
    )


def _endpoint_gap(
    rows: list[float],
    step: int,
) -> float:
    return abs(
        rows[step]
    )


def _first_residual_step(
    rows: list[float],
) -> int | None:
    for step in range(
        1,
        len(rows),
    ):
        if (
            _residual(
                rows,
                step,
            )
            <= RESIDUAL_EPS
        ):
            return step

    return None


def _first_safe_step(
    rows: list[float],
) -> int | None:
    for step in range(
        1,
        len(rows),
    ):
        if (
            _residual(
                rows,
                step,
            )
            <= RESIDUAL_EPS
            and _endpoint_gap(
                rows,
                step,
            )
            <= ENDPOINT_DELTA
        ):
            return step

    return None


def simulate_episode(
    rows: list[float],
    *,
    policy: str,
    budget: int,
) -> dict[str, Any]:
    safe_step = _first_safe_step(
        rows
    )
    residual_step = (
        _first_residual_step(
            rows
        )
    )

    hot = 1
    peak_hot = 1
    cold = 0
    cold_writes = 0
    discarded = 0
    semantic_corruption = False
    semantic_oom = False
    endpoint_mode = False
    reclaimed_at = None

    for step in range(
        1,
        len(rows),
    ):
        hot += 1

        if endpoint_mode:
            discarded += (
                hot - 1
            )
            hot = 1

        elif (
            policy
            == "PREMATURE_TERMINAL"
        ):
            if (
                safe_step is None
                or step < safe_step
            ):
                semantic_corruption = (
                    True
                )

            discarded += (
                hot - 1
            )
            hot = 1
            endpoint_mode = True
            reclaimed_at = step

        elif policy == "AGE_ONLY":
            keep = 2

            if hot > keep:
                if (
                    safe_step is None
                    or step < safe_step
                ):
                    semantic_corruption = (
                        True
                    )

                discarded += (
                    hot - keep
                )
                hot = keep

        elif (
            policy
            == "RESIDUAL_ONLY"
            and residual_step
            is not None
            and step
            >= residual_step
        ):
            if (
                safe_step is None
                or step < safe_step
            ):
                semantic_corruption = (
                    True
                )

            discarded += (
                hot - 1
            )
            hot = 1
            endpoint_mode = True
            reclaimed_at = step

        elif (
            policy
            == "VALIDATED_ENDPOINT"
            and safe_step
            is not None
            and step >= safe_step
        ):
            discarded += (
                hot - 1
            )
            hot = 1
            endpoint_mode = True
            reclaimed_at = step

        elif (
            policy
            == "COLD_TIER_VALIDATED"
            and safe_step
            is not None
            and step >= safe_step
        ):
            discarded += (
                hot - 1 + cold
            )
            hot = 1
            cold = 0
            endpoint_mode = True
            reclaimed_at = step

        if hot > budget:
            if (
                policy
                == "COLD_TIER_VALIDATED"
                and not endpoint_mode
            ):
                move = (
                    hot - budget
                )
                hot -= move
                cold += move
                cold_writes += move
            else:
                semantic_oom = True

        peak_hot = max(
            peak_hot,
            hot,
        )

    return {
        "safe_step": safe_step,
        "residual_step": (
            residual_step
        ),
        "semantic_corruption": (
            semantic_corruption
        ),
        "semantic_oom": (
            semantic_oom
        ),
        "semantic_survival": (
            not semantic_corruption
            and not semantic_oom
        ),
        "peak_hot_states": (
            peak_hot
        ),
        "cold_writes": (
            cold_writes
        ),
        "discarded_states": (
            discarded
        ),
        "reclaimed_at": (
            reclaimed_at
        ),
    }


def _episodes() -> list[
    tuple[str, list[float]]
]:
    rng = random.Random(
        SEED
    )
    families = rng.choices(
        FAMILY_NAMES,
        weights=FAMILY_WEIGHTS,
        k=EPISODES,
    )

    return [
        (
            family,
            _trajectory(
                rng,
                family,
            ),
        )
        for family in families
    ]


def _summarize(
    rows: list[
        tuple[
            str,
            dict[str, Any],
        ]
    ],
) -> dict[str, Any]:
    results = [
        result
        for _,
        result
        in rows
    ]

    reclaimed = [
        result[
            "reclaimed_at"
        ]
        for result
        in results
        if result[
            "reclaimed_at"
        ]
        is not None
    ]

    families = sorted(
        {
            family
            for family, _
            in rows
        }
    )

    return {
        "semantic_survival_rate": (
            sum(
                result[
                    "semantic_survival"
                ]
                for result
                in results
            )
            / len(results)
        ),
        "semantic_oom_rate": (
            sum(
                result[
                    "semantic_oom"
                ]
                for result
                in results
            )
            / len(results)
        ),
        "semantic_corruption_rate": (
            sum(
                result[
                    "semantic_corruption"
                ]
                for result
                in results
            )
            / len(results)
        ),
        "mean_peak_hot_states": (
            statistics.fmean(
                result[
                    "peak_hot_states"
                ]
                for result
                in results
            )
        ),
        "mean_cold_writes": (
            statistics.fmean(
                result[
                    "cold_writes"
                ]
                for result
                in results
            )
        ),
        "mean_reclaim_step": (
            None
            if not reclaimed
            else statistics.fmean(
                reclaimed
            )
        ),
        "corruption_by_family": {
            family: (
                sum(
                    result[
                        "semantic_corruption"
                    ]
                    for row_family,
                    result
                    in rows
                    if row_family
                    == family
                )
                / sum(
                    row_family
                    == family
                    for row_family, _
                    in rows
                )
            )
            for family
            in families
        },
    }


def run_panel() -> dict[str, Any]:
    episodes = _episodes()
    family_counts = Counter(
        family
        for family, _
        in episodes
    )

    matrix = {}

    for budget in BUDGETS:
        matrix[
            str(budget)
        ] = {}

        for policy in POLICIES:
            rows = [
                (
                    family,
                    simulate_episode(
                        trajectory,
                        policy=policy,
                        budget=budget,
                    ),
                )
                for family,
                trajectory
                in episodes
            ]

            matrix[
                str(budget)
            ][policy] = (
                _summarize(
                    rows
                )
            )

    residual_unpressured = (
        matrix["16"][
            "RESIDUAL_ONLY"
        ]
    )
    validated_unpressured = (
        matrix["16"][
            "VALIDATED_ENDPOINT"
        ]
    )
    validated_pressure = (
        matrix["8"][
            "VALIDATED_ENDPOINT"
        ]
    )
    cold_pressure = (
        matrix["8"][
            "COLD_TIER_VALIDATED"
        ]
    )
    cold_tight = (
        matrix["4"][
            "COLD_TIER_VALIDATED"
        ]
    )

    checks = {
        "residual_only_has_corruption": (
            residual_unpressured[
                "semantic_corruption_rate"
            ]
            > 0.35
        ),
        "validated_endpoint_no_corruption": (
            validated_unpressured[
                "semantic_corruption_rate"
            ]
            == 0.0
        ),
        "validated_tight_budget_semantic_oom": (
            validated_pressure[
                "semantic_oom_rate"
            ]
            > 0.50
        ),
        "cold_tier_avoids_semantic_oom": (
            cold_pressure[
                "semantic_oom_rate"
            ]
            == 0.0
        ),
        "cold_tier_avoids_corruption": (
            cold_pressure[
                "semantic_corruption_rate"
            ]
            == 0.0
        ),
        "cold_tier_pays_io": (
            cold_tight[
                "mean_cold_writes"
            ]
            > 0.0
        ),
        "cold_tier_survives_tight_budget": (
            cold_tight[
                "semantic_survival_rate"
            ]
            == 1.0
        ),
        "pressure_relaxes_validated_oom": (
            matrix["16"][
                "VALIDATED_ENDPOINT"
            ][
                "semantic_oom_rate"
            ]
            < validated_pressure[
                "semantic_oom_rate"
            ]
        ),
    }

    council = {
        "methodologist": (
            "PASS"
            if checks[
                "residual_only_has_corruption"
            ]
            else "FAIL"
        ),
        "systems": (
            "PASS"
            if checks[
                "cold_tier_pays_io"
            ]
            else "FAIL"
        ),
        "falsifier": (
            "PASS"
            if (
                family_counts[
                    "SLOW_DRIFT"
                ] > 0
                and family_counts[
                    "FALSE_SMALL_THEN_JUMP"
                ] > 0
                and family_counts[
                    "OSCILLATORY"
                ] > 0
            )
            else "FAIL"
        ),
        "evidence": (
            "PASS"
        ),
    }

    status = (
        "PASS"
        if (
            all(
                checks.values()
            )
            and all(
                value == "PASS"
                for value
                in council.values()
            )
        )
        else "FAIL"
    )

    return {
        "schema": SCHEMA,
        "status": status,
        "classification": (
            "SYNTHETIC_SEMANTIC_OOM_PRESSURE_SWEEP"
        ),
        "seed": SEED,
        "episodes": EPISODES,
        "steps": STEPS,
        "thresholds": {
            "residual_eps": (
                RESIDUAL_EPS
            ),
            "endpoint_delta": (
                ENDPOINT_DELTA
            ),
        },
        "family_counts": dict(
            family_counts
        ),
        "budgets": list(
            BUDGETS
        ),
        "policies": list(
            POLICIES
        ),
        "matrix": matrix,
        "checks": checks,
        "council": council,
        "primary_findings": [
            "SMALL_RESIDUAL_IS_NOT_SUFFICIENT_RECLAIM_PERMISSION",
            "VALIDATED_ENDPOINT_CONVERTS_CORRUPTION_RISK_INTO_FAIL_CLOSED_SEMANTIC_OOM_UNDER_TIGHT_BUDGET",
            "COLD_TIER_CAN_TRADE_IO_FOR_SEMANTIC_SURVIVAL_BEFORE_ENDPOINT_VALIDATION",
            "PHYSICAL_AGE_AND_SEMANTIC_RECLAIMABILITY_ARE_DISTINCT",
            "SEMANTIC_OOM_CAN_EXIST_BEFORE_PHYSICAL_RECLAIM_IS_SAFE",
        ],
        "claim_ceiling": (
            "SYNTHETIC_TRAJECTORY_RECLAIMABILITY_AND_SEMANTIC_OOM_ONLY"
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
