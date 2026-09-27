from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import beta, binom, t


def _mcse(rate: float, n: int) -> float:
    return math.sqrt(max(rate * (1.0 - rate), 0.0) / n)


def _candidate(
    *,
    n_blocks: int,
    reps: int,
    seed: int,
    efficacy_p: float,
    efficacy_alpha: float,
    latency_log_mean: float,
    latency_log_sd: float,
    latency_ratio_target: float,
    latency_confidence: float,
    chunk_size: int = 10000,
) -> dict[str, Any]:
    rng = np.random.default_rng(seed + n_blocks * 1009)
    latency_target_log = math.log(latency_ratio_target)
    tcrit = float(t.ppf(latency_confidence, df=n_blocks - 1))

    efficacy_passes = 0
    latency_passes = 0
    joint_passes = 0
    done = 0

    while done < reps:
        m = min(chunk_size, reps - done)

        successes = rng.binomial(n_blocks, efficacy_p, size=m)
        pvalues = binom.sf(successes - 1, n_blocks, 0.5)
        efficacy_ok = pvalues <= efficacy_alpha

        draws = rng.normal(
            latency_log_mean,
            latency_log_sd,
            size=(m, n_blocks),
        )
        means = draws.mean(axis=1)
        sds = draws.std(axis=1, ddof=1)
        uppers = means + tcrit * sds / math.sqrt(n_blocks)
        latency_ok = uppers <= latency_target_log

        efficacy_passes += int(np.count_nonzero(efficacy_ok))
        latency_passes += int(np.count_nonzero(latency_ok))
        joint_passes += int(np.count_nonzero(efficacy_ok & latency_ok))
        done += m

    efficacy_rate = efficacy_passes / reps
    latency_rate = latency_passes / reps
    joint_rate = joint_passes / reps

    return {
        "blocks": n_blocks,
        "replicates": reps,
        "efficacy_design_assurance": efficacy_rate,
        "efficacy_mcse": _mcse(efficacy_rate, reps),
        "latency_design_assurance": latency_rate,
        "latency_mcse": _mcse(latency_rate, reps),
        "joint_design_assurance": joint_rate,
        "joint_mcse": _mcse(joint_rate, reps),
    }


def analyze(spec: dict[str, Any]) -> dict[str, Any]:
    successes = int(spec["pilot_efficacy_successes"])
    blocks = int(spec["pilot_blocks"])
    if successes != blocks:
        raise ValueError("v1 frozen contract expects all pilot blocks to be efficacy successes")

    exact_lower = float(beta.ppf(0.05, successes, blocks - successes + 1))
    frozen_lower = float(spec["conservative_success_probability"])
    if not math.isclose(exact_lower, frozen_lower, rel_tol=0.0, abs_tol=1e-12):
        raise ValueError(
            f"frozen conservative probability mismatch: computed={exact_lower} frozen={frozen_lower}"
        )

    ratios = np.asarray(spec["pilot_scan_ratio_values"], dtype=float)
    if len(ratios) != blocks or np.any(ratios <= 0.0):
        raise ValueError("pilot scan ratio vector is invalid")

    log_ratios = np.log(ratios)
    log_mean = float(log_ratios.mean())
    log_sd = float(log_ratios.std(ddof=1))
    if not math.isfinite(log_sd) or log_sd <= 0.0:
        raise ValueError("pilot log-ratio variance is not positive")

    reps = int(spec["monte_carlo_resamples_per_candidate"])
    seed = int(spec["seed"])

    rows = []
    for n in map(int, spec["candidate_blocks"]):
        rows.append(
            _candidate(
                n_blocks=n,
                reps=reps,
                seed=seed,
                efficacy_p=frozen_lower,
                efficacy_alpha=float(spec["efficacy_alpha_one_sided"]),
                latency_log_mean=log_mean,
                latency_log_sd=log_sd,
                latency_ratio_target=float(spec["latency_ratio_target"]),
                latency_confidence=float(spec["latency_one_sided_confidence"]),
            )
        )

    target = float(spec["design_success_probability"])
    selected = next(
        (row["blocks"] for row in rows if row["joint_design_assurance"] >= target),
        None,
    )

    return {
        "analysis_id": spec["analysis_id"],
        "status": "PASS",
        "source": {
            "run": int(spec["source_run"]),
            "artifact_id": int(spec["source_artifact_id"]),
            "artifact_digest": str(spec["source_artifact_digest"]),
        },
        "pilot": {
            "blocks": blocks,
            "efficacy_successes": successes,
            "conservative_success_probability": frozen_lower,
            "scan_ratio_geometric_mean": float(math.exp(log_mean)),
            "scan_ratio_log_mean": log_mean,
            "scan_ratio_log_sample_sd": log_sd,
        },
        "candidates": rows,
        "selection": (
            selected if selected is not None else "NONE_WITHIN_FROZEN_RANGE"
        ),
        "selection_target_joint_assurance": target,
        "authority": spec["authority"],
    }


def to_markdown(result: dict[str, Any]) -> str:
    p = result["pilot"]
    lines = [
        "# STRATA-002 Confirmatory Design Monte Carlo v1",
        "",
        f"- conservative efficacy success probability: {p['conservative_success_probability']:.6f}",
        f"- pilot geometric-mean scan ratio: {p['scan_ratio_geometric_mean']:.4f}",
        f"- pilot log-ratio sample SD: {p['scan_ratio_log_sample_sd']:.4f}",
        "",
        "| Blocks | Efficacy assurance | Latency assurance | Joint assurance |",
        "| ---: | ---: | ---: | ---: |",
    ]
    for row in result["candidates"]:
        lines.append(
            f"| {row['blocks']} | "
            f"{row['efficacy_design_assurance']:.4f} | "
            f"{row['latency_design_assurance']:.4f} | "
            f"{row['joint_design_assurance']:.4f} |"
        )
    lines += [
        "",
        f"Selection: **{result['selection']}**",
        "",
        "Design analysis only; no physical confirmatory launch is authorized.",
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
