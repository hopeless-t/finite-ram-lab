from __future__ import annotations

import itertools
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
    OBSERVATIONS_PER_PHASE,
    PHASE_REUSE_INCREMENTS,
    STATE_COUNT,
    STATE_MIB,
    _shared_restore_model,
    _state_rows,
)
from finite_ram_lab.fr_fp_039_hosted_online_value import (
    SIZE_BYTES,
)

SCHEMA = "finite-ram-lab.fr-fp-040-hosted-capacity-value-governor/v0.1"

CAPACITY_SCHEDULE = (
    5,
    3,
    7,
    4,
    6,
)


def _allocate(
    states: list[dict[str, Any]],
    *,
    warm_slots: int,
) -> dict[str, Any]:
    mandatory = {
        row["state_id"]
        for row in states
        if row["mandatory_warm"]
    }

    if len(mandatory) > warm_slots:
        return {
            "feasible": False,
            "reason": (
                "MANDATORY_WARM_EXCEEDS_BUDGET"
            ),
            "mandatory_count": (
                len(mandatory)
            ),
        }

    optional = [
        row
        for row in states
        if row["state_id"]
        not in mandatory
    ]
    optional.sort(
        key=lambda row: (
            -row[
                "value_density_ms_per_mib"
            ],
            row["state_id"],
        )
    )

    remaining = (
        warm_slots
        - len(mandatory)
    )
    warm = (
        mandatory
        | {
            row["state_id"]
            for row
            in optional[:remaining]
        }
    )
    cold = [
        row
        for row in states
        if row["state_id"]
        not in warm
    ]

    return {
        "feasible": True,
        "warm_ids": sorted(warm),
        "cold_ids": sorted(
            row["state_id"]
            for row in cold
        ),
        "expected_cold_penalty_ms": sum(
            row[
                "expected_cold_penalty_ms"
            ]
            for row in cold
        ),
        "max_cold_deadline_risk": (
            0.0
            if not cold
            else max(
                row[
                    "unconditional_deadline_risk"
                ]
                for row in cold
            )
        ),
        "mandatory_count": (
            len(mandatory)
        ),
    }


def _exhaustive(
    states: list[dict[str, Any]],
    *,
    warm_slots: int,
) -> dict[str, Any]:
    mandatory = {
        row["state_id"]
        for row in states
        if row["mandatory_warm"]
    }
    by_id = {
        row["state_id"]: row
        for row in states
    }

    if len(mandatory) > warm_slots:
        return {
            "feasible": False,
            "reason": (
                "MANDATORY_WARM_EXCEEDS_BUDGET"
            ),
            "mandatory_count": (
                len(mandatory)
            ),
        }

    candidates = []

    for subset in itertools.combinations(
        range(STATE_COUNT),
        warm_slots,
    ):
        warm = set(subset)

        if not mandatory.issubset(
            warm
        ):
            continue

        cold_ids = [
            state_id
            for state_id
            in range(STATE_COUNT)
            if state_id not in warm
        ]
        penalty = sum(
            by_id[state_id][
                "expected_cold_penalty_ms"
            ]
            for state_id
            in cold_ids
        )
        candidates.append(
            {
                "warm_ids": sorted(warm),
                "expected_cold_penalty_ms": (
                    penalty
                ),
            }
        )

    best = min(
        candidates,
        key=lambda row: (
            row[
                "expected_cold_penalty_ms"
            ],
            row["warm_ids"],
        ),
    )

    return {
        "feasible": True,
        **best,
        "candidate_count": len(
            candidates
        ),
    }


