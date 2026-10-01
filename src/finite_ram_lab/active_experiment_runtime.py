from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import argparse
import json
from math import isfinite
from pathlib import Path
from typing import Any, Mapping, Sequence


class RuntimeMode(str, Enum):
    OBSERVE = "OBSERVE"
    OPTIMIZE = "OPTIMIZE"
    PROBE = "PROBE"


class DatasetPartition(str, Enum):
    OBSERVATIONAL = "OBSERVATIONAL"
    OPTIMIZATION = "OPTIMIZATION"
    EXPERIMENTAL_INTERVENTION = "EXPERIMENTAL_INTERVENTION"


@dataclass(frozen=True)
class CandidatePlan:
    plan_id: str
    variables: tuple[tuple[str, str | int | float | bool], ...]
    fidelity_gate: bool
    predicted_peak_bytes: int
    predicted_latency_seconds: float
    useful_work: float
    expected_information_gain: float = 0.0

    def __post_init__(self) -> None:
        if not self.plan_id:
            raise ValueError("plan_id_empty")
        if type(self.predicted_peak_bytes) is not int or self.predicted_peak_bytes < 0:
            raise ValueError("predicted_peak_bytes_invalid")
        for name in (
            "predicted_latency_seconds",
            "useful_work",
            "expected_information_gain",
        ):
            value = getattr(self, name)
            if not isinstance(value, (int, float)) or not isfinite(value) or value < 0:
                raise ValueError(f"{name}_invalid")
        keys = [name for name, _ in self.variables]
        if len(keys) != len(set(keys)):
            raise ValueError("duplicate_variable")

    @property
    def variable_map(self) -> dict[str, str | int | float | bool]:
        return dict(self.variables)


@dataclass(frozen=True)
class RuntimeConstraints:
    max_peak_bytes: int
    max_latency_seconds: float
    min_useful_work: float

    def __post_init__(self) -> None:
        if type(self.max_peak_bytes) is not int or self.max_peak_bytes < 0:
            raise ValueError("max_peak_bytes_invalid")
        for name in ("max_latency_seconds", "min_useful_work"):
            value = getattr(self, name)
            if not isinstance(value, (int, float)) or not isfinite(value) or value < 0:
                raise ValueError(f"{name}_invalid")


@dataclass(frozen=True)
class ProbeEnvelope:
    allowed_variables: tuple[str, ...]
    numeric_bounds: tuple[tuple[str, float, float], ...] = ()
    allowed_values: tuple[tuple[str, tuple[str | int | float | bool, ...]], ...] = ()

    def __post_init__(self) -> None:
        if len(self.allowed_variables) != len(set(self.allowed_variables)):
            raise ValueError("duplicate_allowed_variable")
        allowed = set(self.allowed_variables)
        for name, low, high in self.numeric_bounds:
            if name not in allowed:
                raise ValueError("numeric_bound_not_allowed")
            if not isfinite(low) or not isfinite(high) or low > high:
                raise ValueError("numeric_bound_invalid")
        for name, values in self.allowed_values:
            if name not in allowed:
                raise ValueError("allowed_values_variable_not_allowed")
            if not values:
                raise ValueError("allowed_values_empty")

    def validate_change(
        self,
        name: str,
        value: str | int | float | bool,
    ) -> bool:
        if name not in self.allowed_variables:
            return False

        bounds = {key: (low, high) for key, low, high in self.numeric_bounds}
        if name in bounds:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                return False
            low, high = bounds[name]
            if not (low <= float(value) <= high):
                return False

        enumerated = {key: values for key, values in self.allowed_values}
        if name in enumerated and value not in enumerated[name]:
            return False

        return True


@dataclass(frozen=True)
class DecisionReceipt:
    schema: str
    mode: RuntimeMode
    dataset_partition: DatasetPartition
    baseline_plan_id: str
    selected_plan_id: str
    intervention: bool
    hypothesis_id: str | None
    changed_variables: tuple[tuple[str, Any, Any], ...]
    held_constant_variables: tuple[tuple[str, Any], ...]
    predicted_peak_bytes: int
    predicted_latency_seconds: float
    useful_work: float
    expected_information_gain: float
    selection_rule: str
    claim_ceiling: str


