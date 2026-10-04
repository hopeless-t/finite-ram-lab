from __future__ import annotations

import json
import tempfile
import time
from pathlib import Path
from typing import Any

from finite_ram_lab.fr_fp_016_restore_size_scaling import (
    _fadvise_dontneed,
    _prepare_tier,
    _size_bytes,
)
from finite_ram_lab.fr_fp_030_hosted_reuse_lifecycle import (
    _enforce_tier,
)
from finite_ram_lab.fr_fp_037_hosted_dynamic_budget import (
    _snapshot,
)
from finite_ram_lab.fr_fp_038_online_multistate_value import (
    STATE_COUNT,
    STATE_MIB,
    WARM_SLOTS,
    run_panel as run_shadow_panel,
)

SCHEMA = "finite-ram-lab.fr-fp-039-hosted-online-value/v0.1"

SIZE_BYTES = _size_bytes(
    int(STATE_MIB)
)


def run_panel() -> dict[str, Any]:
    shadow = run_shadow_panel()

    if shadow["status"] != "PASS":
        raise RuntimeError(
            "shadow_parent_not_qualified"
        )

    targets = [
        set(
            phase["warm_ids"]
        )
        for phase in shadow[
            "phases"
        ]
    ]

    with tempfile.TemporaryDirectory(
        prefix="fr-fp-039-"
    ) as tmp:
        root = Path(tmp)
        paths: dict[
            int,
            Path,
        ] = {}

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
                    170
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

            paths[state_id] = path

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
                "warm_ids": sorted(
                    initial
                ),
                "changed_ids": [],
                "actuations": [],
                "snapshot": _snapshot(
                    paths,
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
                len(targets),
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
                    total_prefetch_bytes += int(
                        row[
                            "prefetch_bytes"
                        ]
                    )

                elapsed = (
                    time.monotonic_ns()
                    - started
                )
                total_actuations += len(
                    actuations
                )

                after = _snapshot(
                    paths,
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
                        "changed_ids": (
                            changed
                        ),
                        "actuation_count": len(
                            actuations
                        ),
                        "actuation_ns": (
                            elapsed
                        ),
                        "before": before,
                        "after": after,
                        "actuations": (
                            actuations
                        ),
                        "decision_irrelevant_evidence_update": (
                            len(
                                changed
                            )
                            == 0
                        ),
                    }
                )

                phase_rows.append(
                    {
                        "phase": (
                            phase_index
                            + 1
                        ),
                        "warm_ids": sorted(
                            current
                        ),
                        "changed_ids": (
                            changed
                        ),
                        "actuations": (
                            actuations
                        ),
                        "snapshot": after,
                    }
                )

                previous = current

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

    full_reenforcement = (
        (
            len(targets)
            - 1
        )
        * STATE_COUNT
    )
    expected_resident_mib = (
        WARM_SLOTS
        * STATE_MIB
    )
    zero_action_transitions = [
        row
        for row in transition_rows
        if row[
            "actuation_count"
        ]
        == 0
    ]

    checks = {
        "shadow_parent_passes": (
            shadow["status"]
            == "PASS"
        ),
        "five_physical_phases": (
            len(
                phase_rows
            )
            == 5
        ),
        "physical_warm_sets_match_shadow": all(
            set(
                row[
                    "warm_ids"
                ]
            )
            == targets[index]
            for index, row
            in enumerate(
                phase_rows
            )
        ),
        "every_phase_holds_exact_five_slot_budget": all(
            abs(
                row[
                    "snapshot"
                ][
                    "resident_mib"
                ]
                - expected_resident_mib
            )
            <= 0.5
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
            is not None
            and row[
                "snapshot"
            ][
                "cold_max_residency"
            ]
            <= 0.10
            for row in phase_rows
        ),
        "physical_actuation_count_matches_shadow": (
            total_actuations
            == shadow[
                "summary"
            ][
                "minimal_delta_actuations"
            ]
        ),
        "physical_minimal_delta_beats_full_reenforcement": (
            total_actuations
            < full_reenforcement
        ),
        "every_transition_touches_only_changed_ids": all(
            row[
                "actuation_count"
            ]
            == len(
                row[
                    "changed_ids"
                ]
            )
            for row in transition_rows
        ),
        "at_least_one_decision_irrelevant_evidence_phase_executes_zero_actions": (
            bool(
                zero_action_transitions
            )
        ),
        "zero_action_phase_preserves_physical_snapshot": all(
            row[
                "before"
            ]
            == row[
                "after"
            ]
            for row in (
                zero_action_transitions
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
            "HOSTED_PHYSICAL_ONLINE_VALUE_REALLOCATION_WITH_DECISION_RELEVANCE_ACTUATION"
        ),
        "fixture": {
            "state_count": (
                STATE_COUNT
            ),
            "state_mib": (
                STATE_MIB
            ),
            "warm_slots": (
                WARM_SLOTS
            ),
            "warm_mib": (
                expected_resident_mib
            ),
            "phase_count": len(
                targets
            ),
        },
        "shadow": {
            "warm_sets": [
                sorted(
                    target
                )
                for target in targets
            ],
            "minimal_delta_actuations": (
                shadow[
                    "summary"
                ][
                    "minimal_delta_actuations"
                ]
            ),
            "full_reenforcement_actuations": (
                shadow[
                    "summary"
                ][
                    "full_reenforcement_actuations"
                ]
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
                full_reenforcement
            ),
            "actuation_reduction_fraction": (
                1.0
                - total_actuations
                / full_reenforcement
            ),
            "prefetch_bytes": (
                total_prefetch_bytes
            ),
            "zero_action_transition_count": (
                len(
                    zero_action_transitions
                )
            ),
            "observed_resident_mib": [
                row[
                    "snapshot"
                ][
                    "resident_mib"
                ]
                for row in phase_rows
            ],
        },
        "checks": checks,
        "decision": (
            "PHYSICALLY_REALLOCATE_ONLY_WHEN_ONLINE_SEMANTIC_VALUE_CHANGES_THE_OPTIMAL_WARM_SET"
        ),
        "meta_transfer": (
            "decision-relevance pruning now reproduces in physical multi-state placement: new evidence may update beliefs without requiring an actuation"
        ),
        "next": (
            "COMBINE_DYNAMIC_CAPACITY_AND_DYNAMIC_STATE_VALUE_IN_ONE_HOSTED_GOVERNOR"
        ),
        "claim_ceiling": (
            "HOSTED_PHYSICAL_FIVE_PHASE_ONLINE_VALUE_REALLOCATION_ON_ONE_TEN_STATE_EQUAL_SIZE_FIXTURE_ONLY"
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
