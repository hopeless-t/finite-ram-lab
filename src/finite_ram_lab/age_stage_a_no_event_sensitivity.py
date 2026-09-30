from __future__ import annotations

import argparse
import json
import math
from typing import Any

import numpy as np


def hold_probability(
    p_fast: np.ndarray,
    exposure_factor: float,
) -> np.ndarray:
    return 1.0 - np.power(1.0 - p_fast, exposure_factor)


def no_event_marginals(
    *,
    p_low: float,
    p_high: float,
    exposure_factor: float,
    fast_n: int,
    hold_n: int,
    grid_points: int = 200_000,
) -> dict[str, float]:
    """Integrate a no-event panel over the original B410 log-uniform prior.

    This is a design-sensitivity replay, not an empirical prevalence model.
    """
    if not (0.0 < p_low < p_high < 1.0):
        raise ValueError("require 0 < p_low < p_high < 1")
    if exposure_factor <= 0:
        raise ValueError("exposure_factor must be positive")
    if fast_n < 0 or hold_n < 0:
        raise ValueError("sample counts must be nonnegative")

    p_fast = np.exp(
        np.linspace(
            math.log(p_low),
            math.log(p_high),
            int(grid_points),
        )
    )
    p_hold_time = hold_probability(
        p_fast,
        exposure_factor,
    )

    likelihood_touch = np.power(
        1.0 - p_fast,
        fast_n + hold_n,
    )
    likelihood_time = (
        np.power(1.0 - p_fast, fast_n)
        * np.power(1.0 - p_hold_time, hold_n)
    )

    marginal_touch = float(np.mean(likelihood_touch))
    marginal_time = float(np.mean(likelihood_time))
    denominator = marginal_touch + marginal_time

    return {
        "p_no_event_given_TOUCH": marginal_touch,
        "p_no_event_given_TIME": marginal_time,
        "bayes_factor_TOUCH_over_TIME": (
            marginal_touch / marginal_time
        ),
        "equal_model_weight_TOUCH_after_no_event": (
            marginal_touch / denominator
        ),
        "equal_model_weight_TIME_after_no_event": (
            marginal_time / denominator
        ),
    }


def analyze(
    *,
    exposure_factor: float,
    fast_n: int,
    hold_n: int,
    grid_points: int = 200_000,
) -> dict[str, Any]:
    priors = {
        "low": (0.001, 0.01),
        "central": (0.002, 0.05),
        "high": (0.01, 0.10),
    }
    return {
        "schema_version":
            "age-stage-a-no-event-sensitivity-v1",
        "observed_complete_panel": {
            "FAST": int(fast_n),
            "HOLD32": int(hold_n),
            "unexplained_or_known_hazard_events": 0,
        },
        "realized_exposure_factor": float(
            exposure_factor
        ),
        "prior_warning": (
            "B410 log-uniform ranges are design-sensitivity "
            "priors, not fitted empirical prevalence priors."
        ),
        "results": {
            name: no_event_marginals(
                p_low=lo,
                p_high=hi,
                exposure_factor=exposure_factor,
                fast_n=fast_n,
                hold_n=hold_n,
                grid_points=grid_points,
            )
            for name, (lo, hi) in priors.items()
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--exposure-factor",
        type=float,
        required=True,
    )
    parser.add_argument("--fast-n", type=int, required=True)
    parser.add_argument("--hold-n", type=int, required=True)
    parser.add_argument(
        "--grid-points",
        type=int,
        default=200_000,
    )
    args = parser.parse_args()

    result = analyze(
        exposure_factor=args.exposure_factor,
        fast_n=args.fast_n,
        hold_n=args.hold_n,
        grid_points=args.grid_points,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
