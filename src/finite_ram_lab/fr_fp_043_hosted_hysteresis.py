from __future__ import annotations

import json
import tempfile
import time
from pathlib import Path
from typing import Any

from finite_ram_lab.fr_fp_016_restore_size_scaling import (
    _fadvise_dontneed,
    _prepare_tier,
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
    _penalty_for_warm_set,
    run_panel as run_shadow_panel,
)
from finite_ram_lab.fr_fp_039_hosted_online_value import (
    SIZE_BYTES,
)
from finite_ram_lab.fr_fp_042_migration_hysteresis import (
    _max_deadline_risk_for_warm,
    _migration_cost_ms,
)

SCHEMA = "finite-ram-lab.fr-fp-043-hosted-hysteresis/v0.1"

VALIDITY_HORIZON_ROUNDS = 100


def _hysteretic_targets(
    phases: list[dict[str, Any]],
) -> tuple[
    list[set[int]],
    list[dict[str, Any]],
]:
    current = set(
        phases[0]["warm_ids"]
    )
    targets = [
        set(current)
    ]
    decisions = []

    for index in range(
        1,
        len(phases),
    ):
        phase = phases[index]
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
        benefit_horizon = (
            benefit_per_round
            * VALIDITY_HORIZON_ROUNDS
        )
        migration = (
            _migration_cost_ms(
                current,
                candidate,
            )
        )
        current_risk = (
            _max_deadline_risk_for_warm(
                phase["states"],
                current,
            )
        )
        must_move = (
            current_risk
            > MISS_TOLERANCE
            + 1e-12
        )
        move_for_value = (
            candidate != current
            and benefit_horizon
            >= migration[
                "predicted_ms"
            ]
        )
        move = (
            must_move
            or move_for_value
        )

        before = set(current)

        if move:
            current = set(
                candidate
            )

        decisions.append(
            {
                "from_phase": index,
                "to_phase": index + 1,
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
                    benefit_horizon
                ),
                "predicted_migration_ms": (
                    migration[
                        "predicted_ms"
                    ]
                ),
                "current_deadline_risk": (
                    current_risk
                ),
                "must_migrate_for_safety": (
                    must_move
                ),
                "migrate_for_value": (
                    move_for_value
                ),
                "migrated": move,
            }
        )
        targets.append(
            set(current)
        )

    return targets, decisions


