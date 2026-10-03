from __future__ import annotations

import json
from dataclasses import dataclass


SCHEMA = "finite-ram-lab.ksla-bounded-idiocy/v0.1"

BLIND_PROB = 0.15
EXPERT_COST = 8
IDIOT_COST = 1
BUDGET = 16
LAMBDA_COST = 0.39
MC_EPISODES = 200_000

EXPERT_NORMAL_REWARD = 8.0
EXPERT_BLIND_REWARD = 0.0

IDIOT_PMF = (
    (0.0, 0.80),
    (2.0, 0.17),
    (20.0, 0.03),
)


@dataclass(frozen=True)
class Composition:
    experts: int
    idiots: int

    @property
    def cost(self) -> int:
        return (
            self.experts * EXPERT_COST
            + self.idiots * IDIOT_COST
        )


def _validate_pmf(
    pmf: tuple[tuple[float, float], ...],
) -> None:
    if abs(
        sum(prob for _, prob in pmf) - 1.0
    ) > 1e-12:
        raise ValueError("pmf_not_normalized")


def _iid_max_distribution(
    pmf: tuple[tuple[float, float], ...],
    count: int,
) -> tuple[tuple[float, float], ...]:
    _validate_pmf(pmf)

    if count == 0:
        return ((0.0, 1.0),)

    rows = sorted(pmf)
    cumulative = 0.0
    previous = 0.0
    result: list[tuple[float, float]] = []

    for reward, probability in rows:
        cumulative += probability

        mass = (
            cumulative**count
            - previous**count
        )

        result.append(
            (reward, mass)
        )

        previous = cumulative

    return tuple(result)


def expected_progress(
    composition: Composition,
    *,
    blind_prob: float = BLIND_PROB,
    idiot_pmf: tuple[
        tuple[float, float],
        ...
    ] = IDIOT_PMF,
) -> float:
    if composition.experts not in (0, 1):
        raise ValueError(
            "toy_model_allows_zero_or_one_expert"
        )

    idiot_max = _iid_max_distribution(
        idiot_pmf,
        composition.idiots,
    )

    normal_expert = (
        EXPERT_NORMAL_REWARD
        if composition.experts
        else 0.0
    )

    blind_expert = (
        EXPERT_BLIND_REWARD
        if composition.experts
        else 0.0
    )

    normal = sum(
        probability
        * max(
            normal_expert,
            idiot_reward,
        )
        for idiot_reward, probability
        in idiot_max
    )

    blind = sum(
        probability
        * max(
            blind_expert,
            idiot_reward,
        )
        for idiot_reward, probability
        in idiot_max
    )

    return (
        (1.0 - blind_prob) * normal
        + blind_prob * blind
    )


def utility(
    composition: Composition,
    *,
    lambda_cost: float = LAMBDA_COST,
) -> float:
    return (
        expected_progress(composition)
        - lambda_cost
        * composition.cost
    )


def feasible_compositions() -> list[Composition]:
    rows: list[Composition] = []

    for experts in (0, 1):
        for idiots in range(
            0,
            BUDGET + 1,
        ):
            composition = Composition(
                experts=experts,
                idiots=idiots,
            )

            if (
                composition.cost == 0
                or composition.cost > BUDGET
            ):
                continue

            rows.append(composition)

    return rows


def analytic_panel() -> dict:
    rows = []

    for composition in (
        feasible_compositions()
    ):
        rows.append(
            {
                "experts": (
                    composition.experts
                ),
                "idiots": (
                    composition.idiots
                ),
                "cost": (
                    composition.cost
                ),
                "expected_progress": (
                    expected_progress(
                        composition
                    )
                ),
                "utility": utility(
                    composition
                ),
            }
        )

    best_progress = max(
        rows,
        key=lambda row: (
            row["expected_progress"],
            -row["cost"],
        ),
    )

    best_utility = max(
        rows,
        key=lambda row: (
            row["utility"],
            -row["cost"],
        ),
    )

    expert_only = next(
        row
        for row in rows
        if row[
            "experts"
        ] == 1
        and row[
            "idiots"
        ] == 0
    )

    best_idiot_only = max(
        (
            row
            for row in rows
            if row[
                "experts"
            ] == 0
        ),
        key=lambda row: row[
            "utility"
        ],
    )

    dominated_idiot_pmf = (
        (0.0, 0.85),
        (2.0, 0.15),
    )

    dominated_marginal = (
        expected_progress(
            Composition(1, 1),
            blind_prob=0.0,
            idiot_pmf=dominated_idiot_pmf,
        )
        - expected_progress(
            Composition(1, 0),
            blind_prob=0.0,
            idiot_pmf=dominated_idiot_pmf,
        )
    )

    return {
        "rows": rows,
        "best_expected_progress": (
            best_progress
        ),
        "best_utility": (
            best_utility
        ),
        "expert_only": (
            expert_only
        ),
        "best_idiot_only": (
            best_idiot_only
        ),
        "dominated_idiot_control": {
            "blind_prob": 0.0,
            "idiot_pmf": [
                {
                    "reward": reward,
                    "probability": probability,
                }
                for reward, probability
                in dominated_idiot_pmf
            ],
            "marginal_progress_of_first_idiot": (
                dominated_marginal
            ),
            "positive_cost_means_reject": (
                dominated_marginal == 0.0
            ),
        },
    }


