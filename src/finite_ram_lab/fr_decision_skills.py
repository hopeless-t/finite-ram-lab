from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

SCHEMA = "finite-ram-lab.fr-meta-014-decision-skills/v0.1"
SOURCE_HISTORY_CHARACTERS = 17417

INVARIANTS = (
    "UNKNOWN_IS_NOT_SUCCESS",
    "MISSING_EVIDENCE_IS_NOT_ZERO",
    "EVIDENCE_AND_DECISION_REMAIN_SEPARATE",
    "METHOD_IMPROVEMENT_DOES_NOT_EXPAND_AUTHORITY",
)

SKILLS = (
    {
        "id": "PRESERVE_RUNTIME_BENCHMARK",
        "priority": 100,
        "kind": "guard",
        "when": {"runtime_is_measurement": True},
        "action": "PRESERVE_MEASUREMENT_BODY",
        "mc": "UNCHANGED",
        "evidence_prs": [],
        "replications": 1,
        "maturity": "STABLE_GUARD",
        "invalidate_on": ["benchmark_contract_changed"],
    },
    {
        "id": "EXACT_REUSE_BEFORE_SAMPLE_REDUCTION",
        "priority": 90,
        "kind": "positive",
        "when": {
            "deterministic_duplicate_work": True,
            "scientific_contract_unchanged": True,
            "runtime_is_measurement": False,
        },
        "action": "REUSE_EXACT_COMPUTATION",
        "mc": "SKIP",
        "evidence_prs": [108, 110, 112, 113],
        "replications": 4,
        "maturity": "STABLE",
        "invalidate_on": [
            "scientific_contract_changed",
            "runtime_becomes_measurement",
        ],
    },
    {
        "id": "SKIP_MC_FOR_EXACT_TOPOLOGY",
        "priority": 85,
        "kind": "positive",
        "when": {
            "topology_exact": True,
            "decision_uncertain": False,
        },
        "action": "SKIP_MONTE_CARLO",
        "mc": "SKIP",
        "evidence_prs": [107, 111],
        "replications": 2,
        "maturity": "STABLE",
        "invalidate_on": ["topology_becomes_uncertain"],
    },
    {
        "id": "MC_FOR_LOSS_SENSITIVE_UNCERTAINTY",
        "priority": 85,
        "kind": "positive",
        "when": {
            "decision_uncertain": True,
            "loss_sensitive": True,
        },
        "action": "RUN_MONTE_CARLO_ROBUSTNESS",
        "mc": "REQUIRED",
        "evidence_prs": [103, 104],
        "replications": 2,
        "maturity": "STABLE",
        "invalidate_on": ["decision_becomes_exact"],
    },
    {
        "id": "ATOMIC_BUNDLE_ONE_TRANSITION",
        "priority": 70,
        "kind": "positive",
        "when": {"coherent_transition": True},
        "action": "ATOMIC_BUNDLE_THEN_QUALIFY",
        "mc": "SKIP",
        "evidence_prs": [106],
        "replications": 1,
        "maturity": "QUALIFIED",
        "invalidate_on": ["transition_contains_independent_questions"],
    },
    {
        "id": "GENERAL_CI_META_QUALIFICATION",
        "priority": 75,
        "kind": "positive",
        "when": {"meta_module_changed": True},
        "action": "QUALIFY_IN_GENERAL_CI",
        "mc": "SKIP",
        "evidence_prs": [107],
        "replications": 1,
        "maturity": "QUALIFIED",
        "invalidate_on": ["general_ci_no_longer_covers_meta_contract"],
    },
    {
        "id": "CANCEL_SUPERSEDED_NON_MAIN_CI",
        "priority": 95,
        "kind": "positive",
        "when": {
            "same_head_duplicate_ci": True,
            "branch_is_main": False,
        },
        "action": "CANCEL_SUPERSEDED_NON_MAIN_CI",
        "mc": "SKIP",
        "evidence_prs": [111],
        "replications": 2,
        "maturity": "STABLE",
        "invalidate_on": ["ci_heads_diverge", "branch_becomes_main"],
    },
    {
        "id": "NEVER_CANCEL_MAIN_CI",
        "priority": 100,
        "kind": "guard",
        "when": {"branch_is_main": True},
        "action": "KEEP_MAIN_CI",
        "mc": "SKIP",
        "evidence_prs": [111],
        "replications": 2,
        "maturity": "STABLE_GUARD",
        "invalidate_on": [],
    },
    {
        "id": "EPHEMERAL_BUILD_AHEAD_ONLY",
        "priority": 95,
        "kind": "guard",
        "when": {"parent_receipt_frozen": False},
        "action": "DRAFT_EPHEMERALLY_NO_CANONICAL_GIT",
        "mc": "SKIP",
        "evidence_prs": [109, 114],
        "replications": 2,
        "maturity": "STABLE_GUARD",
        "invalidate_on": ["parent_receipt_frozen"],
    },
    {
        "id": "MATERIALIZE_AFTER_RECEIPT",
        "priority": 90,
        "kind": "positive",
        "when": {
            "parent_receipt_frozen": True,
            "prepared_delta_ready": True,
        },
        "action": "MATERIALIZE_ATOMIC_CHILD_ON_RECEIPT_TREE",
        "mc": "SKIP",
        "evidence_prs": [109, 114],
        "replications": 2,
        "maturity": "STABLE",
        "invalidate_on": ["parent_receipt_invalidated"],
    },
    {
        "id": "CACHE_REUSE_PROVE_SCOPE_FIRST",
        "priority": 100,
        "kind": "negative",
        "when": {
            "cache_candidate": True,
            "cache_restore_proven": False,
        },
        "action": "REJECT_CACHE_PROMOTION",
        "mc": "SKIP",
        "evidence_prs": [115],
        "replications": 1,
        "maturity": "QUALIFIED_NEGATIVE",
        "invalidate_on": ["producer_consumer_restore_proven"],
    },
    {
        "id": "CACHE_MEASURE_BEFORE_PROMOTION",
        "priority": 95,
        "kind": "guard",
        "when": {
            "cache_candidate": True,
            "cache_restore_proven": True,
            "cache_speedup_measured": False,
        },
        "action": "MEASURE_CACHE_SPEEDUP_AND_OVERHEAD",
        "mc": "SKIP",
        "evidence_prs": [115],
        "replications": 1,
        "maturity": "QUALIFIED_GUARD",
        "invalidate_on": ["speedup_and_overhead_measured"],
    },
    {
        "id": "FAILURE_BIOPSY_BEFORE_THEORY_UPDATE",
        "priority": 90,
        "kind": "guard",
        "when": {"prediction_mismatch": True},
        "action": "PRESERVE_FAILURE_BIOPSY_THEN_UPDATE_MODEL",
        "mc": "CONDITIONAL",
        "evidence_prs": [106, 109, 114, 115],
        "replications": 4,
        "maturity": "STABLE_GUARD",
        "invalidate_on": [],
    },
)


