from __future__ import annotations

from dataclasses import dataclass
from math import inf
from typing import Sequence

from finite_ram_lab.bounded_frontier_controller import (
    CandidatePlan,
    StateOption,
    option_is_safe,
    pareto_frontier,
    plan_is_feasible,
)
from finite_ram_lab.pareto_beam_controller import extend_plan
from finite_ram_lab.stateoption_quotient import semantic_signature


SemanticSignature = tuple[bool, bool, bool, bool, bool]


@dataclass(frozen=True)
class OrderState:
    plan: CandidatePlan
    semantic_by_state: tuple[tuple[str, SemanticSignature], ...]


@dataclass(frozen=True)
class TransitionStats:
    from_mask: int
    group_index: int
    to_mask: int
    input_states: int
    expanded_states: int
    pareto_states_before_quotient: int
    quotient_states: int


@dataclass(frozen=True)
class OrderEvaluation:
    order: tuple[int, ...]
    order_names: tuple[str, ...]
    total_expanded_states: int
    depth_stats: tuple[TransitionStats, ...]
    final_frontier_vectors: tuple[tuple[float, ...], ...]


@dataclass(frozen=True)
class OrderSearchResult:
    original: OrderEvaluation
    greedy: OrderEvaluation
    optimal: OrderEvaluation
    subset_count: int
    transition_count: int


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


def _group_name(group: Sequence[StateOption]) -> str:
    if not group:
        raise ValueError("empty_option_group")
    names = {option.state_name for option in group}
    if len(names) != 1:
        raise ValueError("mixed_state_group")
    return next(iter(names))


def _validate_groups(
    option_groups: Sequence[Sequence[StateOption]],
) -> tuple[str, ...]:
    if not option_groups:
        raise ValueError("option_groups_empty")
    names = tuple(_group_name(group) for group in option_groups)
    if len(set(names)) != len(names):
        raise ValueError("duplicate_state_group_name")
    return names


def _vector(
    state: OrderState,
    tiers: Sequence[str],
) -> tuple[float, ...]:
    return state.plan.objective_vector(tiers)


def _pareto_states(
    states: Sequence[OrderState],
    tiers: Sequence[str],
) -> tuple[OrderState, ...]:
    frontier = pareto_frontier(
        tuple(state.plan for state in states),
        tiers,
    )
    choices = {plan.choices for plan in frontier}
    return tuple(
        state
        for state in states
        if state.plan.choices in choices
    )


def _canonicalize_states(
    states: Sequence[OrderState],
    tiers: Sequence[str],
) -> tuple[OrderState, ...]:
    grouped: dict[
        tuple[
            tuple[float, ...],
            tuple[tuple[str, SemanticSignature], ...],
        ],
        list[OrderState],
    ] = {}
    for state in states:
        key = (_vector(state, tiers), state.semantic_by_state)
        grouped.setdefault(key, []).append(state)

    out = []
    for tied in grouped.values():
        canonical = min(tied, key=lambda item: item.plan.choices)
        out.append(canonical)

    return tuple(
        sorted(
            out,
            key=lambda item: (
                _vector(item, tiers),
                item.semantic_by_state,
                item.plan.choices,
            ),
        )
    )


def advance_group(
    states: Sequence[OrderState],
    group: Sequence[StateOption],
    capacities: dict[str, int],
    *,
    from_mask: int,
    group_index: int,
) -> tuple[tuple[OrderState, ...], TransitionStats]:
    tiers = tuple(sorted(capacities))
    expanded = []
    group_name = _group_name(group)

    for state in states:
        semantic_map = dict(state.semantic_by_state)
        if group_name in semantic_map:
            raise ValueError("state_group_reused")

        for option in group:
            if not option_is_safe(option):
                continue
            plan = extend_plan(state.plan, option)
            if not plan_is_feasible(plan, capacities):
                continue

            new_semantics = dict(semantic_map)
            new_semantics[group_name] = semantic_signature(option)
            expanded.append(
                OrderState(
                    plan=plan,
                    semantic_by_state=tuple(sorted(new_semantics.items())),
                )
            )

    if not expanded:
        next_states: tuple[OrderState, ...] = ()
        pareto_count = quotient_count = 0
    else:
        partial = _pareto_states(expanded, tiers)
        next_states = _canonicalize_states(partial, tiers)
        pareto_count = len(partial)
        quotient_count = len(next_states)

    to_mask = from_mask | (1 << group_index)
    stats = TransitionStats(
        from_mask=from_mask,
        group_index=group_index,
        to_mask=to_mask,
        input_states=len(states),
        expanded_states=len(expanded),
        pareto_states_before_quotient=pareto_count,
        quotient_states=quotient_count,
    )
    return next_states, stats


def _frontier_vectors(
    states: Sequence[OrderState],
    capacities: dict[str, int],
) -> tuple[tuple[float, ...], ...]:
    tiers = tuple(sorted(capacities))
    return tuple(sorted({_vector(state, tiers) for state in states}))


