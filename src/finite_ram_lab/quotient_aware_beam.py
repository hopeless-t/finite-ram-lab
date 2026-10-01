from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from finite_ram_lab.bounded_frontier_controller import (
    CandidatePlan,
    StateOption,
    option_is_safe,
    pareto_frontier,
    plan_is_feasible,
)
from finite_ram_lab.pareto_beam_controller import (
    _empty_plan,
    _scales,
    _truncate_frontier,
    extend_plan,
)
from finite_ram_lab.stateoption_quotient import (
    compiled_raw_groups,
    semantic_signature,
)


SemanticSignature = tuple[bool, bool, bool, bool, bool]


@dataclass(frozen=True)
class BeamState:
    plan: CandidatePlan
    semantic_path: tuple[SemanticSignature, ...]
    provenance_by_state: tuple[tuple[str, tuple[str, ...]], ...]
    equivalent_path_count: int = 1


@dataclass(frozen=True)
class BeamDepthStats:
    depth: int
    expanded_states: int
    pareto_states_before_quotient: int
    quotient_states: int
    truncated_states: int
    collapsed_path_count: int


@dataclass(frozen=True)
class FrontierProvenance:
    objective_vector: tuple[float, ...]
    canonical_choices: tuple[tuple[str, str], ...]
    provenance_by_state: tuple[tuple[str, tuple[str, ...]], ...]
    equivalent_path_count: int


@dataclass(frozen=True)
class QuotientAwareBeamResult:
    frontier: tuple[CandidatePlan, ...]
    provenance: tuple[FrontierProvenance, ...]
    depth_stats: tuple[BeamDepthStats, ...]


def _merge_provenance(
    left: tuple[tuple[str, tuple[str, ...]], ...],
    right: tuple[tuple[str, tuple[str, ...]], ...],
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    merged: dict[str, set[str]] = {}
    for source in (left, right):
        for state, option_names in source:
            merged.setdefault(state, set()).update(option_names)
    return tuple(
        (state, tuple(sorted(options)))
        for state, options in sorted(merged.items())
    )


def _extend_state(state: BeamState, option: StateOption) -> BeamState:
    plan = extend_plan(state.plan, option)
    addition = ((option.state_name, (option.option_name,)),)
    return BeamState(
        plan=plan,
        semantic_path=state.semantic_path + (semantic_signature(option),),
        provenance_by_state=_merge_provenance(
            state.provenance_by_state,
            addition,
        ),
        equivalent_path_count=state.equivalent_path_count,
    )


def _pareto_states(
    states: Sequence[BeamState],
    tiers: Sequence[str],
) -> tuple[BeamState, ...]:
    frontier = pareto_frontier(
        tuple(state.plan for state in states),
        tiers,
    )
    surviving_choices = {plan.choices for plan in frontier}
    return tuple(
        state
        for state in states
        if state.plan.choices in surviving_choices
    )


def _canonicalize_states(
    states: Sequence[BeamState],
    tiers: Sequence[str],
) -> tuple[BeamState, ...]:
    grouped: dict[
        tuple[tuple[float, ...], tuple[SemanticSignature, ...]],
        list[BeamState],
    ] = {}
    for state in states:
        key = (
            state.plan.objective_vector(tiers),
            state.semantic_path,
        )
        grouped.setdefault(key, []).append(state)

    out = []
    for tied in grouped.values():
        canonical = min(tied, key=lambda item: item.plan.choices)
        provenance = canonical.provenance_by_state
        path_count = 0
        for state in tied:
            provenance = _merge_provenance(
                provenance,
                state.provenance_by_state,
            )
            path_count += state.equivalent_path_count

        out.append(
            BeamState(
                plan=canonical.plan,
                semantic_path=canonical.semantic_path,
                provenance_by_state=provenance,
                equivalent_path_count=path_count,
            )
        )

    return tuple(
        sorted(
            out,
            key=lambda item: (
                item.plan.objective_vector(tiers),
                item.semantic_path,
                item.plan.choices,
            ),
        )
    )


def _truncate_states(
    states: Sequence[BeamState],
    *,
    capacities: dict[str, int],
    tiers: Sequence[str],
    scales: dict[str, float],
    beam_width: int,
) -> tuple[BeamState, ...]:
    selected_plans = _truncate_frontier(
        tuple(state.plan for state in states),
        capacities=capacities,
        tiers=tiers,
        scales=scales,
        beam_width=beam_width,
    )
    selected_choices = {plan.choices for plan in selected_plans}
    return tuple(
        state
        for state in states
        if state.plan.choices in selected_choices
    )


def quotient_aware_beam_controller(
    option_groups: Sequence[Sequence[StateOption]],
    capacities: dict[str, int],
    *,
    beam_width: int = 64,
) -> QuotientAwareBeamResult:
    if type(beam_width) is not int or beam_width < 1:
        raise ValueError("beam_width_invalid")
    if any(not group for group in option_groups):
        raise ValueError("empty_option_group")
    for capacity in capacities.values():
        if type(capacity) is not int or capacity <= 0:
            raise ValueError("capacity_invalid")

    tiers = tuple(sorted(capacities))

    # Use the B455 safety-aware local quotient as a scale reference so exact
    # duplicate multiplicity and locally dominated same-signature options do
    # not change scalar normalization merely because they were repeated.
    scale_groups = compiled_raw_groups(option_groups, capacities)
    scales = _scales(scale_groups)

    beam = (
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
        for state in beam:
            for option in group:
                if not option_is_safe(option):
                    continue
                candidate = _extend_state(state, option)
                if plan_is_feasible(candidate.plan, capacities):
                    expanded.append(candidate)

        if not expanded:
            return QuotientAwareBeamResult(
                frontier=(),
                provenance=(),
                depth_stats=tuple(stats),
            )

        partial = _pareto_states(expanded, tiers)
        quotient = _canonicalize_states(partial, tiers)
        truncated = _truncate_states(
            quotient,
            capacities=capacities,
            tiers=tiers,
            scales=scales,
            beam_width=beam_width,
        )

        stats.append(
            BeamDepthStats(
                depth=depth,
                expanded_states=len(expanded),
                pareto_states_before_quotient=len(partial),
                quotient_states=len(quotient),
                truncated_states=len(truncated),
                collapsed_path_count=sum(
                    state.equivalent_path_count
                    for state in quotient
                ),
            )
        )
        beam = truncated

    final_states = _pareto_states(beam, tiers)
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

    return QuotientAwareBeamResult(
        frontier=frontier,
        provenance=provenance,
        depth_stats=tuple(stats),
    )
