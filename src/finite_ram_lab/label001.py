from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import rankdata, spearmanr


def _sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _as_bool(series: pd.Series) -> np.ndarray:
    if series.dtype == bool:
        return series.to_numpy(dtype=bool)
    values = series.astype(str).str.lower()
    if not values.isin({"true", "false"}).all():
        raise ValueError("aligned column is not boolean-like")
    return values.map({"true": True, "false": False}).to_numpy(dtype=bool)


def _ratio_ci(values: np.ndarray) -> list[float]:
    finite = values[np.isfinite(values)]
    if len(finite) == 0:
        return [float("nan"), float("nan")]
    return [
        float(np.quantile(finite, 0.025)),
        float(np.quantile(finite, 0.975)),
    ]


def _confusion_metrics(tp: float, fp: float, fn: float, tn: float) -> dict[str, float]:
    total = tp + fp + fn + tn
    pos = tp + fn
    neg = tn + fp
    if total <= 0 or pos <= 0 or neg <= 0:
        raise ValueError("insufficient binary class support")
    return {
        "prevalence": float(pos / total),
        "sensitivity": float(tp / pos),
        "specificity": float(tn / neg),
        "agreement": float((tp + tn) / total),
    }


def _confusion_for_frame(df: pd.DataFrame, gap_column: str) -> dict[str, Any]:
    gap = df[gap_column].to_numpy(dtype=float)
    assigned_misaligned = ~_as_bool(df["aligned"])

    observable_misaligned = gap < 0.0
    observable_aligned = gap > 0.0
    binary = observable_misaligned | observable_aligned

    pred = assigned_misaligned[binary]
    truth = observable_misaligned[binary]

    tp = int(np.count_nonzero(pred & truth))
    fp = int(np.count_nonzero(pred & ~truth))
    fn = int(np.count_nonzero(~pred & truth))
    tn = int(np.count_nonzero(~pred & ~truth))
    metrics = _confusion_metrics(tp, fp, fn, tn)

    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "ambiguous": int(np.count_nonzero(~binary)),
        "binary_trials": int(np.count_nonzero(binary)),
        **metrics,
    }


def _bootstrap_confusion(
    df: pd.DataFrame,
    *,
    gap_column: str,
    resamples: int,
    seed: int,
) -> dict[str, Any]:
    blocks = np.asarray(sorted(df["block"].unique()), dtype=int)
    if len(blocks) == 0:
        raise ValueError("no runner blocks")

    rows = []
    for block in blocks:
        g = df[df["block"] == block]
        c = _confusion_for_frame(g, gap_column)
        rows.append([c["tp"], c["fp"], c["fn"], c["tn"]])

    stats = np.asarray(rows, dtype=float)
    rng = np.random.default_rng(seed)
    draw = rng.integers(0, len(blocks), size=(resamples, len(blocks)))
    summed = stats[draw].sum(axis=1)

    tp, fp, fn, tn = (
        summed[:, 0],
        summed[:, 1],
        summed[:, 2],
        summed[:, 3],
    )
    total = tp + fp + fn + tn
    pos = tp + fn
    neg = tn + fp

    prevalence = np.divide(pos, total, out=np.full_like(pos, np.nan), where=total > 0)
    sensitivity = np.divide(tp, pos, out=np.full_like(tp, np.nan), where=pos > 0)
    specificity = np.divide(tn, neg, out=np.full_like(tn, np.nan), where=neg > 0)
    agreement = np.divide(tp + tn, total, out=np.full_like(tp, np.nan), where=total > 0)

    return {
        "resamples": int(resamples),
        "seed": int(seed),
        "ci95": {
            "prevalence": _ratio_ci(prevalence),
            "sensitivity": _ratio_ci(sensitivity),
            "specificity": _ratio_ci(specificity),
            "agreement": _ratio_ci(agreement),
        },
    }


def _weighted_corr_from_sums(
    n: np.ndarray,
    sx: np.ndarray,
    sy: np.ndarray,
    sxx: np.ndarray,
    syy: np.ndarray,
    sxy: np.ndarray,
) -> np.ndarray:
    mx = sx / n
    my = sy / n
    vx = sxx / n - mx * mx
    vy = syy / n - my * my
    cov = sxy / n - mx * my
    denom = np.sqrt(np.maximum(vx, 0.0) * np.maximum(vy, 0.0))
    return np.divide(
        cov,
        denom,
        out=np.full_like(cov, np.nan, dtype=float),
        where=denom > 0.0,
    )


