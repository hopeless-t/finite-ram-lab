from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Iterable


@dataclass(frozen=True)
class TierTraceState:
    name: str
    live_start: float
    live_end: float
    tier: str
    resident_bytes: int
    logical_bytes: int = 0

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("name_empty")
        if not self.tier:
            raise ValueError("tier_empty")
        if not isinstance(self.live_start, (int, float)) or not isfinite(self.live_start):
            raise ValueError("live_start_invalid")
        if not isinstance(self.live_end, (int, float)) or not isfinite(self.live_end):
            raise ValueError("live_end_invalid")
        if self.live_end <= self.live_start:
            raise ValueError("live_interval_invalid")
        if type(self.resident_bytes) is not int or self.resident_bytes < 0:
            raise ValueError("resident_bytes_invalid")
        if type(self.logical_bytes) is not int or self.logical_bytes < 0:
            raise ValueError("logical_bytes_invalid")


def compile_tiered_frontier(states: Iterable[TierTraceState]) -> dict[str, object]:
    items = tuple(states)
    if not items:
        return {
            "logical_peak_bytes": 0,
            "total_resident_peak_bytes": 0,
            "tier_peak_bytes": {},
            "tier_byte_seconds": {},
            "windows": [],
        }

    boundaries = sorted({x for s in items for x in (s.live_start, s.live_end)})
    tiers = sorted({s.tier for s in items})
    tier_peaks = {tier: 0 for tier in tiers}
    tier_areas = {tier: 0.0 for tier in tiers}
    logical_peak = 0
    total_peak = 0
    windows: list[dict[str, object]] = []

    for left, right in zip(boundaries, boundaries[1:]):
        if right <= left:
            continue
        active = tuple(s for s in items if s.live_start <= left and s.live_end >= right)
        duration = right - left
        logical = sum(s.logical_bytes for s in active)
        by_tier = {
            tier: sum(s.resident_bytes for s in active if s.tier == tier)
            for tier in tiers
        }
        total = sum(by_tier.values())

        logical_peak = max(logical_peak, logical)
        total_peak = max(total_peak, total)
        for tier, value in by_tier.items():
            tier_peaks[tier] = max(tier_peaks[tier], value)
            tier_areas[tier] += value * duration

        windows.append({
            "start": left,
            "end": right,
            "logical_bytes": logical,
            "resident_by_tier": by_tier,
            "total_resident_bytes": total,
            "active": [s.name for s in active],
        })

    return {
        "logical_peak_bytes": logical_peak,
        "total_resident_peak_bytes": total_peak,
        "tier_peak_bytes": tier_peaks,
        "tier_byte_seconds": tier_areas,
        "windows": windows,
    }


def capacity_ratios(
    tier_peak_bytes: dict[str, int],
    capacities: dict[str, int],
) -> dict[str, float | None]:
    out: dict[str, float | None] = {}
    for tier, peak in tier_peak_bytes.items():
        capacity = capacities.get(tier)
        if capacity is None:
            out[tier] = None
            continue
        if type(capacity) is not int or capacity <= 0:
            raise ValueError("capacity_invalid")
        out[tier] = peak / capacity
    return out
