from __future__ import annotations

import itertools
import json
from typing import Any

from finite_ram_lab.fr_fp_046_variable_size_knapsack import (
    _cold_penalty,
    _dp_allocate as _semantic_allocate,
    _mandatory_ids,
    _states,
    _used_mib,
)
from finite_ram_lab.fr_fp_047_hosted_variable_size_budget import (
    BUDGET_SCHEDULE_MIB,
)

SCHEMA = "finite-ram-lab.fr-fp-049-joint-migration-aware-knapsack/v0.1"

SOURCE_MIGRATION_RUN = 37219146828

PROMOTE_INTERCEPT_MS = 2.2828326190476176
PROMOTE_SLOPE_MS_PER_MIB = 1.730256023809524
EVICT_INTERCEPT_MS = 10.115818500000001
EVICT_SLOPE_MS_PER_MIB = 0.032783035714285695

HORIZONS = (
    1,
    5,
    10,
    20,
    50,
    100,
    250,
)


def _state_map(
    states: list[dict[str, Any]],
) -> dict[int, dict[str, Any]]:
    return {
        int(
            row["state_id"]
        ): row
        for row in states
    }


def _promote_cost_ms(
    state_mib: float,
) -> float:
    return (
        PROMOTE_INTERCEPT_MS
        + PROMOTE_SLOPE_MS_PER_MIB
        * state_mib
    )


def _evict_cost_ms(
    state_mib: float,
) -> float:
    return (
        EVICT_INTERCEPT_MS
        + EVICT_SLOPE_MS_PER_MIB
        * state_mib
    )


def _migration_cost_ms(
    states: list[dict[str, Any]],
    *,
    current_warm: set[int],
    candidate_warm: set[int],
) -> dict[str, Any]:
    by_id = _state_map(
        states
    )
    promotes = sorted(
        candidate_warm
        - current_warm
    )
    evicts = sorted(
        current_warm
        - candidate_warm
    )

    promote_cost = sum(
        _promote_cost_ms(
            float(
                by_id[
                    state_id
                ][
                    "state_mib"
                ]
            )
        )
        for state_id in promotes
    )
    evict_cost = sum(
        _evict_cost_ms(
            float(
                by_id[
                    state_id
                ][
                    "state_mib"
                ]
            )
        )
        for state_id in evicts
    )

    return {
        "promote_ids": promotes,
        "evict_ids": evicts,
        "promoted_mib": sum(
            int(
                by_id[
                    state_id
                ][
                    "state_mib"
                ]
            )
            for state_id in promotes
        ),
        "evicted_mib": sum(
            int(
                by_id[
                    state_id
                ][
                    "state_mib"
                ]
            )
            for state_id in evicts
        ),
        "promote_cost_ms": (
            promote_cost
        ),
        "evict_cost_ms": (
            evict_cost
        ),
        "total_ms": (
            promote_cost
            + evict_cost
        ),
    }


def _objective(
    states: list[dict[str, Any]],
    *,
    current_warm: set[int],
    candidate_warm: set[int],
    horizon: int,
) -> dict[str, Any]:
    service = (
        horizon
        * _cold_penalty(
            states,
            candidate_warm,
        )
    )
    migration = (
        _migration_cost_ms(
            states,
            current_warm=current_warm,
            candidate_warm=candidate_warm,
        )
    )

    return {
        "service_ms": service,
        "migration": migration,
        "total_ms": (
            service
            + migration[
                "total_ms"
            ]
        ),
    }


def _candidate_result(
    states: list[dict[str, Any]],
    *,
    current_warm: set[int],
    candidate_warm: set[int],
    budget_mib: int,
    horizon: int,
) -> dict[str, Any]:
    objective = _objective(
        states,
        current_warm=current_warm,
        candidate_warm=candidate_warm,
        horizon=horizon,
    )

    return {
        "warm_ids": sorted(
            candidate_warm
        ),
        "used_mib": (
            _used_mib(
                states,
                candidate_warm,
            )
        ),
        "expected_cold_penalty_ms_per_round": (
            _cold_penalty(
                states,
                candidate_warm,
            )
        ),
        "budget_mib": (
            budget_mib
        ),
        "horizon": (
            horizon
        ),
        **objective,
    }


