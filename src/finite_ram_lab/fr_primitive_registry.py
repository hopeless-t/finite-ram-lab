from __future__ import annotations

import json
from dataclasses import dataclass


SCHEMA = "finite-ram-lab.fr-northstar-002-primitive-registry/v0.2"

EVIDENCE_ORDER = {
    "SOURCE_GROUNDED": 0,
    "SYNTHETIC": 1,
    "HOSTED_PHYSICAL": 2,
    "HOST_BOUND_PHYSICAL": 3,
}

PRIMITIVES = (
    {
        "id": "QUANTIZE_STATE",
        "atoms": ["Q"],
        "failure_domains": [
            "REPRESENTATION_HEAVY",
            "LONG_CONTEXT",
        ],
        "evidence": {
            "pr": 91,
            "head_sha": "b471f6592614cac8008e3ec47283c9c96722e432",
            "class": "SYNTHETIC",
            "claim_ceiling": "SOURCE_GROUNDED_FORMULA_AND_SYNTHETIC_STATE_TYPED_QUANTIZATION_ONLY",
        },
        "requires": [
            "state_type_known",
            "quality_floor_known",
            "supported_quantized_representation",
        ],
        "cost_dimensions": [
            "quality",
            "latency",
            "cpu",
            "workspace",
        ],
        "reversible": True,
        "mutates_live_workload": True,
        "live_promotion_allowed": False,
        "fail_closed_on": [
            "unknown_quality_effect",
            "unsupported_kernel",
            "unknown_state_type",
        ],
    },
    {
        "id": "SHARE_IMMUTABLE_MMAP",
        "atoms": ["D"],
        "failure_domains": [
            "DUPLICATION_HEAVY",
            "MULTIWORKER",
        ],
        "evidence": {
            "pr": 90,
            "head_sha": "a1b94c9ccd9b3601ba71f335be35e4bc12249453",
            "class": "HOSTED_PHYSICAL",
            "claim_ceiling": "HOSTED_LINUX_IMMUTABLE_PROCESS_PSS_SHARING_ONLY",
        },
        "requires": [
            "immutable_or_copy_on_write_safe",
            "shared_backing_identity",
            "pss_available_for_validation",
        ],
        "cost_dimensions": [
            "mapping_setup",
            "page_cache",
            "mutation_breakaway",
        ],
        "reversible": True,
        "mutates_live_workload": True,
        "live_promotion_allowed": False,
        "fail_closed_on": [
            "unknown_mutability",
            "private_write_required",
            "backing_identity_mismatch",
        ],
    },
    {
        "id": "PAGED_ALLOCATE",
        "atoms": ["F"],
        "failure_domains": [
            "EXTERNAL_FRAGMENTATION",
            "DYNAMIC_KV",
        ],
        "evidence": {
            "pr": 92,
            "head_sha": "1d1b15ababd4869b9c6468e2f34f4400436fe14f",
            "class": "SYNTHETIC",
            "claim_ceiling": "SOURCE_GROUNDED_SYNTHETIC_ALLOCATOR_GEOMETRY_ONLY",
        },
        "requires": [
            "block_addressable_state",
            "allocator_indirection_supported",
        ],
        "cost_dimensions": [
            "metadata",
            "allocator_ops",
            "kernel_layout_cost",
        ],
        "reversible": True,
        "mutates_live_workload": True,
        "live_promotion_allowed": False,
        "fail_closed_on": [
            "allocator_incompatible",
            "unknown_kernel_cost",
        ],
    },
    {
        "id": "PREFIX_SHARE",
        "atoms": ["D", "F"],
        "failure_domains": [
            "PREFIX_DUPLICATION",
            "DYNAMIC_KV",
        ],
        "evidence": {
            "pr": 92,
            "head_sha": "1d1b15ababd4869b9c6468e2f34f4400436fe14f",
            "class": "SYNTHETIC",
            "claim_ceiling": "SOURCE_GROUNDED_SYNTHETIC_ALLOCATOR_GEOMETRY_ONLY",
        },
        "requires": [
            "prefix_identity_proven",
            "compatible_state_semantics",
        ],
        "cost_dimensions": [
            "metadata",
            "reference_tracking",
        ],
        "reversible": True,
        "mutates_live_workload": True,
        "live_promotion_allowed": False,
        "fail_closed_on": [
            "prefix_identity_unknown",
            "state_mutability_unknown",
        ],
    },
    {
        "id": "REMATERIALIZE_STATE",
        "atoms": ["G", "C"],
        "failure_domains": [
            "REBUILDABLE_STATE",
            "FAST_TIER_PRESSURE",
        ],
        "evidence": {
            "pr": 93,
            "head_sha": "bb94e965f227238e94a86acef52f6db05bb21a27",
            "class": "SYNTHETIC",
            "claim_ceiling": "SOURCE_GROUNDED_SYNTHETIC_REMATERIALIZATION_PLANNER_ONLY",
        },
        "requires": [
            "rebuildable_true",
            "replay_dependencies_known",
            "rebuild_deadline_known",
        ],
        "cost_dimensions": [
            "cpu",
            "latency",
            "tail",
        ],
        "reversible": True,
        "mutates_live_workload": True,
        "live_promotion_allowed": False,
        "fail_closed_on": [
            "rebuildability_unknown",
            "nondeterministic_side_effect",
            "rebuild_deadline_unknown",
        ],
    },
    {
        "id": "OFFLOAD_STATE",
        "atoms": ["R", "T", "X"],
        "failure_domains": [
            "FAST_TIER_PRESSURE",
            "COLD_RESTOREABLE_STATE",
        ],
        "evidence": {
            "pr": 93,
            "head_sha": "bb94e965f227238e94a86acef52f6db05bb21a27",
            "class": "SYNTHETIC",
            "claim_ceiling": "SOURCE_GROUNDED_SYNTHETIC_REMATERIALIZATION_PLANNER_ONLY",
        },
        "requires": [
            "slow_tier_available",
            "restore_deadline_known",
            "transfer_budget_known",
        ],
        "cost_dimensions": [
            "io",
            "latency",
            "tail",
            "staging",
        ],
        "reversible": True,
        "mutates_live_workload": True,
        "live_promotion_allowed": False,
        "fail_closed_on": [
            "unknown_delivery",
            "restore_deadline_unknown",
            "transfer_budget_unknown",
        ],
    },
    {
        "id": "RECLAIM_CLEAN_FILE_CACHE",
        "atoms": ["P", "R"],
        "failure_domains": [
            "PAGECACHE_PRESSURE",
            "OUT_OF_CORE",
        ],
        "evidence": {
            "pr": 94,
            "head_sha": "68856fa4161063e3e4c98827e821d866e0284c52",
            "class": "HOSTED_PHYSICAL",
            "claim_ceiling": "HOSTED_LINUX_CLEAN_FILE_PAGE_CACHE_RESIDENCY_ONLY",
        },
        "requires": [
            "clean_file_backed_state",
            "reclaim_hint_supported",
        ],
        "cost_dimensions": [
            "future_io",
            "latency",
            "page_faults",
        ],
        "reversible": True,
        "mutates_live_workload": True,
        "live_promotion_allowed": False,
        "fail_closed_on": [
            "dirty_state",
            "reclaim_semantics_unknown",
        ],
    },
    {
        "id": "COMPRESS_STATE",
        "atoms": ["Z", "Q"],
        "failure_domains": [
            "COMPRESSIBLE_STATE",
            "COLD_STATE",
        ],
        "evidence": {
            "pr": 95,
            "head_sha": "8fda34c0413a673b5467bccbc3a2c1f567d33ac6",
            "class": "HOSTED_PHYSICAL",
            "claim_ceiling": "HOSTED_LINUX_USERSPACE_CODEC_SURFACE_ONLY",
        },
        "requires": [
            "compressibility_sample_available",
            "codec_available",
            "restore_cost_budget_known",
        ],
        "cost_dimensions": [
            "cpu",
            "decompress_latency",
            "workspace",
            "metadata",
        ],
        "reversible": True,
        "mutates_live_workload": True,
        "live_promotion_allowed": False,
        "fail_closed_on": [
            "incompressible_state",
            "unknown_restore_cost",
        ],
    },
    {
        "id": "DEMAND_FOLD",
        "atoms": ["W", "C"],
        "failure_domains": [
            "CONCURRENCY_PRESSURE",
            "CONTENTIOUS_WORKLOAD",
        ],
        "evidence": {
            "pr": 71,
            "head_sha": "80768cd4b79ae7d83715fe153d4762b2ff005f21",
            "class": "SYNTHETIC",
            "claim_ceiling": "SOURCE_GROUNDED_STEAL_GOVERNOR_TRANSFER_PLUS_SYNTHETIC_DEMAND_FOLDING_SHADOW_ONLY",
        },
        "requires": [
            "application_exposes_reversible_demand_knob",
            "progress_floor_known",
        ],
        "cost_dimensions": [
            "throughput",
            "latency",
        ],
        "reversible": True,
        "mutates_live_workload": True,
        "live_promotion_allowed": False,
        "fail_closed_on": [
            "progress_floor_unknown",
            "demand_knob_not_reversible",
        ],
    },
    {
        "id": "SEMANTIC_TIER",
        "atoms": ["R", "T", "G"],
        "failure_domains": [
            "MULTI_TIER_PRESSURE",
            "SEMANTIC_PRIORITY",
        ],
        "evidence": {
            "pr": 65,
            "head_sha": "ef2c958eb8caa09fd0b998ec276303a6b38e3f06",
            "class": "SYNTHETIC",
            "claim_ceiling": "SYNTHETIC_SEMANTIC_TIER_PLANNER_ONLY",
        },
        "requires": [
            "semantic_priority_known",
            "tier_latency_distribution_known",
            "migration_deadline_known",
        ],
        "cost_dimensions": [
            "semantic_loss",
            "restore_latency",
            "tail",
            "ssd_writes",
        ],
        "reversible": True,
        "mutates_live_workload": True,
        "live_promotion_allowed": False,
        "fail_closed_on": [
            "semantic_priority_unknown",
            "migration_deadline_unknown",
            "unknown_delivery",
        ],
    },
    {
        "id": "DIRECT_TRANSFER_NO_STAGING",
        "atoms": ["X"],
        "failure_domains": [
            "TRANSFER_STAGING_PRESSURE",
        ],
        "evidence": {
            "pr": 100,
            "head_sha": "f6293a4ec0a046becf25d286bf100b5ea1a97678",
            "class": "HOSTED_PHYSICAL",
            "claim_ceiling": "HOSTED_LINUX_PYTHON_TRANSFER_STAGING_PROXY_ONLY",
        },
        "requires": [
            "source_destination_copy_semantics_valid",
            "staging_not_required",
            "payload_size_known",
            "memory_budget_known",
        ],
        "cost_dimensions": [
            "transient_peak",
            "copy_cpu",
            "copy_latency",
        ],
        "reversible": True,
        "mutates_live_workload": True,
        "live_promotion_allowed": False,
        "fail_closed_on": [
            "staging_required",
            "unknown_copy_semantics",
            "unknown_payload_size",
            "unknown_memory_budget",
        ],
    },
    {
        "id": "ZERO_COPY_SHARED_VIEW",
        "atoms": ["X", "D"],
        "failure_domains": [
            "TRANSFER_STAGING_PRESSURE",
        ],
        "evidence": {
            "pr": 100,
            "head_sha": "f6293a4ec0a046becf25d286bf100b5ea1a97678",
            "class": "HOSTED_PHYSICAL",
            "claim_ceiling": "HOSTED_LINUX_PYTHON_TRANSFER_STAGING_PROXY_ONLY",
        },
        "requires": [
            "share_compatible_semantics",
            "source_lifetime_covers_consumer",
            "aliasing_safe",
            "memory_budget_known",
        ],
        "cost_dimensions": [
            "lifetime_coupling",
            "aliasing",
            "consumer_compatibility",
        ],
        "reversible": True,
        "mutates_live_workload": True,
        "live_promotion_allowed": False,
        "fail_closed_on": [
            "share_semantics_unknown",
            "source_lifetime_too_short",
            "aliasing_safety_unknown",
            "unknown_memory_budget",
        ],
    },
)

