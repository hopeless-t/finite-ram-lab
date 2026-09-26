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
    complete_repeats: int

    @property
    def total_trials(self) -> int:
        # 2 pressure levels × 2 fault orders × 2 HOT positions × 3 arms.
        return self.blocks * self.complete_repeats * 24


DESIGNS = (
    Design("D1_16x1", 16, 1),
    Design("D2_24x1", 24, 1),
    Design("D3_32x1", 32, 1),
    Design("D4_16x2", 16, 2),
    Design("D5_24x2", 24, 2),
)

CAPTURE_SCENARIOS = {
    "null_0pct": 0.00,
    "weak_25pct": 0.25,
    "moderate_50pct": 0.50,
    "strong_75pct": 0.75,
}


def load_inputs(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def empirical_pair(mean: np.ndarray, sample_sd: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Reconstruct the two HYP-003 observations summarized by mean + sample SD.

    Every block×pressure×alignment stratum in HYP-003 contains exactly two
    fault-order observations. For n=2 the two deviations from the mean have
    magnitude sample_sd / sqrt(2).
    """
    delta = sample_sd / math.sqrt(2.0)
    return mean - delta, mean + delta


def _hyp_profiles(data: dict[str, Any]) -> dict[str, np.ndarray]:
    cols = data["hyp003_columns"]
    idx = {name: i for i, name in enumerate(cols)}
    rows = data["hyp003_rows"]

    blocks = sorted({int(r[idx["block"]]) for r in rows})
    levels = sorted({int(r[idx["memory_high_mib"]]) for r in rows})
    if len(blocks) != 16 or levels != [160, 162]:
        raise ValueError("unexpected HYP-003 empirical structure")

    shape = (len(blocks), len(levels))
    aligned_mean = np.empty(shape)
    aligned_sd = np.empty(shape)
    mis_mean = np.empty(shape)
    mis_sd = np.empty(shape)

    bpos = {b: i for i, b in enumerate(blocks)}
    lpos = {x: i for i, x in enumerate(levels)}

    for r in rows:
        bi = bpos[int(r[idx["block"]])]
        li = lpos[int(r[idx["memory_high_mib"]])]
        aligned_mean[bi, li] = float(r[idx["aligned_log_mean"]])
        aligned_sd[bi, li] = float(r[idx["aligned_log_sd"]])
        mis_mean[bi, li] = float(r[idx["misaligned_log_mean"]])
        mis_sd[bi, li] = float(r[idx["misaligned_log_sd"]])

    return {
        "blocks": np.asarray(blocks),
        "levels": np.asarray(levels),
        "aligned_mean": aligned_mean,
        "aligned_sd": aligned_sd,
        "mis_mean": mis_mean,
        "mis_sd": mis_sd,
        "gap": mis_mean - aligned_mean,
    }


def _draw_block_arm_mean(
    rng: np.random.Generator,
    base_mean: np.ndarray,
    sample_sd: np.ndarray,
    repeats: int,
) -> np.ndarray:
    """Empirical two-point residual bootstrap within each pressure stratum."""
    sims, blocks, levels = base_mean.shape
    draws_per_level = 2 * repeats
    signs = rng.integers(
        0,
        2,
        size=(sims, blocks, levels, draws_per_level),
        dtype=np.int8,
    ) * 2 - 1
    residual = signs * (
        sample_sd[..., None] / math.sqrt(2.0)
    )
    values = base_mean[..., None] + residual
    # Equal weight to the frozen 160 and 162 MiB levels.
    return values.mean(axis=(2, 3))


def _screen_pvalues(block_contrasts: np.ndarray) -> np.ndarray:
    """One-sided paired t screen used only for design-power ranking.

    The real EXP-003 experiment will use the pre-registered block sign-flip
    inference. This screen mirrors prior design-MC practice in the repository.
    """
    n = block_contrasts.shape[1]
    means = block_contrasts.mean(axis=1)
    sds = block_contrasts.std(axis=1, ddof=1)
    tstat = np.divide(
        means,
        sds / math.sqrt(n),
        out=np.zeros_like(means),
        where=sds > 0,
    )
    # Alternative: CORRECT - NO_HINT < 0.
    return student_t.cdf(tstat, df=n - 1)


def simulate_cell(
    profiles: dict[str, np.ndarray],
    design: Design,
    capture_fraction: float,
    simulations: int,
    seed: int,
) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    source_blocks = rng.integers(
        0,
        len(profiles["blocks"]),
        size=(simulations, design.blocks),
    )

    mis_mean = profiles["mis_mean"][source_blocks]
    mis_sd = profiles["mis_sd"][source_blocks]
    gap = profiles["gap"][source_blocks]

    no_hint = _draw_block_arm_mean(
        rng,
        mis_mean,
        mis_sd,
        design.complete_repeats,
    )
    correct_mean = mis_mean - capture_fraction * gap
    correct = _draw_block_arm_mean(
        rng,
        correct_mean,
        mis_sd,
        design.complete_repeats,
    )

    contrast = correct - no_hint
    pvals = _screen_pvalues(contrast)
    ratios = np.exp(contrast.mean(axis=1))

    return {
        "simulations": simulations,
        "capture_fraction": capture_fraction,
        "screen_detection_rate": float(np.mean(pvals <= 0.05)),
        "median_estimated_ratio_correct_over_nohint": float(
            np.median(ratios)
        ),
        "ratio_p05": float(np.quantile(ratios, 0.05)),
        "ratio_p95": float(np.quantile(ratios, 0.95)),
    }


def redteam_calibration(data: dict[str, Any]) -> dict[str, Any]:
    cols = data["exp002_columns"]
    idx = {name: i for i, name in enumerate(cols)}
    rows = data["exp002_rows"]

    by_block: dict[int, dict[str, list[Any]]] = {}
    for r in rows:
        by_block.setdefault(int(r[idx["block"]]), {})[
            str(r[idx["arm_CNW"]])
        ] = r

    wrong_vs_correct = []
    wrong_vs_nohint = []
    correct_work_vs_nohint = []
    correct_advice = []

    for block in sorted(by_block):
        arms = by_block[block]
        c, n, w = arms["C"], arms["N"], arms["W"]
        wrong_vs_correct.append(
            float(w[idx["log_hot_mean"]]) - float(c[idx["log_hot_mean"]])
        )
        wrong_vs_nohint.append(
            float(w[idx["log_hot_mean"]]) - float(n[idx["log_hot_mean"]])
        )
        correct_work_vs_nohint.append(
            float(c[idx["log_work_mean"]]) - float(n[idx["log_work_mean"]])
        )
        correct_advice.append(float(c[idx["advice_ms_mean"]]))

    def ratio_summary(values: list[float]) -> dict[str, float]:
        a = np.asarray(values, dtype=float)
        return {
            "geometric_mean_ratio": float(np.exp(a.mean())),
            "median_block_ratio": float(np.median(np.exp(a))),
        }

    return {
        "source": "EXP-002 at 164 MiB; stress calibration only, not pooled into benefit simulation",
        "wrong_vs_correct_hot_latency": ratio_summary(wrong_vs_correct),
        "wrong_vs_nohint_hot_latency": ratio_summary(wrong_vs_nohint),
        "correct_vs_nohint_total_interval": ratio_summary(
            correct_work_vs_nohint
        ),
        "correct_pageout_advice_ms": {
            "median_block_mean": float(np.median(correct_advice)),
            "p90_block_mean": float(np.quantile(correct_advice, 0.90)),
        },
    }


def choose_design(
    designs: dict[str, Any],
    null_fp_max: float,
    weak_power_min: float,
    moderate_power_min: float,
) -> dict[str, Any]:
    eligible = []
    for name, row in designs.items():
        cells = row["cells"]
        ok = (
            cells["null_0pct"]["screen_detection_rate"] <= null_fp_max
            and cells["weak_25pct"]["screen_detection_rate"] >= weak_power_min
            and cells["moderate_50pct"]["screen_detection_rate"]
            >= moderate_power_min
        )
        row["selection_eligible"] = bool(ok)
        if ok:
            eligible.append((row["total_trials"], -row["blocks"], name))

    if not eligible:
        # Fail closed: do not silently pick an underpowered design.
        return {
            "status": "NO_DESIGN_MEETS_FROZEN_RULE",
            "selected": None,
        }

    eligible.sort()
    return {
        "status": "SELECTED",
        "selected": eligible[0][2],
    }


def run(spec: dict[str, Any]) -> dict[str, Any]:
    data = load_inputs(spec["input_json"])
    profiles = _hyp_profiles(data)
    simulations = int(spec["simulations_per_cell"])
    seed = int(spec["seed"])

    result: dict[str, Any] = {
        "study_id": "EXP-003-DESIGN-MC",
        "simulations_per_cell": simulations,
        "seed": seed,
        "designs": {},
        "screening_inference": (
            "one-sided paired t screen on runner-block mean log-latency "
            "contrasts; final EXP-003 inference remains block sign-flip"
        ),
        "empirical_model": (
            "runner blocks bootstrap from HYP-003; within block×pressure "
            "residuals are the exact two-point residual distribution implied "
            "by HYP-003 n=2 mean/sample-SD strata; no Gaussian latency model"
        ),
    }

    for di, design in enumerate(DESIGNS):
        cells = {}
        for si, (name, capture) in enumerate(CAPTURE_SCENARIOS.items()):
            cells[name] = simulate_cell(
                profiles,
                design,
                capture,
                simulations,
                seed + di * 100_003 + si * 10_007,
            )
        result["designs"][design.name] = {
            "blocks": design.blocks,
            "complete_repeats": design.complete_repeats,
            "total_trials": design.total_trials,
            "cells": cells,
        }

    sel = spec["selection_rule"]
    result["selection_rule"] = sel
    result["selection"] = choose_design(
        result["designs"],
        float(sel["null_fp_max"]),
        float(sel["weak_25pct_power_min"]),
        float(sel["moderate_50pct_power_min"]),
    )
    result["redteam_calibration"] = redteam_calibration(data)
    result["authority_boundary"] = (
        "Design support only. EXP-002 is used only as separate stress/cost "
        "calibration; it is not pooled with HYP-003 as if pressure regimes "
        "were exchangeable."
    )
    return result


def to_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# EXP-003 Design Monte Carlo",
        "",
        f"Simulations per cell: **{result['simulations_per_cell']}**",
        "",
        "| Design | Blocks | Complete repeats | Total trials | Null FP | 25% capture | 50% capture | 75% capture | Eligible |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for name, d in result["designs"].items():
        c = d["cells"]
        lines.append(
            f"| {name} | {d['blocks']} | {d['complete_repeats']} | "
            f"{d['total_trials']} | "
            f"{c['null_0pct']['screen_detection_rate']:.3f} | "
            f"{c['weak_25pct']['screen_detection_rate']:.3f} | "
            f"{c['moderate_50pct']['screen_detection_rate']:.3f} | "
            f"{c['strong_75pct']['screen_detection_rate']:.3f} | "
            f"{'YES' if d['selection_eligible'] else 'NO'} |"
        )
    lines += [
        "",
        f"Selection status: **{result['selection']['status']}**",
        f"Selected design: **{result['selection']['selected']}**",
        "",
        "EXP-002 Red-Team values are reported separately and do not enter the HYP-003 benefit simulation.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--spec", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--markdown")
    args = p.parse_args()

    spec = json.loads(Path(args.spec).read_text())
    result = run(spec)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    if args.markdown:
        Path(args.markdown).write_text(to_markdown(result))
    print(to_markdown(result))


if __name__ == "__main__":
    main()
