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
        return self.blocks * self.repeats_per_arm * 3


DESIGNS = (
    Design("D1_16x4", 16, 4),
    Design("D2_20x4", 20, 4),
    Design("D3_20x6", 20, 6),
    Design("D4_24x4", 24, 4),
)

SCENARIOS = {
    "null": 0.25,
    "modest": 0.15,
    "material": 0.10,
    "strong": 0.05,
}


def _logit(p: float) -> float:
    return math.log(p / (1.0 - p))


def _draw_latency(
    rng: np.random.Generator,
    probs: np.ndarray,
    repeats: int,
) -> np.ndarray:
    shape = (*probs.shape, repeats)
    slow = rng.random(shape) < probs[..., None]
    fast_values = rng.lognormal(math.log(4.0), 0.40, size=shape)
    slow_values = rng.lognormal(math.log(150.0), 0.90, size=shape)
    # Small independent extreme tail in both arms.
    extreme = rng.random(shape) < 0.03
    slow_values *= np.where(extreme, rng.lognormal(1.0, 0.7, size=shape), 1.0)
    return np.where(slow, slow_values, fast_values)


def simulate(design: Design, correct_branch_p: float, simulations: int, seed: int) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    blocks = design.blocks
    reps = design.repeats_per_arm

    # Runner heterogeneity moves both arm branch probabilities together on log-odds scale.
    u = rng.normal(0.0, 0.80, size=(simulations, blocks))
    p_no = 1.0 / (1.0 + np.exp(-(_logit(0.25) + u)))
    p_correct = 1.0 / (1.0 + np.exp(-(_logit(correct_branch_p) + u)))

    no_hint = _draw_latency(rng, p_no, reps)
    correct = _draw_latency(rng, p_correct, reps)

    contrast = np.log(np.maximum(correct, 1e-9)).mean(axis=2) - np.log(np.maximum(no_hint, 1e-9)).mean(axis=2)
    means = contrast.mean(axis=1)
    sds = contrast.std(axis=1, ddof=1)
    tstat = np.divide(
        means,
        sds / math.sqrt(blocks),
        out=np.zeros_like(means),
        where=sds > 0,
    )
    pvals = 2.0 * student_t.sf(np.abs(tstat), df=blocks - 1)
    ratio = np.exp(means)

    return {
        "simulations": simulations,
        "screen_detection_rate": float(np.mean(pvals <= 0.05)),
        "median_estimated_ratio_correct_over_nohint": float(np.median(ratio)),
        "ratio_p05": float(np.quantile(ratio, 0.05)),
        "ratio_p95": float(np.quantile(ratio, 0.95)),
    }


def run(simulations: int, seed: int) -> dict[str, Any]:
    result: dict[str, Any] = {
        "study_id": "EXP-002-DESIGN-MC",
        "simulations_per_cell": simulations,
        "seed": seed,
        "baseline_slow_branch_probability": 0.25,
        "correct_hint_scenarios": SCENARIOS,
        "designs": {},
        "analysis_note": (
            "Design screening uses a paired t test on runner-block mean log-latency contrasts. "
            "The real experiment will use pre-registered block sign-flip inference."
        ),
    }
    for di, design in enumerate(DESIGNS):
        cells = {}
        for si, (name, p) in enumerate(SCENARIOS.items()):
            cells[name] = simulate(design, p, simulations, seed + di * 100_003 + si * 10_007)
        result["designs"][design.name] = {
            "blocks": design.blocks,
            "repeats_per_arm": design.repeats_per_arm,
            "total_trials_three_arms": design.total_trials,
            "cells": cells,
        }
    return result


def to_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# EXP-002 Design Monte Carlo",
        "",
        f"Simulations per cell: **{result['simulations_per_cell']}**",
        "",
        "| Design | Blocks | Repeats/arm | Total 3-arm trials | Null FP | Modest detect | Material detect | Strong detect |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, d in result["designs"].items():
        c = d["cells"]
        lines.append(
            f"| {name} | {d['blocks']} | {d['repeats_per_arm']} | {d['total_trials_three_arms']} | "
            f"{c['null']['screen_detection_rate']:.3f} | {c['modest']['screen_detection_rate']:.3f} | "
            f"{c['material']['screen_detection_rate']:.3f} | {c['strong']['screen_detection_rate']:.3f} |"
        )
    lines += [
        "",
        "Scenario meaning: baseline slow-branch probability 0.25; correct semantic preparation changes it to 0.25 / 0.15 / 0.10 / 0.05.",
        "This is design support, not evidence for semantic-hint benefit.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--simulations", type=int, default=5000)
    p.add_argument("--seed", type=int, default=2026092614)
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
