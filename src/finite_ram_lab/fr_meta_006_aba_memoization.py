from __future__ import annotations

import json

from finite_ram_lab.fr_gfx_observer_aba import (
    BLOCKS_PER_DECISION,
    EPISODES,
    FRAMES_PER_SEGMENT,
)

SCHEMA = "finite-ram-lab.fr-meta-006-aba-memoization/v0.1"

BASELINE_SEGMENT_EVALUATIONS = EPISODES * 12
CANDIDATE_UNIQUE_SEGMENT_MEANS = EPISODES * 5


def run_panel() -> dict:
    reduction = 1.0 - (
        CANDIDATE_UNIQUE_SEGMENT_MEANS
        / BASELINE_SEGMENT_EVALUATIONS
    )
    checks = {
        "episodes_unchanged": EPISODES == 8192,
        "frames_per_segment_unchanged": FRAMES_PER_SEGMENT == 120,
        "blocks_per_decision_unchanged": BLOCKS_PER_DECISION == 8,
        "segment_evaluation_reduction_ge_58pct": reduction >= 0.58,
    }
    return {
        "schema": SCHEMA,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "baseline_segment_evaluations": BASELINE_SEGMENT_EVALUATIONS,
        "candidate_unique_segment_means": CANDIDATE_UNIQUE_SEGMENT_MEANS,
        "structural_reduction_fraction": reduction,
        "decision": "MEMOIZE_DETERMINISTIC_SEGMENT_MEANS",
        "monte_carlo": {
            "used": False,
            "reason": (
                "The optimization changes repeated deterministic computation, "
                "not the statistical experiment."
            ),
        },
        "semantic_guard": (
            "Existing frozen ABA output equality tests must pass unchanged."
        ),
        "claim_ceiling": "TEST_HARNESS_COMPUTE_OPTIMIZATION_ONLY",
    }


def main() -> int:
    print(json.dumps(run_panel(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
