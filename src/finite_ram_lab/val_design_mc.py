from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


@dataclass(frozen=True)
class Design:
    name: str
    levels: tuple[int, ...]
    blocks: int
    repeats: int

    @property
    def trials(self) -> int:
        return len(self.levels) * self.blocks * self.repeats


DESIGNS = (
    Design("D1_COARSE_BLOCKED", (160, 168, 176, 184, 192), 8, 3),
    Design("D2_FINE_BALANCED", tuple(range(160, 193, 4)), 6, 2),
    Design("D3_FINE_REPLICATED", tuple(range(160, 193, 4)), 8, 2),
    Design("D4_ULTRAFINE_LIGHT", tuple(range(160, 193, 2)), 4, 2),
)

SCENARIOS: dict[str, dict[str, float]] = {
    "sharp": {
        "width_mib": 1.0,
        "runner_sigma": 0.20,
        "trial_sigma": 0.12,
        "level_sigma": 0.05,
    },
    "moderate": {
        "width_mib": 3.0,
        "runner_sigma": 0.25,
        "trial_sigma": 0.15,
        "level_sigma": 0.08,
    },
    "broad": {
        "width_mib": 6.0,
        "runner_sigma": 0.25,
        "trial_sigma": 0.18,
        "level_sigma": 0.10,
    },
    "noisy_nonmonotonic": {
        "width_mib": 3.0,
        "runner_sigma": 0.35,
        "trial_sigma": 0.25,
        "level_sigma": 0.25,
    },
}


def _regime_fraction(levels: np.ndarray, threshold: np.ndarray, width: float) -> np.ndarray:
    # Lower MemoryHigh means deeper pressure. This maps low levels toward 1.
    z = (levels[None, :] - threshold[:, None]) / max(width, 1e-9)
    z = np.clip(z, -50.0, 50.0)
    return 1.0 / (1.0 + np.exp(z))


def _estimate_breakpoint(levels: np.ndarray, y: np.ndarray) -> np.ndarray:
    # y shape: [sim, level]. Choose the two-regime constant split with minimum SSE.
    n_sim, n_level = y.shape
    scores = np.full((n_sim, n_level - 1), np.inf, dtype=float)

    for split in range(1, n_level):
        left = y[:, :split]
        right = y[:, split:]
        left_mean = left.mean(axis=1, keepdims=True)
        right_mean = right.mean(axis=1, keepdims=True)
        sse = ((left - left_mean) ** 2).sum(axis=1)
        sse += ((right - right_mean) ** 2).sum(axis=1)
        scores[:, split - 1] = sse

    best = scores.argmin(axis=1) + 1
    return (levels[best - 1] + levels[best]) / 2.0


def simulate_design(
    design: Design,
    scenario: dict[str, float],
    simulations: int,
    seed: int,
) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    levels = np.asarray(design.levels, dtype=float)

    threshold = rng.uniform(162.0, 190.0, size=simulations)
    frac = _regime_fraction(levels, threshold, scenario["width_mib"])

    low_log = math.log(3.5)
    high_log = math.log(900.0)
    amplitude_jitter = rng.normal(0.0, 0.12, size=(simulations, 1))
    mean_log = low_log + frac * (high_log - low_log + amplitude_jitter)

    # Allow the pressured side to be non-monotonic. This is deliberately a
    # nuisance model rather than a claim about Linux.
    level_noise = rng.normal(
        0.0,
        scenario["level_sigma"],
        size=(simulations, len(levels)),
    ) * frac
    mean_log = mean_log + level_noise

    runner_effect = rng.normal(
        0.0,
        scenario["runner_sigma"],
        size=(simulations, design.blocks, 1, 1),
    )
    trial_noise = rng.normal(
        0.0,
        scenario["trial_sigma"],
        size=(simulations, design.blocks, len(levels), design.repeats),
    )

    log_latency = (
        mean_log[:, None, :, None]
        + runner_effect
        + trial_noise
    )

    # Pairing within runner blocks removes the runner-wide offset before
    # estimating the boundary.
    per_block_level = log_latency.mean(axis=3)
    centered = per_block_level - per_block_level.mean(axis=2, keepdims=True)
    y = centered.mean(axis=1)

    estimate = _estimate_breakpoint(levels, y)
    error = estimate - threshold
    abs_error = np.abs(error)

    return {
        "simulations": simulations,
        "median_abs_error_mib": float(np.median(abs_error)),
        "p90_abs_error_mib": float(np.quantile(abs_error, 0.90)),
        "p95_abs_error_mib": float(np.quantile(abs_error, 0.95)),
        "within_2_mib_rate": float(np.mean(abs_error <= 2.0)),
        "within_4_mib_rate": float(np.mean(abs_error <= 4.0)),
        "within_8_mib_rate": float(np.mean(abs_error <= 8.0)),
        "mean_signed_error_mib": float(np.mean(error)),
    }


