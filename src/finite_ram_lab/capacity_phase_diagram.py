from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from finite_ram_lab.bounded_frontier_controller import (
    CandidatePlan,
    StateOption,
    exact_pareto_controller,
)


@dataclass(frozen=True)
class PhaseCell:
    ram_mib: int
    vram_mib: int
    exact_frontier_points: int
    signature: tuple[tuple[str, tuple[str, ...]], ...]


@dataclass(frozen=True)
class PhaseTransition:
    axis: str
    from_capacity: tuple[int, int]
    to_capacity: tuple[int, int]
    added: tuple[tuple[str, tuple[str, ...]], ...]
    removed: tuple[tuple[str, tuple[str, ...]], ...]


def plan_identity(plan: CandidatePlan) -> tuple[tuple[str, str], ...]:
    return plan.choices


def frontier_signature(
    plans: Sequence[CandidatePlan],
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    by_state: dict[str, set[str]] = {}
    for plan in plans:
        for state, option in plan.choices:
            by_state.setdefault(state, set()).add(option)
    return tuple(
        (state, tuple(sorted(options)))
        for state, options in sorted(by_state.items())
    )


def signature_delta(
    before: tuple[tuple[str, tuple[str, ...]], ...],
    after: tuple[tuple[str, tuple[str, ...]], ...],
) -> tuple[
    tuple[tuple[str, tuple[str, ...]], ...],
    tuple[tuple[str, tuple[str, ...]], ...],
]:
    left = {state: set(options) for state, options in before}
    right = {state: set(options) for state, options in after}
    states = sorted(set(left) | set(right))

    added = []
    removed = []
    for state in states:
        plus = tuple(sorted(right.get(state, set()) - left.get(state, set())))
        minus = tuple(sorted(left.get(state, set()) - right.get(state, set())))
        if plus:
            added.append((state, plus))
        if minus:
            removed.append((state, minus))

    return tuple(added), tuple(removed)


def capacity_leq(
    left: dict[str, int],
    right: dict[str, int],
) -> bool:
    tiers = set(left) | set(right)
    return all(left.get(tier, 0) <= right.get(tier, 0) for tier in tiers)


def frontier_is_monotone_under_capacity_expansion(
    option_groups: Sequence[Sequence[StateOption]],
    smaller: dict[str, int],
    larger: dict[str, int],
) -> bool:
    if not capacity_leq(smaller, larger):
        raise ValueError("capacity_order_invalid")

    before = exact_pareto_controller(option_groups, smaller)
    after = exact_pareto_controller(option_groups, larger)

    before_ids = {plan_identity(plan) for plan in before}
    after_ids = {plan_identity(plan) for plan in after}
    return before_ids <= after_ids


def phase_grid(
    option_groups: Sequence[Sequence[StateOption]],
    *,
    ram_capacities_mib: Sequence[int],
    vram_capacities_mib: Sequence[int],
) -> tuple[PhaseCell, ...]:
    cells = []
    for ram in ram_capacities_mib:
        for vram in vram_capacities_mib:
            exact = exact_pareto_controller(
                option_groups,
                {"RAM": int(ram), "VRAM": int(vram)},
            )
            cells.append(
                PhaseCell(
                    ram_mib=int(ram),
                    vram_mib=int(vram),
                    exact_frontier_points=len(exact),
                    signature=frontier_signature(exact),
                )
            )
    return tuple(cells)


def neighboring_transitions(
    cells: Sequence[PhaseCell],
    *,
    ram_capacities_mib: Sequence[int],
    vram_capacities_mib: Sequence[int],
) -> tuple[PhaseTransition, ...]:
    lookup = {(cell.ram_mib, cell.vram_mib): cell for cell in cells}
    out = []

    for ri, ram in enumerate(ram_capacities_mib):
        for vi, vram in enumerate(vram_capacities_mib):
            current = lookup[(ram, vram)]
            for axis, nri, nvi in (
                ("RAM", ri + 1, vi),
                ("VRAM", ri, vi + 1),
            ):
                if nri >= len(ram_capacities_mib) or nvi >= len(vram_capacities_mib):
                    continue

                nxt = lookup[
                    (
                        ram_capacities_mib[nri],
                        vram_capacities_mib[nvi],
                    )
                ]
                if current.signature == nxt.signature:
                    continue

                added, removed = signature_delta(
                    current.signature,
                    nxt.signature,
                )
                out.append(
                    PhaseTransition(
                        axis=axis,
                        from_capacity=(current.ram_mib, current.vram_mib),
                        to_capacity=(nxt.ram_mib, nxt.vram_mib),
                        added=added,
                        removed=removed,
                    )
                )

    return tuple(out)


def unique_regime_count(cells: Sequence[PhaseCell]) -> int:
    return len({cell.signature for cell in cells if cell.signature})