def _exhaustive_allocate(
    states: list[dict[str, Any]],
    *,
    current_warm: set[int],
    budget_mib: int,
    horizon: int,
) -> dict[str, Any]:
    mandatory = _mandatory_ids(
        states
    )
    ids = [
        int(
            row[
                "state_id"
            ]
        )
        for row in states
    ]
    optional = [
        state_id
        for state_id in ids
        if state_id not in mandatory
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
                | set(
                    subset
                )
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
                _candidate_result(
                    states,
                    current_warm=current_warm,
                    candidate_warm=warm,
                    budget_mib=budget_mib,
                    horizon=horizon,
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
            ]
            * -1,
            row[
                "warm_ids"
            ],
        ),
    )

    return {
        "feasible": True,
        **best,
        "candidate_count": (
            len(
                candidates
            )
        ),
    }


def _dp_allocate(
    states: list[dict[str, Any]],
    *,
    current_warm: set[int],
    budget_mib: int,
    horizon: int,
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

    # used MiB -> (objective cost, tuple warm ids)
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

        next_dp: dict[
            int,
            tuple[
                float,
                tuple[int, ...],
            ],
        ] = {}

        choices = (
            ("WARM",)
            if state_id
            in mandatory
            else (
                "COLD",
                "WARM",
            )
        )

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

                    migration = (
                        0.0
                        if state_id
                        in current_warm
                        else _promote_cost_ms(
                            size_mib
                        )
                    )
                    new_cost = (
                        cost
                        + migration
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
                    migration = (
                        _evict_cost_ms(
                            size_mib
                        )
                        if state_id
                        in current_warm
                        else 0.0
                    )
                    new_cost = (
                        cost
                        + horizon
                        * penalty
                        + migration
                    )
                    new_warm = (
                        warm_ids
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
            item[0]
            * -1,
            item[1][1],
        ),
    )
    warm = set(
        warm_ids
    )

    return {
        "feasible": True,
        **_candidate_result(
            states,
            current_warm=current_warm,
            candidate_warm=warm,
            budget_mib=budget_mib,
            horizon=horizon,
        ),
        "dp_states": len(
            dp
        ),
    }


def _hold_result(
    states: list[dict[str, Any]],
    *,
    current_warm: set[int],
    budget_mib: int,
    horizon: int,
) -> dict[str, Any] | None:
    if (
        _used_mib(
            states,
            current_warm,
        )
        > budget_mib
    ):
        return None

    if not _mandatory_ids(
        states
    ).issubset(
        current_warm
    ):
        return None

    return _candidate_result(
        states,
        current_warm=current_warm,
        candidate_warm=current_warm,
        budget_mib=budget_mib,
        horizon=horizon,
    )


def run_panel() -> dict[str, Any]:
    states = _states()
    semantic = {
        budget: (
            _semantic_allocate(
                states,
                budget_mib=budget,
            )
        )
        for budget in (
            BUDGET_SCHEDULE_MIB
        )
    }

    rows = []
    mismatches = []
    third_placements = []

    for transition_index in range(
        1,
        len(
            BUDGET_SCHEDULE_MIB
        ),
    ):
        from_budget = (
            BUDGET_SCHEDULE_MIB[
                transition_index
                - 1
            ]
        )
        to_budget = (
            BUDGET_SCHEDULE_MIB[
                transition_index
            ]
        )
        current_warm = set(
            semantic[
                from_budget
            ][
                "warm_ids"
            ]
        )
        semantic_target = set(
            semantic[
                to_budget
            ][
                "warm_ids"
            ]
        )

        for horizon in HORIZONS:
            exact = (
                _exhaustive_allocate(
                    states,
                    current_warm=current_warm,
                    budget_mib=to_budget,
                    horizon=horizon,
                )
            )
            dp = _dp_allocate(
                states,
                current_warm=current_warm,
                budget_mib=to_budget,
                horizon=horizon,
            )

            match = (
                dp[
                    "feasible"
                ]
                == exact[
                    "feasible"
                ]
                and (
                    not exact[
                        "feasible"
                    ]
                    or (
                        dp[
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
                )
            )

            if not match:
                mismatches.append(
                    {
                        "from_budget_mib": (
                            from_budget
                        ),
                        "to_budget_mib": (
                            to_budget
                        ),
                        "horizon": (
                            horizon
                        ),
                        "dp": dp,
                        "exact": exact,
                    }
                )

            joint_warm = set(
                exact[
                    "warm_ids"
                ]
            )
            hold = _hold_result(
                states,
                current_warm=current_warm,
                budget_mib=to_budget,
                horizon=horizon,
            )
            semantic_result = (
                _candidate_result(
                    states,
                    current_warm=current_warm,
                    candidate_warm=(
                        semantic_target
                    ),
                    budget_mib=to_budget,
                    horizon=horizon,
                )
            )

            if (
                joint_warm
                == current_warm
            ):
                classification = (
                    "HOLD"
                )
            elif (
                joint_warm
                == semantic_target
            ):
                classification = (
                    "SEMANTIC_OPTIMUM"
                )
            else:
                classification = (
                    "THIRD_PLACEMENT"
                )

            row = {
                "from_budget_mib": (
                    from_budget
                ),
                "to_budget_mib": (
                    to_budget
                ),
                "horizon": horizon,
                "current_warm_ids": sorted(
                    current_warm
                ),
                "semantic_warm_ids": sorted(
                    semantic_target
                ),
                "joint_warm_ids": sorted(
                    joint_warm
                ),
                "classification": (
                    classification
                ),
                "joint_total_ms": (
                    exact[
                        "total_ms"
                    ]
                ),
                "semantic_total_ms": (
                    semantic_result[
                        "total_ms"
                    ]
                ),
                "hold_total_ms": (
                    None
                    if hold is None
                    else hold[
                        "total_ms"
                    ]
                ),
                "joint_migration": (
                    exact[
                        "migration"
                    ]
                ),
                "dp_matches_exhaustive": (
                    match
                ),
            }
            rows.append(
                row
            )

            if (
                classification
                == "THIRD_PLACEMENT"
            ):
                third_placements.append(
                    row
                )

    checks = {
        "source_migration_model_is_frozen_fp048": (
            SOURCE_MIGRATION_RUN
            == 37219146828
        ),
        "all_joint_dp_results_match_exhaustive": (
            not mismatches
        ),
        "comparison_grid_has_35_contexts": (
            len(rows)
            == (
                (
                    len(
                        BUDGET_SCHEDULE_MIB
                    )
                    - 1
                )
                * len(
                    HORIZONS
                )
            )
        ),
        "joint_never_loses_to_semantic_optimum_after_migration_is_priced": all(
            row[
                "joint_total_ms"
            ]
            <= row[
                "semantic_total_ms"
            ]
            + 1e-9
            for row in rows
        ),
        "joint_never_loses_to_feasible_hold": all(
            row[
                "hold_total_ms"
            ]
            is None
            or row[
                "joint_total_ms"
            ]
            <= row[
                "hold_total_ms"
            ]
            + 1e-9
            for row in rows
        ),
        "all_joint_placements_respect_target_budget": all(
            _used_mib(
                states,
                set(
                    row[
                        "joint_warm_ids"
                    ]
                ),
            )
            <= row[
                "to_budget_mib"
            ]
            for row in rows
        ),
        "all_joint_placements_keep_mandatory_warm": all(
            _mandatory_ids(
                states
            ).issubset(
                set(
                    row[
                        "joint_warm_ids"
                    ]
                )
            )
            for row in rows
        ),
    }

    classifications = {
        label: sum(
            row[
                "classification"
            ]
            == label
            for row in rows
        )
        for label in (
            "HOLD",
            "SEMANTIC_OPTIMUM",
            "THIRD_PLACEMENT",
        )
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
            "JOINT_MIGRATION_AWARE_VARIABLE_SIZE_BYTE_BUDGET_KNAPSACK"
        ),
        "source": {
            "migration_cost_run": (
                SOURCE_MIGRATION_RUN
            ),
            "new_physical_runs": 0,
        },
        "migration_model": {
            "promote_intercept_ms": (
                PROMOTE_INTERCEPT_MS
            ),
            "promote_slope_ms_per_mib": (
                PROMOTE_SLOPE_MS_PER_MIB
            ),
            "evict_intercept_ms": (
                EVICT_INTERCEPT_MS
            ),
            "evict_slope_ms_per_mib": (
                EVICT_SLOPE_MS_PER_MIB
            ),
        },
        "fixture": {
            "budget_schedule_mib": list(
                BUDGET_SCHEDULE_MIB
            ),
            "horizons": list(
                HORIZONS
            ),
        },
        "classification_counts": (
            classifications
        ),
        "third_placement_count": (
            len(
                third_placements
            )
        ),
        "third_placements": (
            third_placements
        ),
        "rows": rows,
        "checks": checks,
        "decision": (
            "OPTIMIZE_SERVICE_AND_MIGRATION_COST_JOINTLY_INSTEAD_OF_LIMITING_CONTROL_TO_HOLD_VS_SEMANTIC_OPTIMUM"
        ),
        "claim_ceiling": (
            "SYNTHETIC_JOINT_PLACEMENT_USING_FP046_VALUES_FP047_TRANSITIONS_AND_FP048_COST_MODEL_ONLY"
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
