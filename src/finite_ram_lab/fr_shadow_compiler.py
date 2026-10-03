from __future__ import annotations

import itertools
import json

from finite_ram_lab.fr_gfx_causal_join import (
    causal_asof,
)
from finite_ram_lab.fr_northstar_frontier import (
    WORKLOADS,
    evaluate,
)
from finite_ram_lab.fr_primitive_registry import (
    EVIDENCE_ORDER,
    PRIMITIVES,
)


SCHEMA = "finite-ram-lab.fr-northstar-003-causal-shadow-compiler/v0.1"
SHADOW_BUDGET_MIB = 600.0
EVIDENCE_MAX_AGE_NS = 100

PRIMITIVE_TO_ACTION = {
    "QUANTIZE_STATE": "QUANTIZE",
    "SHARE_IMMUTABLE_MMAP": "SHARE",
    "PAGED_ALLOCATE": "PAGING",
    "REMATERIALIZE_STATE": "REMATERIALIZE",
    "RECLAIM_CLEAN_FILE_CACHE": "RECLAIM_PAGECACHE",
    "COMPRESS_STATE": "COMPRESS",
}

DOMAIN_FOR_PRIMITIVE = {
    "QUANTIZE_STATE": "REPRESENTATION_HEAVY",
    "SHARE_IMMUTABLE_MMAP": "DUPLICATION_HEAVY",
    "PAGED_ALLOCATE": "EXTERNAL_FRAGMENTATION",
    "REMATERIALIZE_STATE": "REBUILDABLE_STATE",
    "RECLAIM_CLEAN_FILE_CACHE": "PAGECACHE_PRESSURE",
    "COMPRESS_STATE": "COMPRESSIBLE_STATE",
}

TARGET_PRIMITIVES = {
    "MULTIWORKER_LLM": [
        "QUANTIZE_STATE",
        "SHARE_IMMUTABLE_MMAP",
        "PAGED_ALLOCATE",
        "RECLAIM_CLEAN_FILE_CACHE",
        "COMPRESS_STATE",
    ],
    "LONG_CONTEXT": [
        "QUANTIZE_STATE",
        "SHARE_IMMUTABLE_MMAP",
        "PAGED_ALLOCATE",
        "REMATERIALIZE_STATE",
        "RECLAIM_CLEAN_FILE_CACHE",
    ],
    "SERVING_FRAGMENTED": [
        "QUANTIZE_STATE",
        "SHARE_IMMUTABLE_MMAP",
        "PAGED_ALLOCATE",
        "REMATERIALIZE_STATE",
        "RECLAIM_CLEAN_FILE_CACHE",
    ],
    "OUT_OF_CORE": [
        "QUANTIZE_STATE",
        "SHARE_IMMUTABLE_MMAP",
        "PAGED_ALLOCATE",
        "RECLAIM_CLEAN_FILE_CACHE",
        "COMPRESS_STATE",
    ],
    "COMPRESSIBLE_CACHE": [
        "SHARE_IMMUTABLE_MMAP",
        "REMATERIALIZE_STATE",
        "RECLAIM_CLEAN_FILE_CACHE",
        "COMPRESS_STATE",
    ],
    "REBUILDABLE_PIPELINE": [
        "QUANTIZE_STATE",
        "SHARE_IMMUTABLE_MMAP",
        "PAGED_ALLOCATE",
        "REMATERIALIZE_STATE",
        "RECLAIM_CLEAN_FILE_CACHE",
    ],
}


def _primitive_by_id(
    primitive_id: str,
) -> dict:
    for primitive in PRIMITIVES:
        if primitive[
            "id"
        ] == primitive_id:
            return primitive

    raise KeyError(
        primitive_id
    )


def _facts_for(
    primitive_ids: list[str],
) -> list[str]:
    facts = set()

    for primitive_id in (
        primitive_ids
    ):
        primitive = _primitive_by_id(
            primitive_id
        )

        facts.update(
            primitive[
                "requires"
            ]
        )

    return sorted(
        facts
    )


def _domains_for(
    primitive_ids: list[str],
) -> list[str]:
    return sorted(
        {
            DOMAIN_FOR_PRIMITIVE[
                primitive_id
            ]
            for primitive_id
            in primitive_ids
        }
    )


