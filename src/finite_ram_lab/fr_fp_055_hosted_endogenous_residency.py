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
from finite_ram_lab.fr_fp_046_variable_size_knapsack import (
    STATE_SIZES_MIB,
)
from finite_ram_lab.fr_fp_047_hosted_variable_size_budget import (
    _enforce_tier_sized,
    _snapshot,
)
from finite_ram_lab.fr_fp_051_online_joint_variable_size import (
    PHASE_HORIZON_ROUNDS,
)
from finite_ram_lab.fr_fp_054_endogenous_resident_budget import (
    run_panel as _shadow_panel,
)

SCHEMA = "finite-ram-lab.fr-fp-055-hosted-endogenous-residency/v0.1"

SELECTED_MEMORY_RENTS = (
    0.0,
    0.10,
    0.25,
    0.40,
)

STATE_COUNT = len(
    STATE_SIZES_MIB
)


def _prepare_fixture(
    root: Path,
    *,
    prefix: str,
    initial_warm: set[int],
) -> tuple[
    dict[int, Path],
    dict[int, int],
]:
    sizes_mib = {
        state_id: int(
            size_mib
        )
        for state_id, size_mib
        in enumerate(
            STATE_SIZES_MIB
        )
    }
    paths: dict[int, Path] = {}

    for state_id in range(
        STATE_COUNT
    ):
        path = root / (
            f"{prefix}-state-{state_id}.bin"
        )
        prepared = _prepare_tier(
            path,
            size_bytes=_size_bytes(
                sizes_mib[
                    state_id
                ]
            ),
            marker=(
                240
                + state_id
            ),
            cold=(
                state_id
                not in initial_warm
            ),
        )

        if not prepared[
            "verified"
        ]:
            raise RuntimeError(
                f"prepare_failed:{prefix}:{state_id}"
            )

        paths[
            state_id
        ] = path

    # Reassert the exact initial placement using the qualified size-aware
    # actuator so every arm starts from the same tier contract.
    for state_id, path in (
        paths.items()
    ):
        _enforce_tier_sized(
            path,
            tier=(
                "WARM"
                if state_id
                in initial_warm
                else "COLD"
            ),
            size_bytes=_size_bytes(
                sizes_mib[
                    state_id
                ]
            ),
        )

    return (
        paths,
        sizes_mib,
    )


def _cleanup(
    paths: dict[int, Path],
) -> None:
    for path in paths.values():
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


