from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import beta

from finite_ram_lab.gate001_policy import _block_arrays, load_input


def clopper_pearson_lower(
    successes: np.ndarray | int,
    trials: np.ndarray | int,
    alpha: float,
) -> np.ndarray:
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be strictly between 0 and 1")

    x = np.asarray(successes, dtype=int)
    n = np.asarray(trials, dtype=int)
    x, n = np.broadcast_arrays(x, n)

    if np.any(n < 0) or np.any(x < 0) or np.any(x > n):
        raise ValueError("invalid binomial counts")

    out = np.zeros(x.shape, dtype=float)
    mask = (n > 0) & (x > 0)
    if np.any(mask):
        out[mask] = beta.ppf(
            alpha,
            x[mask],
            n[mask] - x[mask] + 1,
        )
    return out


def _cost_ratio_summary(
    arr: dict[str, np.ndarray],
    *,
    resamples: int,
    seed: int,
    alpha: float,
) -> dict[str, Any]:
    h_block = arr["A_W"] - arr["A_N"]
    b_block = arr["M_N"] - arr["M_C"]

    h_point = float(np.mean(h_block))
    b_point = float(np.mean(b_block))
    point_valid = h_point > 0.0 and b_point > 0.0
    point_ratio = (b_point / h_point) if point_valid else None

    rng = np.random.default_rng(seed)
    n = len(h_block)
    idx = rng.integers(0, n, size=(resamples, n))
    h = h_block[idx].mean(axis=1)
    b = b_block[idx].mean(axis=1)
    valid = (h > 0.0) & (b > 0.0)

    # Fail closed: invalid-sign bootstrap draws contribute zero benefit/harm
    # ratio rather than being silently dropped from the lower tail.
    ratio = np.zeros(resamples, dtype=float)
    ratio[valid] = b[valid] / h[valid]

    return {
        "harm_point": h_point,
        "benefit_point": b_point,
        "point_ratio": point_ratio,
        "valid_fraction": float(np.mean(valid)),
        "lower_ratio": float(np.quantile(ratio, alpha)),
        "ratio_median": float(np.median(ratio)),
        "ratio_ci95": [
            float(np.quantile(ratio, 0.025)),
            float(np.quantile(ratio, 0.975)),
        ],
    }


def _required_specificity(
    q: np.ndarray,
    sensitivity: np.ndarray,
    cost_ratio: float,
) -> np.ndarray:
    q = np.asarray(q, dtype=float)
    sensitivity = np.asarray(sensitivity, dtype=float)
    q, sensitivity = np.broadcast_arrays(q, sensitivity)

    out = np.full(q.shape, np.inf, dtype=float)
    valid = (
        (q >= 0.0)
        & (q < 1.0)
        & (sensitivity >= 0.0)
        & (sensitivity <= 1.0)
        & (cost_ratio > 0.0)
    )
    out[valid] = (
        1.0
        - (
            q[valid]
            * sensitivity[valid]
            * cost_ratio
            / (1.0 - q[valid])
        )
    )
    return out


def _true_required_specificity(
    q: float,
    sensitivity: float,
    point_ratio: float | None,
) -> float | None:
    if point_ratio is None or point_ratio <= 0.0:
        return None
    return float(
        1.0
        - q * sensitivity * point_ratio / (1.0 - q)
    )


