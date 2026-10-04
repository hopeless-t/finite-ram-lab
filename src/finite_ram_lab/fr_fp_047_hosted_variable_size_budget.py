from __future__ import annotations

import json
import tempfile
import time
from pathlib import Path
from typing import Any

from finite_ram_lab.fr_fp_016_restore_size_scaling import (
    _fadvise_dontneed,
    _file_residency,
    _prepare_tier,
    _size_bytes,
)
from finite_ram_lab.fr_fp_030_hosted_reuse_lifecycle import (
    _enforce_tier,
)
from finite_ram_lab.fr_fp_046_variable_size_knapsack import (
    STATE_SIZES_MIB,
    _dp_allocate,
    _states,
)

SCHEMA = "finite-ram-lab.fr-fp-047-hosted-variable-size-budget/v0.1"

BUDGET_SCHEDULE_MIB = (
    28,
    40,
    56,
    72,
    92,
    44,
)
INFEASIBLE_BUDGET_MIB = 24
STATE_COUNT = len(STATE_SIZES_MIB)


def _snapshot(
    paths: dict[int, Path],
    *,
    sizes_mib: dict[int, int],
    target_warm: set[int],
) -> dict[str, Any]:
    rows = []

    for state_id, path in sorted(
        paths.items()
    ):
        fraction = _file_residency(
            path
        )["resident_fraction"]
        size_mib = sizes_mib[
            state_id
        ]

        rows.append(
            {
                "state_id": state_id,
                "state_mib": size_mib,
                "resident_fraction": fraction,
                "resident_mib": (
                    fraction
                    * size_mib
                ),
                "target_tier": (
                    "WARM"
                    if state_id
                    in target_warm
                    else "COLD"
                ),
            }
        )

    warm_rows = [
        row
        for row in rows
        if row["state_id"]
        in target_warm
    ]
    cold_rows = [
        row
        for row in rows
        if row["state_id"]
        not in target_warm
    ]

    return {
        "resident_mib": sum(
            row[
                "resident_mib"
            ]
            for row in rows
        ),
        "target_warm_mib": sum(
            sizes_mib[
                state_id
            ]
            for state_id
            in target_warm
        ),
        "warm_min_residency": (
            min(
                row[
                    "resident_fraction"
                ]
                for row in warm_rows
            )
            if warm_rows
            else None
        ),
        "cold_max_residency": (
            max(
                row[
                    "resident_fraction"
                ]
                for row in cold_rows
            )
            if cold_rows
            else None
        ),
        "rows": rows,
    }


def _allocation(
    states: list[dict[str, Any]],
    budget_mib: int,
) -> dict[str, Any]:
    result = _dp_allocate(
        states,
        budget_mib=budget_mib,
    )

    if not result[
        "feasible"
    ]:
        raise RuntimeError(
            f"unexpected_infeasible_budget:{budget_mib}"
        )

    return result