def _pareto(design_summaries: dict[str, dict[str, Any]]) -> list[str]:
    names = list(design_summaries)
    pareto: list[str] = []
    for name in names:
        a = design_summaries[name]
        dominated = False
        for other in names:
            if other == name:
                continue
            b = design_summaries[other]
            no_worse = (
                b["trials"] <= a["trials"]
                and b["worst_p95_abs_error_mib"] <= a["worst_p95_abs_error_mib"]
            )
            strictly_better = (
                b["trials"] < a["trials"]
                or b["worst_p95_abs_error_mib"] < a["worst_p95_abs_error_mib"]
            )
            if no_worse and strictly_better:
                dominated = True
                break
        if not dominated:
            pareto.append(name)
    return sorted(pareto)


def run(simulations: int, seed: int) -> dict[str, Any]:
    designs: dict[str, dict[str, Any]] = {}

    for d_index, design in enumerate(DESIGNS):
        scenario_results: dict[str, Any] = {}
        for s_index, (scenario_name, scenario) in enumerate(SCENARIOS.items()):
            scenario_results[scenario_name] = simulate_design(
                design,
                scenario,
                simulations,
                seed + d_index * 100_003 + s_index * 10_007,
            )

        designs[design.name] = {
            "levels_mib": list(design.levels),
            "blocks": design.blocks,
            "repeats": design.repeats,
            "trials": design.trials,
            "scenarios": scenario_results,
            "worst_median_abs_error_mib": max(
                x["median_abs_error_mib"] for x in scenario_results.values()
            ),
            "worst_p95_abs_error_mib": max(
                x["p95_abs_error_mib"] for x in scenario_results.values()
            ),
            "worst_within_4_mib_rate": min(
                x["within_4_mib_rate"] for x in scenario_results.values()
            ),
        }

    return {
        "study_id": "VAL-001-DESIGN-MC",
        "simulations_per_design_scenario": simulations,
        "seed": seed,
        "threshold_prior_mib": [162.0, 190.0],
        "scenarios": SCENARIOS,
        "designs": designs,
        "pareto_trials_vs_worst_p95_error": _pareto(designs),
        "interpretation_boundary": (
            "This simulation compares experiment designs under declared nuisance "
            "models. It does not establish the real boundary or real noise model."
        ),
    }


def to_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# VAL-001 Design Monte Carlo",
        "",
        f"Simulations per design/scenario: **{result['simulations_per_design_scenario']}**",
        "",
        "| Design | Levels | Blocks | Repeats | Trials | Worst median error MiB | Worst P95 error MiB | Worst within ±4 MiB |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, d in result["designs"].items():
        levels = ",".join(str(x) for x in d["levels_mib"])
        lines.append(
            f"| {name} | {levels} | {d['blocks']} | {d['repeats']} | {d['trials']} | "
            f"{d['worst_median_abs_error_mib']:.2f} | {d['worst_p95_abs_error_mib']:.2f} | "
            f"{d['worst_within_4_mib_rate']:.3f} |"
        )
    lines += [
        "",
        "Pareto set (trial count vs worst-case P95 localization error): "
        + ", ".join(result["pareto_trials_vs_worst_p95_error"]),
        "",
        "This is design decision support, not experimental evidence about Linux.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--simulations", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=2026092603)
    parser.add_argument("--out", required=True)
    parser.add_argument("--markdown")
    args = parser.parse_args()

    result = run(args.simulations, args.seed)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    if args.markdown:
        Path(args.markdown).write_text(to_markdown(result))
    print(json.dumps({
        "pareto": result["pareto_trials_vs_worst_p95_error"],
        "designs": {
            k: {
                "trials": v["trials"],
                "worst_p95_abs_error_mib": v["worst_p95_abs_error_mib"],
                "worst_within_4_mib_rate": v["worst_within_4_mib_rate"],
            }
            for k, v in result["designs"].items()
        },
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
