from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from numpy.polynomial.hermite import hermgauss


LEVELS = np.asarray([160.0, 162.0, 164.0, 166.0, 168.0])

DESIGNS = {
    "D1_12x4": {"blocks": 12, "repeats_per_level": 4},
    "D2_16x4": {"blocks": 16, "repeats_per_level": 4},
    "D3_24x3": {"blocks": 24, "repeats_per_level": 3},
    "D4_32x2": {"blocks": 32, "repeats_per_level": 2},
}

SCENARIOS = {
    "sharp": {"midpoint": 162.7, "width": 0.8, "runner_sigma": 0.6},
    "moderate": {"midpoint": 162.8, "width": 1.2, "runner_sigma": 0.8},
    "shifted": {"midpoint": 163.5, "width": 1.0, "runner_sigma": 1.0},
    "broad_noisy": {"midpoint": 163.0, "width": 1.8, "runner_sigma": 1.2},
}


def sigmoid(x: np.ndarray) -> np.ndarray:
    x = np.clip(x, -50.0, 50.0)
    return 1.0 / (1.0 + np.exp(-x))


def marginal_probabilities(scenario: dict[str, float]) -> np.ndarray:
    # Gauss-Hermite integration for E[sigmoid(base + sigma * Z)].
    nodes, weights = hermgauss(80)
    z = np.sqrt(2.0) * nodes
    w = weights / np.sqrt(np.pi)
    base = (scenario["midpoint"] - LEVELS) / scenario["width"]
    logits = base[None, :] + scenario["runner_sigma"] * z[:, None]
    return (w[:, None] * sigmoid(logits)).sum(axis=0)


def simulate(
    blocks: int,
    repeats: int,
    scenario: dict[str, float],
    simulations: int,
    seed: int,
) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    truth = marginal_probabilities(scenario)

    block_effect = rng.normal(
        0.0,
        scenario["runner_sigma"],
        size=(simulations, blocks, 1),
    )
    base = (
        (scenario["midpoint"] - LEVELS)
        / scenario["width"]
    )[None, None, :]
    probs = sigmoid(base + block_effect)
    events = rng.binomial(
        repeats,
        probs,
        size=(simulations, blocks, len(LEVELS)),
    )
    block_rates = events / repeats
    estimate = block_rates.mean(axis=1)

    abs_error = np.abs(estimate - truth[None, :])
    curve_mae = abs_error.mean(axis=1)

    # Runner-cluster normal interval used only as a design diagnostic.
    se = block_rates.std(axis=1, ddof=1) / math.sqrt(blocks)
    lo = np.clip(estimate - 1.96 * se, 0.0, 1.0)
    hi = np.clip(estimate + 1.96 * se, 0.0, 1.0)

    i164 = int(np.where(LEVELS == 164.0)[0][0])
    total_164 = events[:, :, i164].sum(axis=1)
    affected_blocks_164 = (events[:, :, i164] > 0).sum(axis=1)

    return {
        "truth": {
            str(int(level)): float(p)
            for level, p in zip(LEVELS, truth)
        },
        "median_abs_error_164": float(
            np.median(abs_error[:, i164])
        ),
        "p90_abs_error_164": float(
            np.quantile(abs_error[:, i164], 0.90)
        ),
        "median_curve_mae": float(np.median(curve_mae)),
        "p90_curve_mae": float(np.quantile(curve_mae, 0.90)),
        "median_cluster_ci_width_164": float(
            np.median(hi[:, i164] - lo[:, i164])
        ),
        "cluster_ci_coverage_164": float(
            np.mean(
                (lo[:, i164] <= truth[i164])
                & (truth[i164] <= hi[:, i164])
            )
        ),
        "prob_at_least_8_events_164": float(
            np.mean(total_164 >= 8)
        ),
        "prob_at_least_6_affected_blocks_164": float(
            np.mean(affected_blocks_164 >= 6)
        ),
        "median_events_164": float(np.median(total_164)),
        "median_affected_blocks_164": float(
            np.median(affected_blocks_164)
        ),
    }


