from __future__ import annotations

import json
import math
import tempfile
from pathlib import Path
from typing import Any

from finite_ram_lab.fr_fp_054_endogenous_resident_budget import (
    run_panel as _shadow_panel,
)
from finite_ram_lab.fr_fp_055_hosted_endogenous_residency import (
    _run_rent_arm,
)
from finite_ram_lab.fr_fp_056_physical_resident_pareto import (
    _dominates,
    _load as _load_physical_anchors,
)

SCHEMA = "finite-ram-lab.fr-fp-057-decision-directed-physical-refinement/v0.1"

NEW_PHYSICAL_RENTS = (
    0.075,
    0.15,
    0.20,
    0.30,
)

EXISTING_PHYSICAL_RENTS = (
    0.0,
    0.10,
    0.25,
    0.40,
)


def _signature(
    shadow_row: dict[str, Any],
) -> str:
    return "|".join(
        ",".join(
            str(state_id)
            for state_id
            in phase[
                "warm_ids"
            ]
        )
        for phase in shadow_row[
            "rows"
        ]
    )


def _base_time_ms(
    row: dict[str, Any],
) -> float:
    return (
        float(
            row[
                "semantic_service_ms"
            ]
        )
        + float(
            row[
                "physical_actuation_ms"
            ]
        )
    )


def _pareto(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        row
        for row in rows
        if not any(
            _dominates(
                other,
                row,
            )
            for other in rows
            if other is not row
        )
    ]


def _select(
    rows: list[dict[str, Any]],
    *,
    memory_rent: float,
) -> dict[str, Any]:
    return min(
        rows,
        key=lambda row: (
            _base_time_ms(
                row
            )
            + memory_rent
            * float(
                row[
                    "resident_mib_round"
                ]
            ),
            float(
                row[
                    "resident_mib_round"
                ]
            ),
            row[
                "path_id"
            ],
        ),
    )


