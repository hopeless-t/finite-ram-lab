from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics
from typing import Any

from finite_ram_lab.local_adapter_bootstrap import (
    CANDIDATE_Q,
    fingerprint_sha256,
    local_host_fingerprint,
    minimum_samples_for_rank_max_coverage,
)
from finite_ram_lab.repaired_q_frontier import _run_fresh_child


BALANCED_ORDERS = (
    (1, 2, 4, 7),
    (2, 4, 7, 1),
    (4, 7, 1, 2),
    (7, 1, 2, 4),
    (7, 4, 2, 1),
    (4, 2, 1, 7),
    (2, 1, 7, 4),
    (1, 7, 4, 2),
)


def _pareto(rows: list[dict[str, Any]]) -> list[int]:
    out: list[int] = []
    for candidate in rows:
        dominated = False
        for other in rows:
            if other["q"] == candidate["q"]:
                continue
            no_worse = (
                other["median_peak_bytes"] <= candidate["median_peak_bytes"]
                and other["median_work_seconds"] <= candidate["median_work_seconds"]
            )
            strictly_better = (
                other["median_peak_bytes"] < candidate["median_peak_bytes"]
                or other["median_work_seconds"] < candidate["median_work_seconds"]
            )
            if no_worse and strictly_better:
                dominated = True
                break
        if not dominated:
            out.append(int(candidate["q"]))
    return sorted(out)


def _orders(samples_per_q: int) -> list[tuple[int, ...]]:
    if samples_per_q <= 0:
        raise ValueError("samples_per_q_invalid")
    return [
        BALANCED_ORDERS[index % len(BALANCED_ORDERS)]
        for index in range(samples_per_q)
    ]


def run_local_exploration(
    *,
    samples_per_q: int = 8,
    size: int = 2048,
    target_rank_coverage: float = 0.95,
) -> dict[str, Any]:
    before = local_host_fingerprint()
    before_sha = fingerprint_sha256(before)

    values: dict[int, list[dict[str, Any]]] = {
        q: [] for q in CANDIDATE_Q
    }
    execution_blocks = []

    for block_id, order in enumerate(_orders(samples_per_q)):
        block = {
            "block_id": block_id,
            "execution_order": list(order),
            "results": [],
        }
        for q in order:
            result = _run_fresh_child(
                strategy="TILED_WHERE",
                q=q,
                size=size,
            )
            if not result["semantic_exact"]:
                raise RuntimeError(
                    f"semantic_gate_failed:block={block_id}:q={q}"
                )
            row = {
                "q": q,
                "normalized_peak_growth_bytes": int(
                    result["normalized_peak_growth_bytes"]
                ),
                "work_seconds": float(result["work_seconds"]),
                "output_sha256": result["output_sha256"],
            }
            values[q].append(row)
            block["results"].append(row)
        execution_blocks.append(block)

    after = local_host_fingerprint()
    after_sha = fingerprint_sha256(after)
    if before_sha != after_sha:
        raise RuntimeError("local_environment_fingerprint_changed_during_panel")

    digests = {
        row["output_sha256"]
        for q_rows in values.values()
        for row in q_rows
    }
    if len(digests) != 1:
        raise RuntimeError("cross_q_output_digest_mismatch")

    frontier_rows = []
    coverage = samples_per_q / (samples_per_q + 1)
    required_n = minimum_samples_for_rank_max_coverage(target_rank_coverage)

    for q in CANDIDATE_Q:
        peaks = [row["normalized_peak_growth_bytes"] for row in values[q]]
        times = [row["work_seconds"] for row in values[q]]
        if len(peaks) != samples_per_q:
            raise RuntimeError(f"q_sample_count_invalid:q={q}")

        frontier_rows.append(
            {
                "q": q,
                "sample_count": samples_per_q,
                "median_peak_bytes": statistics.median(peaks),
                "empirical_max_peak_bytes": max(peaks),
                "median_work_seconds": statistics.median(times),
                "rank_max_one_step_predictive_coverage_floor": coverage,
                "peak_samples_bytes": peaks,
            }
        )

    pareto_q = _pareto(frontier_rows)
    promotion_rows = [
        {
            "q": q,
            "current_sample_count": samples_per_q,
            "required_sample_count": required_n,
            "additional_samples_required": max(0, required_n - samples_per_q),
        }
        for q in pareto_q
    ]

    return {
        "schema": "finite-ram-lab.local-calibration-exploration/v0.1",
        "status": "EXPLORATION_COMPLETE",
        "claim_ceiling": "HOST_SCOPED_LOCAL_FRESH_PROCESS_EXPLORATION",
        "implementation": "TILED_WHERE",
        "host_binding": {
            "environment_fingerprint": before,
            "environment_fingerprint_sha256": before_sha,
            "stable_across_panel": True,
        },
        "sample_unit": "fresh_local_process_on_bound_host",
        "size": size,
        "seed": 469,
        "samples_per_q": samples_per_q,
        "physical_observations": samples_per_q * len(CANDIDATE_Q),
        "candidate_q": list(CANDIDATE_Q),
        "execution_blocks": execution_blocks,
        "frontier_rows": frontier_rows,
        "local_pareto_q": pareto_q,
        "current_rank_max_coverage_floor": coverage,
        "promotion_target_rank_coverage": target_rank_coverage,
        "promotion_rows": promotion_rows,
        "policy_promotion_allowed": all(
            row["additional_samples_required"] == 0
            for row in promotion_rows
        ),
        "cross_q_output_sha256": next(iter(digests)),
        "hosted_threshold_imported": False,
        "assumption": (
            "Coverage is host-scoped and conditional on exchangeability of fresh "
            "process executions under the fingerprint-bound local environment."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="finite-ram-local-calibrate",
        description="Run a host-bound fresh-process q exploration panel.",
    )
    parser.add_argument("--samples-per-q", type=int, default=8)
    parser.add_argument("--size", type=int, default=2048)
    parser.add_argument("--target-rank-coverage", type=float, default=0.95)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    payload = run_local_exploration(
        samples_per_q=args.samples_per_q,
        size=args.size,
        target_rank_coverage=args.target_rank_coverage,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": payload["status"],
        "host_fingerprint_sha256": payload["host_binding"][
            "environment_fingerprint_sha256"
        ],
        "local_pareto_q": payload["local_pareto_q"],
        "samples_per_q": payload["samples_per_q"],
        "policy_promotion_allowed": payload["policy_promotion_allowed"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
