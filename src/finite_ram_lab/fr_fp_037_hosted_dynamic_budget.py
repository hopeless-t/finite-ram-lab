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
from finite_ram_lab.fr_fp_034_multistate_budget_allocation import (
    STATE_MIB,
    _greedy_allocate,
    _state_rows,
)
from finite_ram_lab.fr_fp_036_dynamic_budget_transition import (
    CAPACITY_SCHEDULE,
    INFEASIBLE_TEST_SLOTS,
)

SCHEMA = "finite-ram-lab.fr-fp-037-hosted-dynamic-budget/v0.1"

STATE_COUNT = 10
SIZE_BYTES = _size_bytes(
    int(STATE_MIB)
)


def _snapshot(
    paths: dict[int, Path],
    *,
    target_warm: set[int],
) -> dict[str, Any]:
    rows = []

    for state_id, path in (
        paths.items()
    ):
        fraction = (
            _file_residency(
                path
            )[
                "resident_fraction"
            ]
        )
        rows.append(
            {
                "state_id": (
                    state_id
                ),
                "resident_fraction": (
                    fraction
                ),
                "target_tier": (
                    "WARM"
                    if state_id
                    in target_warm
                    else "COLD"
                ),
            }
        )

    return {
        "resident_mib": sum(
            row[
                "resident_fraction"
            ]
            * STATE_MIB
            for row in rows
        ),
        "warm_min_residency": (
            min(
                row[
                    "resident_fraction"
                ]
                for row in rows
                if row[
                    "state_id"
                ]
                in target_warm
            )
            if target_warm
            else None
        ),
        "cold_max_residency": (
            max(
                row[
                    "resident_fraction"
                ]
                for row in rows
                if row[
                    "state_id"
                ]
                not in target_warm
            )
            if len(
                target_warm
            )
            < len(rows)
            else None
        ),
        "rows": rows,
    }


def _target_set(
    states: list[dict[str, Any]],
    warm_slots: int,
) -> set[int]:
    allocation = _greedy_allocate(
        states,
        warm_slots=warm_slots,
    )

    if not allocation[
        "feasible"
    ]:
        raise RuntimeError(
            f"infeasible_target:{warm_slots}"
        )

    return set(
        allocation[
            "warm_ids"
        ]
    )