def _run_physical_arm(
    *,
    root: Path,
    arm: str,
    targets: list[set[int]],
) -> dict[str, Any]:
    paths: dict[
        int,
        Path,
    ] = {}
    initial = targets[0]

    for state_id in range(
        STATE_COUNT
    ):
        path = root / (
            f"{arm.lower()}-{state_id}.bin"
        )
        prepared = _prepare_tier(
            path,
            size_bytes=SIZE_BYTES,
            marker=(
                210
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
                f"prepare_failed:{arm}:{state_id}"
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
            "snapshot": _snapshot(
                paths,
                target_warm=initial,
            ),
        }
    ]
    transitions = []
    total_actions = 0
    total_actuation_ns = 0
    total_prefetch_bytes = 0
    previous = set(
        initial
    )

    try:
        for index in range(
            1,
            len(targets),
        ):
            current = targets[index]
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
                total_prefetch_bytes += int(
                    row[
                        "prefetch_bytes"
                    ]
                )

            elapsed = (
                time.monotonic_ns()
                - started
            )
            total_actions += len(
                actuations
            )
            total_actuation_ns += (
                elapsed
            )
            after = _snapshot(
                paths,
                target_warm=current,
            )

            transitions.append(
                {
                    "from_phase": index,
                    "to_phase": index + 1,
                    "changed_ids": (
                        changed
                    ),
                    "actuation_count": (
                        len(actuations)
                    ),
                    "actuation_ns": (
                        elapsed
                    ),
                    "actuations": (
                        actuations
                    ),
                    "after": after,
                }
            )
            phase_rows.append(
                {
                    "phase": index + 1,
                    "warm_ids": sorted(
                        current
                    ),
                    "snapshot": after,
                }
            )
            previous = set(
                current
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

    return {
        "arm": arm,
        "phases": phase_rows,
        "transitions": transitions,
        "physical_actions": (
            total_actions
        ),
        "actuation_ns": (
            total_actuation_ns
        ),
        "prefetch_bytes": (
            total_prefetch_bytes
        ),
    }


def _service_cost_ms(
    phases: list[dict[str, Any]],
    targets: list[set[int]],
) -> float:
    return sum(
        _penalty_for_warm_set(
            phase["states"],
            sorted(target),
        )
        * VALIDITY_HORIZON_ROUNDS
        for phase, target
        in zip(
            phases,
            targets,
        )
    )


def run_panel() -> dict[str, Any]:
    shadow = run_shadow_panel()

    if shadow["status"] != "PASS":
        raise RuntimeError(
            "shadow_parent_not_qualified"
        )

    phases = shadow["phases"]
    immediate_targets = [
        set(
            phase["warm_ids"]
        )
        for phase in phases
    ]
    (
        hysteretic_targets,
        decisions,
    ) = _hysteretic_targets(
        phases
    )

    with tempfile.TemporaryDirectory(
        prefix="fr-fp-043-"
    ) as tmp:
        root = Path(tmp)
        immediate = _run_physical_arm(
            root=root,
            arm="IMMEDIATE_OPTIMUM",
            targets=immediate_targets,
        )
        hysteretic = _run_physical_arm(
            root=root,
            arm="HYSTERETIC",
            targets=hysteretic_targets,
        )

    immediate_service = (
        _service_cost_ms(
            phases,
            immediate_targets,
        )
    )
    hysteretic_service = (
        _service_cost_ms(
            phases,
            hysteretic_targets,
        )
    )
    immediate_actuation_ms = (
        immediate[
            "actuation_ns"
        ]
        / 1_000_000.0
    )
    hysteretic_actuation_ms = (
        hysteretic[
            "actuation_ns"
        ]
        / 1_000_000.0
    )
    immediate_hybrid_total = (
        immediate_service
        + immediate_actuation_ms
    )
    hysteretic_hybrid_total = (
        hysteretic_service
        + hysteretic_actuation_ms
    )

    expected_hysteretic_sets = (
        [
            [4, 6, 7, 8, 9],
            [0, 1, 2, 3, 4],
            [4, 6, 7, 8, 9],
            [4, 6, 7, 8, 9],
            [4, 6, 7, 8, 9],
        ]
    )

    checks = {
        "shadow_parent_passes": (
            shadow["status"]
            == "PASS"
        ),
        "hysteretic_policy_contains_both_migrate_and_hold": (
            any(
                row["migrated"]
                for row in decisions
            )
            and any(
                not row["migrated"]
                for row in decisions
            )
        ),
        "hysteretic_target_sets_match_frozen_h100_expectation": (
            [
                sorted(target)
                for target
                in hysteretic_targets
            ]
            == expected_hysteretic_sets
        ),
        "immediate_uses_twenty_four_physical_actions": (
            immediate[
                "physical_actions"
            ]
            == 24
        ),
        "hysteretic_uses_sixteen_physical_actions": (
            hysteretic[
                "physical_actions"
            ]
            == 16
        ),
        "hysteresis_reduces_physical_actions": (
            hysteretic[
                "physical_actions"
            ]
            < immediate[
                "physical_actions"
            ]
        ),
        "both_arms_keep_exact_five_slot_residency": all(
            abs(
                phase[
                    "snapshot"
                ][
                    "resident_mib"
                ]
                - 40.0
            )
            <= 0.5
            for arm in (
                immediate,
                hysteretic,
            )
            for phase in arm[
                "phases"
            ]
        ),
        "all_warm_states_are_resident": all(
            phase[
                "snapshot"
            ][
                "warm_min_residency"
            ]
            is not None
            and phase[
                "snapshot"
            ][
                "warm_min_residency"
            ]
            >= 0.95
            for arm in (
                immediate,
                hysteretic,
            )
            for phase in arm[
                "phases"
            ]
        ),
        "all_cold_states_are_nonresident": all(
            phase[
                "snapshot"
            ][
                "cold_max_residency"
            ]
            is not None
            and phase[
                "snapshot"
            ][
                "cold_max_residency"
            ]
            <= 0.10
            for arm in (
                immediate,
                hysteretic,
            )
            for phase in arm[
                "phases"
            ]
        ),
        "hysteretic_observed_actuation_time_is_lower": (
            hysteretic_actuation_ms
            < immediate_actuation_ms
        ),
        "hysteretic_hybrid_total_is_lower_on_h100_fixture": (
            hysteretic_hybrid_total
            < immediate_hybrid_total
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
            "HOSTED_PHYSICAL_HYSTERETIC_WARM_PLACEMENT_WITH_MIGRATE_AND_HOLD_REGIMES"
        ),
        "fixture": {
            "validity_horizon_rounds": (
                VALIDITY_HORIZON_ROUNDS
            ),
            "state_count": (
                STATE_COUNT
            ),
            "state_mib": (
                STATE_MIB
            ),
            "warm_slots": 5,
        },
        "decisions": decisions,
        "immediate": {
            **immediate,
            "service_cost_ms": (
                immediate_service
            ),
            "actuation_ms": (
                immediate_actuation_ms
            ),
            "hybrid_total_ms": (
                immediate_hybrid_total
            ),
        },
        "hysteretic": {
            **hysteretic,
            "service_cost_ms": (
                hysteretic_service
            ),
            "actuation_ms": (
                hysteretic_actuation_ms
            ),
            "hybrid_total_ms": (
                hysteretic_hybrid_total
            ),
        },
        "checks": checks,
        "decision": (
            "PHYSICALLY_MIGRATE_ONLY_WHEN_CROSS_VALIDATED_MIGRATION_COST_CAN_BE_AMORTIZED_WITHIN_THE_EXPECTED_VALIDITY_HORIZON"
        ),
        "evidence_boundary": (
            "Physical tier actuation and residency are hosted observations. "
            "Service penalties and the 100-round validity horizon remain model inputs."
        ),
        "next": (
            "ESTIMATE_PLACEMENT_VALIDITY_HORIZON_FROM_ONLINE_CHANGE_EVIDENCE_INSTEAD_OF_SUPPLYING_IT_AS_AN_ORACLE"
        ),
        "claim_ceiling": (
            "HOSTED_PHYSICAL_HYSTERESIS_ON_ONE_FIVE_PHASE_EQUAL_SIZE_FIXED_CAPACITY_H100_FIXTURE_ONLY"
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