def evaluate_order(
    option_groups: Sequence[Sequence[StateOption]],
    capacities: dict[str, int],
    order: Sequence[int],
) -> OrderEvaluation:
    names = _validate_groups(option_groups)
    n = len(option_groups)
    order = tuple(order)
    if tuple(sorted(order)) != tuple(range(n)):
        raise ValueError("order_invalid")

    states = (
        OrderState(
            plan=_empty_plan(),
            semantic_by_state=(),
        ),
    )
    mask = 0
    stats = []

    for group_index in order:
        states, transition = advance_group(
            states,
            option_groups[group_index],
            capacities,
            from_mask=mask,
            group_index=group_index,
        )
        stats.append(transition)
        mask = transition.to_mask

    return OrderEvaluation(
        order=order,
        order_names=tuple(names[index] for index in order),
        total_expanded_states=sum(item.expanded_states for item in stats),
        depth_stats=tuple(stats),
        final_frontier_vectors=_frontier_vectors(states, capacities),
    )


def build_subset_frontiers(
    option_groups: Sequence[Sequence[StateOption]],
    capacities: dict[str, int],
) -> dict[int, tuple[OrderState, ...]]:
    _validate_groups(option_groups)
    n = len(option_groups)

    frontiers: dict[int, tuple[OrderState, ...]] = {
        0: (
            OrderState(
                plan=_empty_plan(),
                semantic_by_state=(),
            ),
        )
    }

    for mask in range(1, 1 << n):
        # Canonical construction path: remove the least-significant set bit.
        bit = mask & -mask
        group_index = bit.bit_length() - 1
        previous = mask ^ bit
        states, _ = advance_group(
            frontiers[previous],
            option_groups[group_index],
            capacities,
            from_mask=previous,
            group_index=group_index,
        )
        frontiers[mask] = states

    return frontiers


def build_transition_table(
    option_groups: Sequence[Sequence[StateOption]],
    capacities: dict[str, int],
    frontiers: dict[int, tuple[OrderState, ...]] | None = None,
) -> dict[tuple[int, int], TransitionStats]:
    _validate_groups(option_groups)
    n = len(option_groups)
    if frontiers is None:
        frontiers = build_subset_frontiers(option_groups, capacities)

    table = {}
    for mask in range(1 << n):
        for group_index in range(n):
            if mask & (1 << group_index):
                continue
            states, stats = advance_group(
                frontiers[mask],
                option_groups[group_index],
                capacities,
                from_mask=mask,
                group_index=group_index,
            )

            expected = frontiers[stats.to_mask]
            if _frontier_vectors(states, capacities) != _frontier_vectors(
                expected,
                capacities,
            ):
                raise AssertionError("subset_frontier_order_dependence")
            table[(mask, group_index)] = stats
    return table


def optimal_order(
    option_groups: Sequence[Sequence[StateOption]],
    capacities: dict[str, int],
) -> tuple[int, ...]:
    names = _validate_groups(option_groups)
    n = len(option_groups)
    frontiers = build_subset_frontiers(option_groups, capacities)
    table = build_transition_table(
        option_groups,
        capacities,
        frontiers,
    )

    best_cost = {0: 0}
    best_path: dict[int, tuple[int, ...]] = {0: ()}

    for mask in range(1 << n):
        if mask not in best_cost:
            continue
        for group_index in range(n):
            if mask & (1 << group_index):
                continue

            transition = table[(mask, group_index)]
            new_mask = transition.to_mask
            candidate_cost = (
                best_cost[mask] + transition.expanded_states
            )
            candidate_path = best_path[mask] + (group_index,)

            incumbent_cost = best_cost.get(new_mask, inf)
            incumbent_path = best_path.get(new_mask)
            if (
                candidate_cost < incumbent_cost
                or (
                    candidate_cost == incumbent_cost
                    and (
                        incumbent_path is None
                        or tuple(names[i] for i in candidate_path)
                        < tuple(names[i] for i in incumbent_path)
                    )
                )
            ):
                best_cost[new_mask] = candidate_cost
                best_path[new_mask] = candidate_path

    return best_path[(1 << n) - 1]


def greedy_order(
    option_groups: Sequence[Sequence[StateOption]],
    capacities: dict[str, int],
) -> tuple[int, ...]:
    names = _validate_groups(option_groups)
    n = len(option_groups)
    frontiers = build_subset_frontiers(option_groups, capacities)
    table = build_transition_table(
        option_groups,
        capacities,
        frontiers,
    )

    mask = 0
    order = []
    while len(order) < n:
        candidates = []
        for group_index in range(n):
            if mask & (1 << group_index):
                continue
            stats = table[(mask, group_index)]
            candidates.append(
                (
                    stats.expanded_states,
                    stats.quotient_states,
                    names[group_index],
                    group_index,
                )
            )
        _, _, _, chosen = min(candidates)
        order.append(chosen)
        mask |= 1 << chosen

    return tuple(order)


def search_orders(
    option_groups: Sequence[Sequence[StateOption]],
    capacities: dict[str, int],
) -> OrderSearchResult:
    n = len(option_groups)
    original_order = tuple(range(n))
    greedy = greedy_order(option_groups, capacities)
    optimal = optimal_order(option_groups, capacities)

    original_eval = evaluate_order(
        option_groups,
        capacities,
        original_order,
    )
    greedy_eval = evaluate_order(
        option_groups,
        capacities,
        greedy,
    )
    optimal_eval = evaluate_order(
        option_groups,
        capacities,
        optimal,
    )

    if not (
        original_eval.final_frontier_vectors
        == greedy_eval.final_frontier_vectors
        == optimal_eval.final_frontier_vectors
    ):
        raise AssertionError("final_frontier_order_dependence")

    transition_count = n * (1 << (n - 1))
    return OrderSearchResult(
        original=original_eval,
        greedy=greedy_eval,
        optimal=optimal_eval,
        subset_count=1 << n,
        transition_count=transition_count,
    )
