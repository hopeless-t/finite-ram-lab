from __future__ import annotations

import itertools
import json
from typing import Any

from finite_ram_lab.fr_fp_046_variable_size_knapsack import (
    _cold_penalty,
    _mandatory_ids,
    _used_mib,
)
from finite_ram_lab.fr_fp_051_online_joint_variable_size import (
    PHASE_HORIZON_ROUNDS,
    run_panel as _fp051_panel,
)
from finite_ram_lab.fr_fp_053_current_run_migration_calibration import (
    _base_evict,
    _base_promote,
    _direction_scales,
    _load as _load_calibration,
)

SCHEMA = "finite-ram-lab.fr-fp-054-endogenous-resident-budget/v0.1"

MEMORY_RENT_MS_PER_MIB_ROUND = (
    0.0,
    0.025,
    0.05,
    0.075,
    0.10,
    0.125,
    0.15,
    0.175,
    0.20,
    0.25,
    0.30,
    0.40,
)


def _state_map(
    states: list[dict[str, Any]],
) -> dict[int, dict[str, Any]]:
    return {
        int(row["state_id"]): row
        for row in states
    }


def _migration_component(
    *,
    state_id: int,
    tier: str,
    current_warm: set[int] | None,
    by_id: dict[int, dict[str, Any]],
    promote_scale: float,
    evict_scale: float,
) -> float:
    if current_warm is None:
        return 0.0

    size_mib = float(
        by_id[
            state_id
        ][
            "state_mib"
        ]
    )

    if (
        tier == "WARM"
        and state_id
        not in current_warm
    ):
        return (
            promote_scale
            * _base_promote(
                size_mib
            )
        )

    if (
        tier == "COLD"
        and state_id
        in current_warm
    ):
        return (
            evict_scale
            * _base_evict(
                size_mib
            )
        )

    return 0.0


def _candidate(
    states: list[dict[str, Any]],
    *,
    warm: set[int],
    current_warm: set[int] | None,
    budget_mib: int,
    memory_rent: float,
    promote_scale: float,
    evict_scale: float,
) -> dict[str, Any]:
    by_id = _state_map(
        states
    )
    used_mib = _used_mib(
        states,
        warm,
    )
    service_ms = (
        PHASE_HORIZON_ROUNDS
        * _cold_penalty(
            states,
            warm,
        )
    )
    migration_ms = sum(
        _migration_component(
            state_id=int(
                row[
                    "state_id"
                ]
            ),
            tier=(
                "WARM"
                if int(
                    row[
                        "state_id"
                    ]
                )
                in warm
                else "COLD"
            ),
            current_warm=(
                current_warm
            ),
            by_id=by_id,
            promote_scale=(
                promote_scale
            ),
            evict_scale=(
                evict_scale
            ),
        )
        for row in states
    )
    rent_ms = (
        PHASE_HORIZON_ROUNDS
        * memory_rent
        * used_mib
    )

    return {
        "warm_ids": sorted(
            warm
        ),
        "used_mib": used_mib,
        "unused_mib": (
            budget_mib
            - used_mib
        ),
        "service_ms": (
            service_ms
        ),
        "migration_ms": (
            migration_ms
        ),
        "resident_rent_ms": (
            rent_ms
        ),
        "total_ms": (
            service_ms
            + migration_ms
            + rent_ms
        ),
    }


