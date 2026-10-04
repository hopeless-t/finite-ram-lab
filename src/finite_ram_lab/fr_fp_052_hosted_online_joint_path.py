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
    run_panel as _shadow_panel,
)

SCHEMA = "finite-ram-lab.fr-fp-052-hosted-online-joint-path/v0.1"

STATE_COUNT = len(STATE_SIZES_MIB)


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
        state_id: int(size_mib)
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
                220
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


def _run_path(
    root: Path,
    *,
    label: str,
    targets: list[set[int]],
    budgets_mib: list[int],
    service_ms_by_phase: list[float],
) -> dict[str, Any]:
    if not (
        len(targets)
        == len(budgets_mib)
        == len(service_ms_by_phase)
        == 5
    ):
        raise ValueError(
            "phase_length_mismatch"
        )

    paths, sizes_mib = (
        _prepare_fixture(
            root,
            prefix=label.lower(),
            initial_warm=targets[0],
        )
    )

    phase_rows = []
    transition_rows = []
    current = targets[0]
    total_actions = 0
    total_actuation_ns = 0
    total_prefetch_bytes = 0

    try:
        initial_snapshot = _snapshot(
            paths,
            sizes_mib=sizes_mib,
            target_warm=current,
        )
        phase_rows.append(
            {
                "phase": 1,
                "budget_mib": (
                    budgets_mib[0]
                ),
                "warm_ids": sorted(
                    current
                ),
                "service_ms": (
                    service_ms_by_phase[0]
                ),
                "snapshot": (
                    initial_snapshot
                ),
                "changed_ids": [],
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
            before = _snapshot(
                paths,
                sizes_mib=sizes_mib,
                target_warm=current,
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
                sizes_mib=sizes_mib,
                target_warm=target,
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
                    "actuation_count": (
                        len(actions)
                    ),
                    "promoted_mib": sum(
                        sizes_mib[
                            state_id
                        ]
                        for state_id
                        in changed
                        if state_id
                        in target
                    ),
                    "evicted_mib": sum(
                        sizes_mib[
                            state_id
                        ]
                        for state_id
                        in changed
                        if state_id
                        not in target
                    ),
                    "actuation_ns": (
                        elapsed_ns
                    ),
                    "before": before,
                    "after": after,
                    "actions": actions,
                }
            )

            phase_rows.append(
                {
                    "phase": (
                        phase_index
                        + 1
                    ),
                    "budget_mib": (
                        budgets_mib[
                            phase_index
                        ]
                    ),
                    "warm_ids": sorted(
                        target
                    ),
                    "service_ms": (
                        service_ms_by_phase[
                            phase_index
                        ]
                    ),
                    "snapshot": after,
                    "changed_ids": (
                        changed
                    ),
                }
            )
            current = target

    finally:
        _cleanup(
            paths
        )

    service_ms = sum(
        service_ms_by_phase
    )
    actuation_ms = (
        total_actuation_ns
        / 1_000_000.0
    )

    return {
        "label": label,
        "phase_rows": phase_rows,
        "transition_rows": (
            transition_rows
        ),
        "service_ms": service_ms,
        "physical_actuation_ms": (
            actuation_ms
        ),
        "physical_hybrid_total_ms": (
            service_ms
            + actuation_ms
        ),
        "physical_actions": (
            total_actions
        ),
        "prefetch_bytes": (
            total_prefetch_bytes
        ),
        "final_warm_ids": sorted(
            current
        ),
    }


def run_panel() -> dict[str, Any]:
    shadow = _shadow_panel()

    joint_rows = (
        shadow[
            "joint"
        ][
            "rows"
        ]
    )
    semantic_rows = (
        shadow[
            "migration_blind_semantic"
        ][
            "rows"
        ]
    )
    budgets = [
        int(row["budget_mib"])
        for row in joint_rows
    ]

    joint_targets = [
        set(
            row[
                "joint_warm_ids"
            ]
        )
        for row in joint_rows
    ]
    semantic_targets = [
        set(
            row[
                "warm_ids"
            ]
        )
        for row in semantic_rows
    ]
    joint_service = [
        float(
            row[
                "service_ms"
            ]
        )
        for row in joint_rows
    ]
    semantic_service = [
        float(
            row[
                "service_ms"
            ]
        )
        for row in semantic_rows
    ]

    with tempfile.TemporaryDirectory(
        prefix="fr-fp-052-"
    ) as tmp:
        root = Path(tmp)

        joint = _run_path(
            root,
            label="JOINT",
            targets=joint_targets,
            budgets_mib=budgets,
            service_ms_by_phase=(
                joint_service
            ),
        )
        semantic = _run_path(
            root,
            label="SEMANTIC",
            targets=semantic_targets,
            budgets_mib=budgets,
            service_ms_by_phase=(
                semantic_service
            ),
        )

    def exact_physical(
        arm: dict[str, Any],
    ) -> bool:
        return all(
            abs(
                row[
                    "snapshot"
                ][
                    "resident_mib"
                ]
                - row[
                    "snapshot"
                ][
                    "target_warm_mib"
                ]
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

    checks = {
        "shadow_parent_passes": (
            shadow[
                "status"
            ]
            == "PASS"
        ),
        "same_five_phase_budget_schedule": (
            budgets
            == [40, 28, 72, 44, 56]
        ),
        "joint_physical_residency_matches_targets": (
            exact_physical(
                joint
            )
        ),
        "semantic_physical_residency_matches_targets": (
            exact_physical(
                semantic
            )
        ),
        "joint_uses_fewer_physical_actions": (
            joint[
                "physical_actions"
            ]
            < semantic[
                "physical_actions"
            ]
        ),
        "joint_uses_less_physical_actuation_time": (
            joint[
                "physical_actuation_ms"
            ]
            < semantic[
                "physical_actuation_ms"
            ]
        ),
        "joint_physical_hybrid_total_beats_semantic_tracking": (
            joint[
                "physical_hybrid_total_ms"
            ]
            < semantic[
                "physical_hybrid_total_ms"
            ]
        ),
        "joint_finishes_at_same_final_semantic_target": (
            joint[
                "final_warm_ids"
            ]
            == semantic[
                "final_warm_ids"
            ]
        ),
        "both_paths_exercise_variable_size_actions": (
            len(
                {
                    action[
                        "state_mib"
                    ]
                    for arm in (
                        joint,
                        semantic,
                    )
                    for row in arm[
                        "transition_rows"
                    ]
                    for action in row[
                        "actions"
                    ]
                }
            )
            >= 3
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
            "HOSTED_PHYSICAL_ONLINE_JOINT_VARIABLE_SIZE_PATH_VALIDATION"
        ),
        "fixture": {
            "state_sizes_mib": list(
                STATE_SIZES_MIB
            ),
            "capacity_schedule_mib": (
                budgets
            ),
            "phase_count": 5,
        },
        "joint": joint,
        "migration_blind_semantic": (
            semantic
        ),
        "shadow_reference": {
            "joint_total_ms": (
                shadow[
                    "joint"
                ][
                    "total_ms"
                ]
            ),
            "migration_blind_total_ms": (
                shadow[
                    "migration_blind_semantic"
                ][
                    "total_ms"
                ]
            ),
        },
        "checks": checks,
        "decision": (
            "PHYSICALLY_FOLLOW_THE_JOINT_SERVICE_PLUS_MIGRATION_OPTIMUM_INSTEAD_OF_MIGRATION_BLIND_SEMANTIC_TRACKING"
        ),
        "evidence_boundary": (
            "WARM/COLD page-cache actuation and transition time are hosted physical. "
            "Per-phase service cost remains the qualified synthetic expected-penalty model."
        ),
        "next": (
            "COMPARE_MODEL_PREDICTION_ERROR_WITH_OBSERVED_MULTI_PHASE_TRANSITIONS_AND_UPDATE_THE_MIGRATION_COST_MODEL_ONLY_IF_THE_HELD_OUT_ERROR_REQUIRES_IT"
        ),
        "claim_ceiling": (
            "HOSTED_PHYSICAL_FIVE_PHASE_VARIABLE_SIZE_JOINT_PATH_ON_ONE_FROZEN_ONLINE_TRACE_ONLY"
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
