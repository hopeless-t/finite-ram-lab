from __future__ import annotations

import json
from typing import Any

from finite_ram_lab.fr_fp_002_semantic_oom import (
    _episodes,
    _first_safe_step,
)
from finite_ram_lab.fr_fp_007_reclaimability_coverage import (
    simulate_always_preemptive,
)

SCHEMA = "finite-ram-lab.fr-fp-008-coverage-timing-frontier/v0.1"

QUALITY_SCALES = (
    1.00,
    0.40,
    0.30,
    0.25,
    0.20,
    0.18,
    0.17,
    0.16,
)

SAFE_SHIFTS = (
    0,
    2,
    4,
    6,
    8,
    10,
)


def _scaled(
    rows: list[float],
    scale: float,
) -> list[float]:
    return [
        value * scale
        for value in rows
    ]


def _cell(
    trajectories: list[list[float]],
    *,
    scale: float,
    safe_shift: int,
) -> dict[str, Any]:
    scaled = [
        _scaled(
            trajectory,
            scale,
        )
        for trajectory
        in trajectories
    ]

    safe_steps = [
        _first_safe_step(
            trajectory
        )
        for trajectory
        in scaled
    ]

    coverage = (
        sum(
            step is not None
            for step in safe_steps
        )
        / len(safe_steps)
    )

    results = [
        simulate_always_preemptive(
            trajectory,
            safe_shift=safe_shift,
        )
        for trajectory
        in scaled
    ]

    oom_rate = (
        sum(
            row[
                "semantic_oom"
            ]
            for row
            in results
        )
        / len(results)
    )

    return {
        "coverage": coverage,
        "semantic_oom_rate": (
            oom_rate
        ),
        "zero_oom": (
            oom_rate == 0.0
        ),
    }


def run_panel() -> dict[str, Any]:
    trajectories = [
        trajectory
        for _family, trajectory
        in _episodes()
    ]

    matrix: dict[str, Any] = {}

    for scale in QUALITY_SCALES:
        key = f"{scale:.2f}"
        matrix[key] = {}

        for shift in SAFE_SHIFTS:
            matrix[key][str(shift)] = (
                _cell(
                    trajectories,
                    scale=scale,
                    safe_shift=shift,
                )
            )

    baseline = matrix[
        "1.00"
    ][
        "0"
    ]

    timing_only = matrix[
        "1.00"
    ][
        "10"
    ]

    coverage_only = matrix[
        "0.16"
    ][
        "0"
    ]

    combined = matrix[
        "0.16"
    ][
        "8"
    ]

    first_full_coverage_scale = None

    for scale in QUALITY_SCALES:
        key = f"{scale:.2f}"

        if (
            matrix[key]["0"][
                "coverage"
            ]
            == 1.0
        ):
            first_full_coverage_scale = (
                scale
            )
            break

    zero_oom_cells = [
        {
            "quality_scale": (
                scale
            ),
            "safe_shift": shift,
        }
        for scale
        in QUALITY_SCALES
        for shift
        in SAFE_SHIFTS
        if matrix[
            f"{scale:.2f}"
        ][
            str(shift)
        ][
            "zero_oom"
        ]
    ]

    checks = {
        "baseline_matches_prior_coverage": (
            abs(
                baseline[
                    "coverage"
                ]
                - 0.806
            )
            < 1e-12
        ),
        "baseline_is_oom": (
            baseline[
                "semantic_oom_rate"
            ]
            > 0.99
        ),
        "timing_only_hits_coverage_floor": (
            abs(
                timing_only[
                    "semantic_oom_rate"
                ]
                - 0.194
            )
            < 1e-12
        ),
        "coverage_only_reaches_full_coverage": (
            coverage_only[
                "coverage"
            ]
            == 1.0
        ),
        "coverage_only_still_ooms": (
            coverage_only[
                "semantic_oom_rate"
            ]
            > 0.30
        ),
        "combined_repairs_oom": (
            combined[
                "coverage"
            ]
            == 1.0
            and combined[
                "semantic_oom_rate"
            ]
            == 0.0
        ),
        "first_full_coverage_scale_is_point16": (
            first_full_coverage_scale
            == 0.16
        ),
        "zero_oom_region_exists": (
            len(
                zero_oom_cells
            )
            > 0
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
            "SYNTHETIC_RECLAIMABILITY_COVERAGE_TIMING_INTERACTION_FRONTIER"
        ),
        "quality_scales": list(
            QUALITY_SCALES
        ),
        "safe_shifts": list(
            SAFE_SHIFTS
        ),
        "matrix": matrix,
        "reference_cells": {
            "baseline": baseline,
            "timing_only": (
                timing_only
            ),
            "coverage_only": (
                coverage_only
            ),
            "combined": combined,
        },
        "first_full_coverage_scale": (
            first_full_coverage_scale
        ),
        "zero_oom_cells": (
            zero_oom_cells
        ),
        "checks": checks,
        "decision": (
            "MODEL_RECLAIMABILITY_AS_JOINT_COVERAGE_AND_TIMING_NOT_ETA_ALONE"
        ),
        "primary_findings": [
            "TIMING_ONLY_CANNOT_CROSS_THE_NEVER_SAFE_COVERAGE_FLOOR",
            "FULL_RECLAIMABILITY_COVERAGE_ALONE_DOES_NOT_MEET_THE_DEADLINE",
            "JOINT_COVERAGE_AND_TIMING_IMPROVEMENT_CAN_CROSS_THE_FROZEN_DEADLINE_FRONTIER",
            "P_RECLAIMABLE_WITHIN_HORIZON_AND_ETA_RECLAIMABLE_ARE_SEPARATE_GOVERNOR_STATE_VARIABLES",
            "APPLICATION_SIDE_ENDPOINT_QUALITY_AND_SYSTEM_TRANSFER_GEOMETRY_INTERACT_NONLINEARLY",
        ],
        "claim_ceiling": (
            "SYNTHETIC_COVERAGE_TIMING_INTERACTION_ONLY"
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
