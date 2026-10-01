from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class TwinPlan:
    arm: str
    peak_mib: float
    ephemeral_excess_mib: float
    memory_high_events_proxy: int
    pgscan_proxy: int
    advice_calls: int

    def vector(self) -> tuple[float, ...]:
        return (
            self.peak_mib,
            self.ephemeral_excess_mib,
            float(self.memory_high_events_proxy),
            float(self.pgscan_proxy),
            float(self.advice_calls),
        )


RELEASE_MIB = {
    "dontneed_32m": 32,
    "dontneed_48m": 48,
    "dontneed_64m": 64,
    "dontneed_80m": 80,
    "dontneed_96m": 96,
}

ADVICE_CALLS = {
    "dontneed_32m": 3,
    "dontneed_48m": 2,
    "dontneed_64m": 2,
    "dontneed_80m": 2,
    "dontneed_96m": 1,
}


def twin_plan(
    *,
    arm: str,
    memory_high_mib: float,
    transient_base_mib: float = 78.609,
    clean_floor_proxy_mib: float = 76.7,
) -> TwinPlan:
    release = RELEASE_MIB[arm]
    intrinsic = transient_base_mib + release
    peak = min(intrinsic, memory_high_mib)
    pressure = int(intrinsic > memory_high_mib)

    return TwinPlan(
        arm=arm,
        peak_mib=peak,
        ephemeral_excess_mib=peak - clean_floor_proxy_mib,
        memory_high_events_proxy=pressure,
        pgscan_proxy=pressure,
        advice_calls=ADVICE_CALLS[arm],
    )


def pareto_arms(plans: Sequence[TwinPlan]) -> tuple[str, ...]:
    out = []
    for i, plan in enumerate(plans):
        a = plan.vector()
        dominated = False
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
            out.append(plan.arm)
    return tuple(sorted(out))


def expected_candidate_frontier(
    memory_high_mib: float,
) -> tuple[str, ...]:
    plans = [
        twin_plan(arm=arm, memory_high_mib=memory_high_mib)
        for arm in RELEASE_MIB
    ]
    return pareto_arms(plans)


def expected_pressure_map(
    memory_high_mib: float,
) -> dict[str, bool]:
    return {
        arm: bool(
            twin_plan(
                arm=arm,
                memory_high_mib=memory_high_mib,
            ).memory_high_events_proxy
        )
        for arm in RELEASE_MIB
    }
