from __future__ import annotations

import json
import statistics
from typing import Any

from finite_ram_lab.fr_fp_002_semantic_oom import (
    _episodes,
    _first_safe_step,
)

SCHEMA = "finite-ram-lab.fr-fp-007-reclaimability-coverage/v0.1"

TRANSFER_LEAD = 4
HOT_BUDGET = 4
SAFE_SHIFTS = tuple(range(0, 11))


def simulate_always_preemptive(
    rows: list[float],
    *,
    safe_shift: int,
) -> dict[str, Any]:
    safe_step = _first_safe_step(rows)

    if safe_step is not None:
        safe_step = max(
            1,
            safe_step - safe_shift,
        )

    hot = 1
    cold = 0
    pending: list[int] = []
    semantic_oom = False
    cold_writes = 0
    peak_hot = 1

    for step in range(
        1,
        len(rows),
    ):
        next_pending = []

        for remaining in pending:
            remaining -= 1

            if remaining <= 0:
                hot -= 1
                cold += 1
                cold_writes += 1
            else:
                next_pending.append(
                    remaining
                )

        pending = next_pending
        hot += 1

        if (
            safe_step is not None
            and step >= safe_step
        ):
            hot = 1
            cold = 0
            pending = []
        else:
            available = (
                hot
                - 1
                - len(pending)
            )

            if available > 0:
                pending.append(
                    TRANSFER_LEAD
                )

        if hot > HOT_BUDGET:
            semantic_oom = True

        peak_hot = max(
            peak_hot,
            hot,
        )

    return {
        "semantic_oom": (
            semantic_oom
        ),
        "cold_writes": (
            cold_writes
        ),
        "peak_hot_states": (
            peak_hot
        ),
        "safe_step": safe_step,
    }


def _summary(
    trajectories: list[list[float]],
    *,
    safe_shift: int,
) -> dict[str, float]:
    rows = [
        simulate_always_preemptive(
            trajectory,
            safe_shift=safe_shift,
        )
        for trajectory in trajectories
    ]

    return {
        "semantic_oom_rate": (
            sum(
                row[
                    "semantic_oom"
                ]
                for row in rows
            )
            / len(rows)
        ),
        "mean_cold_writes": (
            statistics.fmean(
                row[
                    "cold_writes"
                ]
                for row in rows
            )
        ),
        "mean_peak_hot_states": (
            statistics.fmean(
                row[
                    "peak_hot_states"
                ]
                for row in rows
            )
        ),
    }


def run_panel() -> dict[str, Any]:
    trajectories = [
        trajectory
        for _family, trajectory
        in _episodes()
    ]

    safe_steps = [
        _first_safe_step(
            trajectory
        )
        for trajectory
        in trajectories
    ]

    never_safe = sum(
        step is None
        for step in safe_steps
    )
    never_safe_fraction = (
        never_safe
        / len(safe_steps)
    )

    observed_safe = [
        step
        for step in safe_steps
        if step is not None
    ]

    sweep = {
        str(shift): _summary(
            trajectories,
            safe_shift=shift,
        )
        for shift in SAFE_SHIFTS
    }

    baseline = sweep["0"]
    shift4 = sweep["4"]
    shift8 = sweep["8"]
    asymptotic = sweep["10"]

    checks = {
        "baseline_is_deadline_infeasible": (
            baseline[
                "semantic_oom_rate"
            ]
            > 0.99
        ),
        "timing_shift_reduces_oom": (
            shift4[
                "semantic_oom_rate"
            ]
            < baseline[
                "semantic_oom_rate"
            ]
            and shift8[
                "semantic_oom_rate"
            ]
            < shift4[
                "semantic_oom_rate"
            ]
        ),
        "never_safe_fraction_is_material": (
            never_safe_fraction
            > 0.15
        ),
        "large_timing_shift_hits_coverage_floor": (
            abs(
                asymptotic[
                    "semantic_oom_rate"
                ]
                - never_safe_fraction
            )
            < 1e-12
        ),
        "timing_alone_cannot_zero_oom": (
            asymptotic[
                "semantic_oom_rate"
            ]
            > 0.0
        ),
        "safe_coverage_is_complement": (
            abs(
                (
                    len(observed_safe)
                    / len(safe_steps)
                )
                + never_safe_fraction
                - 1.0
            )
            < 1e-12
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
            "SYNTHETIC_RECLAIMABILITY_TIMING_AND_COVERAGE_DECOMPOSITION"
        ),
        "transfer_lead": (
            TRANSFER_LEAD
        ),
        "hot_budget": (
            HOT_BUDGET
        ),
        "trajectories": len(
            trajectories
        ),
        "safe_reclaimability": {
            "observed": len(
                observed_safe
            ),
            "never_safe": (
                never_safe
            ),
            "coverage": (
                len(observed_safe)
                / len(safe_steps)
            ),
            "never_safe_fraction": (
                never_safe_fraction
            ),
            "mean_safe_step_when_observed": (
                statistics.fmean(
                    observed_safe
                )
            ),
            "min_safe_step": min(
                observed_safe
            ),
            "max_safe_step": max(
                observed_safe
            ),
        },
        "safe_shift_sweep": (
            sweep
        ),
        "checks": checks,
        "failure_domains": {
            "TIMING_GAP": (
                "safe reclaimability exists but arrives too late for the transfer deadline"
            ),
            "COVERAGE_GAP": (
                "no safe reclaimability event occurs inside the observed horizon"
            ),
        },
        "decision": (
            "SEPARATE_RECLAIMABILITY_TIMING_FROM_RECLAIMABILITY_COVERAGE"
        ),
        "primary_findings": [
            "EARLIER_SAFE_RECLAIMABILITY_REDUCES_SEMANTIC_OOM_WHEN_SAFE_STATE_EXISTS",
            "TIMING_ACCELERATION_ALONE_CANNOT_REPAIR_TRAJECTORIES_WITH_NO_SAFE_ENDPOINT",
            "THE_ASYMPTOTIC_OOM_FLOOR_EQUALS_THE_NEVER_SAFE_FRACTION_IN_THE_FROZEN_FIXTURE",
            "RECLAIMABILITY_COVERAGE_IS_A_DISTINCT_APPLICATION_CAPABILITY_AXIS",
            "PREDICTIVE_RESIDENCY_NEEDS_BOTH_ETA_AND_PROBABILITY_OR_COVERAGE_OF_SAFE_RECLAIMABILITY",
        ],
        "claim_ceiling": (
            "SYNTHETIC_RECLAIMABILITY_TIMING_AND_COVERAGE_DECOMPOSITION_ONLY"
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
