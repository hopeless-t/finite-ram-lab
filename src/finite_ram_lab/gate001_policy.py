from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np


Q_GRID = (0.10, 0.25, 0.50, 0.75, 0.90)
A_GRID = (0.50, 0.60, 0.70, 0.80, 0.85, 0.90, 0.925, 0.95, 0.975, 0.99, 1.00)


def load_input(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def _block_arrays(data: dict[str, Any], value_column: str) -> dict[str, np.ndarray]:
    columns = data["columns"]
    idx = {name: i for i, name in enumerate(columns)}
    rows = data["rows"]
    blocks = sorted({int(r[idx["block"]]) for r in rows})
    bpos = {b: i for i, b in enumerate(blocks)}

    required = {
        "A_N": (True, "no_hint"),
        "A_C": (True, "correct_pageout"),
        "A_W": (True, "wrong_pageout"),
        "M_N": (False, "no_hint"),
        "M_C": (False, "correct_pageout"),
    }
    out = {name: np.full(len(blocks), np.nan) for name in required}

    for r in rows:
        key = None
        aligned = bool(r[idx["aligned"]])
        arm = str(r[idx["arm"]])
        for name, signature in required.items():
            if signature == (aligned, arm):
                key = name
                break
        if key is not None:
            out[key][bpos[int(r[idx["block"]])]] = float(r[idx[value_column]])

    for name, arr in out.items():
        if np.isnan(arr).any():
            raise ValueError(f"missing empirical policy primitive {name}")
    out["blocks"] = np.asarray(blocks, dtype=int)
    return out


def gate_cost(arr: dict[str, np.ndarray], q: float, a: float) -> np.ndarray:
    return (
        (1.0 - q) * (a * arr["A_N"] + (1.0 - a) * arr["A_W"])
        + q * (a * arr["M_C"] + (1.0 - a) * arr["M_N"])
    )


def nohint_cost(arr: dict[str, np.ndarray], q: float) -> np.ndarray:
    return (1.0 - q) * arr["A_N"] + q * arr["M_N"]


def always_correct_cost(arr: dict[str, np.ndarray], q: float) -> np.ndarray:
    return (1.0 - q) * arr["A_C"] + q * arr["M_C"]


def break_even_accuracy(arr: dict[str, np.ndarray], q: float) -> float | None:
    h = float(np.mean(arr["A_W"] - arr["A_N"]))
    b = float(np.mean(arr["M_N"] - arr["M_C"]))
    den = (1.0 - q) * h + q * b
    if h <= 0.0 or b <= 0.0 or den <= 0.0:
        return None
    return ((1.0 - q) * h) / den


def _bootstrap_mean(
    values: np.ndarray,
    indices: np.ndarray,
) -> np.ndarray:
    return values[indices].mean(axis=1)


def _ci(values: np.ndarray) -> list[float]:
    return [
        float(np.quantile(values, 0.025)),
        float(np.quantile(values, 0.975)),
    ]


def _bootstrap_threshold(
    arr: dict[str, np.ndarray],
    q: float,
    indices: np.ndarray,
) -> dict[str, Any]:
    h = _bootstrap_mean(arr["A_W"] - arr["A_N"], indices)
    b = _bootstrap_mean(arr["M_N"] - arr["M_C"], indices)
    den = (1.0 - q) * h + q * b
    valid = (h > 0.0) & (b > 0.0) & (den > 0.0)
    vals = ((1.0 - q) * h[valid]) / den[valid]
    if len(vals) == 0:
        return {"valid_fraction": 0.0, "median": None, "ci95": None}
    return {
        "valid_fraction": float(np.mean(valid)),
        "median": float(np.median(vals)),
        "ci95": _ci(vals),
    }


def analyze(spec: dict[str, Any]) -> dict[str, Any]:
    data = load_input(spec["input_json"])
    raw = _block_arrays(data, "mean_work_ms")
    logv = _block_arrays(data, "mean_log_work")

    n = len(raw["blocks"])
    if n != 16:
        raise ValueError("frozen GATE-001 input requires 16 runner blocks")

    resamples = int(spec["bootstrap_resamples"])
    seed = int(spec["bootstrap_seed"])
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, n, size=(resamples, n))

    surfaces: dict[str, Any] = {}
    thresholds: dict[str, Any] = {}

    for q_raw in spec["q_grid"]:
        q = float(q_raw)
        qkey = f"{q:.3f}"
        surfaces[qkey] = {}
        thresholds[qkey] = {
            "arithmetic": {
                "point": break_even_accuracy(raw, q),
                "bootstrap": _bootstrap_threshold(raw, q, indices),
            },
            "log": {
                "point": break_even_accuracy(logv, q),
                "bootstrap": _bootstrap_threshold(logv, q, indices),
            },
        }

        raw_no = nohint_cost(raw, q)
        raw_always = always_correct_cost(raw, q)
        log_no = nohint_cost(logv, q)
        log_always = always_correct_cost(logv, q)

        boot_raw_no = _bootstrap_mean(raw_no, indices)
        boot_raw_always = _bootstrap_mean(raw_always, indices)
        boot_log_no = _bootstrap_mean(log_no, indices)
        boot_log_always = _bootstrap_mean(log_always, indices)

        for a_raw in spec["a_grid"]:
            a = float(a_raw)
            akey = f"{a:.3f}"
            raw_gate = gate_cost(raw, q, a)
            log_gate = gate_cost(logv, q, a)

            boot_raw_gate = _bootstrap_mean(raw_gate, indices)
            boot_log_gate = _bootstrap_mean(log_gate, indices)

            raw_ratio_no = boot_raw_gate / boot_raw_no
            raw_ratio_always = boot_raw_gate / boot_raw_always
            log_ratio_no = np.exp(boot_log_gate - boot_log_no)
            log_ratio_always = np.exp(boot_log_gate - boot_log_always)

            point_raw_gate = float(np.mean(raw_gate))
            point_raw_no = float(np.mean(raw_no))
            point_raw_always = float(np.mean(raw_always))
            point_log_gate = float(np.mean(log_gate))
            point_log_no = float(np.mean(log_no))
            point_log_always = float(np.mean(log_always))

            surfaces[qkey][akey] = {
                "q": q,
                "accuracy": a,
                "arithmetic_total_work": {
                    "gate_mean_ms": point_raw_gate,
                    "nohint_mean_ms": point_raw_no,
                    "always_correct_mean_ms": point_raw_always,
                    "gate_over_nohint": point_raw_gate / point_raw_no,
                    "gate_over_nohint_ci95": _ci(raw_ratio_no),
                    "gate_over_always_correct": point_raw_gate / point_raw_always,
                    "gate_over_always_correct_ci95": _ci(raw_ratio_always),
                    "prob_gate_better_nohint_bootstrap": float(np.mean(raw_ratio_no < 1.0)),
                },
                "log_total_work": {
                    "gate_geometric_ms": math.exp(point_log_gate),
                    "nohint_geometric_ms": math.exp(point_log_no),
                    "always_correct_geometric_ms": math.exp(point_log_always),
                    "gate_over_nohint": math.exp(point_log_gate - point_log_no),
                    "gate_over_nohint_ci95": _ci(log_ratio_no),
                    "gate_over_always_correct": math.exp(point_log_gate - point_log_always),
                    "gate_over_always_correct_ci95": _ci(log_ratio_always),
                    "prob_gate_better_nohint_bootstrap": float(np.mean(log_ratio_no < 1.0)),
                },
            }

    return {
        "analysis_id": "GATE-001-DESIGN",
        "status": "PASS",
        "source": data["provenance"],
        "runner_blocks": n,
        "bootstrap_resamples": resamples,
        "bootstrap_seed": seed,
        "q_grid": spec["q_grid"],
        "a_grid": spec["a_grid"],
        "break_even_accuracy": thresholds,
        "policy_surface": surfaces,
        "authority_boundary": (
            "Empirical policy design analysis only. It estimates the selective "
            "gate surface from randomized EXP-003 cells and does not establish "
            "a deployed gate or production prevalence."
        ),
    }


