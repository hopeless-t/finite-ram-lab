from __future__ import annotations

from dataclasses import replace
from math import isfinite
from typing import Sequence

from finite_ram_lab.bounded_frontier_controller import (
    CandidatePlan,
    StateOption,
    dominates,
    exact_candidate_plans,
    option_is_safe,
    pareto_frontier,
    plan_is_feasible,
)


def extend_plan(plan: CandidatePlan, option: StateOption) -> CandidatePlan:
    resident = dict(plan.resident_by_tier)
    area = dict(plan.byte_seconds_by_tier)
    for tier, value in option.resident_by_tier:
        resident[tier] = resident.get(tier, 0) + value
    for tier, value in option.byte_seconds_by_tier:
        area[tier] = area.get(tier, 0.0) + float(value)

    return CandidatePlan(
        choices=plan.choices + ((option.state_name, option.option_name),),
        resident_by_tier=tuple(sorted(resident.items())),
        byte_seconds_by_tier=tuple(sorted(area.items())),
        traffic_bytes=plan.traffic_bytes + option.traffic_bytes,
        compute_cost=plan.compute_cost + option.compute_cost,
        latency_cost=plan.latency_cost + option.latency_cost,
        error_cost=plan.error_cost + option.error_cost,
    )


def _empty_plan() -> CandidatePlan:
    return CandidatePlan(
        choices=(),
        resident_by_tier=(),
        byte_seconds_by_tier=(),
        traffic_bytes=0.0,
        compute_cost=0.0,
        latency_cost=0.0,
        error_cost=0.0,
    )


def _scales(
    option_groups: Sequence[Sequence[StateOption]],
) -> dict[str, float]:
    safe_groups = [
        [option for option in group if option_is_safe(option)]
        for group in option_groups
    ]

    def sum_group_max(attribute: str) -> float:
        return max(
            1.0,
            sum(
                max((float(getattr(option, attribute)) for option in group), default=0.0)
                for group in safe_groups
            ),
        )

    area_total = sum(
        sum(float(value) for _, value in option.byte_seconds_by_tier)
        for group in safe_groups
        for option in group
    )

    return {
        "area": max(1.0, area_total),
        "traffic": sum_group_max("traffic_bytes"),
        "compute": sum_group_max("compute_cost"),
        "latency": sum_group_max("latency_cost"),
        "error": sum_group_max("error_cost"),
    }


def pressure_score(
    plan: CandidatePlan,
    capacities: dict[str, int],
    scales: dict[str, float],
    tiers: Sequence[str],
) -> float:
    resident = dict(plan.resident_by_tier)
    area = dict(plan.byte_seconds_by_tier)
    score = 0.0

    for tier in tiers:
        capacity = capacities[tier]
        if type(capacity) is not int or capacity <= 0:
            raise ValueError("capacity_invalid")
        ratio = resident.get(tier, 0) / capacity
        # Convex pressure term makes approaching a tier cliff expensive.
        score += 4.0 * ratio * ratio
        score += area.get(tier, 0.0) / scales["area"]

    score += plan.traffic_bytes / scales["traffic"]
    score += plan.compute_cost / scales["compute"]
    score += plan.latency_cost / scales["latency"]
    score += plan.error_cost / scales["error"]
    return score


def _truncate_frontier(
    plans: Sequence[CandidatePlan],
    *,
    capacities: dict[str, int],
    tiers: Sequence[str],
    scales: dict[str, float],
    beam_width: int,
) -> tuple[CandidatePlan, ...]:
    if len(plans) <= beam_width:
        return tuple(plans)

    selected: list[CandidatePlan] = []
    seen = set()
    objective_count = len(plans[0].objective_vector(tiers))

    # Preserve one extreme for every objective dimension before scalar pruning.
    for dimension in range(objective_count):
        plan = min(
            plans,
            key=lambda item: (
                item.objective_vector(tiers)[dimension],
                item.choices,
            ),
        )
        if plan.choices not in seen:
            selected.append(plan)
            seen.add(plan.choices)
            if len(selected) >= beam_width:
                return tuple(selected)

    for plan in sorted(
        plans,
        key=lambda item: (
            pressure_score(item, capacities, scales, tiers),
            item.choices,
        ),
    ):
        if plan.choices in seen:
            continue
        selected.append(plan)
        seen.add(plan.choices)
        if len(selected) >= beam_width:
            break

    return tuple(selected)


def beam_pareto_controller(
    option_groups: Sequence[Sequence[StateOption]],
    capacities: dict[str, int],
    *,
    beam_width: int = 64,
) -> tuple[CandidatePlan, ...]:
    if type(beam_width) is not int or beam_width < 1:
        raise ValueError("beam_width_invalid")
    if any(not group for group in option_groups):
        raise ValueError("empty_option_group")
    for capacity in capacities.values():
        if type(capacity) is not int or capacity <= 0:
            raise ValueError("capacity_invalid")

    tiers = tuple(sorted(capacities))
    scales = _scales(option_groups)
    beam = (_empty_plan(),)

    for group in option_groups:
        expanded: list[CandidatePlan] = []
        for plan in beam:
            for option in group:
                if not option_is_safe(option):
                    continue
                candidate = extend_plan(plan, option)
                if plan_is_feasible(candidate, capacities):
                    expanded.append(candidate)

        if not expanded:
            return ()

        # Lossless at a fixed prefix depth: every surviving partial plan has the
        # same remaining option groups, so a dominated prefix can never become
        # non-dominated by adding the same future choice.
        partial_frontier = pareto_frontier(expanded, tiers)
        beam = _truncate_frontier(
            partial_frontier,
            capacities=capacities,
            tiers=tiers,
            scales=scales,
            beam_width=beam_width,
        )

    return pareto_frontier(beam, tiers)


def domination_gap(
    approximate: CandidatePlan,
    exact_frontier: Sequence[CandidatePlan],
    tiers: Sequence[str],
) -> float:
    if not exact_frontier:
        raise ValueError("exact_frontier_empty")

    a = approximate.objective_vector(tiers)
    best = float("inf")
    for exact in exact_frontier:
        e = exact.objective_vector(tiers)
        gap = max(
            max(0.0, (x - y) / max(1.0, abs(y)))
            for x, y in zip(a, e)
        )
        best = min(best, gap)
    return best


def frontier_recovery_metrics(
    approximate: Sequence[CandidatePlan],
    exact_frontier: Sequence[CandidatePlan],
    tiers: Sequence[str],
) -> dict[str, float | int]:
    exact_vectors = {plan.objective_vector(tiers) for plan in exact_frontier}
    approximate_vectors = {plan.objective_vector(tiers) for plan in approximate}

    recovered = len(exact_vectors & approximate_vectors)
    dominated_count = sum(
        any(dominates(exact, plan, tiers) for exact in exact_frontier)
        for plan in approximate
    )

    gaps = [
        domination_gap(plan, exact_frontier, tiers)
        for plan in approximate
    ] if approximate and exact_frontier else []

    return {
        "exact_frontier_points": len(exact_vectors),
        "approx_frontier_points": len(approximate_vectors),
        "recovered_exact_points": recovered,
        "exact_point_coverage": (
            recovered / len(exact_vectors)
            if exact_vectors
            else 1.0
        ),
        "approx_points_dominated_by_exact": dominated_count,
        "approx_dominated_fraction": (
            dominated_count / len(approximate)
            if approximate
            else 0.0
        ),
        "mean_domination_gap": (
            sum(gaps) / len(gaps)
            if gaps
            else 0.0
        ),
        "max_domination_gap": max(gaps, default=0.0),
    }