def _spearman_cluster_bootstrap(
    df: pd.DataFrame,
    *,
    gap_column: str,
    resamples: int,
    seed: int,
) -> dict[str, Any]:
    x = df[gap_column].to_numpy(dtype=float)
    y = np.log(np.maximum(df["hot_retouch_ms"].to_numpy(dtype=float), 1e-12))

    point = float(spearmanr(x, y).statistic)

    # Freeze pooled ranks once, then bootstrap runner blocks as weights.
    # This keeps the interval cluster-aware without 100k expensive rerank operations.
    xr = rankdata(x, method="average").astype(float)
    yr = rankdata(y, method="average").astype(float)

    blocks = np.asarray(sorted(df["block"].unique()), dtype=int)
    bstats = []
    block_values = df["block"].to_numpy(dtype=int)
    for block in blocks:
        mask = block_values == block
        xb = xr[mask]
        yb = yr[mask]
        bstats.append([
            float(mask.sum()),
            float(xb.sum()),
            float(yb.sum()),
            float(np.dot(xb, xb)),
            float(np.dot(yb, yb)),
            float(np.dot(xb, yb)),
        ])
    bstats = np.asarray(bstats, dtype=float)

    rng = np.random.default_rng(seed)
    draw = rng.integers(0, len(blocks), size=(resamples, len(blocks)))
    summed = bstats[draw].sum(axis=1)
    rho = _weighted_corr_from_sums(
        summed[:, 0],
        summed[:, 1],
        summed[:, 2],
        summed[:, 3],
        summed[:, 4],
        summed[:, 5],
    )

    return {
        "point_spearman_rho": point,
        "bootstrap_method": "runner-block bootstrap on frozen pooled rank transform",
        "resamples": int(resamples),
        "seed": int(seed),
        "ci95": _ratio_ci(rho),
    }


def _geom(values: pd.Series) -> float:
    arr = np.maximum(values.to_numpy(dtype=float), 1e-12)
    return float(math.exp(np.log(arr).mean()))


def analyze(spec: dict[str, Any], trials_path: str | Path) -> dict[str, Any]:
    actual_digest = _sha256(trials_path)
    if actual_digest != spec["source_member_sha256"]:
        raise ValueError("trials.csv SHA-256 mismatch")

    df = pd.read_csv(trials_path)
    required = {
        "block",
        "memory_high_mib",
        "aligned",
        "arm",
        "hot_fraction",
        "cold_fraction",
        "hot_first16_fraction",
        "cold_first16_fraction",
        "hot_retouch_ms",
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"missing required columns: {sorted(missing)}")

    df = df[
        (df["arm"] == spec["required_arm"])
        & df["memory_high_mib"].isin(spec["required_pressures_mib"])
    ].copy()

    if len(df) != int(spec["expected_trials"]):
        raise ValueError("unexpected LABEL-001 trial count")
    if df["block"].nunique() != int(spec["expected_runner_blocks"]):
        raise ValueError("unexpected LABEL-001 runner-block count")
    if set(map(int, df["memory_high_mib"].unique())) != set(
        map(int, spec["required_pressures_mib"])
    ):
        raise ValueError("pressure support mismatch")

    df["residency_gap"] = df["hot_fraction"] - df["cold_fraction"]
    df["residency_gap_first16"] = (
        df["hot_first16_fraction"] - df["cold_first16_fraction"]
    )

    primary = _confusion_for_frame(df, "residency_gap")
    bootstrap = _bootstrap_confusion(
        df,
        gap_column="residency_gap",
        resamples=int(spec["cluster_bootstrap_resamples"]),
        seed=int(spec["cluster_bootstrap_seed"]),
    )

    pressure = {}
    for level in sorted(map(int, spec["required_pressures_mib"])):
        g = df[df["memory_high_mib"] == level]
        pressure[str(level)] = _confusion_for_frame(g, "residency_gap")

    mechanism = _spearman_cluster_bootstrap(
        df,
        gap_column="residency_gap",
        resamples=int(spec["cluster_bootstrap_resamples"]),
        seed=int(spec["cluster_bootstrap_seed"]) + 1,
    )

    gap = df["residency_gap"].to_numpy(dtype=float)
    observable_misaligned = gap < 0.0
    observable_aligned = gap > 0.0

    latency = {
        "observable_misaligned_trials": int(observable_misaligned.sum()),
        "observable_aligned_trials": int(observable_aligned.sum()),
        "ambiguous_trials": int((gap == 0.0).sum()),
        "geometric_hot_retouch_ms_misaligned": (
            _geom(df.loc[observable_misaligned, "hot_retouch_ms"])
            if observable_misaligned.any()
            else None
        ),
        "geometric_hot_retouch_ms_aligned": (
            _geom(df.loc[observable_aligned, "hot_retouch_ms"])
            if observable_aligned.any()
            else None
        ),
    }

    secondary = _confusion_for_frame(df, "residency_gap_first16")

    return {
        "analysis_id": "LABEL-001",
        "status": "PASS",
        "provenance": {
            "source_run": int(spec["source_run"]),
            "source_artifact_id": int(spec["source_artifact_id"]),
            "source_artifact_name": str(spec["source_artifact_name"]),
            "source_artifact_sha256": str(spec["source_artifact_sha256"]),
            "source_member": str(spec["source_member"]),
            "source_member_sha256": actual_digest,
        },
        "selection": {
            "arm": str(spec["required_arm"]),
            "pressures_mib": list(map(int, spec["required_pressures_mib"])),
            "runner_blocks": int(df["block"].nunique()),
            "trials": int(len(df)),
        },
        "primary_whole_region": {
            "confusion": primary,
            "runner_block_bootstrap": bootstrap,
            "pressure_stratified": pressure,
            "mechanism_association": mechanism,
            "latency_descriptive": latency,
        },
        "secondary_first16": {
            "confusion": secondary,
            "authority": "SECONDARY_SENSITIVITY_ONLY",
        },
        "interpretation_boundary": (
            "Retrospective NO_HINT label audit only. "
            "No provider is trained or certified and no memory action is authorized."
        ),
    }


