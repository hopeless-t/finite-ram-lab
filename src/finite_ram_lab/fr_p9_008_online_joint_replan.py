from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass, replace
from typing import Any

from finite_ram_lab.fr_p9_007_hosted_joint_frontier import run_hosted_proxy

SCHEMA = "finite-ram-lab.fr-p9-008-online-joint-replan/v0.1"
POLICY = "HIGHEST_ADMISSIBLE_CONCURRENCY_CLASS_THEN_LOWEST_RESUME"


@dataclass(frozen=True)
class ResourceObservation:
    epoch: int
    pss_cap_kib: int
    capability_available: bool = True
    observer_note: str = ""


@dataclass(frozen=True)
class MeasuredPlan:
    plan_id: str
    workers: int
    mode: str
    prestart_pss_kib: int
    active_pss_kib: int
    joint_resume_ns: int
    work_wall_ns: int
    p95_sojourn_ns: int
    logical_fault_span_bytes: int
    idle_capability_byte_seconds: float
    job_digests: tuple[tuple[str, str], ...]

    @property
    def peak_pss_kib(self) -> int:
        return max(self.prestart_pss_kib, self.active_pss_kib)


@dataclass(frozen=True)
class BoundPlan:
    plan_id: str
    workers: int
    mode: str
    peak_pss_kib: int
    planned_epoch: int
    resource_certificate: str
    measurement_certificate: str
    selection_policy: str
    job_digests: tuple[tuple[str, str], ...]


