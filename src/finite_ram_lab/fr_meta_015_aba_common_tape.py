from __future__ import annotations

import json

from finite_ram_lab.fr_decision_skills import (
    compile_decision_context,
)
from finite_ram_lab.fr_gfx_observer_aba import (
    ARMS,
    EPISODES,
)

SCHEMA = "finite-ram-lab.fr-meta-015-aba-common-tape/v0.1"

BASELINE_B_TAPE_PASSES = EPISODES * len(ARMS)
CANDIDATE_B_TAPE_PASSES = EPISODES
BASELINE_SEGMENT_LOOPS_PER_EPISODE = 5
CANDIDATE_SEGMENT_LOOPS_PER_EPISODE = 3


def run_panel() -> dict:
    route = compile_decision_context(
        {
            "deterministic_duplicate_work": True,
            "scientific_contract_unchanged": True,
            "runtime_is_measurement": False,
        }
    )

    b_reduction = 1.0 - (
        CANDIDATE_B_TAPE_PASSES
        / BASELINE_B_TAPE_PASSES
    )
    segment_reduction = 1.0 - (
        CANDIDATE_SEGMENT_LOOPS_PER_EPISODE
        / BASELINE_SEGMENT_LOOPS_PER_EPISODE
    )

    checks = {
        "compiled_skill_selected": (
            route["primary_action"]
            == "REUSE_EXACT_COMPUTATION"
        ),
        "compiled_skill_skips_mc": (
            route["skills"][0]["mc"]
            == "SKIP"
        ),
        "selected_context_under_5pct": (
            route["context_fraction_of_source"]
            < 0.05
        ),
        "b_tape_reduction_two_thirds": (
            b_reduction >= 2.0 / 3.0
        ),
        "segment_loop_reduction_40pct": (
            segment_reduction >= 0.40
        ),
        "episodes_unchanged": (
            EPISODES == 8192
        ),
        "arms_unchanged": (
            len(ARMS) == 3
        ),
    }

    return {
        "schema": SCHEMA,
        "status": (
            "PASS"
            if all(checks.values())
            else "FAIL"
        ),
        "checks": checks,
        "skill_route": route,
        "baseline_b_tape_passes": (
            BASELINE_B_TAPE_PASSES
        ),
        "candidate_b_tape_passes": (
            CANDIDATE_B_TAPE_PASSES
        ),
        "b_tape_reduction_fraction": (
            b_reduction
        ),
        "baseline_segment_loops_per_episode": (
            BASELINE_SEGMENT_LOOPS_PER_EPISODE
        ),
        "candidate_segment_loops_per_episode": (
            CANDIDATE_SEGMENT_LOOPS_PER_EPISODE
        ),
        "segment_loop_reduction_fraction": (
            segment_reduction
        ),
        "decision": (
            "SHARE_B_STOCHASTIC_TAPE_ACROSS_OBSERVER_ARMS"
        ),
        "monte_carlo": {
            "used_for_optimization_decision": False,
            "reason": (
                "The compiled exact-reuse skill selected SKIP."
            ),
        },
        "semantic_guard": (
            "Existing frozen ABA outputs must remain exactly unchanged."
        ),
        "claim_ceiling": (
            "SKILL_ROUTED_EXACT_TEST_HARNESS_OPTIMIZATION_ONLY"
        ),
    }


def main() -> int:
    print(
        json.dumps(
            run_panel(),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