def validate_skills() -> None:
    ids: set[str] = set()
    for skill in SKILLS:
        skill_id = skill["id"]
        if skill_id in ids:
            raise RuntimeError(f"duplicate_skill:{skill_id}")
        ids.add(skill_id)
        if not skill["when"]:
            raise RuntimeError(f"skill_without_trigger:{skill_id}")
        if not skill["action"]:
            raise RuntimeError(f"skill_without_action:{skill_id}")
        if skill["maturity"] not in {
            "STABLE",
            "STABLE_GUARD",
            "QUALIFIED",
            "QUALIFIED_GUARD",
            "QUALIFIED_NEGATIVE",
        }:
            raise RuntimeError(f"unknown_maturity:{skill_id}")


def _evaluate(
    skill: dict[str, Any],
    facts: dict[str, Any],
) -> tuple[str, list[str]]:
    missing: list[str] = []
    matched = 0

    for key, expected in skill["when"].items():
        if key not in facts:
            missing.append(key)
            continue
        if facts[key] != expected:
            return "NO_MATCH", []
        matched += 1

    if not missing:
        return "MATCH", []
    if matched:
        return "PARTIAL", missing
    return "INACTIVE", []


def _capsule(skill: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": skill["id"],
        "action": skill["action"],
        "mc": skill["mc"],
        "maturity": skill["maturity"],
        "evidence_prs": skill["evidence_prs"],
        "invalidate_on": skill["invalidate_on"],
    }


def catalog_stats() -> dict[str, Any]:
    validate_skills()
    serialized = json.dumps(
        SKILLS,
        sort_keys=True,
        separators=(",", ":"),
    )
    return {
        "source_history_characters": SOURCE_HISTORY_CHARACTERS,
        "compiled_catalog_characters": len(serialized),
        "catalog_fraction_of_source": (
            len(serialized) / SOURCE_HISTORY_CHARACTERS
        ),
        "catalog_reduction_fraction": (
            1.0
            - len(serialized)
            / SOURCE_HISTORY_CHARACTERS
        ),
        "skill_count": len(SKILLS),
    }


def compile_decision_context(
    facts: dict[str, Any],
) -> dict[str, Any]:
    validate_skills()
    selected = []
    unresolved: set[str] = set()

    for skill in SKILLS:
        status, missing = _evaluate(skill, facts)
        if status == "MATCH":
            selected.append(skill)
        elif status == "PARTIAL":
            unresolved.update(missing)

    selected.sort(
        key=lambda row: (
            -row["priority"],
            row["id"],
        )
    )

    compact = {
        "invariants": list(INVARIANTS),
        "skills": [_capsule(skill) for skill in selected],
        "unresolved": sorted(unresolved),
    }

    serialized = json.dumps(
        compact,
        sort_keys=True,
        separators=(",", ":"),
    )

    return {
        **compact,
        "primary_action": (
            selected[0]["action"]
            if selected
            else "NO_COMPILED_DECISION"
        ),
        "context_characters": len(serialized),
        "context_fraction_of_source": (
            len(serialized) / SOURCE_HISTORY_CHARACTERS
        ),
        "context_reduction_fraction": (
            1.0
            - len(serialized)
            / SOURCE_HISTORY_CHARACTERS
        ),
    }


