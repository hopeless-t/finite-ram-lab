from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Sequence


DEFAULT_CADENCES_MIB = (32, 48, 64, 80, 96)
DEFAULT_FILE_SPAN_MIB = 96.0
DEFAULT_TRANSIENT_BASE_MIB = 78.609
DEFAULT_CLEAN_FLOOR_PROXY_MIB = 76.7


@dataclass(frozen=True)
class InterventionPlan:
    cadence_mib: int
    peak_mib: float
    ephemeral_excess_mib: float
    pressure: int
    pgscan_proxy: int
    advice_calls: int

    def vector(self) -> tuple[float, ...]:
        return (
            self.peak_mib,
            self.ephemeral_excess_mib,
            float(self.pressure),
            float(self.pgscan_proxy),
            float(self.advice_calls),
        )


def advice_calls(
    *,
    file_span_mib: float,
    cadence_mib: int,
) -> int:
    if file_span_mib <= 0:
        raise ValueError("file_span_invalid")
    if type(cadence_mib) is not int or cadence_mib <= 0:
        raise ValueError("cadence_invalid")
    return int(ceil(file_span_mib / cadence_mib))


def modeled_plan(
    *,
    memory_high_mib: float,
    cadence_mib: int,
    transient_base_mib: float = DEFAULT_TRANSIENT_BASE_MIB,
    clean_floor_mib: float = DEFAULT_CLEAN_FLOOR_PROXY_MIB,
    file_span_mib: float = DEFAULT_FILE_SPAN_MIB,
) -> InterventionPlan:
    if memory_high_mib <= 0:
        raise ValueError("memory_high_invalid")
    intrinsic = transient_base_mib + cadence_mib
    peak = min(intrinsic, memory_high_mib)
    if peak < clean_floor_mib:
        raise ValueError("capacity_below_clean_floor_proxy")
    pressure = int(intrinsic > memory_high_mib)
    return InterventionPlan(
        cadence_mib=cadence_mib,
        peak_mib=float(peak),
        ephemeral_excess_mib=float(peak - clean_floor_mib),
        pressure=pressure,
        pgscan_proxy=pressure,
        advice_calls=advice_calls(
            file_span_mib=file_span_mib,
            cadence_mib=cadence_mib,
        ),
    )


def pareto_cadences(plans: Sequence[InterventionPlan]) -> tuple[int, ...]:
    out = []
    for i, plan in enumerate(plans):
        dominated = False
        a = plan.vector()
        for j, other in enumerate(plans):
            if i == j:
                continue
            b = other.vector()
            if all(x <= y for x, y in zip(b, a)) and any(
                x < y for x, y in zip(b, a)
            ):
                dominated = True
                break
        if not dominated:
            out.append(plan.cadence_mib)
    return tuple(sorted(out))


def brute_frontier(
    *,
    memory_high_mib: float,
    cadences_mib: Sequence[int] = DEFAULT_CADENCES_MIB,
    transient_base_mib: float = DEFAULT_TRANSIENT_BASE_MIB,
    clean_floor_mib: float = DEFAULT_CLEAN_FLOOR_PROXY_MIB,
    file_span_mib: float = DEFAULT_FILE_SPAN_MIB,
) -> tuple[int, ...]:
    return pareto_cadences(
        tuple(
            modeled_plan(
                memory_high_mib=memory_high_mib,
                cadence_mib=cadence,
                transient_base_mib=transient_base_mib,
                clean_floor_mib=clean_floor_mib,
                file_span_mib=file_span_mib,
            )
            for cadence in cadences_mib
        )
    )


def frozen_staircase_frontier(
    *,
    memory_high_mib: float,
    transient_base_mib: float = DEFAULT_TRANSIENT_BASE_MIB,
) -> tuple[int, ...]:
    """Closed form for the frozen 32/48/64/80/96 MiB cadence set.

    Thresholds are inclusive on the pressure-free side because pressure is
    defined by B + K > H.
    """
    t32 = transient_base_mib + 32
    t48 = transient_base_mib + 48
    if memory_high_mib < t32:
        return (96,)
    if memory_high_mib < t48:
        return (32, 96)
    return (32, 48, 96)


def staircase_thresholds(
    *,
    transient_base_mib: float = DEFAULT_TRANSIENT_BASE_MIB,
) -> dict[str, float]:
    return {
        "activate_32_tradeoff_mib": transient_base_mib + 32,
        "activate_48_tradeoff_mib": transient_base_mib + 48,
    }


def cadence_roles() -> dict[int, str]:
    return {
        32: "three-call minimum-memory frontier arm",
        48: "two-call minimum-memory frontier arm",
        64: "two-call mechanism arm dominated by 48",
        80: "two-call threshold-localization arm dominated by 48",
        96: "one-call minimum-intervention frontier arm",
    }
