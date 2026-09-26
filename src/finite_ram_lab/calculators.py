from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_matrix
from scipy.stats import genpareto, qmc, rankdata


CATALOG: dict[str, dict[str, Any]] = {
    "changepoint": {
        "purpose": "Find a single performance-regime breakpoint with segmented linear regression.",
        "input": "CSV/JSON table",
        "params": {"x": "column", "y": "column", "min_segment": 3},
    },
    "exact_oracle": {
        "purpose": "Solve a bounded offline residency problem exactly with MILP.",
        "input": "JSON object containing trace",
        "params": {"capacity": 3, "page_sizes": {}, "miss_costs": None},
    },
    "info_gain": {
        "purpose": "Measure conditional information gain I(target; added | observed) in bits.",
        "input": "CSV/JSON table",
        "params": {"target": "next_page", "observed": ["os_state"], "added": ["app_phase"]},
    },
    "system_id": {
        "purpose": "Fit a small ARX model and select the best input delay by BIC.",
        "input": "CSV/JSON table ordered by time",
        "params": {"input": "demand", "output": "latency", "max_delay": 10},
    },
    "tail_fit": {
        "purpose": "Fit a generalized Pareto distribution above a high threshold.",
        "input": "CSV/JSON table",
        "params": {"value": "latency_ms", "threshold_quantile": 0.95},
    },
    "qmc_design": {
        "purpose": "Generate Sobol or Latin-hypercube parameter designs for controlled experiments.",
        "input": None,
        "params": {
            "method": "sobol",
            "n": 128,
            "parameters": [{"name": "ram_mib", "min": 128, "max": 512}],
        },
    },
    "prcc": {
        "purpose": "Rank parameter influence with partial rank correlation coefficients.",
        "input": "CSV/JSON table",
        "params": {"inputs": ["ram_mib", "scan_len"], "output": "latency_ms"},
    },
}


def _read_table(path: str | Path) -> pd.DataFrame:
    p = Path(path)
    if p.suffix.lower() == ".csv":
        return pd.read_csv(p)
    if p.suffix.lower() in {".json", ".jsonl"}:
        if p.suffix.lower() == ".jsonl":
            return pd.read_json(p, lines=True)
        raw = json.loads(p.read_text())
        if isinstance(raw, list):
            return pd.DataFrame(raw)
        if isinstance(raw, dict) and "rows" in raw:
            return pd.DataFrame(raw["rows"])
        return pd.DataFrame(raw)
    raise ValueError(f"unsupported table format: {p.suffix}")


def _fit_line(x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, float]:
    X = np.column_stack([np.ones(len(x)), x])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    residual = y - X @ beta
    return beta, float(np.sum(residual * residual))


def changepoint(path: str | Path, params: dict[str, Any]) -> dict[str, Any]:
    df = _read_table(path)
    x_name = str(params["x"])
    y_name = str(params["y"])
    min_segment = int(params.get("min_segment", 3))
    x = df[x_name].to_numpy(dtype=float)
    y = df[y_name].to_numpy(dtype=float)
    if len(x) < 2 * min_segment:
        raise ValueError("not enough rows for declared min_segment")
    order = np.argsort(x)
    x = x[order]
    y = y[order]

    base_beta, base_sse = _fit_line(x, y)
    best: tuple[float, int, np.ndarray, np.ndarray] | None = None
    for i in range(min_segment, len(x) - min_segment + 1):
        left_beta, left_sse = _fit_line(x[:i], y[:i])
        right_beta, right_sse = _fit_line(x[i:], y[i:])
        sse = left_sse + right_sse
        if best is None or sse < best[0]:
            best = (sse, i, left_beta, right_beta)
    assert best is not None
    seg_sse, i, left_beta, right_beta = best
    n = len(x)
    eps = 1e-15
    base_bic = n * math.log(max(base_sse / n, eps)) + 2 * math.log(n)
    seg_bic = n * math.log(max(seg_sse / n, eps)) + 5 * math.log(n)
    boundary = float((x[i - 1] + x[i]) / 2)
    return {
        "tool": "changepoint",
        "rows": n,
        "x": x_name,
        "y": y_name,
        "breakpoint": boundary,
        "left_last_x": float(x[i - 1]),
        "right_first_x": float(x[i]),
        "left": {"intercept": float(left_beta[0]), "slope": float(left_beta[1])},
        "right": {"intercept": float(right_beta[0]), "slope": float(right_beta[1])},
        "baseline_sse": base_sse,
        "segmented_sse": seg_sse,
        "delta_bic_baseline_minus_segmented": float(base_bic - seg_bic),
        "interpretation_hint": "positive delta_bic favors the segmented model",
    }