SUPPORT_PRIMITIVES = (
    {
        "id": "ADAPTIVE_OBSERVATION",
        "evidence_pr": 85,
        "role": "Reduce observer cost while preserving anomaly capture.",
    },
    {
        "id": "OBSERVER_ABA_QUALIFICATION",
        "evidence_pr": 86,
        "role": "Measure observer perturbation before trusting telemetry.",
    },
    {
        "id": "READONLY_PROCFS_COLLECTOR",
        "evidence_pr": 87,
        "role": "Collect core memory/pressure evidence without target mutation.",
    },
    {
        "id": "CAUSAL_ASOF_JOIN",
        "evidence_pr": 88,
        "role": "Prevent future-information leakage during shadow replay.",
    },
)


def validate_registry() -> None:
    ids = set()

    for primitive in PRIMITIVES:
        primitive_id = primitive[
            "id"
        ]

        if primitive_id in ids:
            raise RuntimeError(
                "duplicate_primitive:"
                f"{primitive_id}"
            )

        ids.add(
            primitive_id
        )

        evidence = primitive[
            "evidence"
        ]

        if evidence[
            "class"
        ] not in EVIDENCE_ORDER:
            raise RuntimeError(
                "unknown_evidence_class:"
                f"{primitive_id}"
            )

        if primitive[
            "live_promotion_allowed"
        ]:
            if (
                evidence[
                    "class"
                ]
                != "HOST_BOUND_PHYSICAL"
            ):
                raise RuntimeError(
                    "live_promotion_without_host_bound_evidence:"
                    f"{primitive_id}"
                )

        if (
            primitive[
                "mutates_live_workload"
            ]
            and not primitive[
                "fail_closed_on"
            ]
        ):
            raise RuntimeError(
                "mutating_primitive_without_fail_closed_conditions:"
                f"{primitive_id}"
            )

        if not primitive[
            "requires"
        ]:
            raise RuntimeError(
                "primitive_without_preconditions:"
                f"{primitive_id}"
            )