def _run_rent_arm(
    root: Path,
    *,
    rent: float,
    shadow: dict[str, Any],
) -> dict[str, Any]:
    rows = shadow[
        "rows"
    ]
    targets = [
        set(
            row[
                "warm_ids"
            ]
        )
        for row in rows
    ]
    hard_caps = [
        int(
            row[
                "budget_mib"
            ]
        )
        for row in rows
    ]
    shadow_used = [
        int(
            row[
                "used_mib"
            ]
        )
        for row in rows
    ]

    paths, sizes_mib = (
        _prepare_fixture(
            root,
            prefix=(
                f"rent-{rent:.3f}"
                .replace(
                    ".",
                    "_",
                )
            ),
            initial_warm=(
                targets[0]
            ),
        )
    )

    phase_rows = []
    transitions = []
    current = targets[0]
    total_actions = 0
    total_actuation_ns = 0
    total_prefetch_bytes = 0

    try:
        first = _snapshot(
            paths,
            sizes_mib=(
                sizes_mib
            ),
            target_warm=(
                current
            ),
        )
        phase_rows.append(
            {
                "phase": 1,
                "hard_cap_mib": (
                    hard_caps[0]
                ),
                "shadow_used_mib": (
                    shadow_used[0]
                ),
                "target_warm_ids": sorted(
                    current
                ),
                "snapshot": first,
                "physical_unused_mib": (
                    hard_caps[0]
                    - first[
                        "resident_mib"
                    ]
                ),
            }
        )

        for phase_index in range(
            1,
            len(targets),
        ):
            target = targets[
                phase_index
            ]
            changed = sorted(
                current
                ^ target
            )
            actions = []
            started = (
                time.monotonic_ns()
            )

            for state_id in changed:
                tier = (
                    "WARM"
                    if state_id
                    in target
                    else "COLD"
                )
                result = (
                    _enforce_tier_sized(
                        paths[
                            state_id
                        ],
                        tier=tier,
                        size_bytes=_size_bytes(
                            sizes_mib[
                                state_id
                            ]
                        ),
                    )
                )
                total_prefetch_bytes += int(
                    result[
                        "prefetch_bytes"
                    ]
                )
                actions.append(
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
                            tier
                        ),
                        **result,
                    }
                )

            elapsed_ns = (
                time.monotonic_ns()
                - started
            )
            total_actuation_ns += (
                elapsed_ns
            )
            total_actions += len(
                actions
            )

            after = _snapshot(
                paths,
                sizes_mib=(
                    sizes_mib
                ),
                target_warm=(
                    target
                ),
            )

            transitions.append(
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
                    "action_count": (
                        len(actions)
                    ),
                    "actuation_ns": (
                        elapsed_ns
                    ),
                    "actions": (
                        actions
                    ),
                }
            )
            phase_rows.append(
                {
                    "phase": (
                        phase_index
                        + 1
                    ),
                    "hard_cap_mib": (
                        hard_caps[
                            phase_index
                        ]
                    ),
                    "shadow_used_mib": (
                        shadow_used[
                            phase_index
                        ]
                    ),
                    "target_warm_ids": sorted(
                        target
                    ),
                    "snapshot": after,
                    "physical_unused_mib": (
                        hard_caps[
                            phase_index
                        ]
                        - after[
                            "resident_mib"
                        ]
                    ),
                }
            )
            current = target

    finally:
        _cleanup(
            paths
        )

    physical_integral = (
        PHASE_HORIZON_ROUNDS
        * sum(
            float(
                row[
                    "snapshot"
                ][
                    "resident_mib"
                ]
            )
            for row in phase_rows
        )
    )

    return {
        "memory_rent_ms_per_mib_round": (
            rent
        ),
        "phase_rows": (
            phase_rows
        ),
        "transitions": (
            transitions
        ),
        "physical_actions": (
            total_actions
        ),
        "physical_actuation_ms": (
            total_actuation_ns
            / 1_000_000.0
        ),
        "prefetch_bytes": (
            total_prefetch_bytes
        ),
        "physical_resident_mib_round": (
            physical_integral
        ),
        "shadow_resident_mib_round": (
            shadow[
                "resident_mib_round"
            ]
        ),
        "physical_used_mib": [
            float(
                row[
                    "snapshot"
                ][
                    "resident_mib"
                ]
            )
            for row in phase_rows
        ],
        "shadow_used_mib": (
            shadow_used
        ),
        "hard_caps_mib": (
            hard_caps
        ),
    }


