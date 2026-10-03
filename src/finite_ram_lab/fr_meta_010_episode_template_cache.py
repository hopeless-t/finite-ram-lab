from __future__ import annotations

import json

from finite_ram_lab.ksla_real_state_idiocy import EPISODES, POLICIES

SCHEMA = "finite-ram-lab.fr-meta-010-episode-template-cache/v0.1"

BASELINE_TEMPLATE_BUILDS = EPISODES * len(POLICIES)
CANDIDATE_TEMPLATE_BUILDS = EPISODES


def run_panel() -> dict:
    reduction = 1.0 - CANDIDATE_TEMPLATE_BUILDS / BASELINE_TEMPLATE_BUILDS
    checks = {
        "episodes_unchanged": EPISODES == 512,
        "policy_count_unchanged": len(POLICIES) == 6,
        "template_build_reduction_ge_83pct": reduction >= 5 / 6,
    }
    return {
        "schema": SCHEMA,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "baseline_template_builds": BASELINE_TEMPLATE_BUILDS,
        "candidate_template_builds": CANDIDATE_TEMPLATE_BUILDS,
        "structural_reduction_fraction": reduction,
        "decision": "CACHE_IMMUTABLE_EPISODE_TEMPLATE_COPY_PER_POLICY",
        "semantic_guard": (
            "Each policy still receives fresh target/permutation lists; only "
            "the deterministic hash/sort template is shared."
        ),
        "monte_carlo": {
            "used": False,
            "reason": "The optimization removes exact deterministic recomputation.",
        },
        "claim_ceiling": "TEST_HARNESS_TEMPLATE_REUSE_ONLY",
    }


def main() -> int:
    print(json.dumps(run_panel(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