def _build_fixture() -> dict:
    snapshots = []
    evidence = []

    names = list(
        WORKLOADS
    )

    for index, name in enumerate(
        names,
        start=1,
    ):
        timestamp = (
            index * 1000
        )

        snapshots.append(
            {
                "timestamp_monotonic_ns": (
                    timestamp
                ),
                "workload": name,
            }
        )

        primitive_ids = list(
            TARGET_PRIMITIVES[
                name
            ]
        )

        if name == (
            "MULTIWORKER_LLM"
        ):
            causal_ids = [
                primitive_id
                for primitive_id
                in primitive_ids
                if primitive_id
                != "SHARE_IMMUTABLE_MMAP"
            ]

            evidence.append(
                {
                    "timestamp_monotonic_ns": (
                        timestamp - 50
                    ),
                    "workload": name,
                    "failure_domains": (
                        _domains_for(
                            causal_ids
                        )
                    ),
                    "facts": (
                        _facts_for(
                            causal_ids
                        )
                    ),
                }
            )

            evidence.append(
                {
                    "timestamp_monotonic_ns": (
                        timestamp + 10
                    ),
                    "workload": name,
                    "failure_domains": (
                        _domains_for(
                            primitive_ids
                        )
                    ),
                    "facts": (
                        _facts_for(
                            primitive_ids
                        )
                    ),
                    "adversarial_future": (
                        True
                    ),
                }
            )

        else:
            evidence.append(
                {
                    "timestamp_monotonic_ns": (
                        timestamp - 50
                    ),
                    "workload": name,
                    "failure_domains": (
                        _domains_for(
                            primitive_ids
                        )
                    ),
                    "facts": (
                        _facts_for(
                            primitive_ids
                        )
                    ),
                }
            )

    evidence.sort(
        key=lambda row: row[
            "timestamp_monotonic_ns"
        ]
    )

    return {
        "snapshots": snapshots,
        "evidence": evidence,
    }


def _nearest_any(
    *,
    timestamp_ns: int,
    rows: list[dict],
) -> dict:
    if not rows:
        return {
            "value": None,
            "missing": True,
            "stale": False,
            "age_ns": None,
            "source_timestamp_ns": (
                None
            ),
        }

    row = min(
        rows,
        key=lambda item: abs(
            int(
                item[
                    "timestamp_monotonic_ns"
                ]
            )
            - timestamp_ns
        ),
    )

    source_timestamp = int(
        row[
            "timestamp_monotonic_ns"
        ]
    )

    age = abs(
        timestamp_ns
        - source_timestamp
    )

    if (
        age
        > EVIDENCE_MAX_AGE_NS
    ):
        return {
            "value": None,
            "missing": False,
            "stale": True,
            "age_ns": age,
            "source_timestamp_ns": (
                source_timestamp
            ),
        }

    return {
        "value": row,
        "missing": False,
        "stale": False,
        "age_ns": age,
        "source_timestamp_ns": (
            source_timestamp
        ),
    }


def _eligible_action_names(
    evidence_row: dict,
) -> dict:
    domains = set(
        evidence_row.get(
            "failure_domains",
            [],
        )
    )

    facts = set(
        evidence_row.get(
            "facts",
            [],
        )
    )

    accepted = []
    rejected = []

    for primitive in PRIMITIVES:
        primitive_id = primitive[
            "id"
        ]

        if primitive_id not in (
            PRIMITIVE_TO_ACTION
        ):
            rejected.append(
                {
                    "primitive": (
                        primitive_id
                    ),
                    "reason": (
                        "NO_SHADOW_EFFECT_MODEL"
                    ),
                }
            )
            continue

        if not (
            domains
            & set(
                primitive[
                    "failure_domains"
                ]
            )
        ):
            rejected.append(
                {
                    "primitive": (
                        primitive_id
                    ),
                    "reason": (
                        "FAILURE_DOMAIN_NOT_OBSERVED"
                    ),
                }
            )
            continue

        missing = sorted(
            set(
                primitive[
                    "requires"
                ]
            )
            - facts
        )

        if missing:
            rejected.append(
                {
                    "primitive": (
                        primitive_id
                    ),
                    "reason": (
                        "MISSING_PRECONDITION"
                    ),
                    "missing": (
                        missing
                    ),
                }
            )
            continue

        if (
            EVIDENCE_ORDER[
                primitive[
                    "evidence"
                ]["class"]
            ]
            < EVIDENCE_ORDER[
                "SYNTHETIC"
            ]
        ):
            rejected.append(
                {
                    "primitive": (
                        primitive_id
                    ),
                    "reason": (
                        "EVIDENCE_BELOW_SHADOW_FLOOR"
                    ),
                }
            )
            continue

        accepted.append(
            PRIMITIVE_TO_ACTION[
                primitive_id
            ]
        )

    return {
        "accepted_actions": sorted(
            set(
                accepted
            )
        ),
        "rejected": rejected,
    }


