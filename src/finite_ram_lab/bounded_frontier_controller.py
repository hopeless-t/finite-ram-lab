from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from math import isfinite
from typing import Iterable, Sequence


@dataclass(frozen=True)
class StateOption:
    state_name: str
    option_name: str
    resident_by_tier: tuple[tuple[str, int], ...]
    byte_seconds_by_tier: tuple[tuple[str, float], ...]
    traffic_bytes: float = 0.0
    compute_cost: float = 0.0
    latency_cost: float = 0.0
    error_cost: float = 0.0
    releases_semantic_state: bool = False
    release_proven: bool = False
    merges_owners: bool = False
    sharing_proven: bool = False
    error_bound_known: bool = True

    def __post_init__(self) -> None:
        if not self.state_name or not self.option_name:
            raise ValueError("option_identity_invalid")
        _validate_tier_pairs(self.resident_by_tier, integer=True)
        _validate_tier_pairs(self.byte_seconds_by_tier, integer=False)
        for name in ("traffic_bytes", "compute_cost", "latency_cost", "error_cost"):
            value = getattr(self, name)
            if not isinstance(value, (int, float)) or not isfinite(value) or value < 0:
                raise ValueError(f"{name}_invalid")


@dataclass(frozen=True)
class CandidatePlan:
    choices: tuple[tuple[str, str], ...]
    resident_by_tier: tuple[tuple[str, int], ...]
    byte_seconds_by_tier: tuple[tuple[str, float], ...]
    traffic_bytes: float
    compute_cost: float
    latency_cost: float
    error_cost: float

    def objective_vector(self, tiers: Sequence[str]) -> tuple[float, ...]:
        peaks = dict(self.resident_by_tier)
        areas = dict(self.byte_seconds_by_tier)
        return tuple(float(peaks.get(t, 0)) for t in tiers) + tuple(
            float(areas.get(t, 0.0)) for t in tiers
        ) + (
            float(self.traffic_bytes),
            float(self.compute_cost),
            float(self.latency_cost),
            float(self.error_cost),
        )


def _validate_tier_pairs(
    pairs: tuple[tuple[str, int | float], ...],
    *,
    integer: bool,
) -> None:
    seen = set()
    for tier, value in pairs:
        if not tier or tier in seen:
            raise ValueError("tier_pairs_invalid")
        seen.add(tier)
        if integer:
            if type(value) is not int or value < 0:
                raise ValueError("tier_bytes_invalid")
        else:
            if not isinstance(value, (int, float)) or not isfinite(value) or value < 0:
                raise ValueError("tier_area_invalid")


def option_is_safe(option: StateOption) -> bool:
    if option.releases_semantic_state and not option.release_proven:
        return False
    if option.merges_owners and not option.sharing_proven:
        return False
    if option.error_cost > 0 and not option.error_bound_known:
        return False
    return True


def aggregate_options(options: Iterable[StateOption]) -> CandidatePlan:
    resident: dict[str, int] = {}
    area: dict[str, float] = {}
    traffic = compute = latency = error = 0.0
    choices = []

    for option in options:
        choices.append((option.state_name, option.option_name))
        for tier, value in option.resident_by_tier:
            resident[tier] = resident.get(tier, 0) + value
        for tier, value in option.byte_seconds_by_tier:
            area[tier] = area.get(tier, 0.0) + float(value)
        traffic += option.traffic_bytes
        compute += option.compute_cost
        latency += option.latency_cost
        error += option.error_cost

    return CandidatePlan(
        choices=tuple(choices),
        resident_by_tier=tuple(sorted(resident.items())),
        byte_seconds_by_tier=tuple(sorted(area.items())),
        traffic_bytes=traffic,
        compute_cost=compute,
        latency_cost=latency,
        error_cost=error,
    )


def plan_is_feasible(
    plan: CandidatePlan,
    capacities: dict[str, int],
) -> bool:
    for tier, used in plan.resident_by_tier:
        capacity = capacities.get(tier)
        if capacity is None:
            return False
        if type(capacity) is not int or capacity < 0:
            raise ValueError("capacity_invalid")
        if used > capacity:
            return False
    return True


def exact_candidate_plans(
    option_groups: Sequence[Sequence[StateOption]],
    capacities: dict[str, int],
) -> tuple[CandidatePlan, ...]:
    if any(not group for group in option_groups):
        raise ValueError("empty_option_group")

    plans = []
    for selection in product(*option_groups):
        if not all(option_is_safe(option) for option in selection):
            continue
        plan = aggregate_options(selection)
        if plan_is_feasible(plan, capacities):
            plans.append(plan)

    return tuple(plans)


def dominates(
    left: CandidatePlan,
    right: CandidatePlan,
    tiers: Sequence[str],
) -> bool:
    a = left.objective_vector(tiers)
    b = right.objective_vector(tiers)
    return all(x <= y for x, y in zip(a, b)) and any(
        x < y for x, y in zip(a, b)
    )


def pareto_frontier(
    plans: Iterable[CandidatePlan],
    tiers: Sequence[str],
) -> tuple[CandidatePlan, ...]:
    items = tuple(plans)
    frontier = []
    for i, plan in enumerate(items):
        if any(
            j != i and dominates(other, plan, tiers)
            for j, other in enumerate(items)
        ):
            continue
        frontier.append(plan)

    return tuple(
        sorted(
            frontier,
            key=lambda p: (
                p.objective_vector(tiers),
                p.choices,
            ),
        )
    )


def exact_pareto_controller(
    option_groups: Sequence[Sequence[StateOption]],
    capacities: dict[str, int],
) -> tuple[CandidatePlan, ...]:
    tiers = tuple(sorted(capacities))
    plans = exact_candidate_plans(option_groups, capacities)
    return pareto_frontier(plans, tiers)