def _load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text())


def exact_oracle(path: str | Path, params: dict[str, Any]) -> dict[str, Any]:
    payload = _load_json(path)
    trace = payload["trace"] if isinstance(payload, dict) else payload
    trace = [str(x) for x in trace]
    if not trace:
        raise ValueError("trace must not be empty")
    capacity = float(params["capacity"])
    pages = sorted(set(trace))
    sizes = {p: 1.0 for p in pages}
    for k, v in (params.get("page_sizes") or {}).items():
        sizes[str(k)] = float(v)
    if any(sizes[p] <= 0 for p in pages):
        raise ValueError("page sizes must be positive")
    if any(sizes[p] > capacity for p in pages):
        raise ValueError("capacity cannot hold an accessed page")

    per_page_costs = {
        str(k): float(v) for k, v in (params.get("page_miss_costs") or {}).items()
    }
    access_costs = params.get("miss_costs")
    if access_costs is None:
        costs = [per_page_costs.get(p, 1.0) for p in trace]
    else:
        costs = [float(x) for x in access_costs]
        if len(costs) != len(trace):
            raise ValueError("miss_costs length must match trace length")

    T = len(trace)
    P = len(pages)
    pidx = {p: i for i, p in enumerate(pages)}
    nx = T * P
    nvar = nx + T

    def xid(p: str, t: int) -> int:
        return t * P + pidx[p]

    def mid(t: int) -> int:
        return nx + t

    c = np.zeros(nvar)
    for t, cost in enumerate(costs):
        c[mid(t)] = cost

    rows: list[int] = []
    cols: list[int] = []
    vals: list[float] = []
    lbs: list[float] = []
    ubs: list[float] = []
    row = 0

    def add(
        coeff: dict[int, float],
        lb: float = -np.inf,
        ub: float = np.inf,
    ) -> None:
        nonlocal row
        for j, value in coeff.items():
            rows.append(row)
            cols.append(j)
            vals.append(float(value))
        lbs.append(float(lb))
        ubs.append(float(ub))
        row += 1

    for t, accessed in enumerate(trace):
        add({xid(accessed, t): 1.0}, 1.0, 1.0)
        if t == 0:
            add({mid(t): 1.0}, 1.0, 1.0)
            for p in pages:
                if p != accessed:
                    add({xid(p, 0): 1.0}, 0.0, 0.0)
        else:
            add({mid(t): 1.0, xid(accessed, t - 1): 1.0}, 1.0, np.inf)
            for p in pages:
                if p != accessed:
                    add(
                        {xid(p, t): 1.0, xid(p, t - 1): -1.0},
                        -np.inf,
                        0.0,
                    )
        add(
            {xid(p, t): sizes[p] for p in pages},
            -np.inf,
            capacity,
        )

    A = coo_matrix((vals, (rows, cols)), shape=(row, nvar)).tocsr()
    result = milp(
        c,
        integrality=np.ones(nvar),
        bounds=Bounds(np.zeros(nvar), np.ones(nvar)),
        constraints=LinearConstraint(A, np.asarray(lbs), np.asarray(ubs)),
        options={"disp": False},
    )
    if not result.success or result.x is None:
        return {
            "tool": "exact_oracle",
            "status": "ERROR",
            "message": result.message,
        }

    x = result.x[:nx].reshape(T, P)
    misses = np.rint(result.x[nx:]).astype(int)
    schedule = [
        {
            "t": t,
            "access": trace[t],
            "miss": int(misses[t]),
            "resident_after": [
                pages[i] for i, value in enumerate(x[t]) if value > 0.5
            ],
        }
        for t in range(T)
    ]
    return {
        "tool": "exact_oracle",
        "status": "OPTIMAL",
        "capacity": capacity,
        "pages": pages,
        "accesses": T,
        "misses": int(misses.sum()),
        "weighted_miss_cost": float(result.fun),
        "schedule": schedule,
    }


def _conditional_entropy(
    df: pd.DataFrame,
    target: str,
    conditioning: list[str],
) -> float:
    if not conditioning:
        counts = df[target].value_counts(dropna=False).to_numpy(dtype=float)
        probs = counts / counts.sum()
        return float(-(probs * np.log2(probs)).sum())

    total = len(df)
    entropy = 0.0
    grouper = conditioning[0] if len(conditioning) == 1 else conditioning
    for _, group in df.groupby(grouper, dropna=False, sort=False):
        counts = group[target].value_counts(dropna=False).to_numpy(dtype=float)
        probs = counts / counts.sum()
        entropy += (len(group) / total) * float(
            -(probs * np.log2(probs)).sum()
        )
    return entropy