def _selection_intervals(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    breakpoints = {
        0.0,
    }

    for index, left in enumerate(
        rows
    ):
        left_resident = float(
            left[
                "resident_mib_round"
            ]
        )
        left_base = _base_time_ms(
            left
        )

        for right in rows[
            index + 1:
        ]:
            right_resident = float(
                right[
                    "resident_mib_round"
                ]
            )
            right_base = (
                _base_time_ms(
                    right
                )
            )
            resident_delta = (
                left_resident
                - right_resident
            )

            if abs(
                resident_delta
            ) <= 1e-12:
                continue

            crossing = (
                right_base
                - left_base
            ) / resident_delta

            if crossing > 0.0:
                breakpoints.add(
                    float(
                        crossing
                    )
                )

    ordered = sorted(
        breakpoints
    )

    probes = []

    for left, right in zip(
        ordered[:-1],
        ordered[1:],
    ):
        probes.append(
            (
                left,
                right,
                (
                    left
                    + right
                )
                / 2.0,
            )
        )

    probes.append(
        (
            ordered[-1],
            None,
            ordered[-1]
            + max(
                1.0,
                ordered[-1],
            ),
        )
    )

    raw = []

    for lower, upper, probe in probes:
        selected = _select(
            rows,
            memory_rent=probe,
        )
        raw.append(
            {
                "lower_inclusive": (
                    lower
                ),
                "upper_exclusive": (
                    upper
                ),
                "path_id": (
                    selected[
                        "path_id"
                    ]
                ),
            }
        )

    merged = []

    for row in raw:
        if (
            merged
            and merged[-1][
                "path_id"
            ]
            == row[
                "path_id"
            ]
        ):
            merged[-1][
                "upper_exclusive"
            ] = row[
                "upper_exclusive"
            ]
        else:
            merged.append(
                dict(row)
            )

    # Drop zero-width or numerically unreachable intervals.
    return [
        row
        for row in merged
        if (
            row[
                "upper_exclusive"
            ]
            is None
            or row[
                "upper_exclusive"
            ]
            - row[
                "lower_inclusive"
            ]
            > 1e-12
        )
    ]


def run_panel() -> dict[str, Any]:
    shadow = _shadow_panel()
    physical_anchor_data = (
        _load_physical_anchors()
    )

    shadow_by_rent = {
        float(
            row[
                "memory_rent_ms_per_mib_round"
            ]
        ): row
        for row in shadow[
            "sweeps"
        ]
    }

    signature_groups: dict[
        str,
        list[float],
    ] = {}

    for rent, row in (
        shadow_by_rent.items()
    ):
        signature_groups.setdefault(
            _signature(row),
            [],
        ).append(
            rent
        )

    signatures = sorted(
        signature_groups
    )
    path_id_by_signature = {
        signature: (
            f"P{index}"
        )
        for index, signature
        in enumerate(
            signatures
        )
    }

    physically_covered_signatures = {
        _signature(
            shadow_by_rent[
                rent
            ]
        )
        for rent in (
            EXISTING_PHYSICAL_RENTS
        )
    }

    missing_signatures = (
        set(signatures)
        - physically_covered_signatures
    )

    selected_new_signatures = {
        _signature(
            shadow_by_rent[
                rent
            ]
        )
        for rent in (
            NEW_PHYSICAL_RENTS
        )
    }

    with tempfile.TemporaryDirectory(
        prefix="fr-fp-057-"
    ) as tmp:
        root = Path(tmp)
        new_arms = [
            _run_rent_arm(
                root,
                rent=rent,
                shadow=(
                    shadow_by_rent[
                        rent
                    ]
                ),
            )
            for rent in (
                NEW_PHYSICAL_RENTS
            )
        ]

    existing_by_rent = {
        float(
            row[
                "memory_rent_ms_per_mib_round"
            ]
        ): row
        for row in (
            physical_anchor_data[
                "points"
            ]
        )
    }

    points = []

    for rent in (
        EXISTING_PHYSICAL_RENTS
    ):
        shadow_row = (
            shadow_by_rent[
                rent
            ]
        )
        physical = (
            existing_by_rent[
                rent
            ]
        )
        signature = (
            _signature(
                shadow_row
            )
        )
        points.append(
            {
                "path_id": (
                    path_id_by_signature[
                        signature
                    ]
                ),
                "representative_rent": (
                    rent
                ),
                "all_shadow_rents_for_path": sorted(
                    signature_groups[
                        signature
                    ]
                ),
                "signature": signature,
                "resident_mib_round": float(
                    physical[
                        "resident_mib_round"
                    ]
                ),
                "semantic_service_ms": float(
                    physical[
                        "semantic_service_ms"
                    ]
                ),
                "physical_actuation_ms": float(
                    physical[
                        "physical_actuation_ms"
                    ]
                ),
                "evidence": (
                    "EXISTING_HOSTED_PHYSICAL"
                ),
            }
        )

    for rent, arm in zip(
        NEW_PHYSICAL_RENTS,
        new_arms,
    ):
        shadow_row = (
            shadow_by_rent[
                rent
            ]
        )
        signature = (
            _signature(
                shadow_row
            )
        )
        points.append(
            {
                "path_id": (
                    path_id_by_signature[
                        signature
                    ]
                ),
                "representative_rent": (
                    rent
                ),
                "all_shadow_rents_for_path": sorted(
                    signature_groups[
                        signature
                    ]
                ),
                "signature": signature,
                "resident_mib_round": float(
                    arm[
                        "physical_resident_mib_round"
                    ]
                ),
                "semantic_service_ms": float(
                    shadow_row[
                        "service_ms"
                    ]
                ),
                "physical_actuation_ms": float(
                    arm[
                        "physical_actuation_ms"
                    ]
                ),
                "evidence": (
                    "NEW_HOSTED_PHYSICAL"
                ),
                "physical_actions": int(
                    arm[
                        "physical_actions"
                    ]
                ),
                "prefetch_bytes": int(
                    arm[
                        "prefetch_bytes"
                    ]
                ),
                "physical_used_mib": (
                    arm[
                        "physical_used_mib"
                    ]
                ),
                "shadow_used_mib": (
                    arm[
                        "shadow_used_mib"
                    ]
                ),
            }
        )

    points.sort(
        key=lambda row: (
            -float(
                row[
                    "resident_mib_round"
                ]
            ),
            row[
                "path_id"
            ],
        )
    )

    pareto = _pareto(
        points
    )
    intervals = (
        _selection_intervals(
            points
        )
    )

    old_points = [
        row
        for row in points
        if row[
            "evidence"
        ]
        == "EXISTING_HOSTED_PHYSICAL"
    ]

    old_intervals = (
        _selection_intervals(
            old_points
        )
    )

    changed_intervals = [
        row
        for row in intervals
        if row[
            "path_id"
        ]
        not in {
            item[
                "path_id"
            ]
            for item
            in old_intervals
        }
    ]

    physical_match = all(
        all(
            abs(
                float(observed)
                - float(expected)
            )
            <= 0.75
            for observed, expected
            in zip(
                arm[
                    "physical_used_mib"
                ],
                arm[
                    "shadow_used_mib"
                ],
            )
        )
        for arm in new_arms
    )

    checks = {
        "shadow_parent_passes": (
            shadow[
                "status"
            ]
            == "PASS"
        ),
        "twelve_rent_points_collapse_to_eight_unique_paths": (
            len(
                signature_groups
            )
            == 8
        ),
        "four_existing_physical_paths": (
            len(
                physically_covered_signatures
            )
            == 4
        ),
        "exactly_four_unique_paths_remain_unmeasured": (
            len(
                missing_signatures
            )
            == 4
        ),
        "selected_new_rents_cover_every_missing_path_exactly_once": (
            selected_new_signatures
            == missing_signatures
            and len(
                NEW_PHYSICAL_RENTS
            )
            == len(
                missing_signatures
            )
        ),
        "new_physical_residency_matches_shadow_path": (
            physical_match
        ),
        "all_eight_unique_paths_have_physical_evidence": (
            len(
                {
                    row[
                        "signature"
                    ]
                    for row
                    in points
                }
            )
            == 8
        ),
        "pareto_frontier_is_nonempty": (
            bool(
                pareto
            )
        ),
        "explicit_rent_lower_envelope_is_nonempty": (
            bool(
                intervals
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
            "DECISION_DIRECTED_HOSTED_PHYSICAL_COMPLETION_OF_UNIQUE_RESIDENT_POLICY_PATHS"
        ),
        "source": {
            "shadow_rent_points": (
                len(
                    shadow_by_rent
                )
            ),
            "unique_shadow_paths": (
                len(
                    signature_groups
                )
            ),
            "existing_physical_paths": (
                len(
                    physically_covered_signatures
                )
            ),
            "new_physical_paths": (
                len(
                    new_arms
                )
            ),
        },
        "new_physical_representative_rents": list(
            NEW_PHYSICAL_RENTS
        ),
        "points": points,
        "pareto_path_ids": [
            row[
                "path_id"
            ]
            for row in pareto
        ],
        "explicit_memory_rent_selection_intervals": (
            intervals
        ),
        "previous_four_anchor_selection_intervals": (
            old_intervals
        ),
        "new_paths_that_enter_scalar_lower_envelope": (
            sorted(
                {
                    row[
                        "path_id"
                    ]
                    for row
                    in changed_intervals
                }
            )
        ),
        "scalar_gain": None,
        "checks": checks,
        "decision": (
            "PHYSICALLY_MEASURE_EACH_DECISION_RELEVANT_UNIQUE_POLICY_PATH_ONCE_AND_NEVER_DUPLICATE_EQUIVALENT_RENT_POINTS"
        ),
        "meta_transfer": (
            "experiment acquisition is itself residency-managed: deduplicate semantically identical policies before scheduling physical evidence"
        ),
        "next": (
            "COMPILE_THE_FULLY_PHYSICAL_RENT_TO_POLICY_LOWER_ENVELOPE_INTO_A_SMALL_LOOKUP_CAPSULE_AND_SKIP_REOPTIMIZATION_WHILE_THE_POLICY_FAMILY_REMAINS_VALID"
        ),
        "claim_ceiling": (
            "EIGHT_UNIQUE_HOSTED_PHYSICAL_POLICY_PATHS_FROM_THE_FP054_TWELVE_POINT_RENT_SWEEP_ONLY"
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
