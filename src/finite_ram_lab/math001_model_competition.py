from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


Q_PANEL = (1, 2, 4, 8, 16, 32, 64, 128)


def load_evidence(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if int(data["version"]) != 1:
        raise ValueError("unsupported evidence version")
    return data


def _log2_choose(n: int, k: int) -> float:
    if k < 0 or k > n:
        return math.inf
    if k == 0 or k == n:
        return 0.0
    return (
        math.lgamma(n + 1)
        - math.lgamma(k + 1)
        - math.lgamma(n - k + 1)
    ) / math.log(2.0)


def _reconstruct(trial: dict[str, Any], steps: int = 256) -> list[float]:
    deltas = [0.0] * (steps + 1)
    by_step = {int(e["step"]): float(e["delta_pages"]) for e in trial["events"]}
    cur = 0.0
    for step in range(1, steps + 1):
        cur += by_step.get(step, 0.0)
        deltas[step] = cur
    return deltas


def _negative_steps(trial: dict[str, Any]) -> list[int]:
    return sorted(
        int(e["step"])
        for e in trial["events"]
        if float(e["delta_pages"]) < 0
    )


def _positive_steps(trial: dict[str, Any]) -> list[int]:
    return sorted(
        int(e["step"])
        for e in trial["events"]
        if float(e["delta_pages"]) > 0
    )


def _segments(trial: dict[str, Any], steps: int = 256) -> list[tuple[int, int]]:
    neg = _negative_steps(trial)
    bounds = [0, *neg, steps + 1]
    return [(bounds[i], bounds[i + 1] - 1) for i in range(len(bounds) - 1)]


def _stair_values(length: int, q: int, phase: int) -> list[float]:
    base = math.floor(phase / q)
    return [
        float(q * (math.floor((n + phase) / q) - base))
        for n in range(length + 1)
    ]


def _fit_segment_residual(
    observed: list[float],
    q: int,
) -> dict[str, Any]:
    best: dict[str, Any] | None = None
    for phase in range(q):
        pred = _stair_values(len(observed) - 1, q, phase)
        resid = [o - p for o, p in zip(observed, pred)]
        sse = sum(r * r for r in resid)
        mae = sum(abs(r) for r in resid) / len(resid)
        max_abs = max(abs(r) for r in resid)
        row = {
            "phase": phase,
            "sse": sse,
            "rmse": math.sqrt(sse / len(resid)),
            "mae": mae,
            "max_abs": max_abs,
        }
        if best is None or (row["sse"], phase) < (best["sse"], best["phase"]):
            best = row
    assert best is not None
    return best


def residual_scores(
    trial: dict[str, Any],
    q: int,
    *,
    reset_aware: bool,
    steps: int = 256,
) -> dict[str, Any]:
    y = _reconstruct(trial, steps)
    if reset_aware:
        ranges = _segments(trial, steps)
    else:
        ranges = [(0, steps)]

    total_sse = 0.0
    total_abs = 0.0
    count = 0
    max_abs = 0.0
    phases: list[dict[str, Any]] = []

    for start, end in ranges:
        baseline = y[start]
        obs = [y[n] - baseline for n in range(start, end + 1)]
        fit = _fit_segment_residual(obs, q)
        phases.append({"start": start, "end": end, "phase": fit["phase"]})
        total_sse += fit["sse"]
        total_abs += fit["mae"] * len(obs)
        count += len(obs)
        max_abs = max(max_abs, fit["max_abs"])

    return {
        "q": q,
        "reset_aware": reset_aware,
        "sse": total_sse,
        "rmse": math.sqrt(total_sse / count),
        "mae": total_abs / count,
        "max_abs": max_abs,
        "segments": phases,
    }


def linear_score(trial: dict[str, Any], steps: int = 256) -> dict[str, Any]:
    y = _reconstruct(trial, steps)
    xs = list(range(steps + 1))
    denom = sum(x * x for x in xs)
    beta = sum(x * yy for x, yy in zip(xs, y)) / denom
    resid = [yy - beta * x for x, yy in zip(xs, y)]
    sse = sum(r * r for r in resid)
    return {
        "beta": beta,
        "sse": sse,
        "rmse": math.sqrt(sse / len(resid)),
        "mae": sum(abs(r) for r in resid) / len(resid),
        "max_abs": max(abs(r) for r in resid),
    }


def _predicted_positions(length: int, q: int, phase: int) -> set[int]:
    vals = _stair_values(length, q, phase)
    return {
        n for n in range(1, length + 1)
        if vals[n] > vals[n - 1]
    }


def segment_mdl(
    observed_positive_local: set[int],
    length: int,
    q: int,
) -> dict[str, Any]:
    k = len(observed_positive_local)
    arbitrary = _log2_choose(length, k)
    best: dict[str, Any] | None = None

    for phase in range(q):
        pred = _predicted_positions(length, q, phase)
        extras = observed_positive_local - pred
        misses = pred - observed_positive_local
        cost = (
            math.log2(q)
            + _log2_choose(length, len(extras))
            + _log2_choose(length, len(misses))
        )
        row = {
            "phase": phase,
            "bits": cost,
            "extras": sorted(extras),
            "misses": sorted(misses),
            "predicted_count": len(pred),
        }
        if best is None or (row["bits"], phase) < (best["bits"], best["phase"]):
            best = row

    assert best is not None
    best["arbitrary_bits"] = arbitrary
    best["savings_bits"] = arbitrary - best["bits"]
    return best


def trial_mdl(
    trial: dict[str, Any],
    q: int,
    *,
    steps: int = 256,
) -> dict[str, Any]:
    pos = set(_positive_steps(trial))
    total_bits = 0.0
    arbitrary_bits = 0.0
    segments_out = []

    for start, end in _segments(trial, steps):
        # Reset step itself is a baseline observation. Eligible touch positions
        # begin at start+1.
        length = end - start
        local = {p - start for p in pos if start < p <= end}
        score = segment_mdl(local, length, q)
        total_bits += score["bits"]
        arbitrary_bits += score["arbitrary_bits"]
        segments_out.append(
            {
                "start": start,
                "end": end,
                "length": length,
                "observed_positive_local": sorted(local),
                **score,
            }
        )

    return {
        "q": q,
        "bits": total_bits,
        "arbitrary_bits": arbitrary_bits,
        "savings_bits": arbitrary_bits - total_bits,
        "segments": segments_out,
    }


def _heldout_for_q(
    trial: dict[str, Any],
    q: int,
    *,
    steps: int = 256,
) -> dict[str, Any]:
    positives = set(_positive_steps(trial))
    tp = fp = fn = 0
    rows = []

    for start, end in _segments(trial, steps):
        obs = sorted(p for p in positives if start < p <= end)
        if not obs:
            continue
        first = obs[0]
        predicted: list[int] = []
        p = first + q
        while p <= end:
            predicted.append(p)
            p += q
        actual = obs[1:]
        ps = set(predicted)
        ac = set(actual)
        seg_tp = len(ps & ac)
        seg_fp = len(ps - ac)
        seg_fn = len(ac - ps)
        tp += seg_tp
        fp += seg_fp
        fn += seg_fn
        rows.append(
            {
                "start": start,
                "end": end,
                "calibration_jump": first,
                "predicted": predicted,
                "actual_after_calibration": actual,
                "tp": seg_tp,
                "fp": seg_fp,
                "fn": seg_fn,
            }
        )

    precision = tp / (tp + fp) if (tp + fp) else 1.0
    recall = tp / (tp + fn) if (tp + fn) else 1.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall)
        else 0.0
    )
    return {
        "q": q,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "segments": rows,
    }


