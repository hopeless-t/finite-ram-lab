from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics
from typing import Any, Mapping

from finite_ram_lab.local_adapter_bootstrap import (
    CANDIDATE_Q,
    fingerprint_sha256,
    local_host_fingerprint,
    minimum_samples_for_rank_max_coverage,
)
from finite_ram_lab.repaired_q_frontier import _run_fresh_child


EXPLORATION_SCHEMA = "finite-ram-lab.local-calibration-exploration/v0.1"
STATE_SCHEMA = "finite-ram-lab.local-calibration-state/v0.1"


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


def _extension_order(q_values: tuple[int, ...], block_id: int) -> tuple[int, ...]:
    if not q_values:
        raise ValueError("extension_q_empty")
    shift = block_id % len(q_values)
    rotated = q_values[shift:] + q_values[:shift]
    cycle = block_id // len(q_values)
    if cycle % 2:
        rotated = tuple(reversed(rotated))
    return rotated


def _old_observations(
    exploration: Mapping[str, Any],
) -> dict[int, list[dict[str, Any]]]:
    values = {q: [] for q in CANDIDATE_Q}
    for block in exploration["execution_blocks"]:
        for row in block["results"]:
            q = int(row["q"])
            if q not in values:
                raise RuntimeError(f"unexpected_q_in_exploration:{q}")
            values[q].append(
                {
                    "q": q,
                    "normalized_peak_growth_bytes": int(
                        row["normalized_peak_growth_bytes"]
                    ),
                    "work_seconds": float(row["work_seconds"]),
                    "output_sha256": row["output_sha256"],
                    "source": "EXPLORATION",
                }
            )
    expected = int(exploration["samples_per_q"])
    for q, rows in values.items():
        if len(rows) != expected:
            raise RuntimeError(
                f"exploration_sample_count_invalid:q={q}:"
                f"observed={len(rows)}:expected={expected}"
            )
    return values


def extend_local_calibration(
    exploration: Mapping[str, Any],
    *,
    additional_samples_per_q: int = 11,
    size: int = 2048,
    target_rank_coverage: float = 0.95,
) -> dict[str, Any]:
    if exploration.get("schema") != EXPLORATION_SCHEMA:
        raise RuntimeError("exploration_schema_invalid")
    if exploration.get("implementation") != "TILED_WHERE":
        raise RuntimeError("exploration_implementation_invalid")
    if additional_samples_per_q < 0:
        raise ValueError("additional_samples_invalid")
    if int(exploration["size"]) != size:
        raise RuntimeError(
            f"size_mismatch:exploration={exploration['size']}:requested={size}"
        )

    binding = exploration["host_binding"]
    expected_fp = str(binding["environment_fingerprint_sha256"])
    before = local_host_fingerprint()
    before_sha = fingerprint_sha256(before)
    if before_sha != expected_fp:
        raise RuntimeError(
            "local_environment_fingerprint_mismatch:"
            f"expected={expected_fp}:observed={before_sha}"
        )

    initial_pareto = tuple(
        sorted(int(q) for q in exploration["local_pareto_q"])
    )
    if not initial_pareto:
        raise RuntimeError("initial_local_pareto_empty")
    if not set(initial_pareto).issubset(set(CANDIDATE_Q)):
        raise RuntimeError("initial_local_pareto_invalid")

    values = _old_observations(exploration)
    extension_blocks = []

    for block_id in range(additional_samples_per_q):
        order = _extension_order(initial_pareto, block_id)
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
                "source": "PARETO_EXTENSION",
            }
            values[q].append(row)
            block["results"].append(row)
        extension_blocks.append(block)

    after = local_host_fingerprint()
    after_sha = fingerprint_sha256(after)
    if after_sha != expected_fp:
        raise RuntimeError("local_environment_fingerprint_changed_during_extension")

    digests = {
        row["output_sha256"]
        for q_rows in values.values()
        for row in q_rows
    }
    if len(digests) != 1:
        raise RuntimeError("cross_q_output_digest_mismatch")

    rows = []
    for q in CANDIDATE_Q:
        q_rows = values[q]
        peaks = [
            int(row["normalized_peak_growth_bytes"])
            for row in q_rows
        ]
        times = [float(row["work_seconds"]) for row in q_rows]
        n = len(q_rows)
        rows.append(
            {
                "q": q,
                "sample_count": n,
                "median_peak_bytes": statistics.median(peaks),
                "empirical_max_peak_bytes": max(peaks),
                "median_work_seconds": statistics.median(times),
                "rank_max_one_step_predictive_coverage_floor": n / (n + 1),
                "peak_samples_bytes": peaks,
                "work_samples_seconds": times,
                "exploration_sample_count": int(
                    exploration["samples_per_q"]
                ),
                "extension_sample_count": sum(
                    row["source"] == "PARETO_EXTENSION"
                    for row in q_rows
                ),
            }
        )

    final_pareto = _pareto(rows)
    required_n = minimum_samples_for_rank_max_coverage(
        target_rank_coverage
    )
    promotion_rows = []
    rows_by_q = {int(row["q"]): row for row in rows}
    for q in final_pareto:
        row = rows_by_q[q]
        promotion_rows.append(
            {
                "q": q,
                "current_sample_count": int(row["sample_count"]),
                "required_sample_count": required_n,
                "additional_samples_required": max(
                    0,
                    required_n - int(row["sample_count"]),
                ),
            }
        )

    return {
        "schema": STATE_SCHEMA,
        "status": "CALIBRATION_STATE_UPDATED",
        "claim_ceiling": "HOST_SCOPED_LOCAL_PARETO_EXTENSION",
        "implementation": "TILED_WHERE",
        "host_binding": binding,
        "sample_unit": "fresh_local_process_on_bound_host",
        "size": size,
        "seed": 469,
        "candidate_q": list(CANDIDATE_Q),
        "initial_pareto_q": list(initial_pareto),
        "extension_q": list(initial_pareto),
        "additional_samples_per_extended_q": additional_samples_per_q,
        "physical_observations_added": (
            additional_samples_per_q * len(initial_pareto)
        ),
        "extension_blocks": extension_blocks,
        "rows": rows,
        "pareto_q": final_pareto,
        "promotion_target_rank_coverage": target_rank_coverage,
        "promotion_rows": promotion_rows,
        "policy_promotion_allowed": all(
            row["additional_samples_required"] == 0
            for row in promotion_rows
        ),
        "cross_q_output_sha256": next(iter(digests)),
        "hosted_threshold_imported": False,
        "source_exploration_schema": exploration["schema"],
        "assumption": (
            "Coverage is host-scoped and conditional on exchangeability of fresh "
            "process executions under the fingerprint-bound local environment."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="finite-ram-local-calibration-extend",
        description="Extend only the locally observed Pareto q values and merge evidence.",
    )
    parser.add_argument("--exploration", type=Path, required=True)
    parser.add_argument("--additional-samples-per-q", type=int, default=11)
    parser.add_argument("--size", type=int, default=2048)
    parser.add_argument("--target-rank-coverage", type=float, default=0.95)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    exploration = json.loads(args.exploration.read_text())
    payload = extend_local_calibration(
        exploration,
        additional_samples_per_q=args.additional_samples_per_q,
        size=args.size,
        target_rank_coverage=args.target_rank_coverage,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": payload["status"],
        "initial_pareto_q": payload["initial_pareto_q"],
        "final_pareto_q": payload["pareto_q"],
        "physical_observations_added": payload["physical_observations_added"],
        "policy_promotion_allowed": payload["policy_promotion_allowed"],
        "promotion_rows": payload["promotion_rows"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
