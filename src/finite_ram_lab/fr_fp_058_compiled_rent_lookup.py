from __future__ import annotations

import bisect
import json
import sys
from pathlib import Path
from typing import Any

SCHEMA = "finite-ram-lab.fr-fp-058-compiled-rent-lookup/v0.1"

DATA_PATH = (
    Path(__file__).resolve()
    .parents[2]
    / "data"
    / "FR-FP-057-physical-policy-paths.json"
)

COMPILED_THRESHOLDS = (
    0.07350214904258025,
    0.1585393108400696,
    0.1848015299439954,
    0.18778152413473126,
    0.2115197524954894,
    0.32482048730057045,
)

COMPILED_PATHS = (
    "P0",
    "P2",
    "P3",
    "P4",
    "P5",
    "P6",
    "P7",
)

UNSUPPORTED_TYPED_PARETO_PATHS = (
    "P1",
)

SCORE_TIE_ULPS = 64


def _load() -> dict[str, Any]:
    return json.loads(
        DATA_PATH.read_text(
            encoding="utf-8"
        )
    )


def _score(
    row: dict[str, Any],
    *,
    memory_rent: float,
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
        + memory_rent
        * float(
            row[
                "resident_mib_round"
            ]
        )
    )


def direct_select(
    memory_rent: float,
    *,
    rows: list[dict[str, Any]],
) -> str:
    if memory_rent < 0.0:
        raise ValueError(
            "memory_rent_must_be_nonnegative"
        )

    scored = [
        (
            _score(
                row,
                memory_rent=(
                    memory_rent
                ),
            ),
            row,
        )
        for row in rows
    ]
    minimum = min(
        score
        for score, _row
        in scored
    )
    scale = max(
        1.0,
        max(
            abs(score)
            for score, _row
            in scored
        ),
    )
    tie_tolerance = (
        SCORE_TIE_ULPS
        * sys.float_info.epsilon
        * scale
    )
    tied = [
        row
        for score, row
        in scored
        if abs(
            score - minimum
        )
        <= tie_tolerance
    ]

    return min(
        tied,
        key=lambda row: (
            float(
                row[
                    "resident_mib_round"
                ]
            ),
            row[
                "path_id"
            ],
        ),
    )[
        "path_id"
    ]


def compiled_select(
    memory_rent: float,
) -> str:
    if memory_rent < 0.0:
        raise ValueError(
            "memory_rent_must_be_nonnegative"
        )

    index = bisect.bisect_right(
        COMPILED_THRESHOLDS,
        memory_rent,
    )

    return COMPILED_PATHS[
        index
    ]


def _boundary_probes() -> list[float]:
    probes = {
        0.0,
        0.5,
        1.0,
    }

    for value in (
        COMPILED_THRESHOLDS
    ):
        probes.add(
            value
        )
        probes.add(
            max(
                0.0,
                value
                - 1e-12,
            )
        )
        probes.add(
            value
            + 1e-12
        )

    return sorted(
        probes
    )


