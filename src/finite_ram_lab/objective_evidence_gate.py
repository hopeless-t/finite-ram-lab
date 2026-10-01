from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Sequence

from finite_ram_lab.historical_dynamic_replay import (
    ProjectedObservation,
    compare_projected_pair,
)


class EvidenceRole(str, Enum):
    PRIMARY = "PRIMARY"
    DESCRIPTIVE = "DESCRIPTIVE"
    EXCLUDED = "EXCLUDED"


@dataclass(frozen=True)
class ObjectiveEvidence:
    name: str
    role: EvidenceRole
    rationale: str = ""

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("objective_name_empty")


def _available_names(observations: Sequence[ProjectedObservation]) -> set[str]:
    names: set[str] | None = None
    for observation in observations:
        current = {name for name, _ in observation.objectives}
        names = current if names is None else names & current
    return names or set()


def evaluate_objective_evidence_gate(
    smaller: Sequence[ProjectedObservation],
    larger: Sequence[ProjectedObservation],
    evidence: Sequence[ObjectiveEvidence],
    *,
    tolerance: float = 0.0,
) -> dict[str, object]:
    if not evidence:
        raise ValueError("evidence_empty")

    roles = {item.name: item.role for item in evidence}
    if len(roles) != len(evidence):
        raise ValueError("duplicate_objective_evidence")

    primary = tuple(
        item.name for item in evidence if item.role is EvidenceRole.PRIMARY
    )
    descriptive = tuple(
        item.name for item in evidence if item.role is EvidenceRole.DESCRIPTIVE
    )
    excluded = tuple(
        item.name for item in evidence if item.role is EvidenceRole.EXCLUDED
    )

    if not primary:
        raise ValueError("primary_objective_missing")

    available = _available_names(tuple(smaller) + tuple(larger))
    missing_primary = tuple(name for name in primary if name not in available)
    if missing_primary:
        return {
            "status": "INSTRUMENTATION_HOLD",
            "missing_primary_objectives": missing_primary,
            "primary_result": None,
            "sensitivity_result": None,
            "classification": "PRIMARY_OBJECTIVE_MISSING",
        }

    primary_result = compare_projected_pair(
        smaller,
        larger,
        primary,
        tolerance=tolerance,
    )

    usable_descriptive = tuple(
        name for name in descriptive if name in available
    )
    sensitivity_projection = primary + usable_descriptive
    sensitivity_result = compare_projected_pair(
        smaller,
        larger,
        sensitivity_projection,
        tolerance=tolerance,
    )

    primary_lost = set(primary_result["lost_frontier_ids"])
    sensitivity_lost = set(sensitivity_result["lost_frontier_ids"])

    if not primary_lost and sensitivity_lost:
        classification = "PROJECTION_FRAGILE"
    elif primary_lost:
        if primary_lost == sensitivity_lost:
            classification = "PRIMARY_VIOLATION_STABLE_TO_DESCRIPTIVE_EXTENSION"
        else:
            classification = "PRIMARY_VIOLATION_PROJECTION_SENSITIVE"
    else:
        classification = "NO_MEASURED_MONOTONICITY_VIOLATION"

    return {
        "status": "PASS",
        "classification": classification,
        "primary_objectives": primary,
        "descriptive_objectives_used": usable_descriptive,
        "excluded_objectives": excluded,
        "missing_descriptive_objectives": tuple(
            name for name in descriptive if name not in available
        ),
        "primary_result": primary_result,
        "sensitivity_result": sensitivity_result,
    }