def to_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# GATE-001 Empirical Policy Surface",
        "",
        "## Break-even semantic-signal accuracy vs NO_HINT",
        "",
        "| q | Arithmetic point | Arithmetic 95% | Log point | Log 95% |",
        "| ---: | ---: | --- | ---: | --- |",
    ]

    for qkey, row in result["break_even_accuracy"].items():
        def fmt(metric: dict[str, Any]) -> tuple[str, str]:
            p = metric["point"]
            b = metric["bootstrap"]
            point = "NA" if p is None else f"{p:.3f}"
            ci = "NA" if b["ci95"] is None else f"[{b['ci95'][0]:.3f}, {b['ci95'][1]:.3f}]"
            return point, ci
        ap, ac = fmt(row["arithmetic"])
        lp, lc = fmt(row["log"])
        lines.append(f"| {qkey} | {ap} | {ac} | {lp} | {lc} |")

    lines += [
        "",
        "## Selected accuracy grid vs NO_HINT",
        "",
        "| q | a | Arithmetic gate/nohint | Arithmetic 95% | Log gate/nohint | Log 95% |",
        "| ---: | ---: | ---: | --- | ---: | --- |",
    ]

    for qkey, by_a in result["policy_surface"].items():
        for akey, row in by_a.items():
            ar = row["arithmetic_total_work"]
            lg = row["log_total_work"]
            lines.append(
                f"| {qkey} | {akey} | {ar['gate_over_nohint']:.3f} | "
                f"[{ar['gate_over_nohint_ci95'][0]:.3f}, {ar['gate_over_nohint_ci95'][1]:.3f}] | "
                f"{lg['gate_over_nohint']:.3f} | "
                f"[{lg['gate_over_nohint_ci95'][0]:.3f}, {lg['gate_over_nohint_ci95'][1]:.3f}] |"
            )

    lines += [
        "",
        "These are randomized-EXP-003 policy projections, not a new execution experiment.",
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
