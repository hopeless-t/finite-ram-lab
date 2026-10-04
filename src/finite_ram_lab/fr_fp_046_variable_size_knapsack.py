from __future__ import annotations

import itertools
import json
from typing import Any

from finite_ram_lab.fr_fp_034_multistate_budget_allocation import (
    MISS_TOLERANCE,
    _state_rows as _equal_size_state_rows,
)

SCHEMA = "finite-ram-lab.fr-fp-046-variable-size-knapsack/v0.1"

STATE_SIZES_MIB = (
    4,
    6,
    8,
    10,
    12,
    14,
    16,
    8,
    8,
    12,
)

BUDGETS_MIB = (
    24,
    28,
    32,
    36,
    40,
    44,
    48,
    52,
    56,
    60,
    64,
    68,
    72,
    76,
    80,
    84,
    88,
    92,
    96,
    98,
)


def _states() -> list[dict[str, Any]]:
    base = _equal_size_state_rows()

    if len(base) != len(
        STATE_SIZES_MIB
    ):
        raise RuntimeError(
            "state_size_vector_mismatch"
        )

    rows = []

    for row, state_mib in zip(
        base,
        STATE_SIZES_MIB,
    ):
        copied = dict(row)
        copied[
            "state_mib"
        ] = int(
            state_mib
        )
        copied[
            "value_density_ms_per_mib"
        ] = (
            copied[
                "expected_cold_penalty_ms"
            ]
            / state_mib
        )
        rows.append(
            copied
        )

    return rows


def _mandatory_ids(
    states: list[dict[str, Any]],
) -> set[int]:
    return {
        row["state_id"]
        for row in states
        if row["mandatory_warm"]
    }


def _used_mib(
    states: list[dict[str, Any]],
    warm_ids: set[int],
) -> int:
    return sum(
        int(
            row[
                "state_mib"
            ]
        )
        for row in states
        if row[
            "state_id"
        ]
        in warm_ids
    )


def _cold_penalty(
    states: list[dict[str, Any]],
    warm_ids: set[int],
) -> float:
    return sum(
        float(
            row[
                "expected_cold_penalty_ms"
            ]
        )
        for row in states
        if row[
            "state_id"
        ]
        not in warm_ids
    )


def _max_cold_deadline_risk(
    states: list[dict[str, Any]],
    warm_ids: set[int],
) -> float:
    cold = [
        row
        for row in states
        if row[
            "state_id"
        ]
        not in warm_ids
    ]

    if not cold:
        return 0.0

    return max(
        float(
            row[
                "unconditional_deadline_risk"
            ]
        )
        for row in cold
    )


def _result(
    states: list[dict[str, Any]],
    *,
    warm_ids: set[int],
    budget_mib: int,
) -> dict[str, Any]:
    used = _used_mib(
        states,
        warm_ids,
    )

    return {
        "feasible": True,
        "budget_mib": (
            budget_mib
        ),
        "used_mib": used,
        "unused_mib": (
            budget_mib
            - used
        ),
        "warm_ids": sorted(
            warm_ids
        ),
        "cold_ids": sorted(
            row[
                "state_id"
            ]
            for row in states
            if row[
                "state_id"
            ]
            not in warm_ids
        ),
        "expected_cold_penalty_ms": (
            _cold_penalty(
                states,
                warm_ids,
            )
        ),
        "max_cold_deadline_risk": (
            _max_cold_deadline_risk(
                states,
                warm_ids,
            )
        ),
    }


def _infeasible(
    *,
    budget_mib: int,
    mandatory_mib: int,
) -> dict[str, Any]:
    return {
        "feasible": False,
        "reason": (
            "MANDATORY_WARM_BYTES_EXCEED_BUDGET"
        ),
        "budget_mib": (
            budget_mib
        ),
        "mandatory_mib": (
            mandatory_mib
        ),
    }


def _density_greedy(
    states: list[dict[str, Any]],
    *,
    budget_mib: int,
) -> dict[str, Any]:
    mandatory = _mandatory_ids(
        states
    )
    mandatory_mib = _used_mib(
        states,
        mandatory,
    )

    if mandatory_mib > budget_mib:
        return _infeasible(
            budget_mib=budget_mib,
            mandatory_mib=mandatory_mib,
        )

    optional = [
        row
        for row in states
        if row[
            "state_id"
        ]
        not in mandatory
    ]
    optional.sort(
        key=lambda row: (
            -float(
                row[
                    "value_density_ms_per_mib"
                ]
            ),
            row[
                "state_id"
            ],
        )
    )

    warm = set(
        mandatory
    )
    used = mandatory_mib

    for row in optional:
        size = int(
            row[
                "state_mib"
            ]
        )

        if (
            used
            + size
            <= budget_mib
        ):
            warm.add(
                int(
                    row[
                        "state_id"
                    ]
                )
            )
            used += size

    return _result(
        states,
        warm_ids=warm,
        budget_mib=budget_mib,
    )


