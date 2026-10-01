from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import statistics
from typing import Any, Mapping

from finite_ram_lab.coverage_aware_governor import select_q
from finite_ram_lab.lane_concurrency_sweep import _run_fresh_child


Q_VALUES = (1, 2, 4, 7)
FUTURE_SAMPLES_PER_Q = 8
FAMILY_ALPHA = 0.05
PER_Q_ALPHA = FAMILY_ALPHA / len(Q_VALUES)

BALANCED_ORDERS = (
    (1, 2, 4, 7),
    (7, 4, 2, 1),
    (2, 1, 7, 4),
    (4, 7, 1, 2),
    (1, 2, 4, 7),
    (7, 4, 2, 1),
    (2, 1, 7, 4),
    (4, 7, 1, 2),
)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _log_beta(a: float, b: float) -> float:
    return math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)


def beta_binomial_pmf(
    k: int,
    m: int,
    *,
    alpha: float,
    beta: float,
) -> float:
    if not (0 <= k <= m):
        return 0.0
    return math.comb(m, k) * math.exp(
        _log_beta(k + alpha, m - k + beta)
        - _log_beta(alpha, beta)
    )


def beta_binomial_upper_tail(
    observed_exceedances: int,
    future_samples: int,
    *,
    calibration_sample_count: int,
) -> float:
    if calibration_sample_count <= 0:
        raise ValueError("calibration_sample_count_invalid")
    if future_samples <= 0:
        raise ValueError("future_samples_invalid")
    if not (0 <= observed_exceedances <= future_samples):
        raise ValueError("observed_exceedances_invalid")

    # For IID continuous observations, if M_n is the calibration sample maximum,
    # p = P(X_new > M_n | F(M_n)) has the distribution Beta(1, n) before seeing
    # future observations. Integrating Binomial(m, p) yields Beta-Binomial.
    return sum(
        beta_binomial_pmf(
            k,
            future_samples,
            alpha=1.0,
            beta=float(calibration_sample_count),
        )
        for k in range(observed_exceedances, future_samples + 1)
    )


def _calibration_points(
    b469: Mapping[str, Any],
    b472: Mapping[str, Any],
    b474: Mapping[str, Any],
) -> dict[int, dict[str, Any]]:
    q1_boundary = int(b472["union_empirical_max_peak_bytes"])
    q1_n = int(b472["total_sample_count"])
    points = {
        1: {
            "boundary_bytes": q1_boundary,
            "sample_count": q1_n,
            "coverage_floor": float(
                b472["rank_max_one_step_predictive_coverage_floor"]
            ),
        }
    }
    for row in b474["summary_rows"]:
        q = int(row["q"])
        points[q] = {
            "boundary_bytes": int(row["union_empirical_max_peak_bytes"]),
            "sample_count": int(row["union_sample_count"]),
            "coverage_floor": float(
                row["rank_max_one_step_predictive_coverage_floor"]
            ),
        }

    for q in Q_VALUES:
        decision = select_q(
            b469,
            b472,
            b474,
            peak_budget_bytes=points[q]["boundary_bytes"],
            minimum_rank_coverage=0.95,
        )
        if int(decision["selected_q"]) != q:
            raise RuntimeError(
                f"coverage_governor_boundary_selection_changed:q={q}:"
                f"selected={decision['selected_q']}"
            )
    return points


def _classify_q(
    *,
    q: int,
    boundary_bytes: int,
    calibration_sample_count: int,
    observed_peaks: list[int],
) -> dict[str, Any]:
    exceedances = [peak for peak in observed_peaks if peak > boundary_bytes]
    exceed_count = len(exceedances)
    tail_probability = beta_binomial_upper_tail(
        exceed_count,
        len(observed_peaks),
        calibration_sample_count=calibration_sample_count,
    )

    if exceed_count == 0:
        classification = "NO_NEW_MAX"
    elif tail_probability <= PER_Q_ALPHA:
        classification = "LOCAL_DRIFT_SUSPECT"
    else:
        classification = "TAIL_COMPATIBLE_EXCEEDANCE"

    return {
        "q": q,
        "calibration_boundary_bytes": boundary_bytes,
        "calibration_sample_count": calibration_sample_count,
        "future_sample_count": len(observed_peaks),
        "observed_peak_bytes": observed_peaks,
        "new_max_exceed_count": exceed_count,
        "strict_new_max_values": exceedances,
        "max_observed_peak_bytes": max(observed_peaks),
        "max_boundary_overrun_bytes": max(
            [max(0, peak - boundary_bytes) for peak in observed_peaks],
            default=0,
        ),
        "beta_binomial_upper_tail_probability": tail_probability,
        "family_alpha": FAMILY_ALPHA,
        "per_q_bonferroni_alpha": PER_Q_ALPHA,
        "classification": classification,
    }


