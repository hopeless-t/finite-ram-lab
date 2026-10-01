from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Iterable

from finite_ram_lab.live_state_frontier import (
    ReleaseMode,
    State as ReleaseState,
    safe_release_mode,
)


@dataclass(frozen=True)
class TraceState:
    name: str
    live_start: float
    live_end: float
    logical_bytes: int
    encoded_bytes: int
    replicas: int = 1
    metadata_bytes_per_replica: int = 0
    fragmentation_bytes: int = 0
    workspace_bytes: int = 0
    expected_accesses: float = 0.0
    fast_access_cost: float = 0.0
    slow_access_cost: float = 0.0
    recompute_cost: float = 0.0
    recomputable: bool = False
    summary_bytes: int | None = None
    summary_sufficient: bool = False

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("name_empty")
        for field in ("live_start", "live_end"):
            value = getattr(self, field)
            if not isinstance(value, (int, float)) or not isfinite(value):
                raise ValueError(f"{field}_invalid")
        if self.live_end <= self.live_start:
            raise ValueError("live_interval_invalid")
        for field in (
            "logical_bytes",
            "encoded_bytes",
            "metadata_bytes_per_replica",
            "fragmentation_bytes",
            "workspace_bytes",
        ):
            value = getattr(self, field)
            if type(value) is not int or value < 0:
                raise ValueError(f"{field}_invalid")
        if type(self.replicas) is not int or self.replicas < 1:
            raise ValueError("replicas_invalid")
        for field in (
            "expected_accesses",
            "fast_access_cost",
            "slow_access_cost",
            "recompute_cost",
        ):
            value = getattr(self, field)
            if not isinstance(value, (int, float)) or not isfinite(value) or value < 0:
                raise ValueError(f"{field}_invalid")
        if self.summary_bytes is not None:
            if type(self.summary_bytes) is not int or self.summary_bytes < 0:
                raise ValueError("summary_bytes_invalid")
        if self.summary_sufficient and self.summary_bytes is None:
            raise ValueError("summary_sufficient_without_summary")

    @property
    def physical_bytes(self) -> int:
        return (
            self.encoded_bytes * self.replicas
            + self.metadata_bytes_per_replica * self.replicas
            + self.fragmentation_bytes
            + self.workspace_bytes
        )

    def release_state(self) -> ReleaseState:
        return ReleaseState(
            name=self.name,
            size_bytes=max(1, self.physical_bytes),
            expected_accesses=self.expected_accesses,
            fast_access_cost=self.fast_access_cost,
            slow_access_cost=self.slow_access_cost,
            recompute_cost=self.recompute_cost,
            recomputable=self.recomputable,
            summary_bytes=self.summary_bytes,
            summary_sufficient=self.summary_sufficient,
        )


def compile_frontier(states: Iterable[TraceState]) -> dict[str, object]:
    items = tuple(states)
    if not items:
        return {
            "logical_peak_bytes": 0,
            "physical_peak_bytes": 0,
            "logical_byte_seconds": 0.0,
            "physical_byte_seconds": 0.0,
            "peak_windows": [],
            "release_candidates": [],
        }

    boundaries = sorted({x for s in items for x in (s.live_start, s.live_end)})
    logical_peak = 0
    physical_peak = 0
    logical_area = 0.0
    physical_area = 0.0
    windows: list[dict[str, object]] = []

    for left, right in zip(boundaries, boundaries[1:]):
        if right <= left:
            continue
        active = tuple(s for s in items if s.live_start <= left and s.live_end >= right)
        logical = sum(s.logical_bytes for s in active)
        physical = sum(s.physical_bytes for s in active)
        duration = right - left
        logical_area += logical * duration
        physical_area += physical * duration
        logical_peak = max(logical_peak, logical)
        physical_peak = max(physical_peak, physical)
        windows.append({
            "start": left,
            "end": right,
            "logical_bytes": logical,
            "physical_bytes": physical,
            "active": [s.name for s in active],
        })

    peak_windows = [
        w
        for w in windows
        if w["logical_bytes"] == logical_peak or w["physical_bytes"] == physical_peak
    ]

    release_candidates = []
    for state in items:
        mode = safe_release_mode(state.release_state())
        if mode is not ReleaseMode.RETAIN_OR_MOVE:
            release_candidates.append({
                "name": state.name,
                "mode": mode.value,
            })

    return {
        "logical_peak_bytes": logical_peak,
        "physical_peak_bytes": physical_peak,
        "logical_byte_seconds": logical_area,
        "physical_byte_seconds": physical_area,
        "peak_windows": peak_windows,
        "release_candidates": release_candidates,
    }


def potential_dedup_savings(state: TraceState) -> int:
    if state.replicas <= 1:
        return 0
    before = state.encoded_bytes * state.replicas
    after = state.encoded_bytes + state.metadata_bytes_per_replica * state.replicas
    return max(0, before - after)


def capacity_cliff_ratio(physical_peak_bytes: int, effective_capacity_bytes: int) -> float:
    if type(physical_peak_bytes) is not int or physical_peak_bytes < 0:
        raise ValueError("physical_peak_bytes_invalid")
    if type(effective_capacity_bytes) is not int or effective_capacity_bytes <= 0:
        raise ValueError("effective_capacity_bytes_invalid")
    return physical_peak_bytes / effective_capacity_bytes
