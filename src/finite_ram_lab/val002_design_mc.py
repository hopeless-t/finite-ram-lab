from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import t as student_t


@dataclass(frozen=True)
class Design:
    name: str
    blocks: int
    repeats_per_arm: int

    @property
    def total_trials(self) -> int:
        return self.blocks * self.repeats_per_arm * 2


DESIGNS = (
    Design("D1_20x20", 20, 20),
    Design("D2_32x12", 32, 12),
    Design("D3_40x10", 40, 10),
    Design("D4_40x16", 40, 16),
)

SCENARIOS = {
    "null": {"p_no": 0.05, "p_correct": 0.05},
    "moderate": {"p_no": 0.05, "p_correct": 0.025},
    "target": {"p_no": 0.05, "p_correct": 0.01},
    "low_base_target": {"p_no": 0.03, "p_correct": 0.006},
    "high_base_target": {"p_no": 0.08, "p_correct": 0.016},
}


def _logit(p: float) -> float:
    return math.log(p / (1.0 - p))


def simulate(
    design: Design,
    scenario: dict[str, float],
    simulations: int,
    seed: int,
    runner_sigma: float,
    arm_block_sigma: float,
) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    b = design.blocks
    r = design.repeats_per_arm

    shared = rng.normal(0.0, runner_sigma, size=(simulations, b))
    no_specific = rng.normal(0.0, arm_block_sigma, size=(simulations, b))
    correct_specific = rng.normal(0.0, arm_block_sigma, size=(simulations, b))

    p_no = 1.0 / (1.0 + np.exp(-(_logit(scenario["p_no"]) + shared + no_specific)))
    p_correct = 1.0 / (1.0 + np.exp(-(_logit(scenario["p_correct"]) + shared + correct_specific)))

    no_counts = rng.binomial(r, p_no)
    correct_counts = rng.binomial(r, p_correct)
    diff = correct_counts / r - no_counts / r

    means = diff.mean(axis=1)
    sds = diff.std(axis=1, ddof=1)
    tstat = np.divide(
        means,
        sds / math.sqrt(b),
        out=np.zeros_like(means),
        where=sds > 0,
    )
    pvals = 2.0 * student_t.sf(np.abs(tstat), df=b - 1)

    return {
        "simulations": simulations,
        "screen_rejection_rate": float(np.mean(pvals <= 0.05)),
        "direction_correct_rate": float(np.mean(means < 0.0)),
        "median_difference": float(np.median(means)),
        "median_nohint_events": float(np.median(no_counts.sum(axis=1))),
        "median_correct_events": float(np.median(correct_counts.sum(axis=1))),
        "p05_nohint_events": float(np.quantile(no_counts.sum(axis=1), 0.05)),
        "p05_correct_events": float(np.quantile(correct_counts.sum(axis=1), 0.05)),
    }


def run(simulations: int, seed: int) -> dict[str, Any]:
    runner_sigmas = (0.7, 1.1)
    arm_block_sigma = 0.35
    result: dict[str, Any] = {
        "study_id": "VAL-002-DESIGN-MC",
        "simulations_per_cell": simulations,
        "seed": seed,
        "runner_sigmas": list(runner_sigmas),
        "arm_block_sigma": arm_block_sigma,
        "catastrophic_threshold_ms": 500,
        "scenarios": SCENARIOS,
        "designs": {},
        "analysis_note": (
            "Design screening uses a paired t test on runner-block catastrophic-event-rate contrasts. "
            "The confirmatory study will use a pre-registered Monte Carlo sign-flip randomization test."
        ),
    }

    for di, design in enumerate(DESIGNS):
        cells = {}
        for ri, runner_sigma in enumerate(runner_sigmas):
            key = f"runner_sigma_{runner_sigma:.1f}"
            cells[key] = {}
            for si, (scenario_name, scenario) in enumerate(SCENARIOS.items()):
                cells[key][scenario_name] = simulate(
                    design,
                    scenario,
                    simulations,
                    seed + di * 1_000_003 + ri * 100_003 + si * 10_007,
                    runner_sigma,
                    arm_block_sigma,
                )

        null_fp = max(
            cells[k]["null"]["screen_rejection_rate"]
            for k in cells
        )
        moderate = min(
            cells[k]["moderate"]["screen_rejection_rate"]
            for k in cells
        )
        target = min(
            cells[k]["target"]["screen_rejection_rate"]
            for k in cells
        )
        low_base = min(
            cells[k]["low_base_target"]["screen_rejection_rate"]
            for k in cells
        )
        high_base = min(
            cells[k]["high_base_target"]["screen_rejection_rate"]
            for k in cells
        )
        result["designs"][design.name] = {
            "blocks": design.blocks,
            "repeats_per_arm": design.repeats_per_arm,
            "total_trials": design.total_trials,
            "cells": cells,
            "worst_null_false_positive": null_fp,
            "worst_moderate_detection": moderate,
            "worst_target_detection": target,
            "worst_low_base_target_detection": low_base,
            "worst_high_base_target_detection": high_base,
        }
    return result


def to_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# VAL-002 Tail Design Monte Carlo",
        "",
        f"Simulations per cell: **{result['simulations_per_cell']}**",
        "",
        "| Design | Blocks | Repeats/arm | Trials | Null FP | 5%→2.5% detect | 5%→1% detect | 3%→0.6% detect | 8%→1.6% detect |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, d in result["designs"].items():
        lines.append(
            f"| {name} | {d['blocks']} | {d['repeats_per_arm']} | {d['total_trials']} | "
            f"{d['worst_null_false_positive']:.3f} | {d['worst_moderate_detection']:.3f} | "
            f"{d['worst_target_detection']:.3f} | {d['worst_low_base_target_detection']:.3f} | "
            f"{d['worst_high_base_target_detection']:.3f} |"
        )
    lines += [
        "",
        "Runner probabilities are generated with shared logit-normal heterogeneity plus arm-specific block variation.",
        "This is rare-event design support, not confirmatory evidence.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--simulations", type=int, default=10000)
    p.add_argument("--seed", type=int, default=2026092616)
    p.add_argument("--out", required=True)
    p.add_argument("--markdown")
    args = p.parse_args()
    result = run(args.simulations, args.seed)
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    if args.markdown:
        Path(args.markdown).write_text(to_markdown(result))
    print(to_markdown(result))


if __name__ == "__main__":
    main()
