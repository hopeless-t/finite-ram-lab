from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Iterable, Sequence


@dataclass(frozen=True)
class ObservedPlan:
    plan_id: str
    resident_by_tier: tuple[tuple[str, int], ...]
    byte_seconds_by_tier: tuple[tuple[str, float], ...]
    traffic: float = 0.0
    compute: float = 0.0
    latency: float = 0.0
    error: float = 0.0

    def __post_init__(self) -> None:
        if not self.plan_id:
            raise ValueError("plan_id_empty")
        _validate_pairs(self.resident_by_tier, integer=True)
        _validate_pairs(self.byte_seconds_by_tier, integer=False)
        for name in ("traffic", "compute", "latency", "error"):
            value = getattr(self, name)
            if not isinstance(value, (int, float)) or not isfinite(value) or value < 0:
                raise ValueError(f"{name}_invalid")

    def objective_vector(self, tiers: Sequence[str]) -> tuple[float, ...]:
        peaks = dict(self.resident_by_tier)
        areas = dict(self.byte_seconds_by_tier)
        return tuple(float(peaks.get(tier, 0)) for tier in tiers) + tuple(
            float(areas.get(tier, 0.0)) for tier in tiers
        ) + (
            float(self.traffic),
            float(self.compute),
            float(self.latency),
            float(self.error),
        )


def _validate_pairs(pairs, *, integer: bool) -> None:
    seen = set()
    for tier, value in pairs:
        if not tier or tier in seen:
            raise ValueError("tier_pairs_invalid")
        seen.add(tier)
        if integer:
            if type(value) is not int or value < 0:
                raise ValueError("resident_bytes_invalid")
        else:
            if not isinstance(value, (int, float)) or not isfinite(value) or value < 0:
                raise ValueError("byte_seconds_invalid")


def observation_dominates(
    left: ObservedPlan,
    right: ObservedPlan,
    tiers: Sequence[str],
) -> bool:
    a = left.objective_vector(tiers)
    b = right.objective_vector(tiers)
    return all(x <= y for x, y in zip(a, b)) and any(
        x < y for x, y in zip(a, b)
    )


def observed_frontier(
    observations: Iterable[ObservedPlan],
    tiers: Sequence[str],
) -> tuple[ObservedPlan, ...]:
    items = tuple(observations)
    out = []
    for i, plan in enumerate(items):
        if any(
            j != i and observation_dominates(other, plan, tiers)
            for j, other in enumerate(items)
        ):
            continue
        out.append(plan)
    return tuple(sorted(out, key=lambda p: (p.objective_vector(tiers), p.plan_id)))


def objective_delta(
    before: ObservedPlan,
    after: ObservedPlan,
    tiers: Sequence[str],
) -> dict[str, float]:
    if before.plan_id != after.plan_id:
        raise ValueError("plan_identity_mismatch")
    names = (
        tuple(f"peak:{tier}" for tier in tiers)
        + tuple(f"area:{tier}" for tier in tiers)
        + ("traffic", "compute", "latency", "error")
    )
    a = before.objective_vector(tiers)
    b = after.objective_vector(tiers)
    return {name: y - x for name, x, y in zip(names, a, b)}


def changed_coordinates(
    before: ObservedPlan,
    after: ObservedPlan,
    tiers: Sequence[str],
    *,
    tolerance: float = 0.0,
) -> tuple[tuple[str, float], ...]:
    if tolerance < 0:
        raise ValueError("tolerance_invalid")
    return tuple(
        (name, delta)
        for name, delta in objective_delta(before, after, tiers).items()
        if abs(delta) > tolerance
    )


def compare_measured_capacity_pair(
    smaller_observations: Sequence[ObservedPlan],
    larger_observations: Sequence[ObservedPlan],
    tiers: Sequence[str],
    *,
    tolerance: float = 0.0,
) -> dict[str, object]:
    small_by_id = {p.plan_id: p for p in smaller_observations}
    large_by_id = {p.plan_id: p for p in larger_observations}
    if len(small_by_id) != len(smaller_observations):
        raise ValueError("duplicate_plan_id_small")
    if len(large_by_id) != len(larger_observations):
        raise ValueError("duplicate_plan_id_large")

    small_frontier = observed_frontier(smaller_observations, tiers)
    large_frontier = observed_frontier(larger_observations, tiers)
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
                "changed_coordinates": (),
                "dominators": (),
            })
            continue

        own_changes = changed_coordinates(
            before,
            after,
            tiers,
            tolerance=tolerance,
        )
        dominators = tuple(
            p.plan_id
            for p in larger_observations
            if p.plan_id != plan_id and observation_dominates(p, after, tiers)
        )

        dominator_changes = {}
        for dominator_id in dominators:
            if dominator_id in small_by_id:
                changes = changed_coordinates(
                    small_by_id[dominator_id],
                    large_by_id[dominator_id],
                    tiers,
                    tolerance=tolerance,
                )
                if changes:
                    dominator_changes[dominator_id] = changes

        if own_changes:
            classification = "LOST_WITH_SELF_COST_SHIFT"
        elif dominator_changes:
            classification = "LOST_WITH_DOMINATOR_COST_SHIFT"
        elif any(d not in small_by_id for d in dominators):
            classification = "LOST_WITH_NEW_OR_PREVIOUSLY_UNOBSERVED_DOMINATOR"
        else:
            classification = "UNEXPLAINED_STATIC_MONOTONICITY_VIOLATION"

        explanations.append({
            "plan_id": plan_id,
            "classification": classification,
            "changed_coordinates": own_changes,
            "dominators": dominators,
            "dominator_changes": dominator_changes,
        })

    return {
        "small_frontier_ids": tuple(sorted(small_ids)),
        "large_frontier_ids": tuple(sorted(large_ids)),
        "lost_frontier_ids": tuple(lost),
        "added_frontier_ids": tuple(added),
        "monotonicity_violation": bool(lost),
        "explanations": tuple(explanations),
    }


def synthetic_observation(
    plan_id: str,
    *,
    ram: int,
    vram: int,
    ram_area: float | None = None,
    vram_area: float | None = None,
    traffic: float = 0.0,
    compute: float = 0.0,
    latency: float = 0.0,
    error: float = 0.0,
) -> ObservedPlan:
    return ObservedPlan(
        plan_id=plan_id,
        resident_by_tier=(("RAM", ram), ("VRAM", vram)),
        byte_seconds_by_tier=(
            ("RAM", float(ram if ram_area is None else ram_area)),
            ("VRAM", float(vram if vram_area is None else vram_area)),
        ),
        traffic=traffic,
        compute=compute,
        latency=latency,
        error=error,
    )