def simulate_cell(
    *,
    n: int,
    q: float,
    sensitivity: float,
    specificity: float,
    repetitions: int,
    rng: np.random.Generator,
    alpha_component: float,
    primary_cost_ratio_lower: float,
    secondary_cost_ratio_lower: float,
) -> dict[str, Any]:
    if n <= 0 or repetitions <= 0:
        raise ValueError("n and repetitions must be positive")
    for name, value in (
        ("q", q),
        ("sensitivity", sensitivity),
        ("specificity", specificity),
    ):
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"{name} must be between 0 and 1")

    misaligned = rng.binomial(n, q, size=repetitions)
    aligned = n - misaligned
    act_when_misaligned = rng.binomial(misaligned, sensitivity)
    noact_when_aligned = rng.binomial(aligned, specificity)

    q_l = clopper_pearson_lower(
        misaligned,
        np.full(repetitions, n, dtype=int),
        alpha_component,
    )
    t_l = clopper_pearson_lower(
        act_when_misaligned,
        misaligned,
        alpha_component,
    )
    s_l = clopper_pearson_lower(
        noact_when_aligned,
        aligned,
        alpha_component,
    )

    primary_required = _required_specificity(
        q_l,
        t_l,
        primary_cost_ratio_lower,
    )
    secondary_required = _required_specificity(
        q_l,
        t_l,
        secondary_cost_ratio_lower,
    )

    primary_margin = s_l - primary_required
    secondary_margin = s_l - secondary_required
    primary_certified = primary_margin > 0.0
    secondary_certified = secondary_margin > 0.0

    def finite_quantiles(values: np.ndarray) -> dict[str, float | None]:
        finite = values[np.isfinite(values)]
        if len(finite) == 0:
            return {"median": None, "q10": None, "q90": None}
        return {
            "median": float(np.median(finite)),
            "q10": float(np.quantile(finite, 0.10)),
            "q90": float(np.quantile(finite, 0.90)),
        }

    return {
        "n": int(n),
        "repetitions": int(repetitions),
        "primary_certification_rate": float(np.mean(primary_certified)),
        "secondary_certification_rate": float(
            np.mean(secondary_certified)
        ),
        "both_certification_rate": float(
            np.mean(primary_certified & secondary_certified)
        ),
        "median_misaligned_count": float(np.median(misaligned)),
        "zero_misaligned_fraction": float(np.mean(misaligned == 0)),
        "q_lower": finite_quantiles(q_l),
        "sensitivity_lower": finite_quantiles(t_l),
        "specificity_lower": finite_quantiles(s_l),
        "primary_margin": finite_quantiles(primary_margin),
        "secondary_margin": finite_quantiles(secondary_margin),
    }


def analyze(spec: dict[str, Any]) -> dict[str, Any]:
    data = load_input(spec["action_cost_input_json"])
    arithmetic = _block_arrays(data, "mean_work_ms")
    logv = _block_arrays(data, "mean_log_work")

    if len(arithmetic["blocks"]) != 16:
        raise ValueError("SIG-001 requires the frozen 16-block input")

    familywise_alpha = float(spec["familywise_alpha"])
    components = int(spec["bonferroni_components"])
    if components <= 0:
        raise ValueError("bonferroni_components must be positive")
    alpha_component = familywise_alpha / components

    cost_resamples = int(spec["action_cost_bootstrap_resamples"])
    cost_seed = int(spec["action_cost_bootstrap_seed"])

    primary_cost = _cost_ratio_summary(
        logv,
        resamples=cost_resamples,
        seed=cost_seed,
        alpha=alpha_component,
    )
    secondary_cost = _cost_ratio_summary(
        arithmetic,
        resamples=cost_resamples,
        seed=cost_seed + 1,
        alpha=alpha_component,
    )

    if (
        primary_cost["lower_ratio"] <= 0.0
        or secondary_cost["lower_ratio"] <= 0.0
    ):
        raise ValueError(
            "fail-closed action-cost lower ratio is non-positive"
        )

    repetitions = int(spec["simulation_repetitions"])
    rng = np.random.default_rng(int(spec["simulation_seed"]))
    sample_sizes = [int(x) for x in spec["sample_sizes"]]
    target = float(spec["safe_certification_target"])
    unsafe_limit = float(spec["unsafe_false_certification_limit"])

    scenarios: dict[str, Any] = {}
    unsafe_ok = True

    for scenario in spec["scenarios"]:
        sid = str(scenario["id"])
        q = float(scenario["q"])
        sensitivity = float(scenario["sensitivity"])
        specificity = float(scenario["specificity"])
        expected = str(scenario["expected"])

        cells: dict[str, Any] = {}
        for n in sample_sizes:
            cells[str(n)] = simulate_cell(
                n=n,
                q=q,
                sensitivity=sensitivity,
                specificity=specificity,
                repetitions=repetitions,
                rng=rng,
                alpha_component=alpha_component,
                primary_cost_ratio_lower=float(
                    primary_cost["lower_ratio"]
                ),
                secondary_cost_ratio_lower=float(
                    secondary_cost["lower_ratio"]
                ),
            )

        minimum_n = None
        if expected == "safe_candidate":
            for n in sample_sizes:
                if (
                    cells[str(n)]["primary_certification_rate"]
                    >= target
                ):
                    minimum_n = n
                    break
        elif expected == "unsafe_control":
            max_false = max(
                cells[str(n)]["primary_certification_rate"]
                for n in sample_sizes
            )
            unsafe_ok = unsafe_ok and (max_false <= unsafe_limit)
        else:
            raise ValueError(f"unknown scenario expectation {expected}")

        scenarios[sid] = {
            "q": q,
            "sensitivity": sensitivity,
            "specificity": specificity,
            "expected": expected,
            "true_primary_required_specificity": (
                _true_required_specificity(
                    q,
                    sensitivity,
                    primary_cost["point_ratio"],
                )
            ),
            "true_secondary_required_specificity": (
                _true_required_specificity(
                    q,
                    sensitivity,
                    secondary_cost["point_ratio"],
                )
            ),
            "minimum_n_for_primary_target": minimum_n,
            "cells": cells,
        }

    return {
        "analysis_id": "SIG-001-DESIGN-MC",
        "status": "PASS",
        "source": data["provenance"],
        "familywise_alpha": familywise_alpha,
        "bonferroni_components": components,
        "alpha_component": alpha_component,
        "simulation_repetitions": repetitions,
        "simulation_seed": int(spec["simulation_seed"]),
        "sample_sizes": sample_sizes,
        "safe_certification_target": target,
        "unsafe_false_certification_limit": unsafe_limit,
        "primary_metric": str(spec["primary_metric"]),
        "secondary_metric": str(spec["secondary_metric"]),
        "primary_action_cost": primary_cost,
        "secondary_action_cost": secondary_cost,
        "unsafe_controls_pass": bool(unsafe_ok),
        "scenarios": scenarios,
        "authority_boundary": (
            "Calibration design Monte Carlo only. No predictor is "
            "selected or trained, and no ACT or memory intervention "
            "is authorized."
        ),
    }