def _exhaustive(
    states: list[dict[str, Any]],
    *,
    current_warm: set[int] | None,
    budget_mib: int,
    memory_rent: float,
    promote_scale: float,
    evict_scale: float,
) -> dict[str, Any]:
    mandatory = _mandatory_ids(
        states
    )
    ids = [
        int(row["state_id"])
        for row in states
    ]
    optional = [
        state_id
        for state_id in ids
        if state_id
        not in mandatory
    ]
    candidates = []

    for count in range(
        len(optional)
        + 1
    ):
        for subset in itertools.combinations(
            optional,
            count,
        ):
            warm = (
                mandatory
                | set(subset)
            )

            if (
                _used_mib(
                    states,
                    warm,
                )
                > budget_mib
            ):
                continue

            candidates.append(
                _candidate(
                    states,
                    warm=warm,
                    current_warm=(
                        current_warm
                    ),
                    budget_mib=(
                        budget_mib
                    ),
                    memory_rent=(
                        memory_rent
                    ),
                    promote_scale=(
                        promote_scale
                    ),
                    evict_scale=(
                        evict_scale
                    ),
                )
            )

    if not candidates:
        return {
            "feasible": False,
            "reason": (
                "MANDATORY_WARM_BYTES_EXCEED_BUDGET"
            ),
        }

    best = min(
        candidates,
        key=lambda row: (
            row[
                "total_ms"
            ],
            row[
                "used_mib"
            ],
            row[
                "warm_ids"
            ],
        ),
    )

    return {
        "feasible": True,
        **best,
        "candidate_count": (
            len(candidates)
        ),
    }


def _dp(
    states: list[dict[str, Any]],
    *,
    current_warm: set[int] | None,
    budget_mib: int,
    memory_rent: float,
    promote_scale: float,
    evict_scale: float,
) -> dict[str, Any]:
    mandatory = _mandatory_ids(
        states
    )
    mandatory_mib = (
        _used_mib(
            states,
            mandatory,
        )
    )

    if mandatory_mib > budget_mib:
        return {
            "feasible": False,
            "reason": (
                "MANDATORY_WARM_BYTES_EXCEED_BUDGET"
            ),
        }

    by_id = _state_map(
        states
    )

    dp: dict[
        int,
        tuple[
            float,
            tuple[int, ...],
        ],
    ] = {
        0: (
            0.0,
            (),
        )
    }

    for row in states:
        state_id = int(
            row[
                "state_id"
            ]
        )
        size_mib = int(
            row[
                "state_mib"
            ]
        )
        penalty = float(
            row[
                "expected_cold_penalty_ms"
            ]
        )

        choices = (
            ("WARM",)
            if state_id
            in mandatory
            else (
                "COLD",
                "WARM",
            )
        )
        next_dp: dict[
            int,
            tuple[
                float,
                tuple[int, ...],
            ],
        ] = {}

        for used, (
            cost,
            warm_ids,
        ) in dp.items():
            for tier in choices:
                if tier == "WARM":
                    new_used = (
                        used
                        + size_mib
                    )

                    if (
                        new_used
                        > budget_mib
                    ):
                        continue

                    component = (
                        PHASE_HORIZON_ROUNDS
                        * memory_rent
                        * size_mib
                        + _migration_component(
                            state_id=(
                                state_id
                            ),
                            tier="WARM",
                            current_warm=(
                                current_warm
                            ),
                            by_id=by_id,
                            promote_scale=(
                                promote_scale
                            ),
                            evict_scale=(
                                evict_scale
                            ),
                        )
                    )
                    new_warm = tuple(
                        sorted(
                            warm_ids
                            + (
                                state_id,
                            )
                        )
                    )

                else:
                    new_used = used
                    component = (
                        PHASE_HORIZON_ROUNDS
                        * penalty
                        + _migration_component(
                            state_id=(
                                state_id
                            ),
                            tier="COLD",
                            current_warm=(
                                current_warm
                            ),
                            by_id=by_id,
                            promote_scale=(
                                promote_scale
                            ),
                            evict_scale=(
                                evict_scale
                            ),
                        )
                    )
                    new_warm = (
                        warm_ids
                    )

                new_cost = (
                    cost
                    + component
                )
                incumbent = (
                    next_dp.get(
                        new_used
                    )
                )

                if (
                    incumbent
                    is None
                    or new_cost
                    < incumbent[0]
                    - 1e-12
                    or (
                        abs(
                            new_cost
                            - incumbent[0]
                        )
                        <= 1e-12
                        and new_warm
                        < incumbent[1]
                    )
                ):
                    next_dp[
                        new_used
                    ] = (
                        new_cost,
                        new_warm,
                    )

        dp = next_dp

    if not dp:
        return {
            "feasible": False,
            "reason": (
                "NO_FEASIBLE_PLACEMENT"
            ),
        }

    _used, (
        _cost,
        warm_ids,
    ) = min(
        dp.items(),
        key=lambda item: (
            item[1][0],
            item[0],
            item[1][1],
        ),
    )
    warm = set(
        warm_ids
    )

    return {
        "feasible": True,
        **_candidate(
            states,
            warm=warm,
            current_warm=(
                current_warm
            ),
            budget_mib=(
                budget_mib
            ),
            memory_rent=(
                memory_rent
            ),
            promote_scale=(
                promote_scale
            ),
            evict_scale=(
                evict_scale
            ),
        ),
        "dp_states": len(
            dp
        ),
    }