def _shadow() -> dict[str, Any]:
    model = _shared_restore_model()
    cumulative_counts = [
        0
        for _ in range(
            STATE_COUNT
        )
    ]
    observations = 0
    phases = []
    previous: set[int] | None = None
    minimal_actions = 0
    full_actions = 0

    for phase_index, (
        increments,
        warm_slots,
    ) in enumerate(
        zip(
            PHASE_REUSE_INCREMENTS,
            CAPACITY_SCHEDULE,
        ),
        start=1,
    ):
        observations += (
            OBSERVATIONS_PER_PHASE
        )
        cumulative_counts = [
            old + delta
            for old, delta
            in zip(
                cumulative_counts,
                increments,
            )
        ]

        states = _state_rows(
            observations=observations,
            reuse_counts=(
                cumulative_counts
            ),
            model=model,
        )
        greedy = _allocate(
            states,
            warm_slots=warm_slots,
        )
        exact = _exhaustive(
            states,
            warm_slots=warm_slots,
        )

        if not greedy[
            "feasible"
        ]:
            raise RuntimeError(
                f"unexpected_infeasible_phase:{phase_index}"
            )

        warm = set(
            greedy["warm_ids"]
        )

        changed = (
            []
            if previous is None
            else sorted(
                previous
                ^ warm
            )
        )

        if previous is not None:
            minimal_actions += len(
                changed
            )
            full_actions += (
                STATE_COUNT
            )

        phases.append(
            {
                "phase": phase_index,
                "observations_per_state": (
                    observations
                ),
                "reuse_counts": list(
                    cumulative_counts
                ),
                "warm_slots": warm_slots,
                "warm_mib": (
                    warm_slots
                    * STATE_MIB
                ),
                "warm_ids": (
                    greedy["warm_ids"]
                ),
                "cold_ids": (
                    greedy["cold_ids"]
                ),
                "changed_ids": (
                    changed
                ),
                "actuation_count": (
                    len(changed)
                ),
                "expected_cold_penalty_ms": (
                    greedy[
                        "expected_cold_penalty_ms"
                    ]
                ),
                "max_cold_deadline_risk": (
                    greedy[
                        "max_cold_deadline_risk"
                    ]
                ),
                "mandatory_count": (
                    greedy[
                        "mandatory_count"
                    ]
                ),
                "matches_exhaustive": (
                    exact["feasible"]
                    and greedy[
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
                ),
                "candidate_count": (
                    exact[
                        "candidate_count"
                    ]
                ),
                "states": states,
            }
        )
        previous = warm

    return {
        "model": model,
        "phases": phases,
        "summary": {
            "minimal_delta_actuations": (
                minimal_actions
            ),
            "full_reenforcement_actuations": (
                full_actions
            ),
            "actuation_reduction_fraction": (
                0.0
                if full_actions == 0
                else (
                    1.0
                    - minimal_actions
                    / full_actions
                )
            ),
        },
    }


def run_panel() -> dict[str, Any]:
    shadow = _shadow()
    shadow_phases = shadow[
        "phases"
    ]
    targets = [
        set(
            row["warm_ids"]
        )
        for row in shadow_phases
    ]

    with tempfile.TemporaryDirectory(
        prefix="fr-fp-040-"
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
                "warm_slots": (
                    shadow_phases[0][
                        "warm_slots"
                    ]
                ),
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
        previous = initial
        total_actions = 0
        total_prefetch_bytes = 0

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

                after = _snapshot(
                    paths,
                    target_warm=current,
                )
                expected_mib = (
                    shadow_phases[
                        phase_index
                    ][
                        "warm_mib"
                    ]
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
                        "from_warm_slots": (
                            shadow_phases[
                                phase_index
                                - 1
                            ][
                                "warm_slots"
                            ]
                        ),
                        "to_warm_slots": (
                            shadow_phases[
                                phase_index
                            ][
                                "warm_slots"
                            ]
                        ),
                        "changed_ids": (
                            changed
                        ),
                        "actuation_count": (
                            len(actuations)
                        ),
                        "actuation_ns": (
                            elapsed
                        ),
                        "expected_resident_mib": (
                            expected_mib
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
                        "warm_slots": (
                            shadow_phases[
                                phase_index
                            ][
                                "warm_slots"
                            ]
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

    full_actions = (
        (
            len(targets)
            - 1
        )
        * STATE_COUNT
    )

    checks = {
        "five_combined_phases": (
            len(phase_rows) == 5
        ),
        "every_shadow_phase_matches_exhaustive": all(
            row[
                "matches_exhaustive"
            ]
            for row in shadow_phases
        ),
        "physical_warm_sets_match_combined_shadow": all(
            set(
                row["warm_ids"]
            )
            == targets[index]
            for index, row
            in enumerate(
                phase_rows
            )
        ),
        "physical_resident_bytes_match_phase_capacity": all(
            abs(
                row[
                    "snapshot"
                ][
                    "resident_mib"
                ]
                - (
                    row[
                        "warm_slots"
                    ]
                    * STATE_MIB
                )
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
        "physical_actions_match_combined_shadow": (
            total_actions
            == shadow[
                "summary"
            ][
                "minimal_delta_actuations"
            ]
        ),
        "minimal_delta_beats_full_reenforcement": (
            total_actions
            < full_actions
        ),
        "every_transition_touches_only_changed_states": all(
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
            "HOSTED_PHYSICAL_COMBINED_DYNAMIC_CAPACITY_AND_ONLINE_STATE_VALUE_GOVERNOR"
        ),
        "fixture": {
            "state_count": (
                STATE_COUNT
            ),
            "state_mib": (
                STATE_MIB
            ),
            "phase_count": 5,
            "capacity_schedule_slots": list(
                CAPACITY_SCHEDULE
            ),
            "capacity_schedule_mib": [
                value * STATE_MIB
                for value in (
                    CAPACITY_SCHEDULE
                )
            ],
            "observations_added_per_phase_per_state": (
                OBSERVATIONS_PER_PHASE
            ),
        },
        "shadow": shadow,
        "phases": phase_rows,
        "transitions": (
            transition_rows
        ),
        "summary": {
            "physical_actuations": (
                total_actions
            ),
            "full_reenforcement_actuations": (
                full_actions
            ),
            "actuation_reduction_fraction": (
                1.0
                - total_actions
                / full_actions
            ),
            "prefetch_bytes": (
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
            "warm_sets": [
                row[
                    "warm_ids"
                ]
                for row in phase_rows
            ],
        },
        "checks": checks,
        "decision": (
            "RECOMPUTE_THE_OPTIMAL_MULTI_STATE_WARM_SET_FROM_CURRENT_CAPACITY_AND_CURRENT_SEMANTIC_VALUE_THEN_PHYSICALLY_ACTUATE_ONLY_THE_SET_DIFFERENCE"
        ),
        "meta_transfer": (
            "capacity changes and semantic-value changes collapse to the same downstream primitive: compare old and new admissible decisions, then execute only the decision delta"
        ),
        "next": (
            "INTRODUCE_ACTUATION_COST_HYSTERESIS_SO_SMALL_VALUE_CHANGES_DO_NOT_THRASH_PHYSICAL_PLACEMENT"
        ),
        "claim_ceiling": (
            "HOSTED_PHYSICAL_COMBINED_CAPACITY_VALUE_CONTROL_ON_ONE_TEN_STATE_EQUAL_SIZE_FIVE_PHASE_FIXTURE_ONLY"
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