def pareto(designs: dict[str, dict[str, Any]]) -> list[str]:
    names = list(designs)
    keep = []
    for name in names:
        a = designs[name]
        dominated = False
        for other in names:
            if other == name:
                continue
            b = designs[other]
            no_worse = (
                b["trials"] <= a["trials"]
                and b["worst_p90_abs_error_164"]
                <= a["worst_p90_abs_error_164"]
                and b["worst_p90_curve_mae"]
                <= a["worst_p90_curve_mae"]
            )
            strict = (
                b["trials"] < a["trials"]
                or b["worst_p90_abs_error_164"]
                < a["worst_p90_abs_error_164"]
                or b["worst_p90_curve_mae"]
                < a["worst_p90_curve_mae"]
            )
            if no_worse and strict:
                dominated = True
                break
        if not dominated:
            keep.append(name)
    return sorted(keep)


def run(simulations: int, seed: int) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for di, (name, d) in enumerate(DESIGNS.items()):
        scenarios = {}
        for si, (sname, scenario) in enumerate(SCENARIOS.items()):
            scenarios[sname] = simulate(
                int(d["blocks"]),
                int(d["repeats_per_level"]),
                scenario,
                simulations,
                seed + di * 100_003 + si * 10_007,
            )

        out[name] = {
            **d,
            "trials": int(
                d["blocks"]
                * d["repeats_per_level"]
                * len(LEVELS)
            ),
            "scenarios": scenarios,
            "worst_p90_abs_error_164": max(
                x["p90_abs_error_164"]
                for x in scenarios.values()
            ),
            "worst_p90_curve_mae": max(
                x["p90_curve_mae"]
                for x in scenarios.values()
            ),
            "worst_median_ci_width_164": max(
                x["median_cluster_ci_width_164"]
                for x in scenarios.values()
            ),
            "worst_ci_coverage_164": min(
                x["cluster_ci_coverage_164"]
                for x in scenarios.values()
            ),
            "worst_prob_8_events_164": min(
                x["prob_at_least_8_events_164"]
                for x in scenarios.values()
            ),
            "worst_prob_6_blocks_164": min(
                x["prob_at_least_6_affected_blocks_164"]
                for x in scenarios.values()
            ),
        }

    return {
        "study_id": "OBS-003-DESIGN-MC",
        "levels_mib": LEVELS.astype(int).tolist(),
        "simulations_per_design_scenario": simulations,
        "seed": seed,
        "scenarios": SCENARIOS,
        "designs": out,
        "pareto_trials_vs_error": pareto(out),
        "interpretation_boundary": (
            "This Monte Carlo compares sampling designs under declared "
            "misalignment-curve and runner-heterogeneity scenarios. "
            "It does not estimate the real curve."
        ),
    }


def markdown(result: dict[str, Any]) -> str:
    lines = [
        "# OBS-003 Design Monte Carlo",
        "",
        f"Simulations per design/scenario: **{result['simulations_per_design_scenario']}**",
        "",
        "| Design | Blocks | Repeats/level | Trials | Worst P90 abs err @164 | Worst P90 curve MAE | Worst median CI width @164 | Worst P(>=8 events @164) | Worst P(>=6 affected blocks @164) |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, d in result["designs"].items():
        lines.append(
            f"| {name} | {d['blocks']} | {d['repeats_per_level']} | {d['trials']} | "
            f"{d['worst_p90_abs_error_164']:.4f} | {d['worst_p90_curve_mae']:.4f} | "
            f"{d['worst_median_ci_width_164']:.4f} | {d['worst_prob_8_events_164']:.3f} | "
            f"{d['worst_prob_6_blocks_164']:.3f} |"
        )
    lines += [
        "",
        "Pareto set: " + ", ".join(result["pareto_trials_vs_error"]),
        "",
        "Simulation output is design decision support, not Linux evidence.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--simulations", type=int, default=10000)
    p.add_argument("--seed", type=int, default=2026092620)
    p.add_argument("--out", required=True)
    p.add_argument("--markdown")
    args = p.parse_args()

    result = run(args.simulations, args.seed)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    if args.markdown:
        Path(args.markdown).write_text(markdown(result))
    print(json.dumps({
        "pareto": result["pareto_trials_vs_error"],
        "designs": {
            k: {
                "trials": v["trials"],
                "worst_p90_abs_error_164": v["worst_p90_abs_error_164"],
                "worst_p90_curve_mae": v["worst_p90_curve_mae"],
                "worst_prob_6_blocks_164": v["worst_prob_6_blocks_164"],
            }
            for k, v in result["designs"].items()
        },
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
