from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from finite_ram_lab.bounded_frontier_controller import (
    CandidatePlan,
    StateOption,
    exact_pareto_controller,
    option_is_safe,
    plan_is_feasible,
)
from finite_ram_lab.quotient_aware_beam import (
    BeamState,
    FrontierProvenance,
    _canonicalize_states,
    _empty_plan,
    _extend_state,
    _pareto_states,
)


@dataclass(frozen=True)
class ExactDPDepthStats:
    depth: int
    input_states: int
    expanded_states: int
    pareto_states_before_quotient: int
    quotient_states: int
    represented_path_count: int


@dataclass(frozen=True)
class ExactDPResult:
    frontier: tuple[CandidatePlan, ...]
    provenance: tuple[FrontierProvenance, ...]
    depth_stats: tuple[ExactDPDepthStats, ...]


def raw_combination_count(
    option_groups: Sequence[Sequence[StateOption]],
) -> int:
    if not option_groups:
        return 0
    total = 1
    for group in option_groups:
        if not group:
            raise ValueError("empty_option_group")
        total *= len(group)
    return total


def exact_quotient_pareto_dp(
    option_groups: Sequence[Sequence[StateOption]],
    capacities: dict[str, int],
) -> ExactDPResult:
    if any(not group for group in option_groups):
        raise ValueError("empty_option_group")
    for capacity in capacities.values():
        if type(capacity) is not int or capacity <= 0:
            raise ValueError("capacity_invalid")

    tiers = tuple(sorted(capacities))
    states = (
        BeamState(
            plan=_empty_plan(),
            semantic_path=(),
            provenance_by_state=(),
            equivalent_path_count=1,
        ),
    )
    stats = []

    for depth, group in enumerate(option_groups, start=1):
        expanded = []
        for state in states:
            for option in group:
                if not option_is_safe(option):
                    continue
                candidate = _extend_state(state, option)
                if plan_is_feasible(candidate.plan, capacities):
                    expanded.append(candidate)

        if not expanded:
            return ExactDPResult(
                frontier=(),
                provenance=(),
                depth_stats=tuple(stats),
            )

        partial = _pareto_states(expanded, tiers)
        quotient = _canonicalize_states(partial, tiers)

        stats.append(
            ExactDPDepthStats(
                depth=depth,
                input_states=len(states),
                expanded_states=len(expanded),
                pareto_states_before_quotient=len(partial),
                quotient_states=len(quotient),
                represented_path_count=sum(
                    state.equivalent_path_count
                    for state in quotient
                ),
            )
        )
        states = quotient

    final_states = _pareto_states(states, tiers)
    final_states = _canonicalize_states(final_states, tiers)

    frontier = tuple(state.plan for state in final_states)
    provenance = tuple(
        FrontierProvenance(
            objective_vector=state.plan.objective_vector(tiers),
            canonical_choices=state.plan.choices,
            provenance_by_state=state.provenance_by_state,
            equivalent_path_count=state.equivalent_path_count,
        )
        for state in final_states
    )

    return ExactDPResult(
        frontier=frontier,
        provenance=provenance,
        depth_stats=tuple(stats),
    )


def exact_frontier_vectors(
    plans: Sequence[CandidatePlan],
    capacities: dict[str, int],
) -> tuple[tuple[float, ...], ...]:
    tiers = tuple(sorted(capacities))
    return tuple(
        sorted({plan.objective_vector(tiers) for plan in plans})
    )


def dp_matches_cartesian_exact(
    option_groups: Sequence[Sequence[StateOption]],
    capacities: dict[str, int],
) -> bool:
    cartesian = exact_pareto_controller(option_groups, capacities)
    dp = exact_quotient_pareto_dp(option_groups, capacities)
    return (
        exact_frontier_vectors(cartesian, capacities)
        == exact_frontier_vectors(dp.frontier, capacities)
    )


def work_statistics(
    option_groups: Sequence[Sequence[StateOption]],
    capacities: dict[str, int],
) -> dict[str, object]:
    result = exact_quotient_pareto_dp(option_groups, capacities)
    full = raw_combination_count(option_groups)
    expanded = sum(item.expanded_states for item in result.depth_stats)
    max_quotient = max(
        (item.quotient_states for item in result.depth_stats),
        default=0,
    )
    return {
        "raw_cartesian_combinations": full,
        "dp_total_expanded_states": expanded,
        "dp_expanded_over_cartesian": (
            expanded / full
            if full
            else 0.0
        ),
        "dp_max_prefix_frontier_states": max_quotient,
        "depth_stats": result.depth_stats,
        "exact_frontier_points": len(
            exact_frontier_vectors(result.frontier, capacities)
        ),
    }
