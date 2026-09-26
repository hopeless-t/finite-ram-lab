from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

from finite_ram_lab.gate001_policy import _block_arrays, load_input


def required_specificity(h: float, b: float, q: float, sensitivity: float) -> float | None:
    if not 0.0 < q < 1.0:
        raise ValueError("q must be strictly between 0 and 1")
    if not 0.0 <= sensitivity <= 1.0:
        raise ValueError("sensitivity must be between 0 and 1")
    if h <= 0.0 or b <= 0.0:
        return None
    return 1.0 - (q * sensitivity * b) / ((1.0 - q) * h)


def _ci(values: np.ndarray) -> list[float]:
    return [
        float(np.quantile(values, 0.025)),
        float(np.quantile(values, 0.975)),
    ]


def _bootstrap_frontier(
    arr: dict[str, np.ndarray],
    q: float,
    sensitivity: float,
    indices: np.ndarray,
) -> dict[str, Any]:
    harm = (arr["A_W"] - arr["A_N"])[indices].mean(axis=1)
    benefit = (arr["M_N"] - arr["M_C"])[indices].mean(axis=1)
    valid = (harm > 0.0) & (benefit > 0.0)

    if not np.any(valid):
        return {
            "valid_fraction": 0.0,
            "raw_median": None,
            "raw_ci95": None,
            "clipped_median": None,
            "clipped_ci95": None,
            "prob_requirement_at_most_1": None,
            "prob_requirement_at_most_0": None,
        }

    raw = 1.0 - (
        q * sensitivity * benefit[valid]
        / ((1.0 - q) * harm[valid])
    )
    clipped = np.clip(raw, 0.0, 1.0)

    return {
        "valid_fraction": float(np.mean(valid)),
        "raw_median": float(np.median(raw)),
        "raw_ci95": _ci(raw),
        "clipped_median": float(np.median(clipped)),
        "clipped_ci95": _ci(clipped),
        "prob_requirement_at_most_1": float(np.mean(raw <= 1.0)),
        "prob_requirement_at_most_0": float(np.mean(raw <= 0.0)),
    }


def _point_frontier(
    arr: dict[str, np.ndarray],
    q: float,
    sensitivity: float,
) -> dict[str, float | None]:
    h = float(np.mean(arr["A_W"] - arr["A_N"]))
    b = float(np.mean(arr["M_N"] - arr["M_C"]))
    raw = required_specificity(h, b, q, sensitivity)
    return {
        "harm_mean": h,
        "benefit_mean": b,
        "raw_required_specificity": raw,
        "clipped_required_specificity": (
            None if raw is None else float(np.clip(raw, 0.0, 1.0))
        ),
    }


def analyze(spec: dict[str, Any]) -> dict[str, Any]:
    data = load_input(spec["input_json"])
    arithmetic = _block_arrays(data, "mean_work_ms")
    logv = _block_arrays(data, "mean_log_work")

    n = len(arithmetic["blocks"])
    if n != 16:
        raise ValueError("frozen GATE-002 input requires 16 runner blocks")

    resamples = int(spec["bootstrap_resamples"])
    seed = int(spec["bootstrap_seed"])
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, n, size=(resamples, n))

    frontier: dict[str, Any] = {}
    for q_raw in spec["q_grid"]:
        q = float(q_raw)
        qkey = f"{q:.3f}"
        frontier[qkey] = {}

        for t_raw in spec["sensitivity_grid"]:
            sensitivity = float(t_raw)
            tkey = f"{sensitivity:.3f}"
            frontier[qkey][tkey] = {}

            for name, arr in (
                ("arithmetic_total_work", arithmetic),
                ("log_total_work", logv),
            ):
                frontier[qkey][tkey][name] = {
                    "point": _point_frontier(arr, q, sensitivity),
                    "bootstrap": _bootstrap_frontier(
                        arr, q, sensitivity, indices
                    ),
                }

    return {
        "analysis_id": "GATE-002-DESIGN",
        "status": "PASS",
        "source": data["provenance"],
        "runner_blocks": n,
        "bootstrap_resamples": resamples,
        "bootstrap_seed": seed,
        "q_grid": spec["q_grid"],
        "sensitivity_grid": spec["sensitivity_grid"],
        "frontier": frontier,
        "authority_boundary": (
            "Class-conditional policy-frontier analysis only. "
            "It does not estimate production prevalence, sensitivity, "
            "specificity, or authorize ACT."
        ),
    }


def to_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# GATE-002 Class-Conditional Policy Frontier",
        "",
        "Minimum specificity required to beat NO_HINT.",
        "",
        "| q | sensitivity | Arithmetic point | Arithmetic 95% | Log point | Log 95% |",
        "| ---: | ---: | ---: | --- | ---: | --- |",
    ]

    for qkey, by_t in result["frontier"].items():
        for tkey, row in by_t.items():
            ar = row["arithmetic_total_work"]
            lg = row["log_total_work"]

            def fmt(metric: dict[str, Any]) -> tuple[str, str]:
                point = metric["point"]["raw_required_specificity"]
                boot = metric["bootstrap"]
                ptxt = "NA" if point is None else f"{point:.3f}"
                ci = boot["raw_ci95"]
                citxt = "NA" if ci is None else f"[{ci[0]:.3f}, {ci[1]:.3f}]"
                return ptxt, citxt

            ap, ac = fmt(ar)
            lp, lc = fmt(lg)
            lines.append(f"| {qkey} | {tkey} | {ap} | {ac} | {lp} | {lc} |")

    lines += [
        "",
        "Raw thresholds are preserved in JSON; clipped [0,1] operational views are separate.",
        "",
        "This is an empirical policy contract, not a deployed gate.",
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
