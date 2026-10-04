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
    _cold_penalty,
    _states,
    _used_mib,
)
from finite_ram_lab.fr_fp_047_hosted_variable_size_budget import (
    _enforce_tier_sized,
    _snapshot,
)
from finite_ram_lab.fr_fp_049_joint_migration_aware_knapsack import (
    _migration_cost_ms,
)

SCHEMA = "finite-ram-lab.fr-fp-050-hosted-joint-third-placement/v0.1"

CONTEXTS = (
    {
        "label": "GROWTH_56_TO_72_H50",
        "budget_mib": 72,
        "horizon": 50,
        "current_warm_ids": (
            0, 1, 2, 3, 7, 8, 9,
        ),
        "joint_warm_ids": (
            0, 1, 2, 3, 6, 7, 8, 9,
        ),
        "semantic_warm_ids": (
            0, 1, 2, 4, 5, 7, 8, 9,
        ),
        "include_hold": True,
    },
    {
        "label": "SHRINK_92_TO_44_H20",
        "budget_mib": 44,
        "horizon": 20,
        "current_warm_ids": (
            0, 2, 3, 4, 5, 6, 7, 8, 9,
        ),
        "joint_warm_ids": (
            0, 4, 7, 8, 9,
        ),
        "semantic_warm_ids": (
            1, 3, 7, 8, 9,
        ),
        "include_hold": False,
    },
)