def run_panel() -> dict[str, Any]:
    states = _state_rows()
    targets = [
        _target_set(
            states,
            warm_slots,
        )
        for warm_slots
        in CAPACITY_SCHEDULE
    ]

    with tempfile.TemporaryDirectory(
        prefix="fr-fp-037-"
    ) as tmp:
        root = Path(tmp)
        paths = {}

        initial = targets[0]

        for state_id in range(
            STATE_COUNT
        ):
            path = root / (
                f"state-{state_id}.bin"
            )
            prepared = _prepare_tier(
                path,
                size_bytes=SIZE_BYTES,
                marker=(
                    140
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
                "warm_slots": (
                    CAPACITY_SCHEDULE[0]
                ),
                "warm_ids": sorted(
                    initial
                ),
                "snapshot": _snapshot(
                    paths,
                    target_warm=initial,
                ),
                "actuations": [],
            }
        ]

        previous = initial
        total_actuations = 0
        total_prefetch_bytes = 0
        transition_rows = []

        try:
            for phase_index in range(
                1,
                len(
                    CAPACITY_SCHEDULE
                ),
            ):
                current = targets[
                    phase_index
                ]
                changed = sorted(
                    previous
                    ^ current
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
                    actuations.append(
                        {
                            "state_id": (
                                state_id
                            ),
                            "target_tier": (
                                target_tier
                            ),
                            **row,
                        }
                    )
                    total_prefetch_bytes += (
                        row[
                            "prefetch_bytes"
                        ]
                    )

                elapsed = (
                    time.monotonic_ns()
                    - started
                )
                total_actuations += len(
                    changed
                )

                snap = _snapshot(
                    paths,
                    target_warm=current,
                )
                transition = {
                    "from_phase": (
                        phase_index
                    ),
                    "to_phase": (
                        phase_index
                        + 1
                    ),
                    "from_slots": (
                        CAPACITY_SCHEDULE[
                            phase_index
                            - 1
                        ]
                    ),
                    "to_slots": (
                        CAPACITY_SCHEDULE[
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
                    "actuation_ns": (
                        elapsed
                    ),
                    "actuations": (
                        actuations
                    ),
                    "snapshot": snap,
                }
                transition_rows.append(
                    transition
                )
                phase_rows.append(
                    {
                        "phase": (
                            phase_index
                            + 1
                        ),
                        "warm_slots": (
                            CAPACITY_SCHEDULE[
                                phase_index
                            ]
                        ),
                        "warm_ids": sorted(
                            current
                        ),
                        "snapshot": snap,
                        "actuations": (
                            actuations
                        ),
                    }
                )
                previous = current

            infeasible = _greedy_allocate(
                states,
                warm_slots=(
                    INFEASIBLE_TEST_SLOTS
                ),
            )
            before_infeasible = _snapshot(
                paths,
                target_warm=previous,
            )
            infeasible_actuations = []

            if infeasible[
                "feasible"
            ]:
                raise RuntimeError(
                    "infeasible_budget_unexpectedly_feasible"
                )

            after_infeasible = _snapshot(
                paths,
                target_warm=previous,
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
                CAPACITY_SCHEDULE
            )
            - 1
        )
        * STATE_COUNT
    )

    expected_resident = [
        slots
        * STATE_MIB
        for slots in (
            CAPACITY_SCHEDULE
        )
    ]

    observed_resident = [
        row[
            "snapshot"
        ][
            "resident_mib"
        ]
        for row in phase_rows
    ]

    checks = {
        "all_phase_warm_sets_match_shadow_targets": all(
            set(
                row[
                    "warm_ids"
                ]
            )
            == targets[
                index
            ]
            for index, row
            in enumerate(
                phase_rows
            )
        ),
        "every_phase_hits_requested_physical_residency": all(
            abs(
                observed
                - expected
            )
            <= 0.5
            for observed, expected
            in zip(
                observed_resident,
                expected_resident,
            )
        ),
        "every_warm_state_is_physically_resident": all(
            row[
                "snapshot"
            ][
                "warm_min_residency"
            ]
            is None
            or row[
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
        "physical_actuation_count_matches_minimal_shadow": (
            total_actuations
            == 11
        ),
        "minimal_actuation_beats_full_reenforcement": (
            total_actuations
            < full_reenforcement_count
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
        "infeasible_request_executes_zero_actions": (
            len(
                infeasible_actuations
            )
            == 0
        ),
        "infeasible_request_preserves_physical_residency": (
            before_infeasible
            == after_infeasible
        ),
        "infeasible_reason_is_mandatory_warm_budget": (
            infeasible[
                "reason"
            ]
            == "MANDATORY_WARM_EXCEEDS_BUDGET"
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
            "HOSTED_PHYSICAL_DYNAMIC_WARM_BUDGET_MINIMAL_DELTA_ACTUATION"
        ),
        "fixture": {
            "state_count": (
                STATE_COUNT
            ),
            "state_mib": (
                STATE_MIB
            ),
            "capacity_schedule_slots": list(
                CAPACITY_SCHEDULE
            ),
            "capacity_schedule_mib": (
                expected_resident
            ),
            "infeasible_test_slots": (
                INFEASIBLE_TEST_SLOTS
            ),
        },
        "phases": phase_rows,
        "transitions": (
            transition_rows
        ),
        "summary": {
            "minimal_actuations": (
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
            "prefetch_bytes": (
                total_prefetch_bytes
            ),
            "observed_resident_mib": (
                observed_resident
            ),
        },
        "infeasible": {
            "request_slots": (
                INFEASIBLE_TEST_SLOTS
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
            "PHYSICALLY_ACTUATE_ONLY_CHANGED_STATE_TIERS_ACROSS_DYNAMIC_CAPACITY_AND_PRESERVE_PLACEMENT_ON_INFEASIBLE_PRESSURE"
        ),
        "next": (
            "MAKE_STATE_VALUES_CHANGE_ONLINE_FROM_REUSE_EVIDENCE_WHILE_CAPACITY_REMAINS_FINITE"
        ),
        "claim_ceiling": (
            "HOSTED_PHYSICAL_DYNAMIC_CAPACITY_ACTUATION_ON_ONE_TEN_STATE_EQUAL_SIZE_FIXTURE_ONLY"
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
