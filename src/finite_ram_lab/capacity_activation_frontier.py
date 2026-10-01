from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Iterable, Sequence

from finite_ram_lab.bounded_frontier_controller import (
    CandidatePlan,
    StateOption,
    aggregate_options,
    option_is_safe,
)


@dataclass(frozen=True)
class CapacityRequirement:
    by_tier: tuple[tuple[str, int], ...]

    def __post_init__(self) -> None:
        seen = set()
        for tier, value in self.by_tier:
            if not tier or tier in seen:
                raise ValueError("tier_requirement_invalid")
            seen.add(tier)
            if type(value) is not int or value < 0:
                raise ValueError("capacity_requirement_invalid")

    def vector(self, tiers: Sequence[str]) -> tuple[int, ...]:
        values = dict(self.by_tier)
        return tuple(values.get(tier, 0) for tier in tiers)


@dataclass(frozen=True)
class ActivationPoint:
    requirement: CapacityRequirement
    representative_choices: tuple[tuple[str, str], ...]


def requirement_of_plan(
    plan: CandidatePlan,
    tiers: Sequence[str],
) -> CapacityRequirement:
    resident = dict(plan.resident_by_tier)
    return CapacityRequirement(
        tuple((tier, int(resident.get(tier, 0))) for tier in tiers)
    )


def requirement_dominates(
    left: CapacityRequirement,
    right: CapacityRequirement,
    tiers: Sequence[str],
) -> bool:
    a = left.vector(tiers)
    b = right.vector(tiers)
    return all(x <= y for x, y in zip(a, b)) and any(
        x < y for x, y in zip(a, b)
    )


def enumerate_safe_plans(
    option_groups: Sequence[Sequence[StateOption]],
) -> tuple[CandidatePlan, ...]:
    if any(not group for group in option_groups):
        raise ValueError("empty_option_group")

    plans = []
    for selection in product(*option_groups):
        if not all(option_is_safe(option) for option in selection):
            continue
        plans.append(aggregate_options(selection))
    return tuple(plans)


def activation_antichain(
    plans: Iterable[CandidatePlan],
    tiers: Sequence[str],
) -> tuple[ActivationPoint, ...]:
    tiers = tuple(tiers)
    if not tiers or len(set(tiers)) != len(tiers):
        raise ValueError("tiers_invalid")

    # Collapse plans with the same capacity requirement. The activation geometry
    # depends on resident requirements only; cost-vector differences remain a
    # separate Pareto problem after the plan is activated.
    representatives: dict[tuple[int, ...], CandidatePlan] = {}
    for plan in plans:
        requirement = requirement_of_plan(plan, tiers)
        key = requirement.vector(tiers)
        incumbent = representatives.get(key)
        if incumbent is None or plan.choices < incumbent.choices:
            representatives[key] = plan

    points = []
    items = [
        (CapacityRequirement(tuple(zip(tiers, key))), plan)
        for key, plan in representatives.items()
    ]

    for i, (requirement, plan) in enumerate(items):
        if any(
            j != i
            and requirement_dominates(other_requirement, requirement, tiers)
            for j, (other_requirement, _) in enumerate(items)
        ):
            continue
        points.append(
            ActivationPoint(
                requirement=requirement,
                representative_choices=plan.choices,
            )
        )

    return tuple(
        sorted(
            points,
            key=lambda point: (
                point.requirement.vector(tiers),
                point.representative_choices,
            ),
        )
    )


def scenario_activation_frontier(
    option_groups: Sequence[Sequence[StateOption]],
    tiers: Sequence[str],
) -> tuple[ActivationPoint, ...]:
    return activation_antichain(enumerate_safe_plans(option_groups), tiers)


def option_activation_frontier(
    option_groups: Sequence[Sequence[StateOption]],
    *,
    state_name: str,
    option_name: str,
    tiers: Sequence[str],
) -> tuple[ActivationPoint, ...]:
    if not state_name or not option_name:
        raise ValueError("option_identity_invalid")

    selected = []
    for plan in enumerate_safe_plans(option_groups):
        if (state_name, option_name) in plan.choices:
            selected.append(plan)

    return activation_antichain(selected, tiers)


def capacity_covers(
    capacity: dict[str, int],
    requirement: CapacityRequirement,
) -> bool:
    for tier, needed in requirement.by_tier:
        available = capacity.get(tier)
        if available is None:
            return False
        if type(available) is not int or available < 0:
            raise ValueError("capacity_invalid")
        if available < needed:
            return False
    return True


def scenario_is_activated(
    frontier: Sequence[ActivationPoint],
    capacity: dict[str, int],
) -> bool:
    return any(
        capacity_covers(capacity, point.requirement)
        for point in frontier
    )