def run_panel() -> dict[str, Any]:
    parent = _fp051_panel()
    calibration = (
        _load_calibration()
    )
    scales = _direction_scales(
        calibration[
            "joint_pure_direction_calibration"
        ]
    )
    phase_inputs = parent[
        "phase_inputs"
    ]

    sweeps = []
    mismatches = []

    for memory_rent in (
        MEMORY_RENT_MS_PER_MIB_ROUND
    ):
        current: set[int] | None = (
            None
        )
        rows = []

        for phase in phase_inputs:
            dp = _dp(
                phase["states"],
                current_warm=current,
                budget_mib=int(
                    phase[
                        "budget_mib"
                    ]
                ),
                memory_rent=(
                    memory_rent
                ),
                promote_scale=(
                    scales[
                        "promote_scale"
                    ]
                ),
                evict_scale=(
                    scales[
                        "evict_scale"
                    ]
                ),
            )
            exact = _exhaustive(
                phase["states"],
                current_warm=current,
                budget_mib=int(
                    phase[
                        "budget_mib"
                    ]
                ),
                memory_rent=(
                    memory_rent
                ),
                promote_scale=(
                    scales[
                        "promote_scale"
                    ]
                ),
                evict_scale=(
                    scales[
                        "evict_scale"
                    ]
                ),
            )

            match = (
                dp[
                    "feasible"
                ]
                == exact[
                    "feasible"
                ]
                and dp.get(
                    "warm_ids"
                )
                == exact.get(
                    "warm_ids"
                )
                and abs(
                    float(
                        dp.get(
                            "total_ms",
                            0.0,
                        )
                    )
                    - float(
                        exact.get(
                            "total_ms",
                            0.0,
                        )
                    )
                )
                < 1e-9
            )

            if not match:
                mismatches.append(
                    {
                        "memory_rent": (
                            memory_rent
                        ),
                        "phase": (
                            phase[
                                "phase"
                            ]
                        ),
                        "dp": dp,
                        "exact": exact,
                    }
                )

            rows.append(
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
                    **dp,
                }
            )
            current = set(
                dp[
                    "warm_ids"
                ]
            )

        resident_integral = (
            PHASE_HORIZON_ROUNDS
            * sum(
                int(
                    row[
                        "used_mib"
                    ]
                )
                for row in rows
            )
        )

        sweeps.append(
            {
                "memory_rent_ms_per_mib_round": (
                    memory_rent
                ),
                "rows": rows,
                "resident_mib_round": (
                    resident_integral
                ),
                "service_ms": sum(
                    float(
                        row[
                            "service_ms"
                        ]
                    )
                    for row in rows
                ),
                "migration_ms": sum(
                    float(
                        row[
                            "migration_ms"
                        ]
                    )
                    for row in rows
                ),
                "resident_rent_ms": sum(
                    float(
                        row[
                            "resident_rent_ms"
                        ]
                    )
                    for row in rows
                ),
                "total_ms": sum(
                    float(
                        row[
                            "total_ms"
                        ]
                    )
                    for row in rows
                ),
                "phase_used_mib": [
                    int(
                        row[
                            "used_mib"
                        ]
                    )
                    for row in rows
                ],
                "phase_unused_mib": [
                    int(
                        row[
                            "unused_mib"
                        ]
                    )
                    for row in rows
                ],
            }
        )

    zero = sweeps[0]
    baseline_path = (
        _fp051_panel()
    )[
        "joint"
    ][
        "rows"
    ]
    zero_matches_parent = all(
        row[
            "warm_ids"
        ]
        == parent_row[
            "joint_warm_ids"
        ]
        for row, parent_row
        in zip(
            zero[
                "rows"
            ],
            baseline_path,
        )
    )

    aggregate_usage = [
        row[
            "resident_mib_round"
        ]
        for row in sweeps
    ]

    phase_usage = [
        row[
            "phase_used_mib"
        ]
        for row in sweeps
    ]

    checks = {
        "every_dp_result_matches_exhaustive": (
            not mismatches
        ),
        "zero_memory_rent_recovers_fp053_joint_path": (
            zero_matches_parent
        ),
        "aggregate_residency_is_nonincreasing_with_memory_rent": all(
            left
            >= right
            for left, right
            in zip(
                aggregate_usage[:-1],
                aggregate_usage[1:],
            )
        ),
        "each_phase_residency_is_nonincreasing_with_memory_rent": all(
            phase_usage[index][phase]
            >= phase_usage[
                index + 1
            ][phase]
            for index in range(
                len(
                    phase_usage
                )
                - 1
            )
            for phase in range(
                len(
                    phase_inputs
                )
            )
        ),
        "positive_memory_rent_can_leave_hard_capacity_unused": any(
            memory_rent_row[
                "memory_rent_ms_per_mib_round"
            ]
            > 0.0
            and any(
                value > 0
                for value in memory_rent_row[
                    "phase_unused_mib"
                ]
            )
            for memory_rent_row
            in sweeps
        ),
        "high_memory_rent_can_choose_zero_resident_bytes": (
            sweeps[-1][
                "resident_mib_round"
            ]
            == 0
        ),
        "current_run_direction_scales_are_reused": (
            scales[
                "promote_scale"
            ]
            > 0.0
            and scales[
                "evict_scale"
            ]
            > 0.0
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
            "ENDOGENOUS_RESIDENT_USAGE_UNDER_HARD_CAP_WITH_BYTE_TIME_RENT"
        ),
        "fixture": {
            "phase_horizon_rounds": (
                PHASE_HORIZON_ROUNDS
            ),
            "hard_capacity_schedule_mib": [
                int(
                    row[
                        "budget_mib"
                    ]
                )
                for row in phase_inputs
            ],
            "memory_rent_grid_ms_per_mib_round": list(
                MEMORY_RENT_MS_PER_MIB_ROUND
            ),
        },
        "current_run_migration_scales": (
            scales
        ),
        "sweeps": sweeps,
        "checks": checks,
        "decision": (
            "TREAT_WARM_CAPACITY_AS_A_HARD_MAXIMUM_AND_CHOOSE_ACTUAL_RESIDENT_BYTES_ENDOGENOUSLY_BY_PRICING_RESIDENT_BYTE_TIME"
        ),
        "north_star": (
            "minimize resident byte-time while retaining enough semantic value to justify its service and migration cost"
        ),
        "next": (
            "PHYSICALLY_ACTUATE_SELECTED_LOW_MEDIUM_HIGH_MEMORY_RENT_POINTS_AND_VERIFY_THAT_UNUSED_CAPACITY_IS_REAL_NOT_ONLY_SHADOW"
        ),
        "claim_ceiling": (
            "SYNTHETIC_RESIDENT_RENT_FRONTIER_ON_FP051_PHASES_WITH_FP053_CURRENT_RUN_MIGRATION_SCALES_ONLY"
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