def _is_feasible(plan: CandidatePlan, constraints: RuntimeConstraints) -> bool:
    return (
        plan.fidelity_gate
        and plan.predicted_peak_bytes <= constraints.max_peak_bytes
        and plan.predicted_latency_seconds <= constraints.max_latency_seconds
        and plan.useful_work >= constraints.min_useful_work
    )


def _diff(
    baseline: CandidatePlan,
    candidate: CandidatePlan,
) -> tuple[
    tuple[tuple[str, Any, Any], ...],
    tuple[tuple[str, Any], ...],
]:
    left = baseline.variable_map
    right = candidate.variable_map
    if set(left) != set(right):
        raise ValueError("candidate_variable_schema_mismatch")

    changed = []
    held = []
    for name in sorted(left):
        if left[name] == right[name]:
            held.append((name, left[name]))
        else:
            changed.append((name, left[name], right[name]))
    return tuple(changed), tuple(held)


def _validate_probe_candidate(
    baseline: CandidatePlan,
    candidate: CandidatePlan,
    envelope: ProbeEnvelope,
) -> tuple[
    tuple[tuple[str, Any, Any], ...],
    tuple[tuple[str, Any], ...],
] | None:
    changed, held = _diff(baseline, candidate)
    if not changed:
        return None
    for name, _, value in changed:
        if not envelope.validate_change(name, value):
            return None
    return changed, held


def select_runtime_plan(
    *,
    mode: RuntimeMode,
    baseline: CandidatePlan,
    candidates: Sequence[CandidatePlan],
    constraints: RuntimeConstraints,
    hypothesis_id: str | None = None,
    probe_envelope: ProbeEnvelope | None = None,
) -> DecisionReceipt:
    all_candidates = tuple(candidates)
    by_id = {plan.plan_id: plan for plan in all_candidates}
    if len(by_id) != len(all_candidates):
        raise ValueError("duplicate_plan_id")
    if baseline.plan_id not in by_id:
        raise ValueError("baseline_missing")

    if mode is RuntimeMode.OBSERVE:
        selected = baseline
        changed, held = _diff(baseline, selected)
        return DecisionReceipt(
            schema="finite-ram-lab.runtime-decision/v0.1",
            mode=mode,
            dataset_partition=DatasetPartition.OBSERVATIONAL,
            baseline_plan_id=baseline.plan_id,
            selected_plan_id=selected.plan_id,
            intervention=False,
            hypothesis_id=None,
            changed_variables=changed,
            held_constant_variables=held,
            predicted_peak_bytes=selected.predicted_peak_bytes,
            predicted_latency_seconds=selected.predicted_latency_seconds,
            useful_work=selected.useful_work,
            expected_information_gain=0.0,
            selection_rule="baseline_only_no_intervention",
            claim_ceiling="SOFTWARE_DECISION_CONTRACT_ONLY",
        )

    feasible = [plan for plan in all_candidates if _is_feasible(plan, constraints)]
    if not feasible:
        raise RuntimeError("no_feasible_candidate")

    if mode is RuntimeMode.OPTIMIZE:
        selected = min(
            feasible,
            key=lambda plan: (
                plan.predicted_peak_bytes,
                plan.predicted_latency_seconds,
                -plan.useful_work,
                plan.plan_id,
            ),
        )
        changed, held = _diff(baseline, selected)
        return DecisionReceipt(
            schema="finite-ram-lab.runtime-decision/v0.1",
            mode=mode,
            dataset_partition=DatasetPartition.OPTIMIZATION,
            baseline_plan_id=baseline.plan_id,
            selected_plan_id=selected.plan_id,
            intervention=bool(changed),
            hypothesis_id=None,
            changed_variables=changed,
            held_constant_variables=held,
            predicted_peak_bytes=selected.predicted_peak_bytes,
            predicted_latency_seconds=selected.predicted_latency_seconds,
            useful_work=selected.useful_work,
            expected_information_gain=selected.expected_information_gain,
            selection_rule=(
                "min_peak_subject_to_fidelity_latency_and_useful_work_constraints"
            ),
            claim_ceiling="SOFTWARE_DECISION_CONTRACT_ONLY",
        )

    if mode is RuntimeMode.PROBE:
        if not hypothesis_id:
            raise ValueError("probe_hypothesis_required")
        if probe_envelope is None:
            raise ValueError("probe_envelope_required")

        probe_candidates = []
        diff_by_id = {}
        for plan in feasible:
            checked = _validate_probe_candidate(baseline, plan, probe_envelope)
            if checked is None:
                continue
            changed, held = checked
            probe_candidates.append(plan)
            diff_by_id[plan.plan_id] = (changed, held)

        if not probe_candidates:
            raise RuntimeError("no_safe_probe_candidate")

        selected = max(
            probe_candidates,
            key=lambda plan: (
                (
                    plan.expected_information_gain
                    / max(plan.predicted_latency_seconds, 1e-12)
                ),
                plan.expected_information_gain,
                -plan.predicted_peak_bytes,
                plan.plan_id,
            ),
        )
        changed, held = diff_by_id[selected.plan_id]
        return DecisionReceipt(
            schema="finite-ram-lab.runtime-decision/v0.1",
            mode=mode,
            dataset_partition=DatasetPartition.EXPERIMENTAL_INTERVENTION,
            baseline_plan_id=baseline.plan_id,
            selected_plan_id=selected.plan_id,
            intervention=True,
            hypothesis_id=hypothesis_id,
            changed_variables=changed,
            held_constant_variables=held,
            predicted_peak_bytes=selected.predicted_peak_bytes,
            predicted_latency_seconds=selected.predicted_latency_seconds,
            useful_work=selected.useful_work,
            expected_information_gain=selected.expected_information_gain,
            selection_rule=(
                "max_expected_information_gain_per_second_within_probe_envelope"
            ),
            claim_ceiling="SOFTWARE_DECISION_CONTRACT_ONLY",
        )

    raise AssertionError("unreachable_mode")