def _prepare_fixture(
    root: Path,
    *,
    states: list[dict[str, Any]],
    current_warm: set[int],
    marker_base: int,
) -> tuple[
    dict[int, Path],
    dict[int, int],
]:
    sizes_mib = {
        int(row["state_id"]): int(
            row["state_mib"]
        )
        for row in states
    }
    paths: dict[int, Path] = {}

    for state_id in range(
        len(states)
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
                marker_base
                + state_id
            ),
            cold=(
                state_id
                not in current_warm
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
        _enforce_tier_sized(
            path,
            tier=(
                "WARM"
                if state_id
                in current_warm
                else "COLD"
            ),
            size_bytes=_size_bytes(
                sizes_mib[
                    state_id
                ]
            ),
        )

    return paths, sizes_mib


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


def _actuate_candidate(
    *,
    states: list[dict[str, Any]],
    label: str,
    current_warm: set[int],
    target_warm: set[int],
    budget_mib: int,
    horizon: int,
    marker_base: int,
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(
        prefix=(
            "fr-fp-050-"
            + label.lower()
            + "-"
        )
    ) as tmp:
        root = Path(tmp)
        paths, sizes_mib = (
            _prepare_fixture(
                root,
                states=states,
                current_warm=(
                    current_warm
                ),
                marker_base=(
                    marker_base
                ),
            )
        )

        before = _snapshot(
            paths,
            sizes_mib=sizes_mib,
            target_warm=(
                current_warm
            ),
        )
        changed = sorted(
            current_warm
            ^ target_warm
        )
        actuations = []
        started = (
            time.monotonic_ns()
        )

        try:
            for state_id in changed:
                target_tier = (
                    "WARM"
                    if state_id
                    in target_warm
                    else "COLD"
                )
                action_started = (
                    time.monotonic_ns()
                )
                row = (
                    _enforce_tier_sized(
                        paths[
                            state_id
                        ],
                        tier=target_tier,
                        size_bytes=_size_bytes(
                            sizes_mib[
                                state_id
                            ]
                        ),
                    )
                )
                action_ns = (
                    time.monotonic_ns()
                    - action_started
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
                        "action_ns": (
                            action_ns
                        ),
                        **row,
                    }
                )

            total_ns = (
                time.monotonic_ns()
                - started
            )
            after = _snapshot(
                paths,
                sizes_mib=sizes_mib,
                target_warm=(
                    target_warm
                ),
            )

        finally:
            _cleanup(
                paths
            )

    service_ms = (
        horizon
        * _cold_penalty(
            states,
            target_warm,
        )
    )
    predicted_migration = (
        _migration_cost_ms(
            states,
            current_warm=current_warm,
            candidate_warm=(
                target_warm
            ),
        )
    )
    observed_migration_ms = (
        total_ns
        / 1_000_000.0
    )

    return {
        "label": label,
        "budget_mib": (
            budget_mib
        ),
        "horizon": horizon,
        "current_warm_ids": sorted(
            current_warm
        ),
        "target_warm_ids": sorted(
            target_warm
        ),
        "target_used_mib": (
            _used_mib(
                states,
                target_warm,
            )
        ),
        "changed_ids": changed,
        "actuation_count": len(
            actuations
        ),
        "actuations": (
            actuations
        ),
        "before": before,
        "after": after,
        "service_ms": (
            service_ms
        ),
        "predicted_migration_ms": (
            predicted_migration[
                "total_ms"
            ]
        ),
        "observed_migration_ms": (
            observed_migration_ms
        ),
        "hybrid_total_ms": (
            service_ms
            + observed_migration_ms
        ),
        "migration_prediction_relative_error": (
            0.0
            if predicted_migration[
                "total_ms"
            ]
            == 0.0
            else (
                (
                    observed_migration_ms
                    - predicted_migration[
                        "total_ms"
                    ]
                )
                / predicted_migration[
                    "total_ms"
                ]
            )
        ),
    }


def run_panel() -> dict[str, Any]:
    states = _states()
    context_rows = []

    for context_index, context in enumerate(
        CONTEXTS
    ):
        current = set(
            context[
                "current_warm_ids"
            ]
        )
        joint = set(
            context[
                "joint_warm_ids"
            ]
        )
        semantic = set(
            context[
                "semantic_warm_ids"
            ]
        )
        budget = int(
            context[
                "budget_mib"
            ]
        )
        horizon = int(
            context[
                "horizon"
            ]
        )

        joint_row = (
            _actuate_candidate(
                states=states,
                label=(
                    context[
                        "label"
                    ]
                    + "-joint"
                ),
                current_warm=current,
                target_warm=joint,
                budget_mib=budget,
                horizon=horizon,
                marker_base=(
                    240
                    + context_index
                    * 20
                ),
            )
        )
        semantic_row = (
            _actuate_candidate(
                states=states,
                label=(
                    context[
                        "label"
                    ]
                    + "-semantic"
                ),
                current_warm=current,
                target_warm=semantic,
                budget_mib=budget,
                horizon=horizon,
                marker_base=(
                    241
                    + context_index
                    * 20
                ),
            )
        )

        hold_row = None

        if context[
            "include_hold"
        ]:
            hold_row = (
                _actuate_candidate(
                    states=states,
                    label=(
                        context[
                            "label"
                        ]
                        + "-hold"
                    ),
                    current_warm=current,
                    target_warm=current,
                    budget_mib=budget,
                    horizon=horizon,
                    marker_base=(
                        242
                        + context_index
                        * 20
                    ),
                )
            )

        context_rows.append(
            {
                "label": (
                    context[
                        "label"
                    ]
                ),
                "budget_mib": (
                    budget
                ),
                "horizon": (
                    horizon
                ),
                "joint": joint_row,
                "semantic": (
                    semantic_row
                ),
                "hold": hold_row,
                "joint_beats_semantic": (
                    joint_row[
                        "hybrid_total_ms"
                    ]
                    < semantic_row[
                        "hybrid_total_ms"
                    ]
                ),
                "joint_beats_hold": (
                    True
                    if hold_row
                    is None
                    else (
                        joint_row[
                            "hybrid_total_ms"
                        ]
                        < hold_row[
                            "hybrid_total_ms"
                        ]
                    )
                ),
            }
        )

    candidate_rows = [
        row[kind]
        for row in context_rows
        for kind in (
            "joint",
            "semantic",
            "hold",
        )
        if row[kind]
        is not None
    ]

    checks = {
        "two_representative_third_placement_contexts": (
            len(
                context_rows
            )
            == 2
        ),
        "every_candidate_respects_budget": all(
            row[
                "target_used_mib"
            ]
            <= row[
                "budget_mib"
            ]
            for row in (
                candidate_rows
            )
        ),
        "every_physical_target_hits_exact_resident_bytes": all(
            abs(
                row[
                    "after"
                ][
                    "resident_mib"
                ]
                - row[
                    "target_used_mib"
                ]
            )
            <= 0.75
            for row in (
                candidate_rows
            )
        ),
        "every_warm_target_is_resident": all(
            row[
                "after"
            ][
                "warm_min_residency"
            ]
            is not None
            and row[
                "after"
            ][
                "warm_min_residency"
            ]
            >= 0.95
            for row in (
                candidate_rows
            )
        ),
        "every_cold_target_is_nonresident": all(
            row[
                "after"
            ][
                "cold_max_residency"
            ]
            is None
            or row[
                "after"
            ][
                "cold_max_residency"
            ]
            <= 0.10
            for row in (
                candidate_rows
            )
        ),
        "joint_physically_beats_semantic_in_both_contexts": all(
            row[
                "joint_beats_semantic"
            ]
            for row in (
                context_rows
            )
        ),
        "joint_physically_beats_feasible_hold": all(
            row[
                "joint_beats_hold"
            ]
            for row in (
                context_rows
            )
        ),
        "growth_context_exercises_promotion_only_third_placement": (
            context_rows[0][
                "joint"
            ][
                "actuation_count"
            ]
            == 1
            and context_rows[0][
                "joint"
            ][
                "actuations"
            ][0][
                "target_tier"
            ]
            == "WARM"
        ),
        "shrink_context_exercises_multiple_evictions": (
            sum(
                action[
                    "target_tier"
                ]
                == "COLD"
                for action in context_rows[
                    1
                ][
                    "joint"
                ][
                    "actuations"
                ]
            )
            >= 4
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
            "HOSTED_PHYSICAL_JOINT_THIRD_PLACEMENT_VALIDATION"
        ),
        "contexts": (
            context_rows
        ),
        "checks": checks,
        "decision": (
            "PHYSICALLY_SELECT_PARTIAL_MIGRATION_WHEN_IT_BEATS_BOTH_HOLD_AND_MIGRATION_BLIND_SEMANTIC_OPTIMUM"
        ),
        "evidence_boundary": (
            "Tier migration and page-cache residency are hosted physical. "
            "Service cost over the frozen horizon remains the qualified synthetic expected-penalty model."
        ),
        "next": (
            "GENERALIZE_JOINT_OPTIMIZATION_TO_ONLINE_VALUE_UPDATES_AND_DYNAMIC_CAPACITY_USING_THE_PHYSICAL_MIGRATION_MODEL"
        ),
        "claim_ceiling": (
            "HOSTED_PHYSICAL_VALIDATION_OF_TWO_FP049_THIRD_PLACEMENT_CONTEXTS_ONLY"
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