def info_gain(path: str | Path, params: dict[str, Any]) -> dict[str, Any]:
    df = _read_table(path)
    target = str(params["target"])
    observed = [str(x) for x in params.get("observed", [])]
    added = [str(x) for x in params.get("added", [])]
    h_before = _conditional_entropy(df, target, observed)
    h_after = _conditional_entropy(df, target, observed + added)
    gain = h_before - h_after
    return {
        "tool": "info_gain",
        "rows": len(df),
        "target": target,
        "observed": observed,
        "added": added,
        "conditional_entropy_before_bits": h_before,
        "conditional_entropy_after_bits": h_after,
        "information_gain_bits": gain,
        "fraction_of_remaining_uncertainty_removed": (
            gain / h_before if h_before > 0 else 0.0
        ),
    }


def system_id(path: str | Path, params: dict[str, Any]) -> dict[str, Any]:
    df = _read_table(path)
    input_col = str(params["input"])
    output_col = str(params["output"])
    max_delay = int(params.get("max_delay", 10))
    x = df[input_col].to_numpy(dtype=float)
    y = df[output_col].to_numpy(dtype=float)
    if len(x) != len(y) or len(x) < max_delay + 5:
        raise ValueError("insufficient rows for max_delay")

    candidates = []
    for delay in range(max_delay + 1):
        start = max(1, delay)
        target = y[start:]
        ylag = y[start - 1 : -1]
        xin = x[start - delay : len(x) - delay]
        X = np.column_stack([np.ones(len(target)), ylag, xin])
        beta, *_ = np.linalg.lstsq(X, target, rcond=None)
        pred = X @ beta
        residual = target - pred
        rss = float(np.sum(residual * residual))
        n = len(target)
        k = X.shape[1]
        bic = n * math.log(max(rss / n, 1e-15)) + k * math.log(n)
        tss = float(np.sum((target - target.mean()) ** 2))
        r2 = 1.0 - rss / tss if tss > 0 else 0.0
        candidates.append(
            {
                "delay": delay,
                "intercept": float(beta[0]),
                "ar1": float(beta[1]),
                "input_gain": float(beta[2]),
                "rss": rss,
                "bic": bic,
                "r2": r2,
                "residual_std": float(
                    np.std(
                        residual,
                        ddof=min(1, len(residual) - 1),
                    )
                ),
            }
        )
    best = min(candidates, key=lambda r: r["bic"])
    return {
        "tool": "system_id",
        "model": "ARX(1,1) with integer input delay",
        "input": input_col,
        "output": output_col,
        "best": best,
        "candidates": candidates,
    }


def tail_fit(path: str | Path, params: dict[str, Any]) -> dict[str, Any]:
    df = _read_table(path)
    value_col = str(params["value"])
    threshold_q = float(params.get("threshold_quantile", 0.95))
    values = df[value_col].dropna().to_numpy(dtype=float)
    if not 0.5 <= threshold_q < 1.0:
        raise ValueError("threshold_quantile must be in [0.5, 1)")
    threshold = float(np.quantile(values, threshold_q))
    excess = values[values > threshold] - threshold
    if len(excess) < 20:
        raise ValueError("need at least 20 exceedances for the initial tail fit")

    shape, _, scale = genpareto.fit(excess, floc=0.0)
    exceedance_rate = len(excess) / len(values)
    requested_probs = [
        float(x)
        for x in params.get(
            "tail_probabilities",
            [0.01, 0.001],
        )
    ]
    return_levels: dict[str, float | None] = {}
    for probability in requested_probs:
        if probability <= 0 or probability >= exceedance_rate:
            return_levels[str(probability)] = None
            continue
        level = threshold + genpareto.ppf(
            1.0 - probability / exceedance_rate,
            shape,
            loc=0.0,
            scale=scale,
        )
        return_levels[str(probability)] = float(level)

    return {
        "tool": "tail_fit",
        "value": value_col,
        "rows": len(values),
        "threshold_quantile": threshold_q,
        "threshold": threshold,
        "exceedances": int(len(excess)),
        "exceedance_rate": exceedance_rate,
        "gpd_shape": float(shape),
        "gpd_scale": float(scale),
        "return_levels": return_levels,
    }