def eligible(
    *,
    failure_domain: str,
    min_evidence_class: str = "SOURCE_GROUNDED",
    require_reversible: bool = True,
    live_only: bool = False,
) -> list[dict]:
    validate_registry()

    floor = EVIDENCE_ORDER[
        min_evidence_class
    ]

    result = []

    for primitive in PRIMITIVES:
        if (
            failure_domain
            not in primitive[
                "failure_domains"
            ]
        ):
            continue

        if (
            EVIDENCE_ORDER[
                primitive[
                    "evidence"
                ]["class"]
            ]
            < floor
        ):
            continue

        if (
            require_reversible
            and not primitive[
                "reversible"
            ]
        ):
            continue

        if (
            live_only
            and not primitive[
                "live_promotion_allowed"
            ]
        ):
            continue

        result.append(
            primitive
        )

    return result


def run_panel() -> dict:
    validate_registry()

    physical_duplication = [
        row["id"]
        for row in eligible(
            failure_domain=(
                "DUPLICATION_HEAVY"
            ),
            min_evidence_class=(
                "HOSTED_PHYSICAL"
            ),
        )
    ]

    physical_pagecache = [
        row["id"]
        for row in eligible(
            failure_domain=(
                "PAGECACHE_PRESSURE"
            ),
            min_evidence_class=(
                "HOSTED_PHYSICAL"
            ),
        )
    ]

    physical_compression = [
        row["id"]
        for row in eligible(
            failure_domain=(
                "COMPRESSIBLE_STATE"
            ),
            min_evidence_class=(
                "HOSTED_PHYSICAL"
            ),
        )
    ]

    physical_transfer = [
        row["id"]
        for row in eligible(
            failure_domain=(
                "TRANSFER_STAGING_PRESSURE"
            ),
            min_evidence_class=(
                "HOSTED_PHYSICAL"
            ),
        )
    ]

    live_candidates = [
        row["id"]
        for row in PRIMITIVES
        if row[
            "live_promotion_allowed"
        ]
    ]

    frozen = {
        "primitive_count": 12,
        "support_count": 4,
        "physical_duplication": [
            "SHARE_IMMUTABLE_MMAP"
        ],
        "physical_pagecache": [
            "RECLAIM_CLEAN_FILE_CACHE"
        ],
        "physical_compression": [
            "COMPRESS_STATE"
        ],
        "physical_transfer": [
            "DIRECT_TRANSFER_NO_STAGING",
            "ZERO_COPY_SHARED_VIEW"
        ],
        "live_candidates": [],
    }

    actual = {
        "primitive_count": len(
            PRIMITIVES
        ),
        "support_count": len(
            SUPPORT_PRIMITIVES
        ),
        "physical_duplication": (
            physical_duplication
        ),
        "physical_pagecache": (
            physical_pagecache
        ),
        "physical_compression": (
            physical_compression
        ),
        "physical_transfer": (
            physical_transfer
        ),
        "live_candidates": (
            live_candidates
        ),
    }

    if actual != frozen:
        raise RuntimeError(
            "frozen_registry_surface_changed:"
            f"{actual}"
        )

    return {
        "schema": SCHEMA,
        "status": "PASS",
        "classification": (
            "EVIDENCE_BACKED_PRIMITIVE_REGISTRY_VALIDATED"
        ),
        "evidence_order": (
            EVIDENCE_ORDER
        ),
        "primitives": list(
            PRIMITIVES
        ),
        "support_primitives": list(
            SUPPORT_PRIMITIVES
        ),
        "queries": {
            "hosted_physical_duplication": (
                physical_duplication
            ),
            "hosted_physical_pagecache": (
                physical_pagecache
            ),
            "hosted_physical_compression": (
                physical_compression
            ),
            "hosted_physical_transfer": (
                physical_transfer
            ),
            "live_promotion_candidates": (
                live_candidates
            ),
        },
        "governance": {
            "default_live_promotion": (
                "DENY"
            ),
            "minimum_live_evidence": (
                "HOST_BOUND_PHYSICAL"
            ),
            "unknown_applicability": (
                "FAIL_CLOSED"
            ),
            "unknown_delivery": (
                "DO_NOT_RETRY"
            ),
        },
        "primary_findings": [
            "PAST_RESEARCH_CAN_BE_COMPILED_INTO_MACHINE_READABLE_ACTION_PRIMITIVES",
            "EVIDENCE_CLASS_IS_PART_OF_ACTION_SEMANTICS",
            "APPLICABILITY_AND_FAIL_CLOSED_CONDITIONS_MUST_TRAVEL_WITH_THE_ACTION",
            "HOSTED_PHYSICAL_EVIDENCE_IS_NOT_AUTOMATIC_LIVE_PROMOTION_AUTHORITY",
            "THE_CURRENT_REGISTRY_HAS_ZERO_LIVE_PROMOTION_CANDIDATES_BY_DESIGN",
            "TRANSFER_STAGING_PRESSURE_NOW_HAS_HOSTED_PHYSICAL_PRIMITIVES",
        ],
        "claim_ceiling": (
            "REGISTRY_STRUCTURE_AND_EVIDENCE_ROUTING_ONLY"
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
    raise SystemExit(
        main()
    )
