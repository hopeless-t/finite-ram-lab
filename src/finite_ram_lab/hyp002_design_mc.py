from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import t


# Exploratory OBS-003 pooled 160/162 MiB runner-block contrasts:
# recent(B) resident fraction - older(A) resident fraction.
SOURCE_BLOCK_CONTRASTS = np.asarray([
    0.050018310546875,
    0.057891845703125,
    0.0478515625,
    -0.056854248046875,
    0.048858642578125,
    0.059112548828125,
    0.060577392578125,
    0.281768798828125,
    0.07080078125,
    0.152923583984375,
    0.064117431640625,
    0.06842041015625,
    0.064849853515625,
    0.048004150390625,
    0.059906005859375,
    0.0521240234375,
    0.06085205078125,
    0.05316162109375,
    0.112152099609375,
    0.055755615234375,
    0.061248779296875,
    0.05218505859375,
    0.053619384765625,
    0.058868408203125,
    0.0648193359375,
    0.053131103515625,
    0.07391357421875,
    0.22064208984375,
    0.062530517578125,
    0.0574951171875,
    0.05633544921875,
    0.056396484375,
])

DESIGNS = {
    "D1_8": {"blocks": 8},
    "D2_12": {"blocks": 12},
    "D3_16": {"blocks": 16},
    "D4_20": {"blocks": 20},
}

ATTENUATIONS = (1.0, 0.75, 0.50, 0.35)


def simulate_design(
    blocks: int,
    attenuation: float,
    simulations: int,
    seed: int,
) -> dict[str, Any]:
    rng = np.random.default_rng(seed)

    source_mean = float(SOURCE_BLOCK_CONTRASTS.mean())
    residuals = SOURCE_BLOCK_CONTRASTS - source_mean
    target_mean = attenuation * source_mean

    sampled = (
        target_mean
        + rng.choice(
            residuals,
            size=(simulations, blocks),
            replace=True,
        )
    )

    means = sampled.mean(axis=1)
    sds = sampled.std(axis=1, ddof=1)
    se = sds / np.sqrt(blocks)

    # Design-screen proxy only. Final HYP-002 inference is sign-flip randomization.
    tstat = np.divide(
        means,
        se,
        out=np.zeros_like(means),
        where=se > 0,
    )
    critical = float(t.ppf(0.95, blocks - 1))
    detected = tstat > critical

    abs_error = np.abs(means - target_mean)

    return {
        "blocks": blocks,
        "trials": blocks * 8,
        "attenuation": attenuation,
        "target_mean_contrast": target_mean,
        "detection_probability_proxy": float(detected.mean()),
        "median_abs_error": float(np.median(abs_error)),
        "p90_abs_error": float(np.quantile(abs_error, 0.90)),
    }


def run(simulations: int, seed: int) -> dict[str, Any]:
    source_mean = float(SOURCE_BLOCK_CONTRASTS.mean())
    source_sd = float(SOURCE_BLOCK_CONTRASTS.std(ddof=1))

    designs: dict[str, Any] = {}
    for di, (name, d) in enumerate(DESIGNS.items()):
        scenarios = {}
        for ai, attenuation in enumerate(ATTENUATIONS):
            scenarios[str(attenuation)] = simulate_design(
                d["blocks"],
                attenuation,
                simulations,
                seed + di * 100_003 + ai * 10_007,
            )

        designs[name] = {
            "blocks": d["blocks"],
            "trials": d["blocks"] * 8,
            "scenarios": scenarios,
            "power_at_half_effect": scenarios["0.5"][
                "detection_probability_proxy"
            ],
            "p90_error_at_half_effect": scenarios["0.5"][
                "p90_abs_error"
            ],
        }

    qualifying = [
        name
        for name, d in designs.items()
        if d["power_at_half_effect"] >= 0.90
    ]

    return {
        "study_id": "HYP-002-DESIGN-MC",
        "simulations_per_design_scenario": simulations,
        "seed": seed,
        "source": {
            "experiment": "OBS-003 exploratory recency-order analysis",
            "runner_blocks": int(len(SOURCE_BLOCK_CONTRASTS)),
            "mean_contrast": source_mean,
            "sd_contrast": source_sd,
        },
        "attenuations": list(ATTENUATIONS),
        "designs": designs,
        "qualifying_at_half_effect": qualifying,
        "interpretation_boundary": (
            "The t-test is a design-screen proxy over a residual bootstrap model. "
            "Final HYP-002 inference remains runner-block randomization."
        ),
    }


def markdown(result: dict[str, Any]) -> str:
    lines = [
        "# HYP-002 Design Monte Carlo",
        "",
        f"Source mean contrast: **{result['source']['mean_contrast']:.5f}**",
        f"Source SD: **{result['source']['sd_contrast']:.5f}**",
        "",
        "| Design | Blocks | Trials | Detect @100% | @75% | @50% | @35% | P90 error @50% |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    for name, d in result["designs"].items():
        s = d["scenarios"]
        lines.append(
            f"| {name} | {d['blocks']} | {d['trials']} | "
            f"{s['1.0']['detection_probability_proxy']:.3f} | "
            f"{s['0.75']['detection_probability_proxy']:.3f} | "
            f"{s['0.5']['detection_probability_proxy']:.3f} | "
            f"{s['0.35']['detection_probability_proxy']:.3f} | "
            f"{s['0.5']['p90_abs_error']:.5f} |"
        )

    lines += [
        "",
        "Qualifying designs at >=90% screened detection for half effect: "
        + (
            ", ".join(result["qualifying_at_half_effect"])
            if result["qualifying_at_half_effect"]
            else "none"
        ),
        "",
        "Design simulation is not HYP-002 scientific evidence.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--simulations", type=int, default=20000)
    p.add_argument("--seed", type=int, default=2026092623)
    p.add_argument("--out", required=True)
    p.add_argument("--markdown")
    args = p.parse_args()

    result = run(args.simulations, args.seed)
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    if args.markdown:
        Path(args.markdown).write_text(markdown(result))

    print(json.dumps({
        "qualifying": result["qualifying_at_half_effect"],
        "designs": {
            name: {
                "blocks": d["blocks"],
                "trials": d["trials"],
                "power_at_half_effect": d["power_at_half_effect"],
                "p90_error_at_half_effect": d["p90_error_at_half_effect"],
            }
            for name, d in result["designs"].items()
        },
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