def swap_value_formula() -> dict:
    return {
        "old": (
            "E[max(E_1..E_e,I_1..I_k)]"
        ),
        "replace_one_expert_with_idiot": (
            "integral F_E(y)^(e-1) * F_I(y)^k * (F_E(y)-F_I(y)) dy"
        ),
        "interpretation": (
            "idiot substitution has positive progress value exactly where its upper-tail CDF advantage outweighs the expert CDF after current portfolio weighting"
        ),
    }


def blind_spot_tail_formula() -> dict:
    return {
        "model": (
            "expert reward g in normal state, 0 in blind state; idiot reward H with probability p else 0"
        ),
        "blind_probability": "q",
        "expected_progress_one_expert_k_idiots": (
            "H - (H-(1-q)g)*(1-p)^k"
        ),
        "marginal_value_next_idiot": (
            "p*(1-p)^k*(H-(1-q)g)"
        ),
        "cost_stop_rule": (
            "add next idiot while marginal_value > lambda_cost*c_idiot"
        ),
        "core_result": (
            "positive idiocy can be optimal, but its marginal value decays geometrically"
        ),
    }


def _mix64(value: int) -> int:
    value &= (1 << 64) - 1
    value ^= value >> 30
    value = (
        value
        * 0xBF58476D1CE4E5B9
    ) & ((1 << 64) - 1)
    value ^= value >> 27
    value = (
        value
        * 0x94D049BB133111EB
    ) & ((1 << 64) - 1)
    value ^= value >> 31
    return value


def _uniform(
    episode: int,
    slot: int,
) -> float:
    value = _mix64(
        0x4B534C4130303200
        ^ (episode * 0x9E3779B97F4A7C15)
        ^ (slot * 0xD1B54A32D192ED03)
    )

    return (
        value >> 11
    ) / float(1 << 53)


def _idiot_reward(
    episode: int,
    slot: int,
) -> float:
    draw = _uniform(
        episode,
        slot + 1,
    )

    cumulative = 0.0

    for reward, probability in (
        IDIOT_PMF
    ):
        cumulative += probability

        if draw < cumulative:
            return reward

    return IDIOT_PMF[-1][0]


def monte_carlo_panel() -> dict:
    compositions = (
        feasible_compositions()
    )

    sums = {
        composition: 0.0
        for composition in compositions
    }

    for episode in range(
        MC_EPISODES
    ):
        blind = (
            _uniform(
                episode,
                0,
            )
            < BLIND_PROB
        )

        expert_reward = (
            EXPERT_BLIND_REWARD
            if blind
            else EXPERT_NORMAL_REWARD
        )

        idiot_prefix_max = [0.0]
        current = 0.0

        for slot in range(BUDGET):
            current = max(
                current,
                _idiot_reward(
                    episode,
                    slot,
                ),
            )
            idiot_prefix_max.append(
                current
            )

        for composition in (
            compositions
        ):
            expert = (
                expert_reward
                if composition.experts
                else 0.0
            )

            reward = max(
                expert,
                idiot_prefix_max[
                    composition.idiots
                ],
            )

            sums[
                composition
            ] += reward

    rows = []

    for composition in compositions:
        mean = (
            sums[composition]
            / MC_EPISODES
        )

        analytic = expected_progress(
            composition
        )

        rows.append(
            {
                "experts": (
                    composition.experts
                ),
                "idiots": (
                    composition.idiots
                ),
                "cost": (
                    composition.cost
                ),
                "mean_progress": mean,
                "analytic_progress": analytic,
                "absolute_error": abs(
                    mean - analytic
                ),
                "utility": (
                    mean
                    - LAMBDA_COST
                    * composition.cost
                ),
            }
        )

    selected = {
        (row["experts"], row["idiots"]): row
        for row in rows
    }

    return {
        "episodes": MC_EPISODES,
        "matched_random_tape": True,
        "max_absolute_analytic_error": max(
            row["absolute_error"]
            for row in rows
        ),
        "selected": {
            "expert_only": selected[
                (1, 0)
            ],
            "bounded_idiocy": selected[
                (1, 3)
            ],
            "full_budget_mixed": selected[
                (1, 8)
            ],
            "pure_idiot_16": selected[
                (0, 16)
            ],
        },
    }


