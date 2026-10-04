from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA = "finite-ram-lab.fr-fp-056-physical-resident-pareto/v0.1"

DATA_PATH = (
    Path(__file__).resolve()
    .parents[2]
    / "data"
    / "FR-FP-056-physical-resident-pareto.json"
)

REPRESENTATIVE_EXTERNAL_RENTS = (
    0.05,
    0.10,
    0.20,
    0.35,
)


def _load() -> dict[str, Any]:
    return json.loads(
        DATA_PATH.read_text(
            encoding="utf-8"
        )
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


def _dominates(
    left: dict[str, Any],
    right: dict[str, Any],
) -> bool:
    dimensions = (
        "resident_mib_round",
        "semantic_service_ms",
        "physical_actuation_ms",
    )

    no_worse = all(
        float(left[key])
        <= float(right[key])
        for key in dimensions
    )
    strictly_better = any(
        float(left[key])
        < float(right[key])
        for key in dimensions
    )

    return (
        no_worse
        and strictly_better
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


def _candidate_score(
    row: dict[str, Any],
    *,
    memory_rent: float,
) -> float:
    return (
        _base_time_ms(
            row
        )
        + memory_rent
        * float(
            row[
                "resident_mib_round"
            ]
        )
    )


def _select_candidate(
    rows: list[dict[str, Any]],
    *,
    memory_rent: float,
) -> dict[str, Any]:
    return min(
        rows,
        key=lambda row: (
            _candidate_score(
                row,
                memory_rent=(
                    memory_rent
                ),
            ),
            float(
                row[
                    "resident_mib_round"
                ]
            ),
            row[
                "policy_label"
            ],
        ),
    )


def _adjacent_crossover(
    left: dict[str, Any],
    right: dict[str, Any],
) -> float:
    resident_saved = (
        float(
            left[
                "resident_mib_round"
            ]
        )
        - float(
            right[
                "resident_mib_round"
            ]
        )
    )

    if resident_saved <= 0.0:
        raise ValueError(
            "crossover_requires_residency_reduction"
        )

    base_time_increase = (
        _base_time_ms(
            right
        )
        - _base_time_ms(
            left
        )
    )

    return (
        base_time_increase
        / resident_saved
    )


def run_panel() -> dict[str, Any]:
    data = _load()
    rows = [
        {
            **row,
            "base_time_ms": (
                _base_time_ms(
                    row
                )
            ),
        }
        for row in data[
            "points"
        ]
    ]

    rows = sorted(
        rows,
        key=lambda row: (
            -float(
                row[
                    "resident_mib_round"
                ]
            )
        ),
    )

    pareto = _pareto(
        rows
    )
    crossovers = [
        {
            "from": (
                left[
                    "policy_label"
                ]
            ),
            "to": (
                right[
                    "policy_label"
                ]
            ),
            "memory_rent_crossover_ms_per_mib_round": (
                _adjacent_crossover(
                    left,
                    right,
                )
            ),
        }
        for left, right
        in zip(
            rows[:-1],
            rows[1:],
        )
    ]

    selections = [
        {
            "external_memory_rent_ms_per_mib_round": (
                memory_rent
            ),
            "selected_policy": (
                _select_candidate(
                    rows,
                    memory_rent=(
                        memory_rent
                    ),
                )[
                    "policy_label"
                ]
            ),
        }
        for memory_rent in (
            REPRESENTATIVE_EXTERNAL_RENTS
        )
    ]

    resident = [
        float(
            row[
                "resident_mib_round"
            ]
        )
        for row in rows
    ]
    service = [
        float(
            row[
                "semantic_service_ms"
            ]
        )
        for row in rows
    ]
    actuation = [
        float(
            row[
                "physical_actuation_ms"
            ]
        )
        for row in rows
    ]
    crossover_values = [
        float(
            row[
                "memory_rent_crossover_ms_per_mib_round"
            ]
        )
        for row in crossovers
    ]

    checks = {
        "four_hosted_physical_anchors": (
            len(rows) == 4
        ),
        "all_four_anchors_are_pareto_nondominated": (
            len(pareto) == 4
        ),
        "resident_byte_time_strictly_decreases": all(
            left > right
            for left, right
            in zip(
                resident[:-1],
                resident[1:],
            )
        ),
        "semantic_service_cost_strictly_increases": all(
            left < right
            for left, right
            in zip(
                service[:-1],
                service[1:],
            )
        ),
        "physical_actuation_cost_strictly_decreases": all(
            left > right
            for left, right
            in zip(
                actuation[:-1],
                actuation[1:],
            )
        ),
        "adjacent_candidate_crossovers_are_ordered": all(
            left < right
            for left, right
            in zip(
                crossover_values[
                    :-1
                ],
                crossover_values[
                    1:
                ],
            )
        ),
        "explicit_rent_selects_multiple_physical_policies": (
            len(
                {
                    row[
                        "selected_policy"
                    ]
                    for row in (
                        selections
                    )
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
            "TYPED_HOSTED_PHYSICAL_RESIDENT_SERVICE_ACTUATION_PARETO_FRONTIER"
        ),
        "source": data[
            "source"
        ],
        "axes": [
            {
                "name": (
                    "resident_mib_round"
                ),
                "unit": (
                    "MiB-round"
                ),
                "direction": (
                    "MINIMIZE"
                ),
            },
            {
                "name": (
                    "semantic_service_ms"
                ),
                "unit": "ms",
                "direction": (
                    "MINIMIZE"
                ),
            },
            {
                "name": (
                    "physical_actuation_ms"
                ),
                "unit": "ms",
                "direction": (
                    "MINIMIZE"
                ),
            },
        ],
        "points": rows,
        "pareto_policy_labels": [
            row[
                "policy_label"
            ]
            for row in pareto
        ],
        "adjacent_physical_candidate_crossovers": (
            crossovers
        ),
        "representative_explicit_rent_selections": (
            selections
        ),
        "scalar_gain": None,
        "checks": checks,
        "decision": (
            "EXPOSE_THE_PHYSICAL_RESIDENT_SERVICE_ACTUATION_FRONTIER_AND_REQUIRE_AN_EXPLICIT_MEMORY_RENT_BEFORE_SCALAR_POLICY_SELECTION"
        ),
        "boundary": (
            "Crossovers choose only among the four physically tested anchors; "
            "they are not a claim that no untested intermediate policy can be superior."
        ),
        "next": (
            "PHYSICALLY_SAMPLE_AROUND_THE_EMPIRICAL_CROSSOVER_REGIONS_ONLY_IF_THE_ADDITIONAL_POLICY_RESOLUTION_CAN_CHANGE_A_REAL_DECISION"
        ),
        "claim_ceiling": (
            "FOUR_ANCHOR_HOSTED_PHYSICAL_PARETO_AND_CANDIDATE_CROSSOVERS_ONLY"
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