def _compile_with_evidence(
    *,
    workload_name: str,
    evidence_state: dict,
) -> dict:
    workload = WORKLOADS[
        workload_name
    ]

    if (
        evidence_state[
            "missing"
        ]
        or evidence_state[
            "stale"
        ]
        or evidence_state[
            "value"
        ] is None
    ):
        baseline = evaluate(
            workload,
            (),
        )

        return {
            "status": (
                "INSUFFICIENT_EVIDENCE"
            ),
            "actions": [],
            "result": baseline,
            "rejected": [
                {
                    "reason": (
                        "MISSING_OR_STALE_EVIDENCE"
                    ),
                }
            ],
            "evidence_state": (
                evidence_state
            ),
        }

    eligibility = (
        _eligible_action_names(
            evidence_state[
                "value"
            ]
        )
    )

    action_names = tuple(
        eligibility[
            "accepted_actions"
        ]
    )

    best = None

    for width in range(
        len(action_names) + 1
    ):
        for combo in itertools.combinations(
            action_names,
            width,
        ):
            result = evaluate(
                workload,
                combo,
            )

            if not result[
                "qualified"
            ]:
                continue

            candidate = (
                result[
                    "resident_ram_mib"
                ],
                combo,
                result,
            )

            if (
                best is None
                or candidate[0]
                < best[0]
            ):
                best = candidate

    if best is None:
        baseline = evaluate(
            workload,
            (),
        )

        return {
            "status": (
                "NO_QUALIFIED_COMPOSITION"
            ),
            "actions": [],
            "result": baseline,
            "rejected": (
                eligibility[
                    "rejected"
                ]
            ),
            "evidence_state": (
                evidence_state
            ),
        }

    return {
        "status": "QUALIFIED_SHADOW",
        "actions": list(
            best[1]
        ),
        "result": best[2],
        "rejected": (
            eligibility[
                "rejected"
            ]
        ),
        "evidence_state": (
            evidence_state
        ),
    }


