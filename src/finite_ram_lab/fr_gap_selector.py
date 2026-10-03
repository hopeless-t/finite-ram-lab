from __future__ import annotations

import itertools
import json

from finite_ram_lab.fr_northstar_frontier import (
    ACTIONS,
    CONTRACT,
    WORKLOADS,
)
from finite_ram_lab.fr_primitive_registry import (
    PRIMITIVES,
)
from finite_ram_lab.fr_shadow_compiler import (
    PRIMITIVE_TO_ACTION,
)


SCHEMA = "finite-ram-lab.fr-northstar-004-gap-driven-selector/v0.1"


def _registered_for_domains(
    domains: set[str],
) -> list[dict]:
    return [
        primitive
        for primitive in PRIMITIVES
        if domains
        & set(
            primitive[
                "failure_domains"
            ]
        )
    ]


def _evaluate(
    workload: dict,
    actions: tuple[str, ...],
    contract: dict,
) -> dict:
    ram = float(
        workload[
            "base_ram_mib"
        ]
    )

    latency = float(
        workload[
            "base_p99_latency_ms"
        ]
    )

    quality = float(
        workload["quality"]
    )

    reliability = float(
        workload[
            "reliability"
        ]
    )

    cpu = 0.0
    io = 0.0

    for name in actions:
        action = ACTIONS[name]
        atom_fraction = (
            workload[
                "atoms"
            ][
                action[
                    "atom"
                ]
            ]
        )

        ram -= (
            workload[
                "base_ram_mib"
            ]
            * atom_fraction
            * (
                1.0
                - action[
                    "retain_fraction"
                ]
            )
        )

        latency += action[
            "latency_ms"
        ]

        quality += action[
            "quality_delta"
        ]

        reliability += action[
            "reliability_delta"
        ]

        cpu += action[
            "cpu_units"
        ]

        io += action[
            "io_mib"
        ]

    qualified = (
        latency
        <= contract[
            "max_p99_latency_ms"
        ]
        and quality
        >= contract[
            "min_quality"
        ]
        and reliability
        >= contract[
            "min_reliability"
        ]
        and cpu
        <= contract[
            "max_extra_cpu_units"
        ]
        and io
        <= contract[
            "max_extra_io_mib"
        ]
    )

    return {
        "resident_ram_mib": ram,
        "p99_latency_ms": latency,
        "quality": quality,
        "reliability": reliability,
        "extra_cpu_units": cpu,
        "extra_io_mib": io,
        "qualified": qualified,
    }


def _best(
    *,
    workload: dict,
    actions: list[str],
    contract: dict,
) -> dict:
    best_any = None
    best_qualified = None

    for width in range(
        len(actions) + 1
    ):
        for combo in itertools.combinations(
            actions,
            width,
        ):
            row = _evaluate(
                workload,
                combo,
                contract,
            )

            candidate = (
                row[
                    "resident_ram_mib"
                ],
                combo,
                row,
            )

            if (
                best_any is None
                or candidate[0]
                < best_any[0]
            ):
                best_any = candidate

            if (
                row["qualified"]
                and (
                    best_qualified
                    is None
                    or candidate[0]
                    < best_qualified[0]
                )
            ):
                best_qualified = (
                    candidate
                )

    return {
        "best_any": (
            None
            if best_any is None
            else {
                "actions": list(
                    best_any[1]
                ),
                **best_any[2],
            }
        ),
        "best_qualified": (
            None
            if best_qualified is None
            else {
                "actions": list(
                    best_qualified[1]
                ),
                **best_qualified[2],
            }
        ),
    }


