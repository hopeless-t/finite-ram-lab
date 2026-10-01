from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Sequence


class ObjectiveRole(str, Enum):
    PRIMARY = "PRIMARY"
    DESCRIPTIVE = "DESCRIPTIVE"
    EXCLUDED = "EXCLUDED"


@dataclass(frozen=True)
class ObjectiveSpec:
    name: str
    role: ObjectiveRole
    direction: str
    measurement_semantics: str
    contamination_notes: str = ""

    def __post_init__(self) -> None:
        if not self.name or not self.measurement_semantics:
            raise ValueError("objective_identity_invalid")
        if self.direction not in ("MINIMIZE", "MAXIMIZE"):
            raise ValueError("objective_direction_invalid")


@dataclass(frozen=True)
class DynamicFrontierContract:
    experiment_id: str
    capacity_axis: str
    capacity_units: str
    capacity_points: tuple[float, ...]
    stable_plan_identity_fields: tuple[str, ...]
    objectives: tuple[ObjectiveSpec, ...]
    independent_resampling_unit: str
    minimum_independent_units_per_cell: int
    frontier_stability_threshold: float
    missing_data_rule: str
    claim_ceiling: str
    raw_receipt_required: bool = True
    workload_identity_required: bool = True

    def __post_init__(self) -> None:
        if not self.experiment_id:
            raise ValueError("experiment_id_empty")
        if not self.capacity_axis or not self.capacity_units:
            raise ValueError("capacity_axis_invalid")
        if len(self.capacity_points) < 2:
            raise ValueError("capacity_points_insufficient")
        if tuple(sorted(self.capacity_points)) != self.capacity_points:
            raise ValueError("capacity_points_not_sorted")
        if len(set(self.capacity_points)) != len(self.capacity_points):
            raise ValueError("capacity_points_duplicate")
        if not self.stable_plan_identity_fields:
            raise ValueError("plan_identity_fields_empty")
        if not self.independent_resampling_unit:
            raise ValueError("resampling_unit_empty")
        if type(self.minimum_independent_units_per_cell) is not int:
            raise ValueError("minimum_units_invalid")
        if self.minimum_independent_units_per_cell < 2:
            raise ValueError("minimum_units_too_small")
        if not 0.5 < self.frontier_stability_threshold <= 1.0:
            raise ValueError("stability_threshold_invalid")
        if self.missing_data_rule != "FAIL_CLOSED":
            raise ValueError("missing_data_rule_must_fail_closed")
        if not self.claim_ceiling:
            raise ValueError("claim_ceiling_empty")

        names = [objective.name for objective in self.objectives]
        if not names or len(names) != len(set(names)):
            raise ValueError("objective_names_invalid")
        if not any(
            objective.role is ObjectiveRole.PRIMARY
            for objective in self.objectives
        ):
            raise ValueError("primary_objective_missing")


def qualify_dynamic_frontier_receipt(
    contract: DynamicFrontierContract,
    *,
    observed_capacity_points: Sequence[float],
    independent_units_by_capacity: dict[float, int],
    primary_objectives_present: Sequence[str],
    stable_plan_identity: bool,
    workload_identity_stable: bool,
    raw_receipts_present: bool,
    frontier_loss_probability: float | None,
) -> dict[str, object]:
    required_primary = {
        objective.name
        for objective in contract.objectives
        if objective.role is ObjectiveRole.PRIMARY
    }
    present_primary = set(primary_objectives_present)
    failures = []

    if tuple(sorted(set(observed_capacity_points))) != contract.capacity_points:
        failures.append("CAPACITY_MATRIX_INCOMPLETE")

    for point in contract.capacity_points:
        if independent_units_by_capacity.get(point, 0) < contract.minimum_independent_units_per_cell:
            failures.append(f"INSUFFICIENT_REPLICATION:{point}")

    if not required_primary <= present_primary:
        failures.append("PRIMARY_OBJECTIVE_MISSING")

    if not stable_plan_identity:
        failures.append("PLAN_IDENTITY_UNSTABLE")

    if contract.workload_identity_required and not workload_identity_stable:
        failures.append("WORKLOAD_IDENTITY_UNSTABLE")

    if contract.raw_receipt_required and not raw_receipts_present:
        failures.append("RAW_RECEIPT_MISSING")

    promotion = False
    if frontier_loss_probability is not None:
        if not 0.0 <= frontier_loss_probability <= 1.0:
            raise ValueError("frontier_loss_probability_invalid")
        promotion = frontier_loss_probability >= contract.frontier_stability_threshold

    if failures:
        return {
            "status": "QUALIFICATION_HOLD",
            "failures": tuple(failures),
            "frontier_promotion_eligible": False,
            "claim_ceiling": contract.claim_ceiling,
        }

    return {
        "status": "QUALIFIED",
        "failures": (),
        "frontier_promotion_eligible": promotion,
        "frontier_stability_threshold": contract.frontier_stability_threshold,
        "claim_ceiling": contract.claim_ceiling,
    }
