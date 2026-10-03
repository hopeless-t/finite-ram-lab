from __future__ import annotations

import json
from fractions import Fraction
from math import inf
from typing import Iterable


SCHEMA = "finite-ram-lab.ksla-swarm-width-model/v0.1"

KSLA002_ARMS = {
    1: {"rounds": 2753, "proposals": 2753},
    4: {"rounds": 635, "proposals": 2540},
    8: {"rounds": 305, "proposals": 2440},
    16: {"rounds": 232, "proposals": 3712},
    32: {"rounds": 185, "proposals": 5920},
    64: {"rounds": 155, "proposals": 9920},
    128: {"rounds": 122, "proposals": 15616},
}

TOY_PMF = (
    (0.0, 0.75),
    (1.0, 0.15),
    (4.0, 0.08),
    (10.0, 0.02),
)


def _validate_pmf(
    pmf: Iterable[tuple[float, float]],
) -> tuple[tuple[float, float], ...]:
    rows = tuple(sorted(pmf))

    if not rows:
        raise ValueError("empty_pmf")

    probability = sum(
        p
        for _, p in rows
    )

    if abs(probability - 1.0) > 1e-12:
        raise ValueError(
            f"pmf_not_normalized:{probability}"
        )

    if any(
        reward < 0.0
        or p < 0.0
        for reward, p in rows
    ):
        raise ValueError(
            "pmf_must_be_nonnegative"
        )

    return rows


def expected_best_of_batch(
    pmf: Iterable[tuple[float, float]],
    batch: int,
) -> float:
    if batch < 1:
        raise ValueError(
            "batch_must_be_positive"
        )

    rows = _validate_pmf(pmf)

    cumulative = 0.0
    previous_cdf = 0.0
    expectation = 0.0

    for reward, probability in rows:
        cumulative += probability

        max_probability = (
            cumulative**batch
            - previous_cdf**batch
        )

        expectation += (
            reward
            * max_probability
        )

        previous_cdf = cumulative

    return expectation


def marginal_batch_gain(
    pmf: Iterable[tuple[float, float]],
    batch: int,
) -> float:
    if batch < 1:
        raise ValueError(
            "batch_must_be_positive"
        )

    if batch == 1:
        return expected_best_of_batch(
            pmf,
            1,
        )

    return (
        expected_best_of_batch(
            pmf,
            batch,
        )
        - expected_best_of_batch(
            pmf,
            batch - 1,
        )
    )


def toy_diminishing_returns() -> dict:
    expected = {
        batch: expected_best_of_batch(
            TOY_PMF,
            batch,
        )
        for batch in range(
            1,
            65,
        )
    }

    marginal = {
        batch: marginal_batch_gain(
            TOY_PMF,
            batch,
        )
        for batch in range(
            1,
            65,
        )
    }

    monotone = all(
        marginal[batch + 1]
        <= marginal[batch] + 1e-12
        for batch in range(
            1,
            64,
        )
    )

    fixed_cost = 10.0
    per_proposal_cost = 1.0

    efficiency = {
        batch: (
            expected[batch]
            / (
                fixed_cost
                + per_proposal_cost
                * batch
            )
        )
        for batch in expected
    }

    best_batch = max(
        efficiency,
        key=efficiency.get,
    )

    return {
        "pmf": [
            {
                "improvement": reward,
                "probability": probability,
            }
            for reward, probability
            in TOY_PMF
        ],
        "expected_best": expected,
        "marginal_gain": marginal,
        "marginal_gain_nonincreasing": (
            monotone
        ),
        "cost_model": {
            "fixed_cost": fixed_cost,
            "per_proposal_cost": (
                per_proposal_cost
            ),
        },
        "best_efficiency_batch": (
            best_batch
        ),
        "best_efficiency": (
            efficiency[best_batch]
        ),
    }


def _pair_breakpoint(
    left_batch: int,
    right_batch: int,
) -> Fraction | None:
    left = KSLA002_ARMS[
        left_batch
    ]

    right = KSLA002_ARMS[
        right_batch
    ]

    denominator = (
        left["rounds"]
        - right["rounds"]
    )

    if denominator == 0:
        return None

    numerator = (
        right["proposals"]
        - left["proposals"]
    )

    value = Fraction(
        numerator,
        denominator,
    )

    if value < 0:
        return None

    return value


