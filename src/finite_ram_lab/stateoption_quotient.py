from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Sequence

from finite_ram_lab.bounded_frontier_controller import (
    CandidatePlan,
    StateOption,
    exact_pareto_controller,
    option_is_safe,
)
from finite_ram_lab.prelaunch_digital_twin import twin_plan


@dataclass(frozen=True)
class CompiledStateOption:
    option: StateOption
    provenance_option_names: tuple[str, ...]
    semantic_signature: tuple[bool, bool, bool, bool, bool]


def semantic_signature(option: StateOption) -> tuple[bool, bool, bool, bool, bool]:
    return (
        option.releases_semantic_state,
        option.release_proven,
        option.merges_owners,
        option.sharing_proven,
        option.error_bound_known,
    )


def option_objective_vector(
    option: StateOption,
    tiers: Sequence[str],
) -> tuple[float, ...]:
    resident = dict(option.resident_by_tier)
    area = dict(option.byte_seconds_by_tier)
    return tuple(float(resident.get(tier, 0)) for tier in tiers) + tuple(
        float(area.get(tier, 0.0)) for tier in tiers
    ) + (
        float(option.traffic_bytes),
        float(option.compute_cost),
        float(option.latency_cost),
        float(option.error_cost),
    )


def _dominates(left: tuple[float, ...], right: tuple[float, ...]) -> bool:
    if len(left) != len(right):
        raise ValueError("objective_dimension_mismatch")
    return all(x <= y for x, y in zip(left, right)) and any(
        x < y for x, y in zip(left, right)
    )


def compile_state_option_group(
    group: Sequence[StateOption],
    capacities: dict[str, int],
) -> tuple[CompiledStateOption, ...]:
    if not group:
        raise ValueError("empty_option_group")

    state_names = {option.state_name for option in group}
    if len(state_names) != 1:
        raise ValueError("mixed_state_group")

    tiers = tuple(sorted(capacities))
    safe = tuple(option for option in group if option_is_safe(option))
    if not safe:
        return ()

    by_signature: dict[
        tuple[bool, bool, bool, bool, bool],
        list[StateOption],
    ] = {}
    for option in safe:
        by_signature.setdefault(semantic_signature(option), []).append(option)

    compiled = []
    for signature, members in by_signature.items():
        vectors = {
            option.option_name: option_objective_vector(option, tiers)
            for option in members
        }

        local_frontier = []
        for option in members:
            vector = vectors[option.option_name]
            if any(
                other.option_name != option.option_name
                and _dominates(vectors[other.option_name], vector)
                for other in members
            ):
                continue
            local_frontier.append(option)

        by_vector: dict[tuple[float, ...], list[StateOption]] = {}
        for option in local_frontier:
            by_vector.setdefault(
                vectors[option.option_name],
                [],
            ).append(option)

        for vector, tied in by_vector.items():
            canonical = min(tied, key=lambda item: item.option_name)
            compiled.append(
                CompiledStateOption(
                    option=canonical,
                    provenance_option_names=tuple(
                        sorted(option.option_name for option in tied)
                    ),
                    semantic_signature=signature,
                )
            )

    return tuple(
        sorted(
            compiled,
            key=lambda item: (
                option_objective_vector(item.option, tiers),
                item.semantic_signature,
                item.option.option_name,
            ),
        )
    )


def compile_state_option_groups(
    groups: Sequence[Sequence[StateOption]],
    capacities: dict[str, int],
) -> tuple[tuple[CompiledStateOption, ...], ...]:
    return tuple(
        compile_state_option_group(group, capacities)
        for group in groups
    )


def compiled_raw_groups(
    groups: Sequence[Sequence[StateOption]],
    capacities: dict[str, int],
) -> tuple[tuple[StateOption, ...], ...]:
    compiled = compile_state_option_groups(groups, capacities)
    return tuple(
        tuple(item.option for item in group)
        for group in compiled
    )


def _combination_count(groups: Sequence[Sequence[object]]) -> int:
    if not groups:
        return 0
    total = 1
    for group in groups:
        total *= len(group)
    return total


def compilation_statistics(
    groups: Sequence[Sequence[StateOption]],
    capacities: dict[str, int],
) -> dict[str, object]:
    compiled = compile_state_option_groups(groups, capacities)
    raw_count = _combination_count(groups)
    compiled_count = _combination_count(compiled)
    return {
        "raw_group_sizes": tuple(len(group) for group in groups),
        "compiled_group_sizes": tuple(len(group) for group in compiled),
        "raw_combination_count": raw_count,
        "compiled_combination_count": compiled_count,
        "combination_reduction_fraction": (
            1.0 - compiled_count / raw_count
            if raw_count
            else 0.0
        ),
        "provenance": tuple(
            tuple(
                {
                    "canonical": item.option.option_name,
                    "provenance": item.provenance_option_names,
                    "semantic_signature": item.semantic_signature,
                }
                for item in group
            )
            for group in compiled
        ),
    }


def exact_frontier_vectors(
    groups: Sequence[Sequence[StateOption]],
    capacities: dict[str, int],
) -> tuple[tuple[float, ...], ...]:
    if any(not group for group in groups):
        return ()
    tiers = tuple(sorted(capacities))
    frontier = exact_pareto_controller(groups, capacities)
    return tuple(
        sorted({plan.objective_vector(tiers) for plan in frontier})
    )


def quotient_preserves_exact_frontier(
    groups: Sequence[Sequence[StateOption]],
    capacities: dict[str, int],
) -> bool:
    full = exact_frontier_vectors(groups, capacities)
    reduced = exact_frontier_vectors(
        compiled_raw_groups(groups, capacities),
        capacities,
    )
    return full == reduced


def cadence_state_options(
    *,
    memory_high_mib: float,
    state_name: str = "release_cadence",
) -> tuple[StateOption, ...]:
    """Bridge the B449/B452 cadence proxy into the generic StateOption model.

    Units are normalized MiB-equivalent values for this controller experiment.
    advice_calls is mapped to traffic_bytes; pressure and pgscan proxies map to
    compute/latency penalties. This is an integration model, not a syscall-cost
    measurement.
    """
    options = []
    for cadence in (32, 48, 64, 80, 96):
        plan = twin_plan(
            arm=f"dontneed_{cadence}m",
            memory_high_mib=memory_high_mib,
        )
        options.append(
            StateOption(
                state_name=state_name,
                option_name=f"dontneed_{cadence}m",
                resident_by_tier=(("RAM", int(round(plan.peak_mib))), ("VRAM", 0)),
                byte_seconds_by_tier=(("RAM", float(plan.peak_mib)), ("VRAM", 0.0)),
                traffic_bytes=float(plan.advice_calls),
                compute_cost=float(plan.pressure),
                latency_cost=float(plan.pgscan_proxy),
                error_cost=0.0,
            )
        )
    return tuple(options)
