from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.special import gammaln, logsumexp


@dataclass(frozen=True)
class Design:
    name: str
    fast_n: int
    hold_n: int
    exposure_factor: int


def _log_binom_pmf(x: int, n: int, p: np.ndarray) -> np.ndarray:
    return (
        gammaln(n + 1)
        - gammaln(x + 1)
        - gammaln(n - x + 1)
        + x * np.log(p)
        + (n - x) * np.log1p(-p)
    )


def hold_probability(p_fast: np.ndarray, exposure_factor: int) -> np.ndarray:
    return 1.0 - np.power(1.0 - p_fast, exposure_factor)


def evaluate_design(
    design: Design,
    *,
    p_low: float,
    p_high: float,
    draws: int,
    seed: int,
    grid_points: int = 1000,
) -> dict[str, Any]:
    """Sensitivity MC for TOUCH vs TIME mechanism discrimination.

    The baseline unexplained-deviation probability is sampled log-uniformly.
    This is a design prior, not an empirical posterior.

    TOUCH:
      same number of measured touches -> same per-epoch deviation probability.

    TIME:
      wall-clock exposure is multiplied by F while touch count is held fixed:
      p_hold = 1 - (1 - p_fast)^F.
    """
    rng = np.random.default_rng(seed)
    grid = np.exp(
        np.linspace(math.log(p_low), math.log(p_high), grid_points)
    )

    cache: dict[tuple[int, int, str], float] = {}

    def log_marginal(x_fast: int, x_hold: int, model: str) -> float:
        key = (x_fast, x_hold, model)
        if key in cache:
            return cache[key]

        p_fast = grid
        if model == "TOUCH":
            p_hold = grid
        elif model == "TIME":
            p_hold = hold_probability(grid, design.exposure_factor)
        else:
            raise ValueError(model)

        ll = _log_binom_pmf(
            x_fast, design.fast_n, p_fast
        ) + _log_binom_pmf(
            x_hold, design.hold_n, p_hold
        )
        value = float(logsumexp(ll) - math.log(len(grid)))
        cache[key] = value
        return value

    output: dict[str, Any] = {}
    for true_model in ["TOUCH", "TIME"]:
        p_fast = np.exp(
            rng.uniform(math.log(p_low), math.log(p_high), draws)
        )
        p_hold = (
            p_fast
            if true_model == "TOUCH"
            else hold_probability(p_fast, design.exposure_factor)
        )

        x_fast = rng.binomial(design.fast_n, p_fast)
        x_hold = rng.binomial(design.hold_n, p_hold)

        predicted_time = np.empty(draws, dtype=bool)
        for i, (xf, xh) in enumerate(zip(x_fast, x_hold)):
            predicted_time[i] = (
                log_marginal(int(xf), int(xh), "TIME")
                > log_marginal(int(xf), int(xh), "TOUCH")
            )

        correct = (
            predicted_time
            if true_model == "TIME"
            else np.logical_not(predicted_time)
        )
        output[true_model] = {
            "classification_accuracy": float(np.mean(correct)),
            "any_detection": float(np.mean((x_fast + x_hold) > 0)),
            "hold_detection": float(np.mean(x_hold > 0)),
            "mean_events": float(np.mean(x_fast + x_hold)),
        }

    output["balanced_accuracy"] = (
        output["TOUCH"]["classification_accuracy"]
        + output["TIME"]["classification_accuracy"]
    ) / 2.0
    return output


def evaluate_adaptive(
    *,
    p_low: float,
    p_high: float,
    exposure_factor: int,
    draws: int,
    seed: int,
) -> dict[str, Any]:
    """Stage A = FAST x4 + HOLD32 x12.

    Stage B is opened only when Stage A contains at least one unexplained
    deviation in HOLD32. Stage B = HOLD8/HOLD32/HOLD56 x4 each.
    """
    rng = np.random.default_rng(seed)
    p_fast = np.exp(
        rng.uniform(math.log(p_low), math.log(p_high), draws)
    )

    out: dict[str, Any] = {}
    for true_model in ["TOUCH", "TIME"]:
        p_hold = (
            p_fast
            if true_model == "TOUCH"
            else hold_probability(p_fast, exposure_factor)
        )

        stage_a_fast = rng.binomial(4, p_fast)
        stage_a_hold = rng.binomial(12, p_hold)
        trigger = stage_a_hold > 0

        stage_b = [
            rng.binomial(4, p_hold),
            rng.binomial(4, p_hold),
            rng.binomial(4, p_hold),
        ]
        positions = sum((x > 0).astype(int) for x in stage_b)
        trigger_count = max(int(np.sum(trigger)), 1)

        out[true_model] = {
            "stage_a_trigger_probability": float(np.mean(trigger)),
            "expected_total_identities": float(
                16 + 12 * np.mean(trigger)
            ),
            "stage_b_any_position_event_conditional": float(
                np.sum(np.logical_and(positions >= 1, trigger))
                / trigger_count
            ),
            "stage_b_two_or_more_positions_conditional": float(
                np.sum(np.logical_and(positions >= 2, trigger))
                / trigger_count
            ),
        }

    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--draws", type=int, default=100_000)
    p.add_argument("--seed", type=int, default=41_023)
    args = p.parse_args()

    designs = [
        Design("EQ16_F8", 8, 8, 8),
        Design("EQ16_F16", 8, 8, 16),
        Design("HOLDHEAVY16_F8", 4, 12, 8),
        Design("HOLDHEAVY16_F16", 4, 12, 16),
        Design("HOLDHEAVY20_F16", 4, 16, 16),
        Design("HOLDHEAVY24_F16", 8, 16, 16),
    ]
    priors = {
        "low": (0.001, 0.01),
        "central": (0.002, 0.05),
        "high": (0.01, 0.10),
    }

    result: dict[str, Any] = {
        "schema_version": "tx-age-decoupling-design-mc-v1",
        "draws_per_candidate": args.draws,
        "model_prior": {"TOUCH": 0.5, "TIME": 0.5},
        "baseline_probability_prior": {
            "kind": "log_uniform_sensitivity_not_posterior",
            "ranges": priors,
        },
        "candidate_results": {},
        "adaptive_results": {},
    }

    for p_index, (prior_name, (lo, hi)) in enumerate(priors.items()):
        result["candidate_results"][prior_name] = {}
        for i, design in enumerate(designs):
            result["candidate_results"][prior_name][design.name] = (
                evaluate_design(
                    design,
                    p_low=lo,
                    p_high=hi,
                    draws=args.draws,
                    seed=args.seed + p_index * 100 + i * 17,
                )
            )
        result["adaptive_results"][prior_name] = evaluate_adaptive(
            p_low=lo,
            p_high=hi,
            exposure_factor=16,
            draws=max(args.draws, 100_000),
            seed=args.seed + 1088 + p_index,
        )

    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