def qmc_design(params: dict[str, Any]) -> dict[str, Any]:
    method = str(params.get("method", "sobol"))
    n = int(params.get("n", 128))
    seed = int(params.get("seed", 20260926))
    parameters = params["parameters"]
    names = [str(p["name"]) for p in parameters]
    lows = np.asarray([float(p["min"]) for p in parameters])
    highs = np.asarray([float(p["max"]) for p in parameters])
    if np.any(highs <= lows):
        raise ValueError("each parameter max must exceed min")

    d = len(names)
    if method == "sobol":
        engine = qmc.Sobol(d=d, scramble=True, seed=seed)
        if n > 0 and n & (n - 1) == 0:
            unit = engine.random_base2(int(math.log2(n)))
        else:
            unit = engine.random(n)
    elif method in {"latin_hypercube", "lhs"}:
        engine = qmc.LatinHypercube(d=d, seed=seed)
        unit = engine.random(n)
    else:
        raise ValueError("method must be sobol or latin_hypercube")

    samples = qmc.scale(unit, lows, highs)
    rows = [
        {
            "sample_id": i,
            **{
                name: float(samples[i, j])
                for j, name in enumerate(names)
            },
        }
        for i in range(n)
    ]
    return {
        "tool": "qmc_design",
        "method": method,
        "seed": seed,
        "n": n,
        "parameters": parameters,
        "samples": rows,
    }


def _residualize(
    target: np.ndarray,
    controls: np.ndarray,
) -> np.ndarray:
    if controls.size == 0:
        return target - target.mean()
    X = np.column_stack([np.ones(len(target)), controls])
    beta, *_ = np.linalg.lstsq(X, target, rcond=None)
    return target - X @ beta


def prcc(path: str | Path, params: dict[str, Any]) -> dict[str, Any]:
    df = _read_table(path)
    inputs = [str(x) for x in params["inputs"]]
    output = str(params["output"])
    ranked_inputs = np.column_stack(
        [
            rankdata(df[col].to_numpy(dtype=float))
            for col in inputs
        ]
    )
    ranked_output = rankdata(
        df[output].to_numpy(dtype=float)
    )

    results = []
    for i, name in enumerate(inputs):
        controls = np.delete(ranked_inputs, i, axis=1)
        rx = _residualize(ranked_inputs[:, i], controls)
        ry = _residualize(ranked_output, controls)
        denom = float(
            np.sqrt(
                np.sum(rx * rx) * np.sum(ry * ry)
            )
        )
        coeff = (
            float(np.sum(rx * ry) / denom)
            if denom > 0
            else 0.0
        )
        results.append(
            {
                "parameter": name,
                "prcc": coeff,
                "abs_prcc": abs(coeff),
            }
        )

    results.sort(
        key=lambda r: r["abs_prcc"],
        reverse=True,
    )
    return {
        "tool": "prcc",
        "rows": len(df),
        "output": output,
        "ranking": results,
    }


def run_tool(
    tool: str,
    input_path: str | Path | None,
    params: dict[str, Any],
) -> dict[str, Any]:
    if tool == "changepoint":
        if input_path is None:
            raise ValueError("changepoint requires input")
        return changepoint(input_path, params)
    if tool == "exact_oracle":
        if input_path is None:
            raise ValueError("exact_oracle requires input")
        return exact_oracle(input_path, params)
    if tool == "info_gain":
        if input_path is None:
            raise ValueError("info_gain requires input")
        return info_gain(input_path, params)
    if tool == "system_id":
        if input_path is None:
            raise ValueError("system_id requires input")
        return system_id(input_path, params)
    if tool == "tail_fit":
        if input_path is None:
            raise ValueError("tail_fit requires input")
        return tail_fit(input_path, params)
    if tool == "qmc_design":
        return qmc_design(params)
    if tool == "prcc":
        if input_path is None:
            raise ValueError("prcc requires input")
        return prcc(input_path, params)
    raise ValueError(f"unknown tool: {tool}")


def run_spec(spec_path: str | Path) -> dict[str, Any]:
    spec_path = Path(spec_path)
    spec = json.loads(spec_path.read_text())
    tool = str(spec["tool"])
    raw_input = spec.get("input")
    input_path: Path | None = None
    if raw_input:
        candidate = Path(raw_input)
        input_path = (
            candidate
            if candidate.is_absolute()
            else (spec_path.parent / candidate).resolve()
        )
    result = run_tool(
        tool,
        input_path,
        dict(spec.get("params") or {}),
    )
    return {
        "task_id": spec.get("task_id"),
        "tool": tool,
        "spec_path": str(spec_path),
        "result": result,
    }


def template(tool: str) -> dict[str, Any]:
    if tool not in CATALOG:
        raise ValueError(f"unknown tool: {tool}")
    entry = CATALOG[tool]
    return {
        "task_id": f"{tool.upper()}-001",
        "tool": tool,
        "input": (
            "relative/path/to/input.csv"
            if entry["input"]
            else None
        ),
        "params": entry["params"],
    }
