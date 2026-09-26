from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REQUIRED_COLUMNS = (
    "residency_gap_aligned_minus_misaligned",
    "not_full_risk_gap_misaligned_minus_aligned",
    "log_latency_gap_misaligned_minus_aligned",
)


def load_spec(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def accuracy_threshold(q: float, k: float) -> float:
    if not (0.0 <= q <= 1.0):
        raise ValueError("q must be in [0,1]")
    if k <= 0.0:
        raise ValueError("k must be positive")
    return 1.0 - q / k


def _summary(values: np.ndarray) -> dict[str, float | list[float]]:
    return {
        "median": float(np.median(values)),
        "ci95": [
            float(np.quantile(values, 0.025)),
            float(np.quantile(values, 0.975)),
        ],
    }


def analyze(spec: dict[str, Any]) -> dict[str, Any]:
    input_path = Path(spec["input_csv"])
    df = pd.read_csv(input_path)

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"missing required columns: {missing}")
    if len(df) != 16:
        raise ValueError("VOI-001 frozen input requires exactly 16 runner blocks")

    res_gap = df[
        "residency_gap_aligned_minus_misaligned"
    ].to_numpy(dtype=float)
    risk_gap = df[
        "not_full_risk_gap_misaligned_minus_aligned"
    ].to_numpy(dtype=float)
    log_gap = df[
        "log_latency_gap_misaligned_minus_aligned"
    ].to_numpy(dtype=float)

    resamples = int(spec["bootstrap_resamples"])
    seed = int(spec["bootstrap_seed"])
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(df), size=(resamples, len(df)))

    boot_res_gap = res_gap[idx].mean(axis=1)
    boot_risk_gap = risk_gap[idx].mean(axis=1)
    boot_log_gap = log_gap[idx].mean(axis=1)

    observed = {
        "runner_blocks": len(df),
        "mean_residency_gap": float(res_gap.mean()),
        "mean_not_full_risk_gap": float(risk_gap.mean()),
        "mean_log_latency_gap": float(log_gap.mean()),
        "geometric_misaligned_over_aligned_latency_ratio": math.exp(
            float(log_gap.mean())
        ),
    }

    headroom: dict[str, Any] = {}
    for q_raw in spec["opportunity_q"]:
        q = float(q_raw)
        key = f"{q:.2f}"

        res_values = q * boot_res_gap
        risk_values = q * boot_risk_gap
        geo_values = np.exp(q * boot_log_gap)

        headroom[key] = {
            "q": q,
            "observed": {
                "resident_fraction_gain": (
                    q * observed["mean_residency_gap"]
                ),
                "not_full_risk_reduction": (
                    q * observed["mean_not_full_risk_gap"]
                ),
                "geometric_latency_headroom_factor": math.exp(
                    q * observed["mean_log_latency_gap"]
                ),
            },
            "bootstrap": {
                "resident_fraction_gain": _summary(res_values),
                "not_full_risk_reduction": _summary(risk_values),
                "geometric_latency_headroom_factor": _summary(geo_values),
            },
        }

    thresholds: dict[str, Any] = {}
    for q_raw in spec["opportunity_q"]:
        q = float(q_raw)
        thresholds[f"{q:.2f}"] = {
            str(k_raw): accuracy_threshold(q, float(k_raw))
            for k_raw in spec["wrong_action_penalty_k"]
        }

    return {
        "analysis_id": "VOI-001",
        "status": "PASS",
        "input_csv": str(input_path),
        "bootstrap_resamples": resamples,
        "bootstrap_seed": seed,
        "observed_hyp003_block_gaps": observed,
        "perfect_information_headroom_surface": headroom,
        "signal_accuracy_threshold": {
            "formula": "a > 1 - q/k",
            "meaning": (
                "Minimum semantic-signal correctness in the simplified "
                "wrong-action penalty model for signal-driven action to beat "
                "the history-only baseline."
            ),
            "table": thresholds,
        },
        "interpretation_boundary": (
            "Headroom assumes conflict cases could be converted to "
            "aligned-equivalent outcomes at zero action cost. It is not an "
            "achieved intervention speedup or production EVPI."
        ),
    }


def to_markdown(result: dict[str, Any]) -> str:
    o = result["observed_hyp003_block_gaps"]
    lines = [
        "# VOI-001 — Bounded Decision Headroom",
        "",
        "## HYP-003 empirical gaps",
        "",
        f"- mean aligned-minus-misaligned resident fraction: **{o['mean_residency_gap']:.4f}**",
        f"- mean misaligned-minus-aligned not-full risk: **{o['mean_not_full_risk_gap']:.4f}**",
        f"- geometric misaligned/aligned latency ratio: **{o['geometric_misaligned_over_aligned_latency_ratio']:.2f}x**",
        "",
        "## Perfect-information headroom scenarios",
        "",
        "| q | Resident fraction gain | Not-full risk reduction | Geometric latency headroom |",
        "| ---: | ---: | ---: | ---: |",
    ]

    for _, row in result["perfect_information_headroom_surface"].items():
        obs = row["observed"]
        lines.append(
            f"| {row['q']:.2f} | "
            f"{obs['resident_fraction_gain']:.4f} | "
            f"{obs['not_full_risk_reduction']:.4f} | "
            f"{obs['geometric_latency_headroom_factor']:.2f}x |"
        )

    lines += [
        "",
        "## Minimum semantic-signal accuracy",
        "",
        "Analytic threshold: a > 1 - q/k",
        "",
        "| q | k=1 | k=2 | k=4 | k=8 | k=16 | k=32 |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    table = result["signal_accuracy_threshold"]["table"]
    for q_key, row in table.items():
        lines.append(
            "| "
            + " | ".join(
                [q_key]
                + [f"{row[str(k)]:.4f}" for k in (1, 2, 4, 8, 16, 32)]
            )
            + " |"
        )

    lines += [
        "",
        "These are bounded decision-support scenarios, not achieved intervention results.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--spec", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--markdown")
    args = p.parse_args()

    spec = load_spec(args.spec)
    result = analyze(spec)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    if args.markdown:
        Path(args.markdown).write_text(to_markdown(result))

    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
