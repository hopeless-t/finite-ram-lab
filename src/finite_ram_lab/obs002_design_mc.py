from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np


CANDIDATES = (
    {"name": "O1_LIGHT", "blocks": 6, "transition_repeats_per_block": 3, "control_repeats_per_block": 1},
    {"name": "O2_BALANCED", "blocks": 8, "transition_repeats_per_block": 4, "control_repeats_per_block": 1},
    {"name": "O3_HEAVY", "blocks": 10, "transition_repeats_per_block": 4, "control_repeats_per_block": 1},
)


def run(draws: int, seed: int) -> dict[str, Any]:
    rng = np.random.default_rng(seed)

    # Exploratory VAL-001 observation: 3 / 12 transition-zone trials exceeded 50 ms.
    # Uniform Beta(1,1) prior -> Beta(4,10) posterior.
    p = rng.beta(4.0, 10.0, size=draws)

    rows = {}
    for candidate in CANDIDATES:
        n_transition = candidate["blocks"] * candidate["transition_repeats_per_block"]
        counts = rng.binomial(n_transition, p)
        total_trials = candidate["blocks"] * (
            candidate["transition_repeats_per_block"]
            + 2 * candidate["control_repeats_per_block"]
        )
        rows[candidate["name"]] = {
            **candidate,
            "transition_trials": n_transition,
            "total_trials_for_160_164_168": total_trials,
            "posterior_predictive": {
                "prob_at_least_1_severe": float(np.mean(counts >= 1)),
                "prob_at_least_2_severe": float(np.mean(counts >= 2)),
                "prob_at_least_3_severe": float(np.mean(counts >= 3)),
                "median_severe_count": float(np.median(counts)),
                "p05_severe_count": float(np.quantile(counts, 0.05)),
                "p95_severe_count": float(np.quantile(counts, 0.95)),
            },
        }

    return {
        "study_id": "OBS-002-DESIGN-MC",
        "draws": draws,
        "seed": seed,
        "observed_transition_zone": {
            "memory_high_mib": 164,
            "descriptive_severe_threshold_ms": 50,
            "severe_trials": 3,
            "total_trials": 12,
            "posterior": "Beta(4,10) from uniform Beta(1,1) prior",
        },
        "candidates": rows,
        "interpretation_boundary": (
            "The 50 ms threshold is a post-hoc descriptive branch marker used only "
            "for sample-size decision support. It is not an acceptance criterion."
        ),
    }


def to_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# OBS-002 Design Monte Carlo",
        "",
        "Posterior predictive based on the exploratory 3/12 severe transition-zone observation.",
        "",
        "| Design | Blocks | 164 trials | Total 160/164/168 trials | P(>=2 severe) | P(>=3 severe) |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, d in result["candidates"].items():
        pp = d["posterior_predictive"]
        lines.append(
            f"| {name} | {d['blocks']} | {d['transition_trials']} | "
            f"{d['total_trials_for_160_164_168']} | "
            f"{pp['prob_at_least_2_severe']:.4f} | "
            f"{pp['prob_at_least_3_severe']:.4f} |"
        )
    lines += [
        "",
        "This calculation chooses observation effort; it does not validate a latency threshold.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--draws", type=int, default=500000)
    parser.add_argument("--seed", type=int, default=2026092605)
    parser.add_argument("--out", required=True)
    parser.add_argument("--markdown")
    args = parser.parse_args()

    result = run(args.draws, args.seed)
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    if args.markdown:
        Path(args.markdown).write_text(to_markdown(result))
    print(json.dumps(result["candidates"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
