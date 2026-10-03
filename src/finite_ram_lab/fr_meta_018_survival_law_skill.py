from __future__ import annotations

import json

from finite_ram_lab.fr_decision_skills import (
    compile_decision_context,
)

SCHEMA = "finite-ram-lab.fr-meta-018-survival-law-skill/v0.1"


def _exact_facts() -> dict:
    return {
        "semantic_oom_question": True,
        "state_arrival_one_per_step": True,
        "always_preemptive_transfer": True,
        "transfer_initiation_one_per_step": True,
        "transfer_lead_fixed_integer": True,
        "transfer_failure_present": False,
        "safe_reclaimability_collapses_history": True,
    }


def run_panel() -> dict:
    exact = compile_decision_context(
        _exact_facts()
    )
    unknown = compile_decision_context(
        {
            "semantic_oom_question": True,
        }
    )

    broken = _exact_facts()
    broken[
        "transfer_failure_present"
    ] = True
    invalid = compile_decision_context(
        broken
    )

    checks = {
        "qualified_skill_selected": (
            exact["primary_action"]
            == "USE_ANALYTIC_SURVIVAL_LAW"
        ),
        "mc_skipped": (
            exact["skills"][0]["mc"]
            == "SKIP"
        ),
        "evidence_pr_is_127": (
            exact["skills"][0][
                "evidence_prs"
            ]
            == [127]
        ),
        "maturity_is_qualified": (
            exact["skills"][0][
                "maturity"
            ]
            == "QUALIFIED"
        ),
        "unknown_fails_closed": (
            unknown["primary_action"]
            == "NO_COMPILED_DECISION"
            and len(
                unknown["unresolved"]
            )
            > 0
        ),
        "changed_transfer_semantics_invalidate": (
            invalid["primary_action"]
            == "NO_COMPILED_DECISION"
        ),
        "capsule_under_10pct_source_surface": (
            exact[
                "context_fraction_of_source"
            ]
            < 0.10
        ),
    }

    return {
        "schema": SCHEMA,
        "status": (
            "PASS"
            if all(
                checks.values()
            )
            else "FAIL"
        ),
        "checks": checks,
        "exact": exact,
        "unknown": unknown,
        "invalid": invalid,
        "decision": (
            "COMPILE_FR_FP_009_SURVIVAL_LAW_AS_QUALIFIED_MC_SKIP_SKILL"
        ),
        "claim_ceiling": (
            "QUALIFIED_DECISION_SKILL_FOR_FROZEN_SYNTHETIC_SURVIVAL_LAW_ONLY"
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