def to_markdown(result: dict[str, Any]) -> str:
    p = result["primary_whole_region"]
    c = p["confusion"]
    ci = p["runner_block_bootstrap"]["ci95"]
    m = p["mechanism_association"]
    lat = p["latency_descriptive"]

    lines = [
        "# LABEL-001 Natural Residency Outcome Audit",
        "",
        "## Whole-region primary audit",
        "",
        f"- TP / FP / FN / TN: {c['tp']} / {c['fp']} / {c['fn']} / {c['tn']}",
        f"- ambiguous: {c['ambiguous']}",
        f"- observable-misalignment prevalence: {c['prevalence']:.4f} "
        f"(95% cluster bootstrap [{ci['prevalence'][0]:.4f}, {ci['prevalence'][1]:.4f}])",
        f"- assignment-proxy sensitivity: {c['sensitivity']:.4f} "
        f"(95% [{ci['sensitivity'][0]:.4f}, {ci['sensitivity'][1]:.4f}])",
        f"- assignment-proxy specificity: {c['specificity']:.4f} "
        f"(95% [{ci['specificity'][0]:.4f}, {ci['specificity'][1]:.4f}])",
        f"- agreement: {c['agreement']:.4f} "
        f"(95% [{ci['agreement'][0]:.4f}, {ci['agreement'][1]:.4f}])",
        "",
        "## Mechanism check",
        "",
        f"- Spearman rho(residency gap, log HOT retouch): {m['point_spearman_rho']:.4f}",
        f"- cluster-bootstrap 95%: [{m['ci95'][0]:.4f}, {m['ci95'][1]:.4f}]",
        f"- geometric HOT-retouch ms, observable misaligned: "
        f"{lat['geometric_hot_retouch_ms_misaligned']:.3f}",
        f"- geometric HOT-retouch ms, observable aligned: "
        f"{lat['geometric_hot_retouch_ms_aligned']:.3f}",
        "",
        "## Pressure-stratified descriptive audit",
        "",
        "| MemoryHigh MiB | TP | FP | FN | TN | Sensitivity | Specificity | Agreement |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for level, row in p["pressure_stratified"].items():
        lines.append(
            f"| {level} | {row['tp']} | {row['fp']} | {row['fn']} | {row['tn']} | "
            f"{row['sensitivity']:.4f} | {row['specificity']:.4f} | {row['agreement']:.4f} |"
        )

    s = result["secondary_first16"]["confusion"]
    lines += [
        "",
        "## First-16-MiB sensitivity analysis",
        "",
        f"- sensitivity: {s['sensitivity']:.4f}",
        f"- specificity: {s['specificity']:.4f}",
        f"- agreement: {s['agreement']:.4f}",
        f"- ambiguous: {s['ambiguous']}",
        "",
        "This analysis is retrospective and does not certify a provider or authorize ACT.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--spec", required=True)
    p.add_argument("--trials", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--markdown")
    args = p.parse_args()

    spec = json.loads(Path(args.spec).read_text())
    result = analyze(spec, args.trials)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    if args.markdown:
        Path(args.markdown).write_text(to_markdown(result))
    print(to_markdown(result))


if __name__ == "__main__":
    main()