def run_panel() -> dict:
    fixture = _build_fixture()

    evidence_rows = fixture[
        "evidence"
    ]

    timestamps = [
        int(
            row[
                "timestamp_monotonic_ns"
            ]
        )
        for row in evidence_rows
    ]

    causal = {}
    leaky = {}
    causal_future_uses = 0
    leaky_future_uses = 0

    for snapshot in fixture[
        "snapshots"
    ]:
        timestamp = int(
            snapshot[
                "timestamp_monotonic_ns"
            ]
        )

        workload = snapshot[
            "workload"
        ]

        causal_state = causal_asof(
            timestamp_ns=timestamp,
            rows=evidence_rows,
            timestamps=timestamps,
            max_age_ns=(
                EVIDENCE_MAX_AGE_NS
            ),
        )

        causal[
            workload
        ] = _compile_with_evidence(
            workload_name=workload,
            evidence_state=(
                causal_state
            ),
        )

        if (
            causal_state[
                "source_timestamp_ns"
            ]
            is not None
            and causal_state[
                "source_timestamp_ns"
            ]
            > timestamp
        ):
            causal_future_uses += 1

        nearest_state = (
            _nearest_any(
                timestamp_ns=timestamp,
                rows=evidence_rows,
            )
        )

        leaky[
            workload
        ] = _compile_with_evidence(
            workload_name=workload,
            evidence_state=(
                nearest_state
            ),
        )

        if (
            nearest_state[
                "source_timestamp_ns"
            ]
            is not None
            and nearest_state[
                "source_timestamp_ns"
            ]
            > timestamp
        ):
            leaky_future_uses += 1

    causal_at_budget = sum(
        row[
            "status"
        ] == "QUALIFIED_SHADOW"
        and row[
            "result"
        ][
            "resident_ram_mib"
        ]
        <= SHADOW_BUDGET_MIB
        for row in causal.values()
    )

    leaky_at_budget = sum(
        row[
            "status"
        ] == "QUALIFIED_SHADOW"
        and row[
            "result"
        ][
            "resident_ram_mib"
        ]
        <= SHADOW_BUDGET_MIB
        for row in leaky.values()
    )

    stale_snapshot = {
        "timestamp_monotonic_ns": (
            7100
        ),
        "workload": (
            "MULTIWORKER_LLM"
        ),
    }

    stale_state = causal_asof(
        timestamp_ns=(
            stale_snapshot[
                "timestamp_monotonic_ns"
            ]
        ),
        rows=evidence_rows,
        timestamps=timestamps,
        max_age_ns=(
            EVIDENCE_MAX_AGE_NS
        ),
    )

    stale_decision = (
        _compile_with_evidence(
            workload_name=(
                stale_snapshot[
                    "workload"
                ]
            ),
            evidence_state=(
                stale_state
            ),
        )
    )

    frozen = {
        "causal_at_600": 5,
        "leaky_at_600": 6,
        "causal_future_uses": 0,
        "leaky_future_uses": 1,
        "causal_multiworker_ram": (
            681.5
        ),
        "leaky_multiworker_ram": (
            369.9
        ),
        "stale_status": (
            "INSUFFICIENT_EVIDENCE"
        ),
    }

    actual = {
        "causal_at_600": (
            causal_at_budget
        ),
        "leaky_at_600": (
            leaky_at_budget
        ),
        "causal_future_uses": (
            causal_future_uses
        ),
        "leaky_future_uses": (
            leaky_future_uses
        ),
        "causal_multiworker_ram": (
            causal[
                "MULTIWORKER_LLM"
            ][
                "result"
            ][
                "resident_ram_mib"
            ]
        ),
        "leaky_multiworker_ram": (
            leaky[
                "MULTIWORKER_LLM"
            ][
                "result"
            ][
                "resident_ram_mib"
            ]
        ),
        "stale_status": (
            stale_decision[
                "status"
            ]
        ),
    }

    if actual != frozen:
        raise RuntimeError(
            "frozen_shadow_compiler_changed:"
            f"{actual}"
        )

    return {
        "schema": SCHEMA,
        "status": "PASS",
        "classification": (
            "CAUSAL_SHADOW_COMPILER_VALIDATED"
        ),
        "budget_mib": (
            SHADOW_BUDGET_MIB
        ),
        "fixture": fixture,
        "causal_decisions": causal,
        "leaky_nearest_neighbor_decisions": (
            leaky
        ),
        "stale_evidence_decision": (
            stale_decision
        ),
        "summary": {
            "causal_qualified_at_budget": (
                causal_at_budget
            ),
            "leaky_qualified_at_budget": (
                leaky_at_budget
            ),
            "causal_future_evidence_uses": (
                causal_future_uses
            ),
            "leaky_future_evidence_uses": (
                leaky_future_uses
            ),
            "apparent_gain_from_future_leakage": (
                leaky_at_budget
                - causal_at_budget
            ),
        },
        "governance": {
            "shadow_only": True,
            "live_actions_executed": 0,
            "missing_evidence": (
                "FAIL_CLOSED"
            ),
            "stale_evidence": (
                "FAIL_CLOSED"
            ),
            "future_evidence": (
                "FORBIDDEN"
            ),
            "unknown_effect_model": (
                "NOT_SCHEDULABLE"
            ),
        },
        "primary_findings": [
            "CAUSAL_REPLAY_CAN_LOOK_WORSE_THAN_LEAKY_REPLAY_AND_STILL_BE_MORE_CORRECT",
            "FUTURE_EVIDENCE_CAN_CREATE_FALSE_FRONTIER_GAINS",
            "REGISTERED_PRIMITIVE_DOES_NOT_MEAN_SCHEDULABLE_PRIMITIVE",
            "MISSING_OR_STALE_EVIDENCE_MUST_BLOCK_MUTATING_ACTION_SELECTION",
            "SHADOW_COMPILATION_CAN_COMPOSE_MULTIPLE_PRIOR_RESEARCH_PRIMITIVES_WITHOUT_EXECUTING_THEM",
        ],
        "claim_ceiling": (
            "SYNTHETIC_CAUSAL_SHADOW_COMPILER_ONLY"
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