def _exhaustive_allocate(
    states: list[dict[str, Any]],
    *,
    budget_mib: int,
) -> dict[str, Any]:
    mandatory = _mandatory_ids(
        states
    )
    mandatory_mib = _used_mib(
        states,
        mandatory,
    )

    if mandatory_mib > budget_mib:
        return _infeasible(
            budget_mib=budget_mib,
            mandatory_mib=mandatory_mib,
        )

    optional_ids = [
        row[
            "state_id"
        ]
        for row in states
        if row[
            "state_id"
        ]
        not in mandatory
    ]

    candidates = []

    for count in range(
        len(optional_ids)
        + 1
    ):
        for subset in itertools.combinations(
            optional_ids,
            count,
        ):
            warm = (
                mandatory
                | set(
                    subset
                )
            )
            used = _used_mib(
                states,
                warm,
            )

            if used > budget_mib:
                continue

            result = _result(
                states,
                warm_ids=warm,
                budget_mib=budget_mib,
            )
            candidates.append(
                result
            )

    if not candidates:
        return _infeasible(
            budget_mib=budget_mib,
            mandatory_mib=mandatory_mib,
        )

    best = min(
        candidates,
        key=lambda row: (
            row[
                "expected_cold_penalty_ms"
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
        **best,
        "candidate_count": (
            len(candidates)
        ),
    }


def _dp_allocate(
    states: list[dict[str, Any]],
    *,
    budget_mib: int,
) -> dict[str, Any]:
    mandatory = _mandatory_ids(
        states
    )
    mandatory_mib = _used_mib(
        states,
        mandatory,
    )

    if mandatory_mib > budget_mib:
        return _infeasible(
            budget_mib=budget_mib,
            mandatory_mib=mandatory_mib,
        )

    optional = [
        row
        for row in states
        if row[
            "state_id"
        ]
        not in mandatory
    ]
    remaining = (
        budget_mib
        - mandatory_mib
    )

    # used optional MiB -> (avoided penalty, tuple(ids))
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

    for row in optional:
        size = int(
            row[
                "state_mib"
            ]
        )
        value = float(
            row[
                "expected_cold_penalty_ms"
            ]
        )
        state_id = int(
            row[
                "state_id"
            ]
        )
        next_dp = dict(
            dp
        )

        for used, (
            avoided,
            ids,
        ) in dp.items():
            new_used = (
                used
                + size
            )

            if new_used > remaining:
                continue

            candidate = (
                avoided
                + value,
                tuple(
                    sorted(
                        ids
                        + (
                            state_id,
                        )
                    )
                ),
            )
            incumbent = (
                next_dp.get(
                    new_used
                )
            )

            if (
                incumbent
                is None
                or candidate[0]
                > incumbent[0]
                + 1e-12
                or (
                    abs(
                        candidate[0]
                        - incumbent[0]
                    )
                    <= 1e-12
                    and candidate[1]
                    < incumbent[1]
                )
            ):
                next_dp[
                    new_used
                ] = candidate

        dp = next_dp

    best_used, (
        _best_value,
        best_ids,
    ) = max(
        dp.items(),
        key=lambda item: (
            item[1][0],
            item[0],
            tuple(
                -value
                for value in (
                    item[1][1]
                )
            ),
        ),
    )

    warm = (
        mandatory
        | set(
            best_ids
        )
    )

    result = _result(
        states,
        warm_ids=warm,
        budget_mib=budget_mib,
    )

    return {
        **result,
        "dp_states": (
            len(dp)
        ),
        "optional_used_mib": (
            best_used
        ),
    }


def run_panel() -> dict[str, Any]:
    states = _states()
    mandatory = _mandatory_ids(
        states
    )
    mandatory_mib = _used_mib(
        states,
        mandatory,
    )
    frontier = {}
    greedy_failures = []
    exact_penalties = []

    for budget in BUDGETS_MIB:
        greedy = _density_greedy(
            states,
            budget_mib=budget,
        )
        exact = _exhaustive_allocate(
            states,
            budget_mib=budget,
        )
        dp = _dp_allocate(
            states,
            budget_mib=budget,
        )

        exact_match = (
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
                            "expected_cold_penalty_ms"
                        ]
                        - exact[
                            "expected_cold_penalty_ms"
                        ]
                    )
                    < 1e-12
                )
            )
        )
        greedy_match = (
            greedy[
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
                    greedy[
                        "warm_ids"
                    ]
                    == exact[
                        "warm_ids"
                    ]
                    and abs(
                        greedy[
                            "expected_cold_penalty_ms"
                        ]
                        - exact[
                            "expected_cold_penalty_ms"
                        ]
                    )
                    < 1e-12
                )
            )
        )

        row = {
            "budget_mib": (
                budget
            ),
            "greedy": greedy,
            "dp_exact": dp,
            "exhaustive": exact,
            "dp_matches_exhaustive": (
                exact_match
            ),
            "greedy_matches_exhaustive": (
                greedy_match
            ),
        }
        frontier[
            str(
                budget
            )
        ] = row

        if (
            exact[
                "feasible"
            ]
        ):
            exact_penalties.append(
                exact[
                    "expected_cold_penalty_ms"
                ]
            )

        if (
            exact[
                "feasible"
            ]
            and not greedy_match
        ):
            greedy_failures.append(
                {
                    "budget_mib": (
                        budget
                    ),
                    "greedy_warm_ids": (
                        greedy[
                            "warm_ids"
                        ]
                    ),
                    "exact_warm_ids": (
                        exact[
                            "warm_ids"
                        ]
                    ),
                    "greedy_used_mib": (
                        greedy[
                            "used_mib"
                        ]
                    ),
                    "exact_used_mib": (
                        exact[
                            "used_mib"
                        ]
                    ),
                    "greedy_expected_cold_penalty_ms": (
                        greedy[
                            "expected_cold_penalty_ms"
                        ]
                    ),
                    "exact_expected_cold_penalty_ms": (
                        exact[
                            "expected_cold_penalty_ms"
                        ]
                    ),
                    "penalty_gap_ms": (
                        greedy[
                            "expected_cold_penalty_ms"
                        ]
                        - exact[
                            "expected_cold_penalty_ms"
                        ]
                    ),
                }
            )

    feasible_exact = [
        row[
            "dp_exact"
        ]
        for row in (
            frontier.values()
        )
        if row[
            "dp_exact"
        ][
            "feasible"
        ]
    ]

    checks = {
        "ten_states_reuse_fp034_values": (
            len(states) == 10
        ),
        "state_sizes_are_heterogeneous": (
            len(
                set(
                    STATE_SIZES_MIB
                )
            )
            > 1
        ),
        "mandatory_ids_are_preserved_from_fp034": (
            mandatory
            == {
                7,
                8,
                9,
            }
        ),
        "mandatory_bytes_are_28mib": (
            mandatory_mib
            == 28
        ),
        "budget_below_mandatory_bytes_fails_closed": (
            not frontier[
                "24"
            ][
                "dp_exact"
            ][
                "feasible"
            ]
            and frontier[
                "24"
            ][
                "dp_exact"
            ][
                "reason"
            ]
            == "MANDATORY_WARM_BYTES_EXCEED_BUDGET"
        ),
        "dp_matches_exhaustive_for_every_budget": all(
            row[
                "dp_matches_exhaustive"
            ]
            for row in (
                frontier.values()
            )
        ),
        "all_exact_cold_states_respect_deadline_guard": all(
            row[
                "max_cold_deadline_risk"
            ]
            <= MISS_TOLERANCE
            + 1e-12
            for row in feasible_exact
        ),
        "exact_penalty_is_nonincreasing_with_more_budget": all(
            left
            >= right
            - 1e-12
            for left, right
            in zip(
                exact_penalties[:-1],
                exact_penalties[1:],
            )
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
            "VARIABLE_SIZE_MANDATORY_GUARDED_WARM_BUDGET_KNAPSACK"
        ),
        "source": {
            "semantic_values": (
                "FR-FP-034 frozen state values and deadline guards"
            ),
            "new_physical_runs": 0,
        },
        "fixture": {
            "state_sizes_mib": list(
                STATE_SIZES_MIB
            ),
            "budgets_mib": list(
                BUDGETS_MIB
            ),
            "mandatory_warm_ids": sorted(
                mandatory
            ),
            "mandatory_warm_mib": (
                mandatory_mib
            ),
        },
        "states": states,
        "frontier": frontier,
        "greedy_failure_count": (
            len(
                greedy_failures
            )
        ),
        "greedy_failures": (
            greedy_failures
        ),
        "checks": checks,
        "decision": (
            "REPLACE_EQUAL_SIZE_DENSITY_FILL_WITH_EXACT_BYTE_BUDGET_KNAPSACK_WHEN_STATE_SIZES_DIFFER"
        ),
        "theory_update": [
            "equal-size value-density ordering is not a generally exact variable-size allocator",
            "deadline-mandatory WARM bytes must be reserved before optimization",
            "the allocator must fail closed when mandatory bytes exceed capacity",
            "resident capacity is now a byte budget rather than a slot count",
        ],
        "next": (
            "PHYSICALLY_ACTUATE_VARIABLE_SIZE_FILES_UNDER_THE_EXACT_BYTE_BUDGET_AND_CALIBRATE_MIGRATION_COST_PER_BYTE"
        ),
        "claim_ceiling": (
            "SYNTHETIC_VARIABLE_SIZE_ALLOCATION_USING_FP034_VALUES_AND_ONE_FROZEN_SIZE_VECTOR_ONLY"
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
