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
    MISS_TOLERANCE,
    STATE_COUNT,
    STATE_MIB,
    WARM_SLOTS,
    _penalty_for_warm_set,
    run_panel as run_shadow_panel,
)
from finite_ram_lab.fr_fp_042_migration_hysteresis import (
    _max_deadline_risk_for_warm,
    _migration_cost_ms,
)

SCHEMA = "finite-ram-lab.fr-fp-043-hosted-hysteresis-100/v0.1"

PHASE_HORIZON_ROUNDS = 100
SIZE_BYTES = _size_bytes(
    int(STATE_MIB)
)


def _plan_hysteretic(
    phases: list[dict[str, Any]],
) -> dict[str, Any]:
    current = set(
        phases[0]["warm_ids"]
    )
    targets = [
        set(current)
    ]
    transitions = []

    for phase_index in range(
        1,
        len(phases),
    ):
        phase = phases[
            phase_index
        ]
        candidate = set(
            phase["warm_ids"]
        )
        current_penalty = (
            _penalty_for_warm_set(
                phase["states"],
                sorted(current),
            )
        )
        candidate_penalty = (
            phase[
                "expected_cold_penalty_ms"
            ]
        )
        benefit_per_round = max(
            0.0,
            current_penalty
            - candidate_penalty,
        )
        benefit_over_horizon = (
            benefit_per_round
            * PHASE_HORIZON_ROUNDS
        )
        migration = (
            _migration_cost_ms(
                current,
                candidate,
            )
        )
        deadline_risk = (
            _max_deadline_risk_for_warm(
                phase["states"],
                current,
            )
        )
        deadline_safe = (
            deadline_risk
            <= MISS_TOLERANCE
            + 1e-12
        )
        must_migrate = (
            not deadline_safe
        )
        value_migrate = (
            candidate != current
            and benefit_over_horizon
            >= migration[
                "predicted_ms"
            ]
        )
        migrate = (
            must_migrate
            or value_migrate
        )

        before = set(current)

        if migrate:
            current = candidate

        targets.append(
            set(current)
        )
        transitions.append(
            {
                "from_phase": (
                    phase_index
                ),
                "to_phase": (
                    phase_index + 1
                ),
                "before_warm_ids": sorted(
                    before
                ),
                "candidate_warm_ids": sorted(
                    candidate
                ),
                "selected_warm_ids": sorted(
                    current
                ),
                "benefit_ms_per_round": (
                    benefit_per_round
                ),
                "benefit_over_horizon_ms": (
                    benefit_over_horizon
                ),
                "predicted_migration_ms": (
                    migration[
                        "predicted_ms"
                    ]
                ),
                "deadline_risk": (
                    deadline_risk
                ),
                "deadline_safe": (
                    deadline_safe
                ),
                "must_migrate": (
                    must_migrate
                ),
                "migrate_for_value": (
                    value_migrate
                ),
                "migrated": (
                    migrate
                ),
            }
        )

    return {
        "targets": targets,
        "transitions": transitions,
    }


def _prepare_paths(
    root: Path,
    *,
    initial_warm: set[int],
    marker_base: int,
) -> dict[int, Path]:
    paths: dict[int, Path] = {}

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
                marker_base
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
                in initial_warm
                else "COLD"
            ),
        )

    return paths


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


