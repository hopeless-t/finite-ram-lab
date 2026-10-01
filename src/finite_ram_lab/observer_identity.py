from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class ObserverContract:
    name: str
    checkpoint_hook_enabled: bool
    checkpoint_side_effects: tuple[str, ...]
    recorder_enabled: bool
    recorder_inside_measured_interval: bool

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("name_empty")
        if any(not x for x in self.checkpoint_side_effects):
            raise ValueError("checkpoint_side_effect_invalid")


def observer_semantics_equal(
    left: ObserverContract,
    right: ObserverContract,
) -> bool:
    return (
        left.checkpoint_hook_enabled == right.checkpoint_hook_enabled
        and left.checkpoint_side_effects == right.checkpoint_side_effects
        and left.recorder_enabled == right.recorder_enabled
        and left.recorder_inside_measured_interval
        == right.recorder_inside_measured_interval
    )


def capacity_pair_identity_check(
    *,
    workload_bytes_equal: bool,
    runner_equal: bool,
    python_equal: bool,
    cgroup_controls_equal_except_capacity: bool,
    arm_semantics_equal: bool,
    observer_left: ObserverContract,
    observer_right: ObserverContract,
) -> dict[str, object]:
    failures: list[str] = []

    if not workload_bytes_equal:
        failures.append("WORKLOAD_IMPLEMENTATION_DRIFT")
    if not runner_equal:
        failures.append("RUNNER_DRIFT")
    if not python_equal:
        failures.append("PYTHON_RUNTIME_DRIFT")
    if not cgroup_controls_equal_except_capacity:
        failures.append("CGROUP_CONTROL_DRIFT")
    if not arm_semantics_equal:
        failures.append("ARM_SEMANTICS_DRIFT")
    if not observer_semantics_equal(observer_left, observer_right):
        failures.append("OBSERVER_SEMANTICS_DRIFT")

    return {
        "status": "IDENTITY_PASS" if not failures else "IDENTITY_HOLD",
        "failures": tuple(failures),
        "observer_equal": observer_semantics_equal(observer_left, observer_right),
    }


STRATA004_OBSERVER = ObserverContract(
    name="STRATA-004",
    checkpoint_hook_enabled=False,
    checkpoint_side_effects=(),
    recorder_enabled=False,
    recorder_inside_measured_interval=False,
)

STRATA005_OBSERVER = ObserverContract(
    name="STRATA-005",
    checkpoint_hook_enabled=True,
    checkpoint_side_effects=("recorder.sample(memory.current)",),
    recorder_enabled=True,
    recorder_inside_measured_interval=True,
)