def _coherence(positions: list[int], q: int) -> float | None:
    if not positions:
        return None
    re = sum(math.cos(2 * math.pi * p / q) for p in positions)
    im = sum(math.sin(2 * math.pi * p / q) for p in positions)
    return math.sqrt(re * re + im * im) / len(positions)


def analyze(data: dict[str, Any]) -> dict[str, Any]:
    touch = sorted(
        (t for t in data["trials"] if t["mode"] == "touch"),
        key=lambda t: int(t["block"]),
    )
    controls = [t for t in data["trials"] if t["mode"] == "control"]

    per_block = []
    for trial in touch:
        stationary = {
            str(q): residual_scores(trial, q, reset_aware=False)
            for q in Q_PANEL
        }
        reset = {
            str(q): residual_scores(trial, q, reset_aware=True)
            for q in Q_PANEL
        }
        mdl = {str(q): trial_mdl(trial, q) for q in Q_PANEL}
        linear = linear_score(trial)
        per_block.append(
            {
                "block": trial["block"],
                "linear": linear,
                "stationary": stationary,
                "reset_aware": reset,
                "mdl": mdl,
                "negative_steps": _negative_steps(trial),
                "positive_steps": _positive_steps(trial),
                "coherence": {
                    str(q): _coherence(_positive_steps(trial), q)
                    for q in Q_PANEL
                },
            }
        )

    total_reset_sse = {
        q: sum(b["reset_aware"][str(q)]["sse"] for b in per_block)
        for q in Q_PANEL
    }
    total_mdl = {
        q: sum(b["mdl"][str(q)]["bits"] for b in per_block)
        for q in Q_PANEL
    }

    min_sse_q = min(Q_PANEL, key=lambda q: (total_reset_sse[q], q))
    min_mdl_q = min(Q_PANEL, key=lambda q: (total_mdl[q], q))

    folds = []
    for held in touch:
        training = [t for t in touch if t["block"] != held["block"]]
        train_mdl = {
            q: sum(trial_mdl(t, q)["bits"] for t in training)
            for q in Q_PANEL
        }
        trained_q = min(Q_PANEL, key=lambda q: (train_mdl[q], q))
        pred = _heldout_for_q(held, trained_q)
        folds.append(
            {
                "heldout_block": held["block"],
                "trained_q": trained_q,
                **pred,
            }
        )

    all_pred = {q: [_heldout_for_q(t, q) for t in touch] for q in Q_PANEL}
    q_prediction = {}
    for q in Q_PANEL:
        tp = fp = fn = 0
        for fold in all_pred[q]:
            for seg in fold["segments"]:
                tp += seg["tp"]
                fp += seg["fp"]
                fn += seg["fn"]
        precision = tp / (tp + fp) if tp + fp else 1.0
        recall = tp / (tp + fn) if tp + fn else 1.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if precision + recall
            else 0.0
        )
        q_prediction[str(q)] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }

    controls_positive = sum(len(_positive_steps(t)) for t in controls)

    q64_folds = [f for f in folds if f["trained_q"] == 64]
    decision = "MIXED_MODEL"
    if (
        min_sse_q == 64
        and min_mdl_q == 64
        and len(q64_folds) == len(folds)
        and all(abs(f["f1"] - 1.0) < 1e-12 for f in folds)
        and controls_positive == 0
    ):
        decision = "MODEL64_WINS"
    elif min_sse_q == min_mdl_q and all(
        f["trained_q"] == min_sse_q for f in folds
    ):
        decision = "OTHER_Q_WINS"

    null_probability = 64 / math.comb(256, 4)

    return {
        "experiment_id": "MATH-001-MODEL-COMPETITION-v1",
        "source_experiment": data["experiment_id"],
        "source_run": data["run_id"],
        "decision": decision,
        "minimum_reset_sse_q": min_sse_q,
        "minimum_mdl_q": min_mdl_q,
        "total_reset_sse": {str(k): v for k, v in total_reset_sse.items()},
        "total_mdl_bits": {str(k): v for k, v in total_mdl.items()},
        "q_prediction": q_prediction,
        "leave_one_block_out": folds,
        "per_block": per_block,
        "controls_positive_events": controls_positive,
        "clean_four_jump_uniform_null_probability": null_probability,
        "clean_four_jump_arbitrary_position_bits": _log2_choose(256, 4),
        "q64_phase_bits": math.log2(64),
        "inference_boundary": (
            "Mathematical model comparison over hosted MEMCG-001 evidence; "
            "does not establish hardware DRAM behavior."
        ),
    }