def _run_physical_policy(
    *,
    root: Path,
    phases: list[dict[str, Any]],
    targets: list[set[int]],
    marker_base: int,
    name: str,
) -> dict[str, Any]:
    paths = _prepare_paths(
        root,
        initial_warm=targets[0],
        marker_base=marker_base,
    )
    expected_resident_mib = (
        WARM_SLOTS
        * STATE_MIB
    )
    phase_rows = []
    transition_rows = []
    service_cost_ms = 0.0
    migration_cost_ms = 0.0
    total_actions = 0

    try:
        initial_snapshot = (
            _snapshot(
                paths,
                target_warm=(
                    targets[0]
                ),
            )
        )
        phase_rows.append(
            {
                "phase": 1,
                "warm_ids": sorted(
                    targets[0]
                ),
                "snapshot": (
                    initial_snapshot
                ),
            }
        )
        service_cost_ms += (
            _penalty_for_warm_set(
                phases[0]["states"],
                sorted(
                    targets[0]
                ),
            )
            * PHASE_HORIZON_ROUNDS
        )

        previous = set(
            targets[0]
        )

        for phase_index in range(
            1,
            len(phases),
        ):
            current = set(
                targets[
                    phase_index
                ]
            )
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
                    paths[state_id],
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

            elapsed_ns = (
                time.monotonic_ns()
                - started
            )
            elapsed_ms = (
                elapsed_ns
                / 1_000_000.0
            )
            migration_cost_ms += (
                elapsed_ms
            )
            total_actions += len(
                actuations
            )

            snapshot = _snapshot(
                paths,
                target_warm=current,
            )
            service = (
                _penalty_for_warm_set(
                    phases[
                        phase_index
                    ]["states"],
                    sorted(
                        current
                    ),
                )
                * PHASE_HORIZON_ROUNDS
            )
            service_cost_ms += (
                service
            )

            transition_rows.append(
                {
                    "from_phase": (
                        phase_index
                    ),
                    "to_phase": (
                        phase_index + 1
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
                        elapsed_ns
                    ),
                    "actuation_ms": (
                        elapsed_ms
                    ),
                    "actuations": (
                        actuations
                    ),
                    "snapshot": snapshot,
                }
            )
            phase_rows.append(
                {
                    "phase": (
                        phase_index + 1
                    ),
                    "warm_ids": sorted(
                        current
                    ),
                    "snapshot": (
                        snapshot
                    ),
                    "service_cost_ms": (
                        service
                    ),
                }
            )
            previous = current

        physical_checks = {
            "all_phase_warm_sets_match_targets": all(
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
            "every_phase_hits_40mib_residency": all(
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
            "every_warm_state_is_resident": all(
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
            "every_cold_state_is_nonresident": all(
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
        }

        return {
            "name": name,
            "targets": [
                sorted(target)
                for target in targets
            ],
            "phases": phase_rows,
            "transitions": (
                transition_rows
            ),
            "service_cost_ms": (
                service_cost_ms
            ),
            "observed_migration_cost_ms": (
                migration_cost_ms
            ),
            "observed_total_ms": (
                service_cost_ms
                + migration_cost_ms
            ),
            "physical_actions": (
                total_actions
            ),
            "migration_count": sum(
                bool(
                    row[
                        "changed_ids"
                    ]
                )
                for row in (
                    transition_rows
                )
            ),
            "physical_checks": (
                physical_checks
            ),
        }

    finally:
        _cleanup(
            paths
        )


def run_panel() -> dict[str, Any]:
    shadow = run_shadow_panel()

    if shadow["status"] != "PASS":
        raise RuntimeError(
            "shadow_parent_not_qualified"
        )

    phases = shadow[
        "phases"
    ]
    immediate_targets = [
        set(
            phase[
                "warm_ids"
            ]
        )
        for phase in phases
    ]
    plan = _plan_hysteretic(
        phases
    )
    hysteretic_targets = (
        plan["targets"]
    )

    with tempfile.TemporaryDirectory(
        prefix="fr-fp-043-immediate-"
    ) as immediate_tmp:
        immediate = (
            _run_physical_policy(
                root=Path(
                    immediate_tmp
                ),
                phases=phases,
                targets=(
                    immediate_targets
                ),
                marker_base=210,
                name=(
                    "IMMEDIATE_OPTIMUM"
                ),
            )
        )

    with tempfile.TemporaryDirectory(
        prefix="fr-fp-043-hysteretic-"
    ) as hysteretic_tmp:
        hysteretic = (
            _run_physical_policy(
                root=Path(
                    hysteretic_tmp
                ),
                phases=phases,
                targets=(
                    hysteretic_targets
                ),
                marker_base=230,
                name=(
                    "HYSTERETIC_100"
                ),
            )
        )

    planned_migrations = [
        row[
            "migrated"
        ]
        for row in plan[
            "transitions"
        ]
    ]

    checks = {
        "hundred_round_horizon_is_frozen": (
            PHASE_HORIZON_ROUNDS
            == 100
        ),
        "hysteresis_contains_both_hold_and_migrate": (
            any(
                planned_migrations
            )
            and any(
                not value
                for value in (
                    planned_migrations
                )
            )
        ),
        "planned_sequence_is_two_migrations_then_holds": (
            planned_migrations
            == [
                True,
                True,
                False,
                False,
            ]
        ),
        "immediate_physical_placement_passes": all(
            immediate[
                "physical_checks"
            ].values()
        ),
        "hysteretic_physical_placement_passes": all(
            hysteretic[
                "physical_checks"
            ].values()
        ),
        "hysteretic_executes_fewer_migrations": (
            hysteretic[
                "migration_count"
            ]
            < immediate[
                "migration_count"
            ]
        ),
        "hysteretic_executes_fewer_physical_actions": (
            hysteretic[
                "physical_actions"
            ]
            < immediate[
                "physical_actions"
            ]
        ),
        "hysteretic_service_cost_is_not_better_than_semantic_optimum": (
            hysteretic[
                "service_cost_ms"
            ]
            >= immediate[
                "service_cost_ms"
            ]
        ),
        "hysteretic_observed_total_beats_immediate_observed_total": (
            hysteretic[
                "observed_total_ms"
            ]
            < immediate[
                "observed_total_ms"
            ]
        ),
        "safety_never_forces_a_migration_on_fixture": all(
            row[
                "deadline_safe"
            ]
            for row in plan[
                "transitions"
            ]
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
            "HOSTED_PHYSICAL_MIXED_HOLD_MIGRATE_HYSTERESIS"
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
                WARM_SLOTS
                * STATE_MIB
            ),
            "phase_count": (
                len(phases)
            ),
            "phase_horizon_rounds": (
                PHASE_HORIZON_ROUNDS
            ),
        },
        "hysteresis_plan": (
            plan
        ),
        "immediate": (
            immediate
        ),
        "hysteretic": (
            hysteretic
        ),
        "checks": checks,
        "decision": (
            "PHYSICALLY_MIGRATE_ONLY_WHEN_EXPECTED_HORIZON_BENEFIT_AMORTIZES_MIGRATION_OR_SAFETY_REQUIRES_IT"
        ),
        "theory_update": [
            "migration-aware placement can contain both HOLD and MIGRATE regimes on one physical trace",
            "semantic service optimum and physical control optimum are not identical",
            "the validity horizon is a first-class control input",
        ],
        "next": (
            "MAKE_THE_VALIDITY_HORIZON_ITSELF_AN_UNCERTAIN_ESTIMATE_AND_REQUIRE_ROBUST_AMORTIZATION_BEFORE_MIGRATION"
        ),
        "claim_ceiling": (
            "HOSTED_PHYSICAL_100_ROUND_HYSTERESIS_ON_FP038_EQUAL_SIZE_FIVE_PHASE_FIXTURE_ONLY"
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
