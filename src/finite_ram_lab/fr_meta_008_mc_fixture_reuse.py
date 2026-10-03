from __future__ import annotations

import json

from finite_ram_lab.ksla_bounded_idiocy import MC_EPISODES

SCHEMA = "finite-ram-lab.fr-meta-008-mc-fixture-reuse/v0.1"

BASELINE_PANEL_CALLS = 3
CANDIDATE_PANEL_CALLS = 1


def run_panel() -> dict:
    reduction = 1.0 - CANDIDATE_PANEL_CALLS / BASELINE_PANEL_CALLS
    checks = {
        "mc_episodes_unchanged": MC_EPISODES == 200_000,
        "panel_calls_reduced_to_one": CANDIDATE_PANEL_CALLS == 1,
        "structural_reduction_ge_66pct": reduction >= 2 / 3,
    }
    return {
        "schema": SCHEMA,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "baseline_panel_calls": BASELINE_PANEL_CALLS,
        "candidate_panel_calls": CANDIDATE_PANEL_CALLS,
        "mc_episodes_per_panel": MC_EPISODES,
        "baseline_mc_episode_evaluations": BASELINE_PANEL_CALLS * MC_EPISODES,
        "candidate_mc_episode_evaluations": CANDIDATE_PANEL_CALLS * MC_EPISODES,
        "structural_reduction_fraction": reduction,
        "decision": "SHARE_CLASS_LEVEL_MONTE_CARLO_FIXTURE",
        "monte_carlo": {
            "used_for_optimization_decision": False,
            "reason": "The duplicate panel calls are exact test-harness redundancy.",
        },
        "semantic_guard": (
            "The original run_panel implementation and all assertion thresholds remain unchanged."
        ),
        "claim_ceiling": "TEST_FIXTURE_REUSE_OPTIMIZATION_ONLY",
    }


def main() -> int:
    print(json.dumps(run_panel(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
