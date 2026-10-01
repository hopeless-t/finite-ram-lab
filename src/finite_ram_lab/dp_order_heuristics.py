from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from finite_ram_lab.bounded_frontier_controller import StateOption
from finite_ram_lab.dp_group_order import (
    OrderEvaluation,
    OrderState,
    _empty_plan,
    _validate_groups,
    advance_group,
    evaluate_order,
    greedy_order,
    optimal_order,
)


@dataclass(frozen=True)
class HeuristicComparison:
    original: OrderEvaluation
    immediate_greedy: OrderEvaluation
    frontier_greedy: OrderEvaluation
    rollout: OrderEvaluation
    optimal: OrderEvaluation


def _initial_states() -> tuple[OrderState, ...]:
    return (
        OrderState(
            plan=_empty_plan(),
            semantic_by_state=(),
        ),
    )


def _frontier_greedy_tail(
    option_groups: Sequence[Sequence[StateOption]],
    capacities: dict[str, int],
    *,
    states: tuple[OrderState, ...],
    remaining: tuple[int, ...],
    mask: int,
) -> tuple[tuple[int, ...], int]:
    names = _validate_groups(option_groups)
    order = []
    total_cost = 0
    current_states = states
    current_mask = mask
    left = list(remaining)

    while left:
        choices = []
        cached = {}
        for group_index in left:
            next_states, stats = advance_group(
                current_states,
                option_groups[group_index],
                capacities,
                from_mask=current_mask,
                group_index=group_index,
            )
            cached[group_index] = (next_states, stats)
            choices.append(
                (
                    stats.quotient_states,
                    stats.expanded_states,
                    names[group_index],
                    group_index,
                )
            )

        _, _, _, chosen = min(choices)
        next_states, stats = cached[chosen]
        total_cost += stats.expanded_states
        order.append(chosen)
        current_states = next_states
        current_mask = stats.to_mask
        left.remove(chosen)

    return tuple(order), total_cost


def frontier_size_greedy_order(
    option_groups: Sequence[Sequence[StateOption]],
    capacities: dict[str, int],
) -> tuple[int, ...]:
    _validate_groups(option_groups)
    n = len(option_groups)
    order, _ = _frontier_greedy_tail(
        option_groups,
        capacities,
        states=_initial_states(),
        remaining=tuple(range(n)),
        mask=0,
    )
    return order


def rollout_order(
    option_groups: Sequence[Sequence[StateOption]],
    capacities: dict[str, int],
) -> tuple[int, ...]:
    names = _validate_groups(option_groups)
    n = len(option_groups)
    states = _initial_states()
    mask = 0
    remaining = list(range(n))
    order = []

    while remaining:
        candidates = []
        cached = {}

        for group_index in remaining:
            next_states, stats = advance_group(
                states,
                option_groups[group_index],
                capacities,
                from_mask=mask,
                group_index=group_index,
            )
            tail_remaining = tuple(
                index
                for index in remaining
                if index != group_index
            )
            _, tail_cost = _frontier_greedy_tail(
                option_groups,
                capacities,
                states=next_states,
                remaining=tail_remaining,
                mask=stats.to_mask,
            )
            projected_cost = stats.expanded_states + tail_cost
            cached[group_index] = (next_states, stats)
            candidates.append(
                (
                    projected_cost,
                    stats.quotient_states,
                    stats.expanded_states,
                    names[group_index],
                    group_index,
                )
            )

        _, _, _, _, chosen = min(candidates)
        next_states, stats = cached[chosen]
        order.append(chosen)
        states = next_states
        mask = stats.to_mask
        remaining.remove(chosen)

    return tuple(order)


def compare_heuristics(
    option_groups: Sequence[Sequence[StateOption]],
    capacities: dict[str, int],
) -> HeuristicComparison:
    n = len(option_groups)

    original_order = tuple(range(n))
    immediate = greedy_order(option_groups, capacities)
    frontier = frontier_size_greedy_order(option_groups, capacities)
    rollout = rollout_order(option_groups, capacities)
    optimal = optimal_order(option_groups, capacities)

    evaluations = [
        evaluate_order(option_groups, capacities, original_order),
        evaluate_order(option_groups, capacities, immediate),
        evaluate_order(option_groups, capacities, frontier),
        evaluate_order(option_groups, capacities, rollout),
        evaluate_order(option_groups, capacities, optimal),
    ]

    vectors = evaluations[0].final_frontier_vectors
    if any(item.final_frontier_vectors != vectors for item in evaluations[1:]):
        raise AssertionError("heuristic_frontier_mismatch")

    return HeuristicComparison(
        original=evaluations[0],
        immediate_greedy=evaluations[1],
        frontier_greedy=evaluations[2],
        rollout=evaluations[3],
        optimal=evaluations[4],
    )


def cost_ratio(
    evaluation: OrderEvaluation,
    optimal: OrderEvaluation,
) -> float:
    if optimal.total_expanded_states <= 0:
        return 1.0
    return evaluation.total_expanded_states / optimal.total_expanded_states
