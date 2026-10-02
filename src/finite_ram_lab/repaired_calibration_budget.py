from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Mapping


PARETO_Q = (2, 4, 7)


def minimum_samples_for_rank_max_coverage(target: float) -> int:
    if not (0.0 < target < 1.0):
        raise ValueError("target_invalid")
    return math.ceil(target / (1.0 - target))


def build_budget(
    b487: Mapping[str, Any],
    *,
    target_coverage: float = 0.95,
) -> dict[str, Any]:
    if b487.get("schema") != "finite-ram-lab.b487-result/v0.1":
        raise RuntimeError("b487_schema_invalid")
    if b487.get("repaired_pareto_q") != list(PARETO_Q):
        raise RuntimeError("repaired_pareto_changed")

    required = minimum_samples_for_rank_max_coverage(target_coverage)
    current = int(b487["runner_block_count"])
    additional = max(0, required - current)

    rows = [
        {
            "q": q,
            "current_independent_runner_samples": current,
            "required_sample_count": required,
            "additional_runner_samples_required": additional,
            "target_coverage": target_coverage,
            "current_rank_max_coverage_floor": current / (current + 1),
        }
        for q in PARETO_Q
    ]

    return {
        "schema": "finite-ram-lab.repaired-calibration-budget/v0.1",
        "status": "PROPOSAL_ONLY",
        "claim_ceiling": "EXCHANGEABILITY_CONDITIONAL_REPAIRED_CALIBRATION_BUDGET",
        "implementation": "TILED_WHERE",
        "pareto_q": list(PARETO_Q),
        "dominated_q_excluded": [1],
        "target_coverage": target_coverage,
        "required_sample_count_per_q": required,
        "rows": rows,
        "total_additional_runner_observations": additional * len(PARETO_Q),
        "reference_targets": {
            "coverage_0_95_required_n": minimum_samples_for_rank_max_coverage(0.95),
            "coverage_0_99_required_n": minimum_samples_for_rank_max_coverage(0.99),
        },
        "source_workflow_run_id": b487["workflow_run_id"],
        "source_aggregate_sha256": b487["aggregate_sha256"],
        "assumption": (
            "future repaired-runtime observations are exchangeable with comparable "
            "independent hosted-runner observations; this is not a worst-case guarantee"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--target-coverage", type=float, default=0.95)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    result = build_budget(
        json.loads(args.source.read_text()),
        target_coverage=args.target_coverage,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