def run_tail_vs_drift_panel(
    b469: Mapping[str, Any],
    b472: Mapping[str, Any],
    b474: Mapping[str, Any],
    *,
    repetitions: int = FUTURE_SAMPLES_PER_Q,
    size: int = 2048,
    seed: int = 476,
    value_limit: int = 50,
    tile_rows: int = 64,
) -> dict[str, Any]:
    if repetitions != FUTURE_SAMPLES_PER_Q:
        raise ValueError("b476_requires_eight_future_samples_per_q")

    points = _calibration_points(b469, b472, b474)
    observations: dict[int, list[dict[str, Any]]] = {q: [] for q in Q_VALUES}
    execution_rows = []

    for repetition, order in enumerate(BALANCED_ORDERS):
        row = {"repetition": repetition, "order": list(order), "results": []}
        for q in order:
            result = _run_fresh_child(
                q=q,
                size=size,
                lane_count=7,
                seed=seed,
                value_limit=value_limit,
                tile_rows=tile_rows,
            )
            if not result["semantic_exact"]:
                raise RuntimeError(
                    f"semantic_gate_failed:q={q}:rep={repetition}"
                )
            item = {
                "q": q,
                "repetition": repetition,
                "observed_peak_bytes": int(
                    result["normalized_peak_growth_bytes"]
                ),
                "work_seconds": float(result["work_seconds"]),
                "output_sha256": result["output_sha256"],
            }
            observations[q].append(item)
            row["results"].append(item)
        execution_rows.append(row)

    digests = {
        item["output_sha256"]
        for values in observations.values()
        for item in values
    }
    if len(digests) != 1:
        raise RuntimeError("cross_q_output_digest_mismatch")

    q_rows = []
    for q in Q_VALUES:
        peaks = [item["observed_peak_bytes"] for item in observations[q]]
        classified = _classify_q(
            q=q,
            boundary_bytes=int(points[q]["boundary_bytes"]),
            calibration_sample_count=int(points[q]["sample_count"]),
            observed_peaks=peaks,
        )
        classified["median_work_seconds"] = statistics.median(
            item["work_seconds"] for item in observations[q]
        )
        classified["semantic_exact_count"] = len(observations[q])
        q_rows.append(classified)

    suspect_q = [
        row["q"]
        for row in q_rows
        if row["classification"] == "LOCAL_DRIFT_SUSPECT"
    ]
    total_exceedances = sum(row["new_max_exceed_count"] for row in q_rows)

    if suspect_q:
        overall = "DRIFT_SUSPECT"
    elif total_exceedances:
        overall = "TAIL_COMPATIBLE_EXCEEDANCES"
    else:
        overall = "NO_BOUNDARY_EXCEEDANCES"

    return {
        "schema": "finite-ram-lab.tail-vs-drift-panel/v0.1",
        "claim_ceiling": "IID_CONTINUOUS_REFERENCE_TAIL_VS_DRIFT_DIAGNOSTIC",
        "repetitions_per_q": repetitions,
        "total_future_observations": repetitions * len(Q_VALUES),
        "balanced_orders": [list(order) for order in BALANCED_ORDERS],
        "family_alpha": FAMILY_ALPHA,
        "per_q_bonferroni_alpha": PER_Q_ALPHA,
        "size": size,
        "seed": seed,
        "value_limit": value_limit,
        "tile_rows": tile_rows,
        "output_sha256": next(iter(digests)),
        "execution_rows": execution_rows,
        "q_rows": q_rows,
        "overall": {
            "classification": overall,
            "suspect_q": suspect_q,
            "total_new_max_exceedances": total_exceedances,
        },
        "assumptions": [
            "future executions are comparable to calibration executions",
            "IID continuous reference model is used only for the batch exceedance diagnostic",
            "page-quantized ties and environment drift can violate the reference model",
            "a non-significant batch does not prove absence of drift"
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--b469", type=Path, required=True)
    parser.add_argument("--b472", type=Path, required=True)
    parser.add_argument("--b474", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--repetitions", type=int, default=FUTURE_SAMPLES_PER_Q)
    parser.add_argument("--size", type=int, default=2048)
    parser.add_argument("--seed", type=int, default=476)
    args = parser.parse_args()

    payload = run_tail_vs_drift_panel(
        _load(args.b469),
        _load(args.b472),
        _load(args.b474),
        repetitions=args.repetitions,
        size=args.size,
        seed=args.seed,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "overall": payload["overall"],
                "q_rows": payload["q_rows"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