def _candidate_from_json(payload: Mapping[str, Any]) -> CandidatePlan:
    variables = payload.get("variables", {})
    if not isinstance(variables, dict):
        raise ValueError("variables_must_be_object")
    return CandidatePlan(
        plan_id=str(payload["plan_id"]),
        variables=tuple(sorted(variables.items())),
        fidelity_gate=bool(payload["fidelity_gate"]),
        predicted_peak_bytes=int(payload["predicted_peak_bytes"]),
        predicted_latency_seconds=float(payload["predicted_latency_seconds"]),
        useful_work=float(payload["useful_work"]),
        expected_information_gain=float(payload.get("expected_information_gain", 0.0)),
    )


def _envelope_from_json(payload: Mapping[str, Any]) -> ProbeEnvelope:
    allowed_variables = tuple(str(item) for item in payload.get("allowed_variables", []))
    numeric_bounds = tuple(
        (str(name), float(bounds[0]), float(bounds[1]))
        for name, bounds in sorted(payload.get("numeric_bounds", {}).items())
    )
    allowed_values = tuple(
        (str(name), tuple(values))
        for name, values in sorted(payload.get("allowed_values", {}).items())
    )
    return ProbeEnvelope(
        allowed_variables=allowed_variables,
        numeric_bounds=numeric_bounds,
        allowed_values=allowed_values,
    )


def decision_from_spec(payload: Mapping[str, Any]) -> DecisionReceipt:
    mode = RuntimeMode(str(payload["mode"]))
    plans = tuple(_candidate_from_json(item) for item in payload["candidates"])
    baseline_id = str(payload["baseline_plan_id"])
    by_id = {plan.plan_id: plan for plan in plans}
    if baseline_id not in by_id:
        raise ValueError("baseline_missing")

    raw_constraints = payload["constraints"]
    constraints = RuntimeConstraints(
        max_peak_bytes=int(raw_constraints["max_peak_bytes"]),
        max_latency_seconds=float(raw_constraints["max_latency_seconds"]),
        min_useful_work=float(raw_constraints["min_useful_work"]),
    )
    envelope = (
        _envelope_from_json(payload["probe_envelope"])
        if mode is RuntimeMode.PROBE
        else None
    )
    return select_runtime_plan(
        mode=mode,
        baseline=by_id[baseline_id],
        candidates=plans,
        constraints=constraints,
        hypothesis_id=payload.get("hypothesis_id"),
        probe_envelope=envelope,
    )


def receipt_to_json(receipt: DecisionReceipt) -> dict[str, Any]:
    payload = asdict(receipt)
    payload["mode"] = receipt.mode.value
    payload["dataset_partition"] = receipt.dataset_partition.value
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    payload = json.loads(args.spec.read_text())
    receipt = decision_from_spec(payload)
    serialized = receipt_to_json(receipt)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(serialized, indent=2, sort_keys=True) + "\n")
    print(json.dumps(serialized, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
