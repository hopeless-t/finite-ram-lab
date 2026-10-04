from __future__ import annotations

import json
from typing import Any

from finite_ram_lab.fr_fp_038_online_multistate_value import (
    OBSERVATIONS_PER_PHASE,
    PHASE_REUSE_INCREMENTS,
    _shared_restore_model,
    _state_rows as _equal_size_state_rows,
)
from finite_ram_lab.fr_fp_046_variable_size_knapsack import (
    STATE_SIZES_MIB,
    _cold_penalty,
    _dp_allocate as _semantic_allocate,
    _used_mib,
)
from finite_ram_lab.fr_fp_049_joint_migration_aware_knapsack import (
    _candidate_result,
    _dp_allocate as _joint_allocate,
    _exhaustive_allocate as _joint_exhaustive,
    _migration_cost_ms,
)

SCHEMA = "finite-ram-lab.fr-fp-051-online-joint-variable-size/v0.1"

CAPACITY_SCHEDULE_MIB = (
    40,
    28,
    72,
    44,
    56,
)
PHASE_HORIZON_ROUNDS = (
    OBSERVATIONS_PER_PHASE
)


def _variable_size_states(
    *,
    observations: int,
    reuse_counts: list[int],
    model: dict[str, Any],
) -> list[dict[str, Any]]:
    base = _equal_size_state_rows(
        observations=observations,
        reuse_counts=reuse_counts,
        model=model,
    )

    rows = []

    for row, size_mib in zip(
        base,
        STATE_SIZES_MIB,
    ):
        copied = dict(row)
        copied[
            "state_mib"
        ] = int(
            size_mib
        )
        copied[
            "value_density_ms_per_mib"
        ] = (
            copied[
                "expected_cold_penalty_ms"
            ]
            / size_mib
        )
        rows.append(
            copied
        )

    return rows


def _semantic_result(
    states: list[dict[str, Any]],
    *,
    budget_mib: int,
) -> dict[str, Any]:
    result = _semantic_allocate(
        states,
        budget_mib=budget_mib,
    )

    if not result[
        "feasible"
    ]:
        raise RuntimeError(
            f"unexpected_semantic_infeasible:{budget_mib}"
        )

    return result


def _migration_blind_total(
    phases: list[dict[str, Any]],
) -> dict[str, Any]:
    current: set[int] | None = None
    rows = []
    total_service = 0.0
    total_migration = 0.0

    for phase in phases:
        target = set(
            phase[
                "semantic"
            ][
                "warm_ids"
            ]
        )
        service = (
            PHASE_HORIZON_ROUNDS
            * _cold_penalty(
                phase[
                    "states"
                ],
                target,
            )
        )

        if current is None:
            migration = {
                "total_ms": 0.0,
                "promote_ids": [],
                "evict_ids": [],
                "promoted_mib": 0,
                "evicted_mib": 0,
            }
        else:
            migration = (
                _migration_cost_ms(
                    phase[
                        "states"
                    ],
                    current_warm=current,
                    candidate_warm=target,
                )
            )

        rows.append(
            {
                "phase": (
                    phase[
                        "phase"
                    ]
                ),
                "warm_ids": sorted(
                    target
                ),
                "service_ms": (
                    service
                ),
                "migration_ms": (
                    migration[
                        "total_ms"
                    ]
                ),
                "total_ms": (
                    service
                    + migration[
                        "total_ms"
                    ]
                ),
            }
        )
        total_service += service
        total_migration += (
            migration[
                "total_ms"
            ]
        )
        current = target

    return {
        "rows": rows,
        "service_ms": total_service,
        "migration_ms": total_migration,
        "total_ms": (
            total_service
            + total_migration
        ),
    }


