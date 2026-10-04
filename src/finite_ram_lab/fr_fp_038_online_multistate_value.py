from __future__ import annotations

import itertools
import json
from typing import Any

from finite_ram_lab.fr_fp_025_risk_aware_tier_frontier import (
    _build_empirical_priors,
    _deadline_risk,
    _expected_positive_penalty_ms,
    _load,
)
from finite_ram_lab.fr_fp_027_reuse_evidence_budget import (
    clopper_pearson_upper,
)

SCHEMA = "finite-ram-lab.fr-fp-038-online-multistate-value/v0.1"

STATE_COUNT = 10
STATE_MIB = 8.0
WARM_SLOTS = 5
HOSTED_BASELINE_MS = 3.299338
CONFIDENCE = 0.95
DEADLINE_MS = 25.0
MISS_TOLERANCE = 0.05
OBSERVATIONS_PER_PHASE = 20

PHASE_REUSE_INCREMENTS = (
    (0, 0, 1, 1, 2, 2, 3, 3, 4, 4),
    (8, 7, 6, 5, 4, 3, 2, 1, 0, 0),
    (0, 1, 2, 3, 4, 5, 6, 7, 8, 9),
    (5, 5, 5, 5, 5, 5, 5, 5, 5, 5),
    (7, 6, 5, 4, 3, 2, 1, 0, 0, 0),
)


def _shared_restore_model() -> dict[str, Any]:
    data = _load()
    priors = _build_empirical_priors(
        data["rows"]
    )
    residuals = priors["residual"]
    warm_ms = priors["warm_ms"]

    return {
        "conditional_penalty_ms": (
            _expected_positive_penalty_ms(
                baseline_ms=HOSTED_BASELINE_MS,
                residuals=residuals,
                warm_ms=warm_ms,
            )
        ),
        "conditional_deadline_risk": (
            _deadline_risk(
                baseline_ms=HOSTED_BASELINE_MS,
                residuals=residuals,
                deadline_ms=DEADLINE_MS,
            )
        ),
    }


def _state_rows(
    *,
    observations: int,
    reuse_counts: list[int],
    model: dict[str, Any],
) -> list[dict[str, Any]]:
    rows = []

    for state_id, reused in enumerate(
        reuse_counts
    ):
        upper = clopper_pearson_upper(
            reused=reused,
            observations=observations,
            confidence=CONFIDENCE,
        )
        expected_penalty = (
            upper
            * model[
                "conditional_penalty_ms"
            ]
        )
        deadline_risk = (
            upper
            * model[
                "conditional_deadline_risk"
            ]
        )
        rows.append(
            {
                "state_id": state_id,
                "observations": observations,
                "reuse_count": reused,
                "reuse_upper": upper,
                "expected_cold_penalty_ms": (
                    expected_penalty
                ),
                "value_density_ms_per_mib": (
                    expected_penalty
                    / STATE_MIB
                ),
                "unconditional_deadline_risk": (
                    deadline_risk
                ),
                "mandatory_warm": (
                    deadline_risk
                    > MISS_TOLERANCE
                ),
            }
        )

    return rows