def run_panel() -> dict[str, Any]:
    data = _load()
    rows = data[
        "points"
    ]

    grid = [
        index
        / 100_000.0
        for index in range(
            50_001
        )
    ]
    probes = sorted(
        set(
            grid
            + _boundary_probes()
        )
    )

    mismatches = []

    for memory_rent in probes:
        direct = direct_select(
            memory_rent,
            rows=rows,
        )
        compiled = (
            compiled_select(
                memory_rent
            )
        )

        if direct != compiled:
            mismatches.append(
                {
                    "memory_rent": (
                        memory_rent
                    ),
                    "direct": direct,
                    "compiled": (
                        compiled
                    ),
                }
            )

    full_evidence_payload = {
        "points": rows,
        "typed_pareto_path_ids": (
            data[
                "typed_pareto_path_ids"
            ]
        ),
        "scalar_supported_path_ids": (
            data[
                "scalar_supported_path_ids"
            ]
        ),
    }

    compiled_payload = {
        "thresholds": list(
            COMPILED_THRESHOLDS
        ),
        "paths": list(
            COMPILED_PATHS
        ),
        "invalidates_on": [
            "physical policy-path evidence changes",
            "semantic service values change",
            "physical actuation values change",
            "resident byte-time values change",
        ],
    }

    full_chars = len(
        json.dumps(
            full_evidence_payload,
            sort_keys=True,
            separators=(
                ",",
                ":",
            ),
        )
    )
    compiled_chars = len(
        json.dumps(
            compiled_payload,
            sort_keys=True,
            separators=(
                ",",
                ":",
            ),
        )
    )
    compression_fraction = (
        compiled_chars
        / full_chars
    )

    direct_supported = sorted(
        {
            direct_select(
                value,
                rows=rows,
            )
            for value in probes
        }
    )

    checks = {
        "parent_has_eight_physical_paths": (
            len(rows) == 8
        ),
        "compiled_capsule_has_seven_supported_paths": (
            len(
                COMPILED_PATHS
            )
            == 7
        ),
        "six_thresholds_define_seven_intervals": (
            len(
                COMPILED_THRESHOLDS
            )
            + 1
            == len(
                COMPILED_PATHS
            )
        ),
        "thresholds_are_strictly_ordered": all(
            left < right
            for left, right
            in zip(
                COMPILED_THRESHOLDS[
                    :-1
                ],
                COMPILED_THRESHOLDS[
                    1:
                ],
            )
        ),
        "compiled_lookup_matches_direct_physical_scoring_everywhere_tested": (
            not mismatches
        ),
        "direct_surface_uses_exactly_the_compiled_supported_paths": (
            direct_supported
            == sorted(
                COMPILED_PATHS
            )
        ),
        "typed_pareto_but_scalar_unsupported_path_is_not_hot": all(
            path
            not in COMPILED_PATHS
            for path in (
                UNSUPPORTED_TYPED_PARETO_PATHS
            )
        ),
        "unsupported_path_remains_in_cold_typed_evidence": all(
            path
            in data[
                "typed_pareto_path_ids"
            ]
            for path in (
                UNSUPPORTED_TYPED_PARETO_PATHS
            )
        ),
        "compiled_capsule_is_under_30pct_of_full_typed_evidence": (
            compression_fraction
            < 0.30
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
            "EXACT_COMPILED_LOOKUP_FOR_FULLY_PHYSICAL_MEMORY_RENT_POLICY_FAMILY"
        ),
        "source": data[
            "source"
        ],
        "compiled_capsule": (
            compiled_payload
        ),
        "validation": {
            "rent_points_tested": (
                len(probes)
            ),
            "mismatches": len(
                mismatches
            ),
            "mismatch_rows": (
                mismatches[:20]
            ),
            "direct_supported_paths": (
                direct_supported
            ),
        },
        "resident_surface": {
            "full_typed_evidence_chars": (
                full_chars
            ),
            "compiled_capsule_chars": (
                compiled_chars
            ),
            "compiled_fraction": (
                compression_fraction
            ),
            "cold_only_typed_pareto_paths": list(
                UNSUPPORTED_TYPED_PARETO_PATHS
            ),
        },
        "checks": checks,
        "decision": (
            "USE_COMPILED_RENT_INTERVAL_LOOKUP_AND_SKIP_DP_KNAPSACK_WHILE_THE_QUALIFIED_PHYSICAL_POLICY_FAMILY_IS_VALID"
        ),
        "meta_transfer": (
            "retain the decision boundary hot; keep the richer physical Pareto evidence cold and rehydrate it only when the compiled family invalidates"
        ),
        "claim_ceiling": (
            "COMPILED_LOOKUP_FOR_THE_EIGHT_FP057_HOSTED_PHYSICAL_POLICY_PATHS_ONLY"
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