def to_markdown(result: dict[str, Any]) -> str:
    p = result["primary_action_cost"]
    s = result["secondary_action_cost"]
    lines = [
        "# SIG-001 Calibration Design Monte Carlo",
        "",
        "## Conservative action-cost ratios",
        "",
        "| Metric | Point b/h | Lower ratio | Valid fraction |",
        "| --- | ---: | ---: | ---: |",
        (
            f"| {result['primary_metric']} | "
            f"{p['point_ratio']:.3f} | {p['lower_ratio']:.3f} | "
            f"{p['valid_fraction']:.5f} |"
        ),
        (
            f"| {result['secondary_metric']} | "
            f"{s['point_ratio']:.3f} | {s['lower_ratio']:.3f} | "
            f"{s['valid_fraction']:.5f} |"
        ),
        "",
        "## Certification rates",
        "",
        "| Scenario | q | t | s | Expected | Minimum N @ primary target |",
        "| --- | ---: | ---: | ---: | --- | ---: |",
    ]

    for sid, scenario in result["scenarios"].items():
        min_n = scenario["minimum_n_for_primary_target"]
        min_text = "NA" if min_n is None else str(min_n)
        lines.append(
            f"| {sid} | {scenario['q']:.2f} | "
            f"{scenario['sensitivity']:.2f} | "
            f"{scenario['specificity']:.2f} | "
            f"{scenario['expected']} | {min_text} |"
        )

    lines += [
        "",
        "### Per-sample-size primary certification",
        "",
        "| Scenario | "
        + " | ".join(str(n) for n in result["sample_sizes"])
        + " |",
        "| --- | "
        + " | ".join("---:" for _ in result["sample_sizes"])
        + " |",
    ]

    for sid, scenario in result["scenarios"].items():
        rates = [
            scenario["cells"][str(n)]["primary_certification_rate"]
            for n in result["sample_sizes"]
        ]
        lines.append(
            "| "
            + sid
            + " | "
            + " | ".join(f"{x:.3f}" for x in rates)
            + " |"
        )

    lines += [
        "",
        f"Unsafe controls pass: {result['unsafe_controls_pass']}",
        "",
        "ABSTAIN is accounted as NO-ACT. This study sizes calibration "
        "evidence; it does not authorize ACT.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--spec", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--markdown")
    args = p.parse_args()

    spec = json.loads(Path(args.spec).read_text())
    result = analyze(spec)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    if args.markdown:
        Path(args.markdown).write_text(to_markdown(result))

    print(to_markdown(result))


if __name__ == "__main__":
    main()