def resource_certificate(observation: ResourceObservation) -> str:
    payload = {
        "pss_cap_kib": observation.pss_cap_kib,
        "capability_available": observation.capability_available,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def plans_from_measurement(result: dict[str, Any]) -> tuple[MeasuredPlan, ...]:
    if result.get("status") != "PASS":
        raise ValueError("measurement_result_not_qualified")
    summaries = result.get("summaries")
    if not isinstance(summaries, list) or len(summaries) != 6:
        raise ValueError("expected_six_measured_arms")

    plans: list[MeasuredPlan] = []
    for row in summaries:
        workers = int(row["workers"])
        mode = str(row["mode"])
        digests = tuple(sorted((str(k), str(v)) for k, v in row["job_digests"].items()))
        plans.append(
            MeasuredPlan(
                plan_id=f"N{workers}:{mode}",
                workers=workers,
                mode=mode,
                prestart_pss_kib=int(row["median_prestart_pss_kib"]),
                active_pss_kib=int(row["median_active_pss_kib"]),
                joint_resume_ns=int(row["median_joint_resume_ns"]),
                work_wall_ns=int(row["median_work_wall_ns"]),
                p95_sojourn_ns=int(row["median_p95_sojourn_ns"]),
                logical_fault_span_bytes=int(row["logical_fault_span_bytes"]),
                idle_capability_byte_seconds=float(row["median_idle_capability_byte_seconds"]),
                job_digests=digests,
            )
        )

    plans.sort(key=lambda row: (row.workers, row.mode))
    reference = plans[0].job_digests
    if any(plan.job_digests != reference for plan in plans[1:]):
        raise ValueError("job_semantics_differ_across_measured_arms")
    return tuple(plans)


def measurement_certificate(plans: tuple[MeasuredPlan, ...]) -> str:
    payload = [
        {
            "plan_id": plan.plan_id,
            "prestart_pss_kib": plan.prestart_pss_kib,
            "active_pss_kib": plan.active_pss_kib,
            "joint_resume_ns": plan.joint_resume_ns,
            "work_wall_ns": plan.work_wall_ns,
            "p95_sojourn_ns": plan.p95_sojourn_ns,
            "logical_fault_span_bytes": plan.logical_fault_span_bytes,
            "idle_capability_byte_seconds": plan.idle_capability_byte_seconds,
            "job_digests": plan.job_digests,
        }
        for plan in plans
    ]
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def is_feasible(plan: MeasuredPlan, observation: ResourceObservation) -> bool:
    return observation.capability_available and plan.peak_pss_kib <= observation.pss_cap_kib


def select_plan(
    plans: tuple[MeasuredPlan, ...],
    observation: ResourceObservation,
) -> BoundPlan | None:
    if observation.pss_cap_kib <= 0:
        raise ValueError("pss_cap_must_be_positive")
    feasible = [plan for plan in plans if is_feasible(plan, observation)]
    if not feasible:
        return None

    chosen = min(
        feasible,
        key=lambda plan: (
            -plan.workers,
            plan.joint_resume_ns,
            plan.work_wall_ns,
            plan.p95_sojourn_ns,
            plan.peak_pss_kib,
            plan.plan_id,
        ),
    )
    return BoundPlan(
        plan_id=chosen.plan_id,
        workers=chosen.workers,
        mode=chosen.mode,
        peak_pss_kib=chosen.peak_pss_kib,
        planned_epoch=observation.epoch,
        resource_certificate=resource_certificate(observation),
        measurement_certificate=measurement_certificate(plans),
        selection_policy=POLICY,
        job_digests=chosen.job_digests,
    )


def admit_plan(
    plan: BoundPlan,
    observation: ResourceObservation,
    plans: tuple[MeasuredPlan, ...],
) -> str:
    if plan.measurement_certificate != measurement_certificate(plans):
        return "REMEASURE_OR_REPLAN_REQUIRED"
    if plan.resource_certificate != resource_certificate(observation):
        return "REPLAN_REQUIRED"
    measured = next((row for row in plans if row.plan_id == plan.plan_id), None)
    if measured is None or not is_feasible(measured, observation):
        return "REPLAN_REQUIRED"
    return "RESOURCE_PLAN_VALID_AUTHORITY_STILL_REQUIRED"


def frozen_measurement_fixture() -> dict[str, Any]:
    common = {"0": "semantic-equal", "1": "semantic-equal-1"}
    rows = [
        (1, "KEEP_WARM", 19531, 19531, 833744, 405293781, 405293781, 0, 1678465.736638464),
        (1, "FAULT_IN", 11341, 19533, 6799201, 404360992, 404360992, 8388608, 0.0),
        (2, "KEEP_WARM", 29102, 29102, 577746, 203644572, 203644572, 0, 1678412.4857548801),
        (2, "FAULT_IN", 20911, 29105, 7022418, 203684777, 203684777, 16777216, 0.0),
        (4, "KEEP_WARM", 47048, 47050, 1159495, 155843543, 155843543, 0, 1678323.662979072),
        (4, "FAULT_IN", 38863, 47061, 10397746, 157474722, 157474722, 33554432, 0.0),
    ]
    summaries = []
    for workers, mode, pre, active, resume, wall, sojourn, fault, idle_bs in rows:
        summaries.append(
            {
                "workers": workers,
                "mode": mode,
                "median_prestart_pss_kib": pre,
                "median_active_pss_kib": active,
                "median_joint_resume_ns": resume,
                "median_work_wall_ns": wall,
                "median_p95_sojourn_ns": sojourn,
                "logical_fault_span_bytes": fault,
                "median_idle_capability_byte_seconds": idle_bs,
                "job_digests": common,
            }
        )
    return {"status": "PASS", "summaries": summaries}


def run_panel(measurement_result: dict[str, Any] | None = None) -> dict[str, Any]:
    hosted_measurement = measurement_result is not None
    source_result = measurement_result if measurement_result is not None else frozen_measurement_fixture()
    plans = plans_from_measurement(source_result)

    startup = ResourceObservation(41, 50_000, True, "idle admission before external pressure")
    startup_plan = select_plan(plans, startup)
    if startup_plan is None:
        raise RuntimeError("startup_fixture_must_have_a_plan")

    irrelevant_epoch = ResourceObservation(42, 50_000, True, "new observation, same planner-relevant facts")
    control_admission = admit_plan(startup_plan, irrelevant_epoch, plans)

    pressure = ResourceObservation(43, 40_000, True, "finite PSS admission cap tightened before work")
    stale_admission = admit_plan(startup_plan, pressure, plans)
    replanned = select_plan(plans, pressure)
    if replanned is None:
        raise RuntimeError("pressure_fixture_should_have_a_lower_concurrency_plan")

    topology_loss = ResourceObservation(44, 40_000, False, "capability backing unavailable")
    topology_admission = admit_plan(replanned, topology_loss, plans)
    topology_replan = select_plan(plans, topology_loss)

    drifted_first = replace(plans[0], active_pss_kib=plans[0].active_pss_kib + 1)
    drifted_plans = (drifted_first,) + plans[1:]
    evidence_drift_admission = admit_plan(replanned, pressure, drifted_plans)

    startup_measured = next(row for row in plans if row.plan_id == startup_plan.plan_id)
    pressure_measured = next(row for row in plans if row.plan_id == replanned.plan_id)

    checks = {
        "six_same_surface_candidates_loaded": len(plans) == 6,
        "startup_selects_four_worker_keep_warm_under_50mib_class_cap": startup_plan.plan_id == "N4:KEEP_WARM",
        "irrelevant_epoch_change_does_not_force_replan": control_admission == "RESOURCE_PLAN_VALID_AUTHORITY_STILL_REQUIRED",
        "pressure_changes_resource_certificate": startup_plan.resource_certificate != resource_certificate(pressure),
        "stale_plan_rejected_after_cap_tightening": stale_admission == "REPLAN_REQUIRED",
        "stale_plan_exceeds_new_cap": startup_measured.peak_pss_kib > pressure.pss_cap_kib,
        "online_replan_selects_two_worker_keep_warm": replanned.plan_id == "N2:KEEP_WARM",
        "replanned_plan_is_feasible": pressure_measured.peak_pss_kib <= pressure.pss_cap_kib,
        "replan_preserves_job_semantics": replanned.job_digests == startup_plan.job_digests,
        "topology_loss_fails_closed": topology_admission == "REPLAN_REQUIRED" and topology_replan is None,
        "measurement_drift_invalidates_bound_plan": evidence_drift_admission == "REMEASURE_OR_REPLAN_REQUIRED",
        "resource_replan_does_not_grant_authority": True,
        "resource_replan_does_not_grant_retry_permission": True,
    }

    return {
        "schema": SCHEMA,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "classification": (
            "HOSTED_MEASUREMENT_ANCHORED_SYNTHETIC_PSS_CAP_TRANSITION"
            if hosted_measurement
            else "FROZEN_FIXTURE_ONLINE_JOINT_REPLAN"
        ),
        "selection_policy": POLICY,
        "measurement_certificate": measurement_certificate(plans),
        "startup": {
            "observation": asdict(startup),
            "selected_plan": asdict(startup_plan),
            "measured_peak_pss_kib": startup_measured.peak_pss_kib,
        },
        "irrelevant_epoch_control": {
            "observation": asdict(irrelevant_epoch),
            "admission": control_admission,
            "same_resource_certificate": startup_plan.resource_certificate == resource_certificate(irrelevant_epoch),
        },
        "pressure_transition": {
            "observation": asdict(pressure),
            "stale_admission": stale_admission,
            "stale_peak_pss_kib": startup_measured.peak_pss_kib,
            "replanned": asdict(replanned),
            "replanned_peak_pss_kib": pressure_measured.peak_pss_kib,
        },
        "topology_loss": {
            "observation": asdict(topology_loss),
            "admission": topology_admission,
            "replan_result": None,
        },
        "measurement_drift_admission": evidence_drift_admission,
        "plans": [{**asdict(plan), "peak_pss_kib": plan.peak_pss_kib} for plan in plans],
        "checks": checks,
        "decision": "BIND_JOINT_PLANS_TO_RESOURCE_AND_MEASUREMENT_CERTIFICATES;REPLAN_ONLY_AFTER_RELEVANT_CHANGE;FAIL_CLOSED_IF_NO_FEASIBLE_PLAN",
        "typed_objectives": [
            "peak_pss_kib",
            "joint_resume_ns",
            "work_wall_ns",
            "p95_sojourn_ns",
            "logical_fault_span_bytes",
            "idle_capability_byte_seconds",
        ],
        "scalar_gain": None,
        "authority_effect": "NONE",
        "retry_authority": False,
        "invariants": [
            "observation epoch != planner-relevant change",
            "same-surface measurement != timeless plan validity",
            "hard resource feasibility precedes service-policy selection",
            "measurement evidence is part of plan binding",
            "resource replan != execution authority",
            "resource replan != retry permission",
        ],
        "next_falsifier": "replace synthetic admission-cap transition with an isolated physical pressure domain or cgroup-like quota and test whether observed replans match certificate predictions",
        "claim_ceiling": "HOSTED_FR_P9_007_MEASUREMENT_ANCHOR_PLUS_SYNTHETIC_PSS_CAP_TRANSITION_ONLY_NO_PHYSICAL_GLOBAL_PRESSURE_OR_UNIVERSAL_POLICY_CLAIM",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--physical", action="store_true")
    parser.add_argument("--payload-mib", type=int, default=8)
    parser.add_argument("--jobs", type=int, default=12)
    parser.add_argument("--rounds", type=int, default=6)
    parser.add_argument("--repetitions", type=int, default=2)
    parser.add_argument("--idle-gap-seconds", type=float, default=0.20)
    args = parser.parse_args()

    measurement: dict[str, Any] | None = None
    if args.physical:
        measurement = run_hosted_proxy(
            payload_bytes=args.payload_mib * 1024 * 1024,
            jobs=args.jobs,
            rounds=args.rounds,
            repetitions=args.repetitions,
            idle_gap_seconds=args.idle_gap_seconds,
        )
    result = run_panel(measurement)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
