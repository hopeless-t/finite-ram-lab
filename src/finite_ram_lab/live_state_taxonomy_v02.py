from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class SemanticAction(str, Enum):
    REDUCE = "REDUCE"
    REMATERIALIZE = "REMATERIALIZE"
    RETAIN = "RETAIN"


class PhysicalAction(str, Enum):
    DEDUP_OWNERSHIP = "DEDUP_OWNERSHIP"
    COMPRESS = "COMPRESS"
    TEMPORALIZE = "TEMPORALIZE"
    PLACE = "PLACE"
    BORROW = "BORROW"
    UNLOAD = "UNLOAD"


CONTROL_ORDER = {
    "SEMANTIC_REDUCTION": 0,
    "OWNERSHIP": 1,
    "REPRESENTATION": 2,
    "TEMPORALIZATION": 3,
    "PLACEMENT": 4,
    "PHASE_BORROWING": 5,
    "LIFETIME": 6,
}

ACTION_STAGE = {
    "REDUCE": "SEMANTIC_REDUCTION",
    "REMATERIALIZE": "SEMANTIC_REDUCTION",
    "DEDUP_OWNERSHIP": "OWNERSHIP",
    "SHARE": "OWNERSHIP",
    "COMPRESS": "REPRESENTATION",
    "TEMPORALIZE": "TEMPORALIZATION",
    "REORDER": "TEMPORALIZATION",
    "MOVE": "PLACEMENT",
    "PLACE": "PLACEMENT",
    "BORROW": "PHASE_BORROWING",
    "UNLOAD": "LIFETIME",
}


@dataclass(frozen=True)
class SemanticState:
    name: str
    logical_bytes: int
    owners: tuple[str, ...]
    future_sufficient_summary_bytes: int | None = None
    recomputable: bool = False

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("name_empty")
        if type(self.logical_bytes) is not int or self.logical_bytes < 0:
            raise ValueError("logical_bytes_invalid")
        if not self.owners or any(not x for x in self.owners):
            raise ValueError("owners_invalid")
        if len(set(self.owners)) != len(self.owners):
            raise ValueError("duplicate_owner")
        if self.future_sufficient_summary_bytes is not None:
            if (
                type(self.future_sufficient_summary_bytes) is not int
                or self.future_sufficient_summary_bytes < 0
            ):
                raise ValueError("summary_bytes_invalid")


@dataclass(frozen=True)
class PhysicalState:
    semantic_name: str
    representation: str
    resident_tier: str | None
    backing_tier: str | None
    resident_bytes: int
    replicas: int = 1
    phase: str = "steady"

    def __post_init__(self) -> None:
        if not self.semantic_name or not self.representation or not self.phase:
            raise ValueError("physical_identity_invalid")
        if self.resident_tier is None and self.resident_bytes != 0:
            raise ValueError("bytes_without_resident_tier")
        if type(self.resident_bytes) is not int or self.resident_bytes < 0:
            raise ValueError("resident_bytes_invalid")
        if type(self.replicas) is not int or self.replicas < 1:
            raise ValueError("replicas_invalid")


def semantic_release_action(state: SemanticState) -> SemanticAction:
    summary = state.future_sufficient_summary_bytes
    if summary is not None and summary < state.logical_bytes:
        return SemanticAction.REDUCE
    if state.recomputable:
        return SemanticAction.REMATERIALIZE
    return SemanticAction.RETAIN


def ordered_control_stages(actions: Iterable[str]) -> tuple[str, ...]:
    stages = set()
    for action in actions:
        try:
            stage = ACTION_STAGE[action]
        except KeyError as exc:
            raise ValueError(f"unknown_action:{action}") from exc
        stages.add(stage)
    return tuple(sorted(stages, key=CONTROL_ORDER.__getitem__))


def physical_resident_bytes_by_tier(
    states: Iterable[PhysicalState],
) -> dict[str, int]:
    out: dict[str, int] = {}
    for state in states:
        if state.resident_tier is None:
            continue
        out[state.resident_tier] = (
            out.get(state.resident_tier, 0)
            + state.resident_bytes * state.replicas
        )
    return out


def ownership_replica_lower_bound(state: SemanticState) -> int:
    """Minimum semantic owner count, not a requirement for physical copies.

    Immutable/shareable state may have one physical copy for many owners.
    Mutable owner-local state generally cannot be collapsed without an explicit
    sharing protocol. The taxonomy records ownership separately so the physical
    planner can decide this rather than inferring copies from consumers.
    """
    return len(state.owners)


EXEMPLAR_ACTIONS = {
    "ozaki_ii": ("REDUCE", "REORDER"),
    "flashattention": ("REDUCE", "REORDER"),
    "pagedattention": ("SHARE", "MOVE"),
    "checkmate_dtr": ("REMATERIALIZE",),
    "flexgen": ("COMPRESS", "MOVE"),
    "gemmul8_memory_saving": ("REORDER",),
    "strata_kv_streaming": ("COMPRESS", "MOVE"),
    "strata_expert_residency": ("SHARE", "MOVE"),
    "strata_prompt_cache_lending": ("BORROW",),
    "strata_idle_unload": ("UNLOAD",),
}
