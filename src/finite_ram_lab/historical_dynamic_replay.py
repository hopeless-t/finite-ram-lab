from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Iterable, Sequence


@dataclass(frozen=True)
class ProjectedObservation:
    plan_id: str
    objectives: tuple[tuple[str, float], ...]

    def __post_init__(self) -> None:
        if not self.plan_id:
            raise ValueError("plan_id_empty")
        if not self.objectives:
            raise ValueError("objectives_empty")
        seen = set()
        for name, value in self.objectives:
            if not name or name in seen:
                raise ValueError("objective_name_invalid")
            seen.add(name)
            if not isinstance(value, (int, float)) or not isfinite(value):
                raise ValueError("objective_value_invalid")

    def vector(self, names: Sequence[str]) -> tuple[float, ...]:
        values = dict(self.objectives)
        if any(name not in values for name in names):
            raise ValueError("objective_projection_mismatch")
        return tuple(float(values[name]) for name in names)


def projected_frontier(
    observations: Iterable[ProjectedObservation],
    objective_names: Sequence[str],
) -> tuple[ProjectedObservation, ...]:
    items = tuple(observations)
    out = []
    for i, plan in enumerate(items):
        a = plan.vector(objective_names)
        dominated = False
        for j, other in enumerate(items):
            if i == j:
                continue
            b = other.vector(objective_names)
            if all(x <= y for x, y in zip(b, a)) and any(
                x < y for x, y in zip(b, a)
            ):
                dominated = True
                break
        if not dominated:
            out.append(plan)
    return tuple(sorted(out, key=lambda p: (p.vector(objective_names), p.plan_id)))


def changed_objectives(
    before: ProjectedObservation,
    after: ProjectedObservation,
    objective_names: Sequence[str],
    *,
    tolerance: float = 0.0,
) -> tuple[tuple[str, float], ...]:
    if before.plan_id != after.plan_id:
        raise ValueError("plan_identity_mismatch")
    if tolerance < 0:
        raise ValueError("tolerance_invalid")

    a = before.vector(objective_names)
    b = after.vector(objective_names)
    return tuple(
        (name, y - x)
        for name, x, y in zip(objective_names, a, b)
        if abs(y - x) > tolerance
    )


def _dominates(
    left: ProjectedObservation,
    right: ProjectedObservation,
    objective_names: Sequence[str],
) -> bool:
    a = left.vector(objective_names)
    b = right.vector(objective_names)
    return all(x <= y for x, y in zip(a, b)) and any(
        x < y for x, y in zip(a, b)
    )


def compare_projected_pair(
    smaller: Sequence[ProjectedObservation],
    larger: Sequence[ProjectedObservation],
    objective_names: Sequence[str],
    *,
    tolerance: float = 0.0,
) -> dict[str, object]:
    small_by_id = {p.plan_id: p for p in smaller}
    large_by_id = {p.plan_id: p for p in larger}
    if len(small_by_id) != len(smaller):
        raise ValueError("duplicate_plan_id_small")
    if len(large_by_id) != len(larger):
        raise ValueError("duplicate_plan_id_large")

    small_frontier = projected_frontier(smaller, objective_names)
    large_frontier = projected_frontier(larger, objective_names)
    small_ids = {p.plan_id for p in small_frontier}
    large_ids = {p.plan_id for p in large_frontier}

    lost = sorted(small_ids - large_ids)
    added = sorted(large_ids - small_ids)
    explanations = []

    for plan_id in lost:
        before = small_by_id[plan_id]
        after = large_by_id.get(plan_id)

        if after is None:
            explanations.append({
                "plan_id": plan_id,
                "classification": "MISSING_LARGER_OBSERVATION",
                "changed_objectives": (),
                "dominators": (),
                "dominator_changes": {},
            })
            continue

        own_changes = changed_objectives(
            before,
            after,
            objective_names,
            tolerance=tolerance,
        )

        dominators = tuple(
            sorted(
                p.plan_id
                for p in larger
                if p.plan_id != plan_id
                and _dominates(p, after, objective_names)
            )
        )

        dominator_changes = {}
        for dominator_id in dominators:
            if dominator_id not in small_by_id:
                continue
            changes = changed_objectives(
                small_by_id[dominator_id],
                large_by_id[dominator_id],
                objective_names,
                tolerance=tolerance,
            )
            if changes:
                dominator_changes[dominator_id] = changes

        new_dominator = any(
            dominator_id not in small_by_id
            for dominator_id in dominators
        )

        if own_changes and dominator_changes:
            classification = "LOST_WITH_SELF_AND_DOMINATOR_COST_SHIFT"
        elif own_changes:
            classification = "LOST_WITH_SELF_COST_SHIFT"
        elif dominator_changes:
            classification = "LOST_WITH_DOMINATOR_COST_SHIFT"
        elif new_dominator:
            classification = "LOST_WITH_NEW_OR_PREVIOUSLY_UNOBSERVED_DOMINATOR"
        else:
            classification = "UNEXPLAINED_STATIC_MONOTONICITY_VIOLATION"

        explanations.append({
            "plan_id": plan_id,
            "classification": classification,
            "changed_objectives": own_changes,
            "dominators": dominators,
            "dominator_changes": dominator_changes,
        })

    return {
        "objective_names": tuple(objective_names),
        "small_frontier_ids": tuple(sorted(small_ids)),
        "large_frontier_ids": tuple(sorted(large_ids)),
        "lost_frontier_ids": tuple(lost),
        "added_frontier_ids": tuple(added),
        "monotonicity_violation": bool(lost),
        "explanations": tuple(explanations),
    }


def strata005_observations(
    summary: dict[str, object],
    memory_high_mib: int,
) -> tuple[ProjectedObservation, ...]:
    try:
        cells = summary["cells"][str(memory_high_mib)]
    except (KeyError, TypeError) as exc:
        raise ValueError("memory_high_not_found") from exc

    observations = []
    for arm, cell in sorted(cells.items()):
        observations.append(
            ProjectedObservation(
                plan_id=str(arm),
                objectives=(
                    ("peak_ram_bytes", float(cell["median_max_scan_memory_bytes"])),
                    ("memory_high_events", float(cell["median_memory_high_events"])),
                    ("pgscan", float(cell["median_pgscan"])),
                    ("scan_elapsed_ns", float(cell["median_scan_elapsed_ns"])),
                ),
            )
        )
    return tuple(observations)


STRATA005_OBJECTIVES = (
    "peak_ram_bytes",
    "memory_high_events",
    "pgscan",
    "scan_elapsed_ns",
)
