from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite
from typing import Iterable


class ReleaseMode(str, Enum):
    REDUCE_AND_RELEASE = "REDUCE_AND_RELEASE"
    DROP_REMATERIALIZE = "DROP_REMATERIALIZE"
    RETAIN_OR_MOVE = "RETAIN_OR_MOVE"


@dataclass(frozen=True)
class State:
    name: str
    size_bytes: int
    expected_accesses: float
    fast_access_cost: float
    slow_access_cost: float
    recompute_cost: float
    recomputable: bool = False
    summary_bytes: int | None = None
    summary_sufficient: bool = False

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("name_empty")
        if type(self.size_bytes) is not int or self.size_bytes <= 0:
            raise ValueError("size_bytes_invalid")
        for name in (
            "expected_accesses",
            "fast_access_cost",
            "slow_access_cost",
            "recompute_cost",
        ):
            value = getattr(self, name)
            if not isinstance(value, (int, float)) or not isfinite(value) or value < 0:
                raise ValueError(f"{name}_invalid")
        if self.summary_bytes is not None:
            if type(self.summary_bytes) is not int or self.summary_bytes < 0:
                raise ValueError("summary_bytes_invalid")
        if self.summary_sufficient and self.summary_bytes is None:
            raise ValueError("summary_sufficient_without_summary")


def safe_release_mode(state: State) -> ReleaseMode:
    """Return the strongest correctness-preserving release mode known locally.

    A state can be reduced away only when an explicitly declared future-sufficient
    summary is smaller than the state. Otherwise it can be dropped only when it is
    explicitly declared recomputable. Missing proof stays RETAIN_OR_MOVE.
    """
    if (
        state.summary_sufficient
        and state.summary_bytes is not None
        and state.summary_bytes < state.size_bytes
    ):
        return ReleaseMode.REDUCE_AND_RELEASE
    if state.recomputable:
        return ReleaseMode.DROP_REMATERIALIZE
    return ReleaseMode.RETAIN_OR_MOVE


def resident_value_density(state: State) -> float:
    """Expected fast-tier access-cost savings per resident byte."""
    saved_per_access = max(0.0, state.slow_access_cost - state.fast_access_cost)
    return state.expected_accesses * saved_per_access / state.size_bytes


def release_net_benefit(
    state: State,
    *,
    shadow_price_per_byte_second: float,
    horizon_seconds: float,
    transform_cost: float = 0.0,
) -> float:
    """Local exchange value for releasing a state over a bounded horizon.

    Positive means modeled carrying-cost savings exceed summary/recompute cost.
    RETAIN_OR_MOVE is represented by negative infinity because safe release has
    not been established by the model.
    """
    for name, value in (
        ("shadow_price_per_byte_second", shadow_price_per_byte_second),
        ("horizon_seconds", horizon_seconds),
        ("transform_cost", transform_cost),
    ):
        if not isinstance(value, (int, float)) or not isfinite(value) or value < 0:
            raise ValueError(f"{name}_invalid")

    mode = safe_release_mode(state)
    if mode is ReleaseMode.REDUCE_AND_RELEASE:
        assert state.summary_bytes is not None
        freed = state.size_bytes - state.summary_bytes
        return shadow_price_per_byte_second * freed * horizon_seconds - transform_cost

    if mode is ReleaseMode.DROP_REMATERIALIZE:
        expected_recompute = state.expected_accesses * state.recompute_cost
        return (
            shadow_price_per_byte_second * state.size_bytes * horizon_seconds
            - expected_recompute
            - transform_cost
        )

    return float("-inf")


def exact_fast_residency(states: Iterable[State], capacity_bytes: int) -> dict[str, object]:
    """Solve a tiny bounded fast-tier placement problem exactly by enumeration.

    This is model-validation infrastructure, not a production scheduler.
    It maximizes expected access-cost savings subject to byte capacity.
    """
    if type(capacity_bytes) is not int or capacity_bytes < 0:
        raise ValueError("capacity_bytes_invalid")

    items = tuple(states)
    if len(items) > 20:
        raise ValueError("exact_enumerator_state_limit")

    best_value = -1.0
    best_size = 0
    best_names: tuple[str, ...] = ()

    for mask in range(1 << len(items)):
        size = 0
        value = 0.0
        names: list[str] = []
        feasible = True

        for index, state in enumerate(items):
            if mask & (1 << index):
                size += state.size_bytes
                if size > capacity_bytes:
                    feasible = False
                    break
                value += (
                    state.expected_accesses
                    * max(0.0, state.slow_access_cost - state.fast_access_cost)
                )
                names.append(state.name)

        if not feasible:
            continue

        if (
            value > best_value
            or (value == best_value and size < best_size)
            or (
                value == best_value
                and size == best_size
                and tuple(names) < best_names
            )
        ):
            best_value = value
            best_size = size
            best_names = tuple(names)

    return {
        "resident": list(best_names),
        "used_bytes": best_size,
        "expected_access_savings": best_value,
    }


def greedy_fast_residency(states: Iterable[State], capacity_bytes: int) -> dict[str, object]:
    """Value-density heuristic for larger bounded-horizon placement problems."""
    if type(capacity_bytes) is not int or capacity_bytes < 0:
        raise ValueError("capacity_bytes_invalid")

    ordered = sorted(
        tuple(states),
        key=lambda state: (-resident_value_density(state), state.size_bytes, state.name),
    )

    remaining = capacity_bytes
    resident: list[str] = []
    used = 0
    value = 0.0

    for state in ordered:
        if state.size_bytes <= remaining:
            resident.append(state.name)
            remaining -= state.size_bytes
            used += state.size_bytes
            value += (
                state.expected_accesses
                * max(0.0, state.slow_access_cost - state.fast_access_cost)
            )

    return {
        "resident": resident,
        "used_bytes": used,
        "expected_access_savings": value,
    }