def run_panel() -> dict[str, Any]:
    shadow = _shadow_panel()

    by_rent = {
        float(
            row[
                "memory_rent_ms_per_mib_round"
            ]
        ): row
        for row in shadow[
            "sweeps"
        ]
    }

    selected = {
        rent: by_rent[rent]
        for rent in (
            SELECTED_MEMORY_RENTS
        )
    }

    with tempfile.TemporaryDirectory(
        prefix="fr-fp-055-"
    ) as tmp:
        root = Path(tmp)
        arms = [
            _run_rent_arm(
                root,
                rent=rent,
                shadow=selected[
                    rent
                ],
            )
            for rent in (
                SELECTED_MEMORY_RENTS
            )
        ]

    def placement_exact(
        arm: dict[str, Any],
    ) -> bool:
        return all(
            abs(
                float(
                    row[
                        "snapshot"
                    ][
                        "resident_mib"
                    ]
                )
                - float(
                    row[
                        "shadow_used_mib"
                    ]
                )
            )
            <= 0.75
            and (
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
            )
            and (
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
            )
            for row in arm[
                "phase_rows"
            ]
        )

    physical_integrals = [
        float(
            arm[
                "physical_resident_mib_round"
            ]
        )
        for arm in arms
    ]

    checks = {
        "shadow_parent_passes": (
            shadow[
                "status"
            ]
            == "PASS"
        ),
        "four_representative_rent_points": (
            len(arms) == 4
        ),
        "every_physical_snapshot_matches_shadow_used_bytes": all(
            placement_exact(
                arm
            )
            for arm in arms
        ),
        "every_physical_resident_integral_matches_shadow": all(
            abs(
                float(
                    arm[
                        "physical_resident_mib_round"
                    ]
                )
                - float(
                    arm[
                        "shadow_resident_mib_round"
                    ]
                )
            )
            <= (
                0.75
                * PHASE_HORIZON_ROUNDS
                * 5
            )
            for arm in arms
        ),
        "physical_residency_is_nonincreasing_with_memory_rent": all(
            left
            >= right
            for left, right
            in zip(
                physical_integrals[
                    :-1
                ],
                physical_integrals[
                    1:
                ],
            )
        ),
        "positive_rent_physically_leaves_capacity_unused": all(
            any(
                row[
                    "physical_unused_mib"
                ]
                > 0.75
                for row in arm[
                    "phase_rows"
                ]
            )
            for arm in arms
            if arm[
                "memory_rent_ms_per_mib_round"
            ]
            > 0.0
        ),
        "highest_rent_physically_keeps_all_states_cold": (
            arms[-1][
                "memory_rent_ms_per_mib_round"
            ]
            == 0.40
            and all(
                row[
                    "snapshot"
                ][
                    "resident_mib"
                ]
                <= 0.75
                for row in arms[-1][
                    "phase_rows"
                ]
            )
            and all(
                not row[
                    "target_warm_ids"
                ]
                for row in arms[-1][
                    "phase_rows"
                ]
            )
        ),
        "low_rent_retains_more_physical_byte_time_than_mid_and_high": (
            physical_integrals[0]
            > physical_integrals[1]
            > physical_integrals[2]
            > physical_integrals[3]
        ),
    }

    baseline_integral = (
        arms[0][
            "physical_resident_mib_round"
        ]
    )

    for arm in arms:
        arm[
            "resident_integral_reduction_vs_zero_rent"
        ] = (
            0.0
            if baseline_integral
            <= 0.0
            else (
                1.0
                - arm[
                    "physical_resident_mib_round"
                ]
                / baseline_integral
            )
        )

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
            "HOSTED_PHYSICAL_ENDOGENOUS_RESIDENT_BYTE_TIME_FRONTIER"
        ),
        "fixture": {
            "state_sizes_mib": list(
                STATE_SIZES_MIB
            ),
            "selected_memory_rents_ms_per_mib_round": list(
                SELECTED_MEMORY_RENTS
            ),
            "phase_horizon_rounds": (
                PHASE_HORIZON_ROUNDS
            ),
        },
        "arms": arms,
        "checks": checks,
        "decision": (
            "PHYSICALLY_LEAVE_WARM_CAPACITY_UNUSED_WHEN_RESIDENT_BYTE_TIME_COST_EXCEEDS_THE_SEMANTIC_VALUE_IT_SAVES"
        ),
        "evidence_boundary": (
            "Page-cache residency, unused resident capacity and tier actuation are hosted physical. "
            "Semantic service cost and memory-rent policy remain frozen modeled inputs."
        ),
        "next": (
            "DERIVE_THE_PARETO_SET_OVER_PHYSICAL_RESIDENT_BYTE_TIME_SERVICE_COST_AND_ACTUATION_COST_WITHOUT_COLLAPSING_THEM_INTO_ONE_HIDDEN_SCALAR"
        ),
        "claim_ceiling": (
            "HOSTED_PHYSICAL_RESIDENT_RENT_ACTUATION_AT_FOUR_POLICY_POINTS_ON_ONE_VARIABLE_SIZE_FIVE_PHASE_FIXTURE_ONLY"
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