def run_panel() -> dict[str, Any]:
    model = _shared_restore_model()
    cumulative_counts = [
        0
        for _ in range(
            len(
                STATE_SIZES_MIB
            )
        )
    ]
    observations = 0
    phase_inputs = []

    for phase_index, (
        increments,
        budget_mib,
    ) in enumerate(
        zip(
            PHASE_REUSE_INCREMENTS,
            CAPACITY_SCHEDULE_MIB,
        ),
        start=1,
    ):
        observations += (
            OBSERVATIONS_PER_PHASE
        )
        cumulative_counts = [
            old + delta
            for old, delta
            in zip(
                cumulative_counts,
                increments,
            )
        ]
        states = (
            _variable_size_states(
                observations=observations,
                reuse_counts=(
                    cumulative_counts
                ),
                model=model,
            )
        )
        semantic = (
            _semantic_result(
                states,
                budget_mib=(
                    budget_mib
                ),
            )
        )

        phase_inputs.append(
            {
                "phase": phase_index,
                "budget_mib": (
                    budget_mib
                ),
                "observations": (
                    observations
                ),
                "reuse_counts": list(
                    cumulative_counts
                ),
                "states": states,
                "semantic": (
                    semantic
                ),
            }
        )

    migration_blind = (
        _migration_blind_total(
            phase_inputs
        )
    )

    first = phase_inputs[0]
    current = set(
        first[
            "semantic"
        ][
            "warm_ids"
        ]
    )
    first_service = (
        PHASE_HORIZON_ROUNDS
        * _cold_penalty(
            first[
                "states"
            ],
            current,
        )
    )

    joint_rows = [
        {
            "phase": 1,
            "budget_mib": (
                first[
                    "budget_mib"
                ]
            ),
            "classification": (
                "INITIAL_SEMANTIC"
            ),
            "current_warm_ids": (
                None
            ),
            "semantic_warm_ids": sorted(
                current
            ),
            "joint_warm_ids": sorted(
                current
            ),
            "used_mib": (
                _used_mib(
                    first[
                        "states"
                    ],
                    current,
                )
            ),
            "service_ms": (
                first_service
            ),
            "migration_ms": 0.0,
            "total_ms": (
                first_service
            ),
            "dp_matches_exhaustive": (
                True
            ),
        }
    ]

    total_service = first_service
    total_migration = 0.0
    mismatches = []

    for phase in phase_inputs[
        1:
    ]:
        semantic_target = set(
            phase[
                "semantic"
            ][
                "warm_ids"
            ]
        )
        dp = _joint_allocate(
            phase[
                "states"
            ],
            current_warm=current,
            budget_mib=(
                phase[
                    "budget_mib"
                ]
            ),
            horizon=(
                PHASE_HORIZON_ROUNDS
            ),
        )
        exact = _joint_exhaustive(
            phase[
                "states"
            ],
            current_warm=current,
            budget_mib=(
                phase[
                    "budget_mib"
                ]
            ),
            horizon=(
                PHASE_HORIZON_ROUNDS
            ),
        )

        match = (
            dp[
                "feasible"
            ]
            == exact[
                "feasible"
            ]
            and dp[
                "warm_ids"
            ]
            == exact[
                "warm_ids"
            ]
            and abs(
                dp[
                    "total_ms"
                ]
                - exact[
                    "total_ms"
                ]
            )
            < 1e-9
        )

        if not match:
            mismatches.append(
                {
                    "phase": (
                        phase[
                            "phase"
                        ]
                    ),
                    "dp": dp,
                    "exact": exact,
                }
            )

        joint = set(
            exact[
                "warm_ids"
            ]
        )

        if joint == current:
            classification = (
                "HOLD"
            )
        elif joint == semantic_target:
            classification = (
                "SEMANTIC_OPTIMUM"
            )
        else:
            classification = (
                "THIRD_PLACEMENT"
            )

        service = (
            PHASE_HORIZON_ROUNDS
            * _cold_penalty(
                phase[
                    "states"
                ],
                joint,
            )
        )
        migration = (
            _migration_cost_ms(
                phase[
                    "states"
                ],
                current_warm=current,
                candidate_warm=joint,
            )
        )
        semantic_from_joint = (
            _candidate_result(
                phase[
                    "states"
                ],
                current_warm=current,
                candidate_warm=(
                    semantic_target
                ),
                budget_mib=(
                    phase[
                        "budget_mib"
                    ]
                ),
                horizon=(
                    PHASE_HORIZON_ROUNDS
                ),
            )
        )

        joint_rows.append(
            {
                "phase": (
                    phase[
                        "phase"
                    ]
                ),
                "budget_mib": (
                    phase[
                        "budget_mib"
                    ]
                ),
                "classification": (
                    classification
                ),
                "current_warm_ids": sorted(
                    current
                ),
                "semantic_warm_ids": sorted(
                    semantic_target
                ),
                "joint_warm_ids": sorted(
                    joint
                ),
                "used_mib": (
                    _used_mib(
                        phase[
                            "states"
                        ],
                        joint,
                    )
                ),
                "service_ms": (
                    service
                ),
                "migration_ms": (
                    migration[
                        "total_ms"
                    ]
                ),
                "total_ms": (
                    service
                    + migration[
                        "total_ms"
                    ]
                ),
                "semantic_from_joint_total_ms": (
                    semantic_from_joint[
                        "total_ms"
                    ]
                ),
                "dp_matches_exhaustive": (
                    match
                ),
            }
        )

        total_service += service
        total_migration += (
            migration[
                "total_ms"
            ]
        )
        current = joint

    joint_total = (
        total_service
        + total_migration
    )
    classifications = {
        label: sum(
            row[
                "classification"
            ]
            == label
            for row in joint_rows[
                1:
            ]
        )
        for label in (
            "HOLD",
            "SEMANTIC_OPTIMUM",
            "THIRD_PLACEMENT",
        )
    }

    checks = {
        "five_online_phases": (
            len(
                phase_inputs
            )
            == 5
        ),
        "all_joint_dp_results_match_exhaustive": (
            not mismatches
        ),
        "joint_path_respects_each_byte_budget": all(
            row[
                "used_mib"
            ]
            <= row[
                "budget_mib"
            ]
            for row in (
                joint_rows
            )
        ),
        "at_least_one_online_third_placement": (
            classifications[
                "THIRD_PLACEMENT"
            ]
            > 0
        ),
        "joint_total_beats_migration_blind_semantic_tracking": (
            joint_total
            < migration_blind[
                "total_ms"
            ]
        ),
        "every_joint_step_beats_semantic_target_from_same_current_state": all(
            row[
                "classification"
            ]
            == "INITIAL_SEMANTIC"
            or row[
                "total_ms"
            ]
            <= row[
                "semantic_from_joint_total_ms"
            ]
            + 1e-9
            for row in joint_rows
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
        "classification": (
            "ONLINE_DYNAMIC_CAPACITY_VARIABLE_SIZE_JOINT_MIGRATION_AWARE_PLACEMENT"
        ),
        "fixture": {
            "state_sizes_mib": list(
                STATE_SIZES_MIB
            ),
            "capacity_schedule_mib": list(
                CAPACITY_SCHEDULE_MIB
            ),
            "phase_horizon_rounds": (
                PHASE_HORIZON_ROUNDS
            ),
            "phase_count": (
                len(
                    phase_inputs
                )
            ),
        },
        "phase_inputs": (
            phase_inputs
        ),
        "joint": {
            "rows": joint_rows,
            "service_ms": (
                total_service
            ),
            "migration_ms": (
                total_migration
            ),
            "total_ms": (
                joint_total
            ),
            "classification_counts": (
                classifications
            ),
        },
        "migration_blind_semantic": (
            migration_blind
        ),
        "checks": checks,
        "decision": (
            "REOPTIMIZE_ONLINE_STATE_PLACEMENT_DIRECTLY_IN_SERVICE_PLUS_MIGRATION_COST_SPACE"
        ),
        "meta_transfer": (
            "semantic-value updates and capacity changes feed one joint admissible-placement optimizer; no separate hysteresis gate over a migration-blind optimum is required"
        ),
        "next": (
            "PHYSICALLY_ACTUATE_THE_FIVE_PHASE_JOINT_PATH_AND_COMPARE_WITH_MIGRATION_BLIND_SEMANTIC_TRACKING"
        ),
        "claim_ceiling": (
            "SYNTHETIC_FIVE_PHASE_VARIABLE_SIZE_DYNAMIC_CAPACITY_JOINT_OPTIMIZATION_USING_REUSED_HOSTED_COST_EVIDENCE_ONLY"
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