def render_md(result: dict[str, Any]) -> str:
    lines = [
        "# MATH-001 Model Competition Result",
        "",
        f"- decision: **{result['decision']}**",
        f"- minimum reset-aware SSE Q: **{result['minimum_reset_sse_q']} pages**",
        f"- minimum MDL Q: **{result['minimum_mdl_q']} pages**",
        f"- controls positive events: **{result['controls_positive_events']}**",
        "",
        "## Held-out prediction",
        "",
    ]
    for fold in result["leave_one_block_out"]:
        lines.append(
            f"- block {fold['heldout_block']}: Q={fold['trained_q']}, "
            f"precision={fold['precision']:.3f}, "
            f"recall={fold['recall']:.3f}, F1={fold['f1']:.3f}"
        )
    lines += [
        "",
        "## Q competition",
        "",
        "| Q pages | reset SSE | MDL bits | predictive F1 |",
        "| ---: | ---: | ---: | ---: |",
    ]
    for q in Q_PANEL:
        lines.append(
            f"| {q} | {result['total_reset_sse'][str(q)]:.3f} | "
            f"{result['total_mdl_bits'][str(q)]:.3f} | "
            f"{result['q_prediction'][str(q)]['f1']:.3f} |"
        )
    lines += [
        "",
        "## Simple combinatorial sanity check",
        "",
        f"- arbitrary positions for four jumps among 256: "
        f"{result['clean_four_jump_arbitrary_position_bits']:.3f} bits",
        f"- one Q64 phase: {result['q64_phase_bits']:.3f} bits",
        f"- conditional uniform-null exact-64-spacing probability: "
        f"{result['clean_four_jump_uniform_null_probability']:.9g}",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--json-out", required=True)
    p.add_argument("--md-out", required=True)
    args = p.parse_args()

    result = analyze(load_evidence(args.input))
    jout = Path(args.json_out)
    mout = Path(args.md_out)
    jout.parent.mkdir(parents=True, exist_ok=True)
    mout.parent.mkdir(parents=True, exist_ok=True)
    jout.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    mout.write_text(render_md(result), encoding="utf-8")
    print(json.dumps({
        "decision": result["decision"],
        "minimum_reset_sse_q": result["minimum_reset_sse_q"],
        "minimum_mdl_q": result["minimum_mdl_q"],
        "folds": [
            {
                "block": f["heldout_block"],
                "q": f["trained_q"],
                "f1": f["f1"],
            }
            for f in result["leave_one_block_out"]
        ],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