def run_panel() -> dict[str, Any]:
    states = _states()
    sizes_mib = {
        int(row["state_id"]): int(
            row["state_mib"]
        )
        for row in states
    }
    allocations = [
        _allocation(
            states,
            budget,
        )
        for budget in (
            BUDGET_SCHEDULE_MIB
        )
    ]
    targets = [
        set(
            row["warm_ids"]
        )
        for row in allocations
    ]

    with tempfile.TemporaryDirectory(
        prefix="fr-fp-047-"
    ) as tmp:
        root = Path(tmp)
        paths: dict[int, Path] = {}

        initial = targets[0]

        for state_id in range(
            STATE_COUNT
        ):
            path = root / (
                f"state-{state_id}.bin"
            )
            prepared = _prepare_tier(
                path,
                size_bytes=_size_bytes(
                    sizes_mib[
                        state_id
                    ]
                ),
                marker=(
                    190
                    + state_id
                ),
                cold=(
                    state_id
                    not in initial
                ),
            )

            if not prepared[
                "verified"
            ]:
                raise RuntimeError(
                    f"prepare_failed:{state_id}"
                )

            paths[
                state_id
            ] = path

        for state_id, path in (
            paths.items()
        ):
            _enforce_tier(
                path,
                tier=(
                    "WARM"
                    if state_id
                    in initial
                    else "COLD"
                ),
            )

        phase_rows = [
            {
                "phase": 1,
                "budget_mib": (
                    BUDGET_SCHEDULE_MIB[0]
                ),
                "allocation": (
                    allocations[0]
                ),
                "warm_ids": sorted(
                    initial
                ),
                "changed_ids": [],
                "snapshot": _snapshot(
                    paths,
                    sizes_mib=sizes_mib,
                    target_warm=initial,
                ),
            }
        ]

        transition_rows = []
        total_actuations = 0
        total_prefetch_bytes = 0
        previous = initial

        try:
            for phase_index in range(
                1,
                len(
                    BUDGET_SCHEDULE_MIB
                ),
            ):
                current = targets[
                    phase_index
                ]
                changed = sorted(
                    previous
                    ^ current
                )
                before = _snapshot(
                    paths,
                    sizes_mib=sizes_mib,
                    target_warm=previous,
                )
                actuations = []
                started = (
                    time.monotonic_ns()
                )

                for state_id in changed:
                    target_tier = (
                        "WARM"
                        if state_id
                        in current
                        else "COLD"
                    )
                    row = _enforce_tier(
                        paths[
                            state_id
                        ],
                        tier=target_tier,
                    )
                    total_prefetch_bytes += int(
                        row[
                            "prefetch_bytes"
                        ]
                    )
                    actuations.append(
                        {
                            "state_id": (
                                state_id
                            ),
                            "state_mib": (
                                sizes_mib[
                                    state_id
                                ]
                            ),
                            "target_tier": (
                                target_tier
                            ),
                            **row,
                        }
                    )

                elapsed_ns = (
                    time.monotonic_ns()
                    - started
                )
                total_actuations += len(
                    actuations
                )

                after = _snapshot(
                    paths,
                    sizes_mib=sizes_mib,
                    target_warm=current,
                )

                transition_rows.append(
                    {
                        "from_phase": (
                            phase_index
                        ),
                        "to_phase": (
                            phase_index
                            + 1
                        ),
                        "from_budget_mib": (
                            BUDGET_SCHEDULE_MIB[
                                phase_index
                                - 1
                            ]
                        ),
                        "to_budget_mib": (
                            BUDGET_SCHEDULE_MIB[
                                phase_index
                            ]
                        ),
                        "changed_ids": (
                            changed
                        ),
                        "actuation_count": (
                            len(
                                actuations
                            )
                        ),
                        "promoted_mib": sum(
                            sizes_mib[
                                state_id
                            ]
                            for state_id
                            in changed
                            if state_id
                            in current
                        ),
                        "evicted_mib": sum(
                            sizes_mib[
                                state_id
                            ]
                            for state_id
                            in changed
                            if state_id
                            not in current
                        ),
                        "actuation_ns": (
                            elapsed_ns
                        ),
                        "before": before,
                        "after": after,
                        "actuations": (
                            actuations
                        ),
                    }
                )

                phase_rows.append(
                    {
                        "phase": (
                            phase_index
                            + 1
                        ),
                        "budget_mib": (
                            BUDGET_SCHEDULE_MIB[
                                phase_index
                            ]
                        ),
                        "allocation": (
                            allocations[
                                phase_index
                            ]
                        ),
                        "warm_ids": sorted(
                            current
                        ),
                        "changed_ids": (
                            changed
                        ),
                        "snapshot": after,
                    }
                )
                previous = current

            infeasible = _dp_allocate(
                states,
                budget_mib=(
                    INFEASIBLE_BUDGET_MIB
                ),
            )
            before_infeasible = (
                _snapshot(
                    paths,
                    sizes_mib=sizes_mib,
                    target_warm=previous,
                )
            )
            infeasible_actuations = []

            if infeasible[
                "feasible"
            ]:
                raise RuntimeError(
                    "infeasible_budget_unexpectedly_feasible"
                )

            after_infeasible = (
                _snapshot(
                    paths,
                    sizes_mib=sizes_mib,
                    target_warm=previous,
                )
            )

        finally:
            for path in (
                paths.values()
            ):
                try:
                    _fadvise_dontneed(
                        path
                    )
                except Exception:
                    pass

                try:
                    path.unlink()
                except FileNotFoundError:
                    pass

    full_reenforcement_count = (
        (
            len(
                BUDGET_SCHEDULE_MIB
            )
            - 1
        )
        * STATE_COUNT
    )

    checks = {
        "ten_variable_size_states": (
            STATE_COUNT
            == 10
            and len(
                set(
                    STATE_SIZES_MIB
                )
            )
            > 1
        ),
        "all_physical_warm_sets_match_exact_knapsack": all(
            set(
                row[
                    "warm_ids"
                ]
            )
            == set(
                row[
                    "allocation"
                ][
                    "warm_ids"
                ]
            )
            for row in phase_rows
        ),
        "every_phase_hits_exact_allocated_resident_bytes": all(
            abs(
                row[
                    "snapshot"
                ][
                    "resident_mib"
                ]
                - row[
                    "allocation"
                ][
                    "used_mib"
                ]
            )
            <= 0.75
            for row in phase_rows
        ),
        "every_warm_state_is_physically_resident": all(
            row[
                "snapshot"
            ][
                "warm_min_residency"
            ]
            is not None
            and row[
                "snapshot"
            ][
                "warm_min_residency"
            ]
            >= 0.95
            for row in phase_rows
        ),
        "every_cold_state_is_physically_nonresident": all(
            row[
                "snapshot"
            ][
                "cold_max_residency"
            ]
            is None
            or row[
                "snapshot"
            ][
                "cold_max_residency"
            ]
            <= 0.10
            for row in phase_rows
        ),
        "every_transition_actuates_only_changed_ids": all(
            row[
                "actuation_count"
            ]
            == len(
                row[
                    "changed_ids"
                ]
            )
            for row in (
                transition_rows
            )
        ),
        "minimal_delta_beats_full_reenforcement": (
            total_actuations
            < full_reenforcement_count
        ),
        "variable_size_actions_are_exercised": (
            len(
                {
                    action[
                        "state_mib"
                    ]
                    for row in (
                        transition_rows
                    )
                    for action in row[
                        "actuations"
                    ]
                }
            )
            >= 3
        ),
        "infeasible_budget_executes_zero_actions": (
            not infeasible[
                "feasible"
            ]
            and len(
                infeasible_actuations
            )
            == 0
        ),
        "infeasible_reason_is_mandatory_bytes": (
            infeasible[
                "reason"
            ]
            == "MANDATORY_WARM_BYTES_EXCEED_BUDGET"
        ),
        "infeasible_budget_preserves_physical_snapshot": (
            before_infeasible
            == after_infeasible
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
            "HOSTED_PHYSICAL_VARIABLE_SIZE_EXACT_BYTE_BUDGET_ALLOCATION"
        ),
        "fixture": {
            "state_sizes_mib": list(
                STATE_SIZES_MIB
            ),
            "budget_schedule_mib": list(
                BUDGET_SCHEDULE_MIB
            ),
            "infeasible_budget_mib": (
                INFEASIBLE_BUDGET_MIB
            ),
        },
        "phases": phase_rows,
        "transitions": (
            transition_rows
        ),
        "summary": {
            "physical_actuations": (
                total_actuations
            ),
            "full_reenforcement_actuations": (
                full_reenforcement_count
            ),
            "actuation_reduction_fraction": (
                1.0
                - total_actuations
                / full_reenforcement_count
            ),
            "total_prefetch_bytes": (
                total_prefetch_bytes
            ),
            "observed_resident_mib": [
                row[
                    "snapshot"
                ][
                    "resident_mib"
                ]
                for row in phase_rows
            ],
            "allocated_used_mib": [
                row[
                    "allocation"
                ][
                    "used_mib"
                ]
                for row in phase_rows
            ],
        },
        "infeasible": {
            "budget_mib": (
                INFEASIBLE_BUDGET_MIB
            ),
            "reason": (
                infeasible[
                    "reason"
                ]
            ),
            "actuation_count": 0,
            "before": (
                before_infeasible
            ),
            "after": (
                after_infeasible
            ),
        },
        "checks": checks,
        "decision": (
            "PHYSICALLY_ENFORCE_EXACT_VARIABLE_SIZE_KNAPSACK_PLACEMENT_UNDER_A_BYTE_BUDGET"
        ),
        "next": (
            "CALIBRATE_PROMOTE_AND_EVICT_MIGRATION_COST_AS_A_FUNCTION_OF_BYTES_AND_DIRECTION"
        ),
        "claim_ceiling": (
            "HOSTED_PHYSICAL_VARIABLE_SIZE_ALLOCATION_ON_ONE_TEN_STATE_SIZE_VECTOR_AND_BUDGET_SCHEDULE_ONLY"
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
