from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import Sequence

from finite_ram_lab.bounded_frontier_controller import (
    StateOption,
    exact_pareto_controller,
)
from finite_ram_lab.mixed_capacity_cliff import mixed_option_groups
from finite_ram_lab.pareto_beam_controller import (
    beam_pareto_controller,
    frontier_recovery_metrics,
)
from finite_ram_lab.stateoption_quotient import (
    cadence_state_options,
    compiled_raw_groups,
    compilation_statistics,
)


@dataclass(frozen=True)
class BeamComparison:
    width: int
    raw_mean_coverage: float
    quotient_mean_coverage: float
    quotient_better_cases: int
    quotient_worse_cases: int
    equal_cases: int


def _option(state: str, name: str, values: tuple[int, ...]) -> StateOption:
    ram, vram, ram_area, vram_area, traffic, compute, latency = values
    return StateOption(
        state_name=state,
        option_name=name,
        resident_by_tier=(("RAM", ram), ("VRAM", vram)),
        byte_seconds_by_tier=(
            ("RAM", float(ram_area)),
            ("VRAM", float(vram_area)),
        ),
        traffic_bytes=float(traffic),
        compute_cost=float(compute),
        latency_cost=float(latency),
        error_cost=0.0,
    )


def _vectors(plans) -> set[tuple[float, ...]]:
    return {
        plan.objective_vector(("RAM", "VRAM"))
        for plan in plans
    }


def _synthetic_groups(rng: Random, case: int) -> tuple[tuple[StateOption, ...], ...]:
    groups = []
    for group_index in range(3):
        state = f"s{case}_{group_index}"
        bases = [
            _option(
                state,
                f"b{base_index}",
                tuple(rng.randint(0, 20) for _ in range(7)),
            )
            for base_index in range(rng.randint(2, 3))
        ]
        raw = list(bases)

        tied = rng.choice(bases)
        raw.append(
            StateOption(
                state_name=state,
                option_name="dup",
                resident_by_tier=tied.resident_by_tier,
                byte_seconds_by_tier=tied.byte_seconds_by_tier,
                traffic_bytes=tied.traffic_bytes,
                compute_cost=tied.compute_cost,
                latency_cost=tied.latency_cost,
                error_cost=tied.error_cost,
            )
        )

        source = rng.choice(bases)
        resident = dict(source.resident_by_tier)
        area = dict(source.byte_seconds_by_tier)
        raw.append(
            _option(
                state,
                "dom",
                (
                    resident["RAM"] + 2,
                    resident["VRAM"] + 2,
                    int(area["RAM"]) + 2,
                    int(area["VRAM"]) + 2,
                    int(source.traffic_bytes) + 2,
                    int(source.compute_cost) + 2,
                    int(source.latency_cost) + 2,
                ),
            )
        )
        groups.append(tuple(raw))
    return tuple(groups)


def synthetic_beam_panel(
    *,
    cases: int = 200,
    seed: int = 45602,
    widths: Sequence[int] = (4, 8, 16, 32),
) -> dict[str, object]:
    if cases < 1:
        raise ValueError("cases_invalid")
    rng = Random(seed)
    capacities = {"RAM": 1000, "VRAM": 1000}

    totals = {
        width: {
            "raw": 0.0,
            "quotient": 0.0,
            "better": 0,
            "worse": 0,
            "equal": 0,
        }
        for width in widths
    }
    reductions = []

    for case in range(cases):
        groups = _synthetic_groups(rng, case)
        exact_vectors = _vectors(
            exact_pareto_controller(groups, capacities)
        )
        compiled = compiled_raw_groups(groups, capacities)

        raw_combinations = 1
        compiled_combinations = 1
        for group in groups:
            raw_combinations *= len(group)
        for group in compiled:
            compiled_combinations *= len(group)
        reductions.append(
            1.0 - compiled_combinations / raw_combinations
        )

        for width in widths:
            raw_vectors = _vectors(
                beam_pareto_controller(
                    groups,
                    capacities,
                    beam_width=width,
                )
            )
            quotient_vectors = _vectors(
                beam_pareto_controller(
                    compiled,
                    capacities,
                    beam_width=width,
                )
            )
            raw_coverage = len(raw_vectors & exact_vectors) / len(exact_vectors)
            quotient_coverage = (
                len(quotient_vectors & exact_vectors) / len(exact_vectors)
            )

            totals[width]["raw"] += raw_coverage
            totals[width]["quotient"] += quotient_coverage
            if quotient_coverage > raw_coverage:
                totals[width]["better"] += 1
            elif quotient_coverage < raw_coverage:
                totals[width]["worse"] += 1
            else:
                totals[width]["equal"] += 1

    comparisons = tuple(
        BeamComparison(
            width=width,
            raw_mean_coverage=totals[width]["raw"] / cases,
            quotient_mean_coverage=totals[width]["quotient"] / cases,
            quotient_better_cases=totals[width]["better"],
            quotient_worse_cases=totals[width]["worse"],
            equal_cases=totals[width]["equal"],
        )
        for width in widths
    )

    return {
        "cases": cases,
        "seed": seed,
        "mean_combination_reduction": sum(reductions) / len(reductions),
        "minimum_combination_reduction": min(reductions),
        "maximum_combination_reduction": max(reductions),
        "comparisons": comparisons,
    }


def fixed_mixed_panel(
    *,
    widths: Sequence[int] = (4, 8, 16, 32, 64, 96),
) -> dict[str, object]:
    groups = mixed_option_groups() + (
        cadence_state_options(memory_high_mib=144),
    )
    capacities = {"RAM": 50000, "VRAM": 50000}
    compiled = compiled_raw_groups(groups, capacities)
    exact = exact_pareto_controller(groups, capacities)

    rows = []
    for width in widths:
        raw = frontier_recovery_metrics(
            beam_pareto_controller(
                groups,
                capacities,
                beam_width=width,
            ),
            exact,
            ("RAM", "VRAM"),
        )
        quotient = frontier_recovery_metrics(
            beam_pareto_controller(
                compiled,
                capacities,
                beam_width=width,
            ),
            exact,
            ("RAM", "VRAM"),
        )
        rows.append(
            {
                "width": width,
                "raw_exact_point_coverage": raw["exact_point_coverage"],
                "quotient_exact_point_coverage": quotient[
                    "exact_point_coverage"
                ],
            }
        )

    return {
        "compilation": compilation_statistics(groups, capacities),
        "exact_frontier_points": len(_vectors(exact)),
        "rows": tuple(rows),
    }


def width_needed_for_target(
    comparisons: Sequence[BeamComparison],
    *,
    target_coverage: float,
    mode: str,
) -> int | None:
    if not 0.0 <= target_coverage <= 1.0:
        raise ValueError("target_coverage_invalid")
    if mode not in ("raw", "quotient"):
        raise ValueError("mode_invalid")

    for row in sorted(comparisons, key=lambda item: item.width):
        coverage = (
            row.raw_mean_coverage
            if mode == "raw"
            else row.quotient_mean_coverage
        )
        if coverage >= target_coverage:
            return row.width
    return None