def classify_gap(
    *,
    workload_name: str,
    budget_mib: float,
    failure_domains: list[str],
    facts: list[str],
    contract: dict | None = None,
) -> dict:
    workload = WORKLOADS[
        workload_name
    ]

    active_contract = dict(
        CONTRACT
    )

    if contract is not None:
        active_contract.update(
            contract
        )

    domains = set(
        failure_domains
    )

    facts_set = set(
        facts
    )

    registered = (
        _registered_for_domains(
            domains
        )
    )

    if not registered:
        return {
            "classification": (
                "CAPABILITY_GAP"
            ),
            "next_step": (
                "OPEN_NEW_MECHANISM_LANE"
            ),
            "reason": (
                "No registered primitive attacks the observed failure domain."
            ),
            "registered": [],
        }

    evidence_ready = []
    evidence_blocked = []

    for primitive in registered:
        missing = sorted(
            set(
                primitive[
                    "requires"
                ]
            )
            - facts_set
        )

        if missing:
            evidence_blocked.append(
                {
                    "primitive": (
                        primitive["id"]
                    ),
                    "missing": missing,
                }
            )
        else:
            evidence_ready.append(
                primitive
            )

    modeled_ready = [
        primitive
        for primitive in evidence_ready
        if primitive["id"]
        in PRIMITIVE_TO_ACTION
    ]

    modeled_counterfactual = [
        primitive
        for primitive in registered
        if primitive["id"]
        in PRIMITIVE_TO_ACTION
    ]

    if (
        not modeled_ready
        and evidence_blocked
    ):
        counterfactual_actions = sorted(
            {
                PRIMITIVE_TO_ACTION[
                    primitive["id"]
                ]
                for primitive
                in modeled_counterfactual
            }
        )

        counterfactual = _best(
            workload=workload,
            actions=(
                counterfactual_actions
            ),
            contract=(
                active_contract
            ),
        )

        if (
            counterfactual[
                "best_qualified"
            ] is not None
            and counterfactual[
                "best_qualified"
            ][
                "resident_ram_mib"
            ]
            <= budget_mib
        ):
            return {
                "classification": (
                    "EVIDENCE_GAP"
                ),
                "next_step": (
                    "MEASURE_MISSING_PRECONDITIONS"
                ),
                "reason": (
                    "Existing modeled primitives could close the gap if their applicability evidence were available."
                ),
                "evidence_blocked": (
                    evidence_blocked
                ),
            }

    if (
        evidence_ready
        and not modeled_ready
    ):
        return {
            "classification": (
                "MODEL_GAP"
            ),
            "next_step": (
                "QUALIFY_EFFECT_MODEL"
            ),
            "reason": (
                "Applicable registered primitives exist, but none has a schedulable effect model."
            ),
            "registered": [
                row["id"]
                for row
                in evidence_ready
            ],
        }

    ready_actions = sorted(
        {
            PRIMITIVE_TO_ACTION[
                primitive["id"]
            ]
            for primitive
            in modeled_ready
        }
    )

    ready = _best(
        workload=workload,
        actions=ready_actions,
        contract=active_contract,
    )

    if (
        ready[
            "best_qualified"
        ] is not None
        and ready[
            "best_qualified"
        ][
            "resident_ram_mib"
        ]
        <= budget_mib
    ):
        return {
            "classification": (
                "FRONTIER_REACHED"
            ),
            "next_step": (
                "NO_NEW_RESEARCH"
            ),
            "best": (
                ready[
                    "best_qualified"
                ]
            ),
        }

    all_modeled_actions = sorted(
        {
            PRIMITIVE_TO_ACTION[
                primitive["id"]
            ]
            for primitive
            in modeled_counterfactual
        }
    )

    all_modeled = _best(
        workload=workload,
        actions=(
            all_modeled_actions
        ),
        contract=active_contract,
    )

    if (
        evidence_blocked
        and all_modeled[
            "best_qualified"
        ] is not None
        and all_modeled[
            "best_qualified"
        ][
            "resident_ram_mib"
        ]
        <= budget_mib
    ):
        return {
            "classification": (
                "EVIDENCE_GAP"
            ),
            "next_step": (
                "MEASURE_MISSING_PRECONDITIONS"
            ),
            "reason": (
                "Completing applicability evidence would make an existing composition sufficient."
            ),
            "evidence_blocked": (
                evidence_blocked
            ),
        }

    if (
        ready[
            "best_any"
        ] is not None
        and ready[
            "best_any"
        ][
            "resident_ram_mib"
        ]
        <= budget_mib
        and not ready[
            "best_any"
        ][
            "qualified"
        ]
    ):
        return {
            "classification": (
                "CONTRACT_GAP"
            ),
            "next_step": (
                "FIND_LOWER_COST_COMPOSITION_OR_REVISIT_CONTRACT"
            ),
            "reason": (
                "Known capabilities can hit the RAM budget only by violating another task contract."
            ),
            "best_unqualified": (
                ready[
                    "best_any"
                ]
            ),
        }

    unmodeled_ready = [
        primitive["id"]
        for primitive
        in evidence_ready
        if primitive["id"]
        not in PRIMITIVE_TO_ACTION
    ]

    if unmodeled_ready:
        return {
            "classification": (
                "MODEL_GAP"
            ),
            "next_step": (
                "QUALIFY_EFFECT_MODEL"
            ),
            "reason": (
                "A potentially relevant registered capability is applicable but lacks an effect model."
            ),
            "unmodeled": (
                unmodeled_ready
            ),
        }

    return {
        "classification": (
            "CAPABILITY_GAP"
        ),
        "next_step": (
            "OPEN_NEW_MECHANISM_LANE"
        ),
        "reason": (
            "Current evidence-complete modeled primitives cannot reach the RAM budget while satisfying the contract."
        ),
        "ready_actions": (
            ready_actions
        ),
    }


def _facts_for(
    primitive_ids: list[str],
) -> list[str]:
    facts = set()

    for primitive in PRIMITIVES:
        if primitive[
            "id"
        ] in primitive_ids:
            facts.update(
                primitive[
                    "requires"
                ]
            )

    return sorted(
        facts
    )


