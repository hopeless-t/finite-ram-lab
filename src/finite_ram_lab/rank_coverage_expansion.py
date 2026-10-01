from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics
from typing import Any, Mapping

from finite_ram_lab.lane_concurrency_sweep import _run_fresh_child
from finite_ram_lab.rank_coverage_budget import rank_max_coverage_floor


Q_VALUES = (2, 4, 7)
ADDITIONAL_PER_Q = 11
BALANCED_ORDERS = (
    (2, 4, 7),
    (4, 7, 2),
    (7, 2, 4),
    (2, 7, 4),
    (7, 4, 2),
    (4, 2, 7),
    (2, 4, 7),
    (4, 7, 2),
    (7, 2, 4),
    (2, 7, 4),
    (7, 4, 2),
)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _prior_rows(
    b469: Mapping[str, Any],
    b471: Mapping[str, Any],
) -> dict[int, dict[str, Any]]:
    if b469.get("schema") != "finite-ram-lab.b469-result/v0.1":
        raise RuntimeError("b469_schema_invalid")
    if b471.get("schema") != "finite-ram-lab.b471-result/v0.1":
        raise RuntimeError("b471_schema_invalid")

    rows = {}
    for q in Q_VALUES:
        old = next(row for row in b469["summary_rows"] if int(row["q"]) == q)
        fresh = next(
            row for row in b471["summary_rows"] if int(row["selected_q"]) == q
        )
        rows[q] = {
            "b469_samples": int(old.get("samples", 4)),
            "b471_samples": int(fresh.get("samples", 4)),
            "prior_sample_count": int(old.get("samples", 4))
            + int(fresh.get("samples", 4)),
            "b469_max_peak_bytes": int(old["max_peak_bytes"]),
            "b471_max_peak_bytes": int(fresh["max_observed_peak_bytes"]),
            "prior_union_max_peak_bytes": max(
                int(old["max_peak_bytes"]),
                int(fresh["max_observed_peak_bytes"]),
            ),
        }
    return rows


def run_expansion(
    b469: Mapping[str, Any],
    b471: Mapping[str, Any],
    *,
    additional_per_q: int = ADDITIONAL_PER_Q,
    size: int = 2048,
    seed: int = 474,
    value_limit: int = 50,
    tile_rows: int = 64,
) -> dict[str, Any]:
    if additional_per_q != ADDITIONAL_PER_Q:
        raise ValueError("b474_requires_eleven_per_q")

    prior = _prior_rows(b469, b471)
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
                raise RuntimeError(f"semantic_gate_failed:q={q}:rep={repetition}")
            item = {
                "q": q,
                "repetition": repetition,
                "observed_peak_bytes": int(result["normalized_peak_growth_bytes"]),
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

    summary_rows = []
    for q in Q_VALUES:
        values = observations[q]
        peaks = [item["observed_peak_bytes"] for item in values]
        new_max = max(peaks)
        prior_row = prior[q]
        union_max = max(prior_row["prior_union_max_peak_bytes"], new_max)
        total_n = prior_row["prior_sample_count"] + len(values)
        summary_rows.append(
            {
                "q": q,
                **prior_row,
                "additional_sample_count": len(values),
                "new_observed_peak_bytes": peaks,
                "new_median_peak_bytes": statistics.median(peaks),
                "new_max_peak_bytes": new_max,
                "prior_boundary_exceed_count": sum(
                    peak > prior_row["prior_union_max_peak_bytes"]
                    for peak in peaks
                ),
                "union_sample_count": total_n,
                "union_empirical_max_peak_bytes": union_max,
                "union_max_moved_bytes": (
                    union_max - prior_row["prior_union_max_peak_bytes"]
                ),
                "rank_max_one_step_predictive_coverage_floor": (
                    rank_max_coverage_floor(total_n)
                ),
                "median_work_seconds": statistics.median(
                    item["work_seconds"] for item in values
                ),
                "semantic_exact_count": len(values),
            }
        )

    return {
        "schema": "finite-ram-lab.rank-coverage-expansion/v0.1",
        "claim_ceiling": "EXCHANGEABILITY_CONDITIONAL_MULTI_Q_CALIBRATION",
        "q_values": list(Q_VALUES),
        "additional_per_q": additional_per_q,
        "total_new_observations": additional_per_q * len(Q_VALUES),
        "balanced_orders": [list(order) for order in BALANCED_ORDERS],
        "size": size,
        "seed": seed,
        "value_limit": value_limit,
        "tile_rows": tile_rows,
        "output_sha256": next(iter(digests)),
        "execution_rows": execution_rows,
        "summary_rows": summary_rows,
        "all_q_at_least_95pct_rank_floor": all(
            row["rank_max_one_step_predictive_coverage_floor"] >= 0.95
            for row in summary_rows
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--b469", type=Path, required=True)
    parser.add_argument("--b471", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--additional-per-q", type=int, default=ADDITIONAL_PER_Q)
    parser.add_argument("--size", type=int, default=2048)
    parser.add_argument("--seed", type=int, default=474)
    args = parser.parse_args()

    payload = run_expansion(
        _load(args.b469),
        _load(args.b471),
        additional_per_q=args.additional_per_q,
        size=args.size,
        seed=args.seed,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "all_q_at_least_95pct_rank_floor": payload[
                    "all_q_at_least_95pct_rank_floor"
                ],
                "summary_rows": payload["summary_rows"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