def _allocate(
    states: list[dict[str, Any]],
) -> dict[str, Any]:
    mandatory = {
        row["state_id"]
        for row in states
        if row["mandatory_warm"]
    }

    if len(mandatory) > WARM_SLOTS:
        return {
            "feasible": False,
            "reason": (
                "MANDATORY_WARM_EXCEEDS_BUDGET"
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
        WARM_SLOTS
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
    }


def _exhaustive(
    states: list[dict[str, Any]],
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

    candidates = []

    for subset in itertools.combinations(
        range(STATE_COUNT),
        WARM_SLOTS,
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
        **best,
        "candidate_count": len(
            candidates
        ),
    }


def _penalty_for_warm_set(
    states: list[dict[str, Any]],
    warm_ids: list[int],
) -> float:
    warm = set(warm_ids)

    return sum(
        row[
            "expected_cold_penalty_ms"
        ]
        for row in states
        if row["state_id"]
        not in warm
    )


def run_panel() -> dict[str, Any]:
    model = _shared_restore_model()
    cumulative_counts = [
        0
        for _ in range(
            STATE_COUNT
        )
    ]
    observations = 0
    phases = []
    prior_warm: set[int] | None = None
    static_warm_ids: list[int] | None = None
    minimal_actions = 0
    full_reenforcement_actions = 0
    adaptive_penalty_sum = 0.0
    static_penalty_sum = 0.0

    for phase_index, increments in enumerate(
        PHASE_REUSE_INCREMENTS,
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
            states
        )
        exact = _exhaustive(
            states
        )

        if not greedy["feasible"]:
            raise RuntimeError(
                "unexpected_infeasible_phase"
            )

        warm = set(
            greedy["warm_ids"]
        )

        if static_warm_ids is None:
            static_warm_ids = list(
                greedy["warm_ids"]
            )

        adaptive_penalty = (
            greedy[
                "expected_cold_penalty_ms"
            ]
        )
        static_penalty = (
            _penalty_for_warm_set(
                states,
                static_warm_ids,
            )
        )
        adaptive_penalty_sum += (
            adaptive_penalty
        )
        static_penalty_sum += (
            static_penalty
        )

        if prior_warm is None:
            changed_ids: list[int] = []
        else:
            changed_ids = sorted(
                prior_warm
                ^ warm
            )
            minimal_actions += len(
                changed_ids
            )
            full_reenforcement_actions += (
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
                "warm_ids": (
                    greedy[
                        "warm_ids"
                    ]
                ),
                "cold_ids": (
                    greedy[
                        "cold_ids"
                    ]
                ),
                "changed_ids": (
                    changed_ids
                ),
                "actuation_count": len(
                    changed_ids
                ),
                "expected_cold_penalty_ms": (
                    adaptive_penalty
                ),
                "phase1_static_penalty_ms": (
                    static_penalty
                ),
                "max_cold_deadline_risk": (
                    greedy[
                        "max_cold_deadline_risk"
                    ]
                ),
                "matches_exhaustive": (
                    greedy["warm_ids"]
                    == exact["warm_ids"]
                    and abs(
                        adaptive_penalty
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
        prior_warm = warm

    action_reduction = (
        0.0
        if full_reenforcement_actions == 0
        else (
            1.0
            - minimal_actions
            / full_reenforcement_actions
        )
    )
    penalty_reduction = (
        1.0
        - adaptive_penalty_sum
        / static_penalty_sum
    )

    checks = {
        "five_online_phases": (
            len(phases) == 5
        ),
        "every_phase_matches_exhaustive": all(
            phase[
                "matches_exhaustive"
            ]
            for phase in phases
        ),
        "every_phase_uses_exactly_five_warm_slots": all(
            len(
                phase[
                    "warm_ids"
                ]
            )
            == WARM_SLOTS
            for phase in phases
        ),
        "every_cold_state_meets_deadline_tolerance": all(
            phase[
                "max_cold_deadline_risk"
            ]
            <= MISS_TOLERANCE
            + 1e-12
            for phase in phases
        ),
        "online_values_change_the_optimal_warm_set": (
            len(
                {
                    tuple(
                        phase[
                            "warm_ids"
                        ]
                    )
                    for phase in phases
                }
            )
            >= 3
        ),
        "at_least_one_new_evidence_phase_requires_zero_actuation": any(
            phase["phase"] > 1
            and phase[
                "actuation_count"
            ]
            == 0
            for phase in phases
        ),
        "minimal_delta_beats_full_reenforcement": (
            minimal_actions
            < full_reenforcement_actions
        ),
        "online_reallocation_beats_phase1_static_placement": (
            adaptive_penalty_sum
            < static_penalty_sum
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
            "ONLINE_REUSE_EVIDENCE_MULTI_STATE_FINITE_WARM_BUDGET_REALLOCATION"
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
            "phase_count": len(
                PHASE_REUSE_INCREMENTS
            ),
            "observations_added_per_phase_per_state": (
                OBSERVATIONS_PER_PHASE
            ),
            "confidence": CONFIDENCE,
            "deadline_ms": (
                DEADLINE_MS
            ),
            "miss_tolerance": (
                MISS_TOLERANCE
            ),
        },
        "shared_restore_model": (
            model
        ),
        "phases": phases,
        "summary": {
            "minimal_delta_actuations": (
                minimal_actions
            ),
            "full_reenforcement_actuations": (
                full_reenforcement_actions
            ),
            "actuation_reduction_fraction": (
                action_reduction
            ),
            "adaptive_expected_cold_penalty_sum_ms": (
                adaptive_penalty_sum
            ),
            "phase1_static_expected_cold_penalty_sum_ms": (
                static_penalty_sum
            ),
            "expected_penalty_reduction_fraction": (
                penalty_reduction
            ),
            "unique_warm_sets": len(
                {
                    tuple(
                        phase[
                            "warm_ids"
                        ]
                    )
                    for phase in phases
                }
            ),
        },
        "checks": checks,
        "decision": (
            "REALLOCATE_FINITE_WARM_CAPACITY_ONLY_WHEN_ONLINE_REUSE_EVIDENCE_CHANGES_THE_OPTIMAL_STATE_SET"
        ),
        "next": (
            "PHYSICALLY_ACTUATE_THE_ONLINE_VALUE_CHANGES_AND_VERIFY_ZERO_ACTION_ON_DECISION_IRRELEVANT_EVIDENCE_PHASES"
        ),
        "claim_ceiling": (
            "SYNTHETIC_FIVE_PHASE_ONLINE_REUSE_EVIDENCE_REALLOCATION_ON_ONE_TEN_STATE_EQUAL_SIZE_FIXTURE_ONLY"
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
