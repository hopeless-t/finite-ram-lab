from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CleanDynamicTrial:
    memory_high_mib: int
    arm: str
    max_scan_memory_bytes: int
    post_scan_pre_observer_bytes: int
    post_scan_post_observer_bytes: int
    memory_high_events: int
    pgscan: int
    advice_calls: int
    scan_elapsed_ns: int

    def __post_init__(self) -> None:
        if type(self.memory_high_mib) is not int or self.memory_high_mib <= 0:
            raise ValueError("memory_high_invalid")
        if not self.arm:
            raise ValueError("arm_empty")
        for name in (
            "max_scan_memory_bytes",
            "post_scan_pre_observer_bytes",
            "post_scan_post_observer_bytes",
            "memory_high_events",
            "pgscan",
            "advice_calls",
            "scan_elapsed_ns",
        ):
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise ValueError(f"{name}_invalid")


def derive_clean_frontier_metrics(trial: CleanDynamicTrial) -> dict[str, int]:
    if trial.max_scan_memory_bytes < trial.post_scan_pre_observer_bytes:
        raise ValueError("peak_below_pre_observer_floor")

    return {
        "peak_ram_bytes": trial.max_scan_memory_bytes,
        "clean_floor_bytes": trial.post_scan_pre_observer_bytes,
        "ephemeral_excess_bytes": (
            trial.max_scan_memory_bytes
            - trial.post_scan_pre_observer_bytes
        ),
        "observer_current_delta_bytes": (
            trial.post_scan_post_observer_bytes
            - trial.post_scan_pre_observer_bytes
        ),
        "memory_high_events": trial.memory_high_events,
        "pgscan": trial.pgscan,
        "advice_calls": trial.advice_calls,
        "scan_elapsed_ns": trial.scan_elapsed_ns,
    }


CAPACITY_POINTS_MIB = (144, 160, 176)
ARMS = (
    "buffered",
    "dontneed_32m",
    "dontneed_48m",
    "dontneed_64m",
    "dontneed_80m",
    "dontneed_96m",
)
BLOCKS = 8


def expected_trial_count() -> int:
    return len(CAPACITY_POINTS_MIB) * len(ARMS) * BLOCKS


def validate_design_matrix(
    identities: set[tuple[int, int, str]],
) -> bool:
    expected = {
        (high, block, arm)
        for high in CAPACITY_POINTS_MIB
        for block in range(BLOCKS)
        for arm in ARMS
    }
    return identities == expected
