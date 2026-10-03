from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

SCHEMA = "finite-ram-lab.fr-meta-016-skill-lifecycle/v0.1"

REQUIRED_EVIDENCE_FIELDS = (
    "positive_replays",
    "independent_examples",
    "negative_observations",
    "contradictions",
    "invalidated",
    "scope_explicit",
    "invariants_pass",
    "authority_expanded",
)

RESIDENT_STATES = {
    "QUALIFIED",
    "STABLE",
    "QUALIFIED_NEGATIVE",
}


def classify_evidence(
    evidence: dict[str, Any],
) -> str:
    missing = [
        key
        for key in REQUIRED_EVIDENCE_FIELDS
        if key not in evidence
    ]

    if missing:
        return "INSUFFICIENT_EVIDENCE"

    if (
        not evidence["scope_explicit"]
        or not evidence["invariants_pass"]
        or evidence["authority_expanded"]
    ):
        return "BLOCKED"

    if (
        evidence["invalidated"]
        or evidence["contradictions"] > 0
    ):
        return "RETIRED"

    if (
        evidence["negative_observations"] > 0
        and evidence["positive_replays"] == 0
    ):
        return "QUALIFIED_NEGATIVE"

    if (
        evidence["positive_replays"] >= 2
        and evidence["independent_examples"] >= 2
    ):
        return "STABLE"

    if evidence["positive_replays"] >= 1:
        return "QUALIFIED"

    return "CANDIDATE"


def resident_allowed(
    state: str,
) -> bool:
    return state in RESIDENT_STATES


def apply_maturity(
    skill: dict[str, Any],
    evidence: dict[str, Any],
) -> dict[str, Any]:
    before = deepcopy(skill)
    result = deepcopy(skill)
    result["maturity"] = classify_evidence(
        evidence
    )

    for key in (
        "id",
        "when",
        "action",
        "mc",
        "evidence_prs",
        "invalidate_on",
    ):
        if result.get(key) != before.get(key):
            raise RuntimeError(
                "skill_semantics_mutated:"
                f"{skill.get('id')}:{key}"
            )

    return result


def residency_index(
    skills: list[dict[str, Any]],
    evidence_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    resident = []
    cold = []
    unresolved = []

    for skill in skills:
        skill_id = skill["id"]
        evidence = evidence_by_id.get(
            skill_id
        )

        if evidence is None:
            unresolved.append(
                skill_id
            )
            continue

        governed = apply_maturity(
            skill,
            evidence,
        )
        state = governed["maturity"]

        row = {
            "id": skill_id,
            "maturity": state,
        }

        if resident_allowed(state):
            resident.append(row)
        else:
            cold.append(row)

    return {
        "resident": resident,
        "cold": cold,
        "unresolved": unresolved,
    }


def run_panel() -> dict[str, Any]:
    examples = {
        "exact_reuse": {
            "positive_replays": 5,
            "independent_examples": 5,
            "negative_observations": 0,
            "contradictions": 0,
            "invalidated": False,
            "scope_explicit": True,
            "invariants_pass": True,
            "authority_expanded": False,
        },
        "ci_concurrency": {
            "positive_replays": 2,
            "independent_examples": 2,
            "negative_observations": 0,
            "contradictions": 0,
            "invalidated": False,
            "scope_explicit": True,
            "invariants_pass": True,
            "authority_expanded": False,
        },
        "cache_negative": {
            "positive_replays": 0,
            "independent_examples": 1,
            "negative_observations": 1,
            "contradictions": 0,
            "invalidated": False,
            "scope_explicit": True,
            "invariants_pass": True,
            "authority_expanded": False,
        },
        "invalidated_old_rule": {
            "positive_replays": 3,
            "independent_examples": 3,
            "negative_observations": 0,
            "contradictions": 1,
            "invalidated": True,
            "scope_explicit": True,
            "invariants_pass": True,
            "authority_expanded": False,
        },
        "unknown": {
            "positive_replays": 1,
        },
    }

    states = {
        name: classify_evidence(
            row
        )
        for name, row
        in examples.items()
    }

    checks = {
        "exact_reuse_stable": (
            states["exact_reuse"]
            == "STABLE"
        ),
        "ci_concurrency_stable": (
            states["ci_concurrency"]
            == "STABLE"
        ),
        "cache_is_scoped_negative": (
            states["cache_negative"]
            == "QUALIFIED_NEGATIVE"
        ),
        "contradicted_rule_retires": (
            states["invalidated_old_rule"]
            == "RETIRED"
        ),
        "unknown_does_not_promote": (
            states["unknown"]
            == "INSUFFICIENT_EVIDENCE"
        ),
        "retired_not_resident": (
            not resident_allowed(
                "RETIRED"
            )
        ),
        "negative_guard_can_be_resident": (
            resident_allowed(
                "QUALIFIED_NEGATIVE"
            )
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
        "states": states,
        "resident_states": sorted(
            RESIDENT_STATES
        ),
        "decision": (
            "GOVERN_SKILL_MATURITY_AND_EVICT_STALE_SKILLS_FROM_RESIDENT_CONTEXT"
        ),
        "governance": {
            "auto_mutable_field": (
                "maturity only"
            ),
            "trigger_mutation": "DENY",
            "action_mutation": "DENY",
            "authority_expansion": "DENY",
            "retired_storage": (
                "cold history; do not delete evidence"
            ),
            "unknown_evidence": (
                "INSUFFICIENT_EVIDENCE"
            ),
        },
        "claim_ceiling": (
            "SKILL_LIFECYCLE_AND_RESIDENCY_GOVERNANCE_ONLY"
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
