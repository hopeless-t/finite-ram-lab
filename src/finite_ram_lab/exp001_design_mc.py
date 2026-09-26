from __future__ import annotations

import argparse
import itertools
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


@dataclass(frozen=True)
class Design:
    name: str
    blocks: int
    repeats_per_arm: int

    @property
    def trials(self) -> int:
        return self.blocks * self.repeats_per_arm * 2


DESIGNS = (
    Design("D1_6x2", 6, 2),
    Design("D2_8x2", 8, 2),
    Design("D3_8x3", 8, 3),
    Design("D4_12x2", 12, 2),
)

SCENARIOS = {
    "moderate": {"trial_sigma": 0.50, "effect_sigma": 0.20, "outlier_rate": 0.00, "outlier_sigma": 0.0},
    "heavy": {"trial_sigma": 0.80, "effect_sigma": 0.45, "outlier_rate": 0.00, "outlier_sigma": 0.0},
    "branchy": {"trial_sigma": 0.65, "effect_sigma": 0.55, "outlier_rate": 0.10, "outlier_sigma": 1.5},
}

EFFECTS = {"null": 1.0, "two_x": 2.0, "five_x": 5.0, "twenty_x": 20.0}


def _sign_patterns(n: int) -> np.ndarray:
    return np.asarray(list(itertools.product((-1.0, 1.0), repeat=n)), dtype=np.float32)


def exact_signflip_reject(contrasts: np.ndarray, alpha: float = 0.05, chunk: int = 200) -> np.ndarray:
    sims, blocks = contrasts.shape
    signs = _sign_patterns(blocks)
    observed = np.abs(contrasts.mean(axis=1))
    reject = np.zeros(sims, dtype=bool)
    for start in range(0, sims, chunk):
        stop = min(start + chunk, sims)
        c = contrasts[start:stop].T
        perm = np.abs((signs @ c) / blocks)
        p = (perm >= observed[start:stop][None, :] - 1e-12).mean(axis=0)
        reject[start:stop] = p <= alpha
    return reject


def simulate(
    design: Design,
    scenario: dict[str, float],
    effect_ratio: float,
    simulations: int,
    seed: int,
) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    b = design.blocks
    r = design.repeats_per_arm

    runner = rng.normal(0.0, 0.55, size=(simulations, b, 1))
    block_effect = rng.normal(
        math.log(effect_ratio),
        scenario["effect_sigma"],
        size=(simulations, b, 1),
    )

    cold = runner + rng.normal(0.0, scenario["trial_sigma"], size=(simulations, b, r))
    hot = runner + block_effect + rng.normal(0.0, scenario["trial_sigma"], size=(simulations, b, r))

    if scenario["outlier_rate"] > 0:
        for arr in (cold, hot):
            mask = rng.random(size=arr.shape) < scenario["outlier_rate"]
            arr += mask * rng.normal(0.0, scenario["outlier_sigma"], size=arr.shape)

    contrasts = hot.mean(axis=2) - cold.mean(axis=2)
    reject = exact_signflip_reject(contrasts)
    estimate = np.exp(contrasts.mean(axis=1))

    return {
        "simulations": simulations,
        "detection_rate": float(reject.mean()),
        "median_estimated_ratio": float(np.median(estimate)),
        "estimated_ratio_p05": float(np.quantile(estimate, 0.05)),
        "estimated_ratio_p95": float(np.quantile(estimate, 0.95)),
    }


def run(simulations: int, seed: int) -> dict[str, Any]:
    out: dict[str, Any] = {
        "study_id": "EXP-001-DESIGN-MC",
        "simulations_per_cell": simulations,
        "seed": seed,
        "designs": {},
        "scenarios": SCENARIOS,
        "effects": EFFECTS,
    }
    for di, design in enumerate(DESIGNS):
        cells = {}
        for si, (scenario_name, scenario) in enumerate(SCENARIOS.items()):
            cells[scenario_name] = {}
            for ei, (effect_name, effect_ratio) in enumerate(EFFECTS.items()):
                cells[scenario_name][effect_name] = simulate(
                    design, scenario, effect_ratio, simulations,
                    seed + di * 100_003 + si * 10_007 + ei * 1009,
                )
        out["designs"][design.name] = {
            "blocks": design.blocks,
            "repeats_per_arm": design.repeats_per_arm,
            "trials": design.trials,
            "cells": cells,
            "worst_null_false_positive": max(
                cells[s]["null"]["detection_rate"] for s in SCENARIOS
            ),
            "worst_two_x_detection": min(
                cells[s]["two_x"]["detection_rate"] for s in SCENARIOS
            ),
            "worst_five_x_detection": min(
                cells[s]["five_x"]["detection_rate"] for s in SCENARIOS
            ),
            "worst_twenty_x_detection": min(
                cells[s]["twenty_x"]["detection_rate"] for s in SCENARIOS
            ),
        }
    return out


def to_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# EXP-001 Design Monte Carlo",
        "",
        f"Simulations per cell: **{result['simulations_per_cell']}**",
        "",
        "| Design | Blocks | Repeats/arm | Trials | Worst null FP | Worst 2x detect | Worst 5x detect | Worst 20x detect |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, d in result["designs"].items():
        lines.append(
            f"| {name} | {d['blocks']} | {d['repeats_per_arm']} | {d['trials']} | "
            f"{d['worst_null_false_positive']:.3f} | {d['worst_two_x_detection']:.3f} | "
            f"{d['worst_five_x_detection']:.3f} | {d['worst_twenty_x_detection']:.3f} |"
        )
    lines += [
        "",
        "The study uses exact block-level sign-flip inference, matching the planned primary analysis.",
        "This is experiment-design support, not evidence about Linux.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--simulations", type=int, default=3000)
    p.add_argument("--seed", type=int, default=2026092610)
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