def run_panel() -> dict:
    all_core_ids = [
        "QUANTIZE_STATE",
        "SHARE_IMMUTABLE_MMAP",
        "PAGED_ALLOCATE",
        "REMATERIALIZE_STATE",
        "RECLAIM_CLEAN_FILE_CACHE",
        "COMPRESS_STATE",
    ]

    full_domains = [
        "REPRESENTATION_HEAVY",
        "DUPLICATION_HEAVY",
        "EXTERNAL_FRAGMENTATION",
        "REBUILDABLE_STATE",
        "PAGECACHE_PRESSURE",
        "COMPRESSIBLE_STATE",
    ]

    evidence_gap = (
        classify_gap(
            workload_name=(
                "MULTIWORKER_LLM"
            ),
            budget_mib=600.0,
            failure_domains=(
                full_domains
            ),
            facts=_facts_for(
                [
                    primitive_id
                    for primitive_id
                    in all_core_ids
                    if primitive_id
                    != "SHARE_IMMUTABLE_MMAP"
                ]
            ),
        )
    )

    model_gap = classify_gap(
        workload_name=(
            "OUT_OF_CORE"
        ),
        budget_mib=600.0,
        failure_domains=[
            "MULTI_TIER_PRESSURE"
        ],
        facts=_facts_for(
            [
                "SEMANTIC_TIER"
            ]
        ),
    )

    capability_gap = (
        classify_gap(
            workload_name=(
                "OUT_OF_CORE"
            ),
            budget_mib=600.0,
            failure_domains=[
                "TRANSFER_STAGING_PRESSURE"
            ],
            facts=[],
        )
    )

    contract_gap = classify_gap(
        workload_name=(
            "LONG_CONTEXT"
        ),
        budget_mib=950.0,
        failure_domains=[
            "REPRESENTATION_HEAVY"
        ],
        facts=_facts_for(
            [
                "QUANTIZE_STATE"
            ]
        ),
        contract={
            "min_quality": 0.995,
        },
    )

    frontier_reached = classify_gap(
        workload_name=(
            "MULTIWORKER_LLM"
        ),
        budget_mib=600.0,
        failure_domains=(
            full_domains
        ),
        facts=_facts_for(
            all_core_ids
        ),
    )

    frozen = {
        "evidence_gap": (
            "EVIDENCE_GAP"
        ),
        "model_gap": (
            "MODEL_GAP"
        ),
        "capability_gap": (
            "CAPABILITY_GAP"
        ),
        "contract_gap": (
            "CONTRACT_GAP"
        ),
        "frontier_reached": (
            "FRONTIER_REACHED"
        ),
        "new_mechanism_cases": 1,
    }

    rows = {
        "evidence_gap": evidence_gap,
        "model_gap": model_gap,
        "capability_gap": (
            capability_gap
        ),
        "contract_gap": contract_gap,
        "frontier_reached": (
            frontier_reached
        ),
    }

    actual = {
        key: row[
            "classification"
        ]
        for key, row
        in rows.items()
    }

    actual[
        "new_mechanism_cases"
    ] = sum(
        row[
            "next_step"
        ]
        == "OPEN_NEW_MECHANISM_LANE"
        for row in rows.values()
    )

    if actual != frozen:
        raise RuntimeError(
            "frozen_gap_selector_changed:"
            f"{actual}"
        )

    return {
        "schema": SCHEMA,
        "status": "PASS",
        "classification": (
            "GAP_DRIVEN_RESEARCH_SELECTOR_VALIDATED"
        ),
        "cases": rows,
        "summary": {
            "cases": len(
                rows
            ),
            "new_mechanism_cases": (
                actual[
                    "new_mechanism_cases"
                ]
            ),
            "research_sprawl_avoided_cases": (
                len(rows)
                - actual[
                    "new_mechanism_cases"
                ]
                - 1
            ),
            "frontier_already_reached_cases": (
                sum(
                    row[
                        "classification"
                    ]
                    == "FRONTIER_REACHED"
                    for row
                    in rows.values()
                )
            ),
        },
        "policy": {
            "EVIDENCE_GAP": (
                "measure missing applicability evidence"
            ),
            "MODEL_GAP": (
                "qualify an effect model for an existing primitive"
            ),
            "CAPABILITY_GAP": (
                "open a new mechanism research lane"
            ),
            "CONTRACT_GAP": (
                "seek a lower-cost composition or explicitly revisit the task contract"
            ),
            "FRONTIER_REACHED": (
                "do not create new research; move to replay/host qualification"
            ),
        },
        "primary_findings": [
            "MOST_FRONTIER_MISSES_DO_NOT_AUTOMATICALLY_JUSTIFY_A_NEW_MECHANISM",
            "MISSING_EVIDENCE_AND_MISSING_CAPABILITY_ARE_DIFFERENT_RESEARCH_PROBLEMS",
            "REGISTERED_CAPABILITY_WITHOUT_EFFECT_MODEL_SHOULD_TRIGGER_MODEL_QUALIFICATION_NOT_NEW_MECHANISM_WORK",
            "CONTRACT_VIOLATION_SHOULD_NOT_BE_DISGUISED_AS_A_MEMORY_WIN",
            "THE_EXPERIMENT_SELECTOR_CAN_MAKE_RESEARCH_SPRAWL_FAIL_CLOSED",
        ],
        "claim_ceiling": (
            "SYNTHETIC_GAP_CLASSIFICATION_AND_RESEARCH_ROUTING_ONLY"
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