def ksla002_cost_envelope() -> dict:
    batches = sorted(
        KSLA002_ARMS
    )

    breakpoints = {
        Fraction(0, 1)
    }

    for index, left in enumerate(
        batches
    ):
        for right in batches[
            index + 1 :
        ]:
            point = _pair_breakpoint(
                left,
                right,
            )

            if point is not None:
                breakpoints.add(
                    point
                )

    points = sorted(
        breakpoints
    )

    intervals: list[
        tuple[
            Fraction,
            Fraction | None,
            int,
        ]
    ] = []

    for index, lower in enumerate(
        points
    ):
        upper = (
            points[index + 1]
            if index + 1
            < len(points)
            else None
        )

        if upper is None:
            sample = (
                float(lower)
                + max(
                    1.0,
                    float(lower)
                    * 0.1,
                )
            )
        else:
            sample = (
                float(lower)
                + float(upper)
            ) / 2.0

        objective = {
            batch: (
                row["proposals"]
                + sample
                * row["rounds"]
            )
            for batch, row in (
                KSLA002_ARMS.items()
            )
        }

        best = min(
            objective,
            key=objective.get,
        )

        if (
            intervals
            and intervals[-1][2]
            == best
            and intervals[-1][1]
            == lower
        ):
            previous = intervals[-1]

            intervals[-1] = (
                previous[0],
                upper,
                best,
            )
        else:
            intervals.append(
                (
                    lower,
                    upper,
                    best,
                )
            )

    active = [
        interval
        for interval in intervals
        if interval[2]
        in {
            8,
            16,
            32,
            64,
            128,
        }
    ]

    expected = [
        (
            Fraction(0, 1),
            Fraction(
                1272,
                73,
            ),
            8,
        ),
        (
            Fraction(
                1272,
                73,
            ),
            Fraction(
                2208,
                47,
            ),
            16,
        ),
        (
            Fraction(
                2208,
                47,
            ),
            Fraction(
                400,
                3,
            ),
            32,
        ),
        (
            Fraction(
                400,
                3,
            ),
            Fraction(
                5696,
                33,
            ),
            64,
        ),
        (
            Fraction(
                5696,
                33,
            ),
            None,
            128,
        ),
    ]

    if active != expected:
        raise RuntimeError(
            f"cost_envelope_changed:{active}"
        )

    return {
        "objective": (
            "J(batch)=proposals+lambda_round*rounds"
        ),
        "lambda_interpretation": (
            "cost_of_one_serial_round_in_proposal-equivalent_units"
        ),
        "frontier": [
            {
                "batch": batch,
                "rounds": row[
                    "rounds"
                ],
                "proposals": row[
                    "proposals"
                ],
            }
            for batch, row in sorted(
                KSLA002_ARMS.items()
            )
        ],
        "optimal_intervals": [
            {
                "lambda_lower": (
                    float(lower)
                ),
                "lambda_lower_exact": (
                    f"{lower.numerator}/{lower.denominator}"
                ),
                "lambda_upper": (
                    None
                    if upper is None
                    else float(upper)
                ),
                "lambda_upper_exact": (
                    None
                    if upper is None
                    else (
                        f"{upper.numerator}/{upper.denominator}"
                    )
                ),
                "optimal_batch": batch,
            }
            for lower, upper, batch
            in active
        ],
        "dominated_batches": [
            1,
            4,
        ],
    }


def model_equations() -> dict:
    return {
        "state_potential": (
            "V(s)>=0"
        ),
        "single_proposal_improvement": (
            "Y=max(0,V(s)-V(T(s,A)))"
        ),
        "batch_progress": (
            "G_b=max(Y_1,...,Y_b)"
        ),
        "cdf": (
            "P(G_b<=y)=F_s(y)^b"
        ),
        "expected_progress": (
            "E[G_b]=integral_0^inf(1-F_s(y)^b)dy"
        ),
        "marginal_gain": (
            "Delta_b=integral_0^inf F_s(y)^b(1-F_s(y))dy"
        ),
        "accept_probability": (
            "P(G_b>0)=1-(1-p_s)^b"
        ),
        "cost": (
            "C_s(b)=c_fixed+b*c_validate+c_apply*P(G_b>0)+c_queue(b)+resource_prices"
        ),
        "local_efficiency": (
            "eta_s(b)=E[G_b]/C_s(b)"
        ),
        "heterogeneous_progress": (
            "E[G_bvec]=integral_0^inf(1-product_a F_a,s(y)^b_a)dy"
        ),
        "bellman": (
            "J(s)=min_bvec C(s,bvec)+E[J(next_state)]"
        ),
    }


def experiment_design_correction() -> dict:
    return {
        "problem": (
            "KSLA-002 used batch-specific action draw domains, so different swarm widths did not observe nested prefixes of one common proposal stream."
        ),
        "fix": (
            "Use common-random-number proposal tapes. For a round, batch b receives the first b proposals from the same frozen tape."
        ),
        "reason": (
            "This converts batch-width comparisons into matched counterfactuals and reduces random-stream confounding."
        ),
        "frozen_identity": (
            "seed + round_id + proposal_index + action_family + distribution parameters"
        ),
    }


def run_panel() -> dict:
    toy = toy_diminishing_returns()
    envelope = (
        ksla002_cost_envelope()
    )

    if not toy[
        "marginal_gain_nonincreasing"
    ]:
        raise RuntimeError(
            "diminishing_returns_failed"
        )

    if toy[
        "best_efficiency_batch"
    ] != 12:
        raise RuntimeError(
            "toy_knee_changed"
        )

    return {
        "schema": SCHEMA,
        "status": "PASS",
        "classification": (
            "ANALYTIC_SWARM_WIDTH_MODEL_VALIDATED"
        ),
        "model": model_equations(),
        "toy_order_statistics": toy,
        "ksla002_empirical_cost_envelope": (
            envelope
        ),
        "experiment_design_correction": (
            experiment_design_correction()
        ),
        "optimizer_guidance": {
            "known_stationary_single_family": (
                "exact order-statistic scan over discrete batch widths"
            ),
            "known_stationary_multiple_families": (
                "marginal-gain-per-cost allocation under resource constraints"
            ),
            "state_dependent_known_model": (
                "dynamic programming / approximate MDP over compressed state buckets"
            ),
            "unknown_or_drifting_action_families": (
                "contextual or cost-aware bandit for online allocation"
            ),
            "tail_and_rare_failure_estimation": (
                "matched-seed Monte Carlo, then importance sampling when rare tails dominate"
            ),
            "expensive_black_box_hyperparameters": (
                "Bayesian optimization after the analytical model defines safe coordinates and constraints"
            ),
        },
        "claim_ceiling": (
            "ANALYTIC_AND_SYNTHETIC_SWARM_WIDTH_MODEL_ONLY"
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