def run_panel() -> dict[str, Any]:
    stats = catalog_stats()

    exact = compile_decision_context(
        {
            "deterministic_duplicate_work": True,
            "scientific_contract_unchanged": True,
            "runtime_is_measurement": False,
        }
    )
    benchmark = compile_decision_context(
        {
            "deterministic_duplicate_work": True,
            "scientific_contract_unchanged": True,
            "runtime_is_measurement": True,
        }
    )
    cache_unknown = compile_decision_context(
        {"cache_candidate": True}
    )
    cache_reject = compile_decision_context(
        {
            "cache_candidate": True,
            "cache_restore_proven": False,
        }
    )
    exact_topology = compile_decision_context(
        {
            "topology_exact": True,
            "decision_uncertain": False,
        }
    )
    uncertain = compile_decision_context(
        {
            "decision_uncertain": True,
            "loss_sensitive": True,
        }
    )
    main_ci = compile_decision_context(
        {
            "same_head_duplicate_ci": True,
            "branch_is_main": True,
        }
    )
    research_ci = compile_decision_context(
        {
            "same_head_duplicate_ci": True,
            "branch_is_main": False,
        }
    )
    pre_receipt = compile_decision_context(
        {"parent_receipt_frozen": False}
    )
    post_receipt = compile_decision_context(
        {
            "parent_receipt_frozen": True,
            "prepared_delta_ready": True,
        }
    )

    checks = {
        "catalog_is_smaller_than_30pct_of_source": (
            stats["catalog_fraction_of_source"] < 0.30
        ),
        "selected_capsule_is_smaller_than_5pct_of_source": (
            exact["context_fraction_of_source"] < 0.05
        ),
        "exact_reuse_selected": (
            exact["primary_action"] == "REUSE_EXACT_COMPUTATION"
        ),
        "runtime_benchmark_preserved": (
            benchmark["primary_action"] == "PRESERVE_MEASUREMENT_BODY"
        ),
        "cache_unknown_fails_closed": (
            cache_unknown["primary_action"] == "NO_COMPILED_DECISION"
            and "cache_restore_proven" in cache_unknown["unresolved"]
        ),
        "negative_cache_skill_selected": (
            cache_reject["primary_action"] == "REJECT_CACHE_PROMOTION"
        ),
        "exact_topology_skips_mc": (
            exact_topology["primary_action"] == "SKIP_MONTE_CARLO"
        ),
        "uncertainty_runs_mc": (
            uncertain["primary_action"] == "RUN_MONTE_CARLO_ROBUSTNESS"
        ),
        "main_ci_preserved": (
            main_ci["primary_action"] == "KEEP_MAIN_CI"
        ),
        "research_ci_cancelled_when_superseded": (
            research_ci["primary_action"]
            == "CANCEL_SUPERSEDED_NON_MAIN_CI"
        ),
        "pre_receipt_is_ephemeral": (
            pre_receipt["primary_action"]
            == "DRAFT_EPHEMERALLY_NO_CANONICAL_GIT"
        ),
        "post_receipt_materializes": (
            post_receipt["primary_action"]
            == "MATERIALIZE_ATOMIC_CHILD_ON_RECEIPT_TREE"
        ),
    }

    return {
        "schema": SCHEMA,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "catalog": stats,
        "examples": {
            "exact_reuse": exact,
            "runtime_benchmark": benchmark,
            "cache_unknown": cache_unknown,
            "cache_reject": cache_reject,
            "exact_topology": exact_topology,
            "uncertain": uncertain,
            "main_ci": main_ci,
            "research_ci": research_ci,
            "pre_receipt": pre_receipt,
            "post_receipt": post_receipt,
        },
        "decision": (
            "COMPILE_REPEATED_RESEARCH_DECISIONS_INTO_SMALL_SKILL_CAPSULES"
        ),
        "fallback": (
            "If no compiled skill matches or required facts are unresolved, "
            "fall back to the full L0/L1/L2 research loop."
        ),
        "authority": (
            "Decision skills reduce re-reasoning and context surface only; "
            "they never grant execution authority."
        ),
        "claim_ceiling": (
            "COMPILED_DECISION_ROUTING_AND_CONTEXT_SURFACE_ONLY"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--facts")
    group.add_argument("--facts-file")
    args = parser.parse_args()

    if args.facts:
        result = compile_decision_context(
            json.loads(args.facts)
        )
    elif args.facts_file:
        result = compile_decision_context(
            json.loads(
                Path(args.facts_file).read_text(
                    encoding="utf-8"
                )
            )
        )
    else:
        result = run_panel()

    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
