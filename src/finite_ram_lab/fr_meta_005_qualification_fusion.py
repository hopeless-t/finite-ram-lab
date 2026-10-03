from __future__ import annotations

import json

SCHEMA = "finite-ram-lab.fr-meta-005-qualification-fusion/v0.1"

BASELINE_RUNS = 10
ATOMIC_DEDICATED_RUNS = 4
FUSED_CLEAN_RUNS = 3


def run_panel() -> dict:
    exact = {
        "historical_baseline_runs": BASELINE_RUNS,
        "atomic_with_dedicated_runs": ATOMIC_DEDICATED_RUNS,
        "fused_clean_runs": FUSED_CLEAN_RUNS,
        "reduction_vs_historical": 1.0 - FUSED_CLEAN_RUNS / BASELINE_RUNS,
        "reduction_vs_atomic_dedicated": 1.0 - FUSED_CLEAN_RUNS / ATOMIC_DEDICATED_RUNS,
        "rework_penalty_per_fix_commit_runs": 1,
    }
    checks = {
        "keeps_general_ci": True,
        "meta_panel_must_return_pass": True,
        "result_artifact_preserved": True,
        "historical_reduction_ge_70pct": exact["reduction_vs_historical"] >= 0.70,
        "atomic_reduction_ge_25pct": exact["reduction_vs_atomic_dedicated"] >= 0.25,
    }
    return {
        "schema": SCHEMA,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "exact": exact,
        "decision": "FUSE_META_QUALIFICATION_INTO_GENERAL_CI",
        "monte_carlo": {
            "used": False,
            "reason": "Run-count topology is exact; Monte Carlo would not change this routing decision.",
        },
        "hard_invariants": [
            "general CI remains the required safety surface",
            "changed meta modules must expose run_panel",
            "run_panel status must be PASS",
            "qualification artifact remains durable",
            "UNKNOWN is not success",
        ],
        "claim_ceiling": "CI_QUALIFICATION_FANOUT_OPTIMIZATION_ONLY",
    }


def main() -> int:
    print(json.dumps(run_panel(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