def run_panel() -> dict:
    analytic = analytic_panel()
    monte_carlo = (
        monte_carlo_panel()
    )

    best_progress = analytic[
        "best_expected_progress"
    ]

    best_utility = analytic[
        "best_utility"
    ]

    if (
        best_progress["experts"],
        best_progress["idiots"],
    ) != (1, 8):
        raise RuntimeError(
            "hard_budget_mix_reference_changed"
        )

    if (
        best_utility["experts"],
        best_utility["idiots"],
    ) != (1, 3):
        raise RuntimeError(
            "bounded_idiocy_reference_changed"
        )

    if (
        monte_carlo[
            "max_absolute_analytic_error"
        ]
        > 0.08
    ):
        raise RuntimeError(
            "monte_carlo_analytic_mismatch"
        )

    selected = monte_carlo[
        "selected"
    ]

    if (
        selected[
            "bounded_idiocy"
        ]["utility"]
        <= selected[
            "expert_only"
        ]["utility"]
    ):
        raise RuntimeError(
            "bounded_idiocy_failed_to_beat_expert_control"
        )

    if (
        selected[
            "bounded_idiocy"
        ]["utility"]
        <= selected[
            "pure_idiot_16"
        ]["utility"]
    ):
        raise RuntimeError(
            "bounded_idiocy_failed_to_beat_idiot_control"
        )

    if not analytic[
        "dominated_idiot_control"
    ][
        "positive_cost_means_reject"
    ]:
        raise RuntimeError(
            "dominated_idiot_control_failed"
        )

    return {
        "schema": SCHEMA,
        "status": "PASS",
        "classification": (
            "ANALYTIC_PLUS_MATCHED_MONTE_CARLO_BOUNDED_IDIOCY_VALIDATED"
        ),
        "hypothesis": (
            "A SMALL POSITIVE IDIOT SHARE CAN BE OPTIMAL WHEN CHEAP RANDOM PROPOSALS COVER EXPERT BLIND SPOTS OR UPPER-TAIL OPPORTUNITIES, BUT IDIOCY HAS DIMINISHING MARGINAL VALUE AND MUST BE PRICED."
        ),
        "toy_parameters": {
            "blind_probability": (
                BLIND_PROB
            ),
            "expert_cost": (
                EXPERT_COST
            ),
            "idiot_cost": (
                IDIOT_COST
            ),
            "budget": BUDGET,
            "lambda_cost": (
                LAMBDA_COST
            ),
            "expert_normal_reward": (
                EXPERT_NORMAL_REWARD
            ),
            "expert_blind_reward": (
                EXPERT_BLIND_REWARD
            ),
            "idiot_pmf": [
                {
                    "reward": reward,
                    "probability": probability,
                }
                for reward, probability
                in IDIOT_PMF
            ],
        },
        "analytic": analytic,
        "swap_value_formula": (
            swap_value_formula()
        ),
        "blind_spot_tail_formula": (
            blind_spot_tail_formula()
        ),
        "monte_carlo": monte_carlo,
        "primary_findings": [
            "PURE_EXPERT_CAN_BE_BLIND",
            "PURE_IDIOT_CAN_BE_TOO_WASTEFUL",
            "BOUNDED_IDIOCY_CAN_DOMINATE_BOTH_EXTREMES_UNDER_A_RESOURCE_PRICE",
            "IDIOT_VALUE_COMES_FROM_COMPLEMENTARY_SUPPORT_OR_UPPER_TAIL_NOT_FROM_LOW_MEAN_QUALITY",
            "IDIOT_MARGINAL_VALUE_DECAYS_SO_UNBOUNDED_IDIOCY_IS_NOT_JUSTIFIED",
            "MATCHED_RANDOM_TAPES_ARE_REQUIRED_FOR_POLICY_COMPARISON",
        ],
        "claim_ceiling": (
            "TOY_ANALYTIC_AND_MATCHED_MONTE_CARLO_BOUNDED_IDIOCY_ONLY"
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
