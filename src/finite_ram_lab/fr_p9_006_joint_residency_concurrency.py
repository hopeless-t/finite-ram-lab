from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

SCHEMA = "finite-ram-lab.fr-p9-006-joint-residency-concurrency/v0.1"


@dataclass(frozen=True)
class WorkerProfile:
    workers: int
    active_pss_kib: int
    work_wall_ns: int


@dataclass(frozen=True)
class ResidencyProfile:
    policy: str
    idle_capability_pss_kib: int
    requested_transfer_bytes: int
    resume_penalty_ns: int
    resident_byte_seconds: float


@dataclass(frozen=True)
class JointPlan:
    workers: int
    residency_policy: str
    prestart_pss_kib: int
    requested_transfer_bytes: int
    predicted_completion_ns: int
    resident_byte_seconds: float
    feasible: bool


# The worker shape is copied from qualified FR-P9-005 hosted medians only as an
# evidence anchor. The joint composition below is synthetic and must not be
# promoted as a physical host planner result.
WORKERS = (
    WorkerProfile(1, 15395, 256_454_324),
    WorkerProfile(2, 24937, 128_979_271),
    WorkerProfile(4, 42864, 70_568_943),
)

# The 8 MiB warm residency and fault penalty are a deliberately frozen joint
# fixture inspired by FR-P9-003's phase-residency shape. They are not asserted
# to be directly comparable physical measurements with FR-P9-005.
RESIDENCIES = (
    ResidencyProfile(
        policy="KEEP_WARM",
        idle_capability_pss_kib=8192,
        requested_transfer_bytes=0,
        resume_penalty_ns=0,
        resident_byte_seconds=8 * 1024 * 1024 * 1.0,
    ),
    ResidencyProfile(
        policy="FAULT_IN",
        idle_capability_pss_kib=0,
        requested_transfer_bytes=8 * 1024 * 1024,
        resume_penalty_ns=2_668_202,
        resident_byte_seconds=0.0,
    ),
)

MEMORY_CAP_KIB = 50_000


def enumerate_joint_plans(
    *,
    memory_cap_kib: int = MEMORY_CAP_KIB,
) -> tuple[JointPlan, ...]:
    if memory_cap_kib <= 0:
        raise ValueError("memory_cap_must_be_positive")
    rows: list[JointPlan] = []
    for worker in WORKERS:
        for residency in RESIDENCIES:
            prestart = worker.active_pss_kib + residency.idle_capability_pss_kib
            rows.append(
                JointPlan(
                    workers=worker.workers,
                    residency_policy=residency.policy,
                    prestart_pss_kib=prestart,
                    requested_transfer_bytes=residency.requested_transfer_bytes,
                    predicted_completion_ns=(
                        worker.work_wall_ns + residency.resume_penalty_ns
                    ),
                    resident_byte_seconds=residency.resident_byte_seconds,
                    feasible=prestart <= memory_cap_kib,
                )
            )
    return tuple(rows)


def _dominates(a: JointPlan, b: JointPlan) -> bool:
    fields = (
        "prestart_pss_kib",
        "requested_transfer_bytes",
        "predicted_completion_ns",
        "resident_byte_seconds",
    )
    no_worse = all(getattr(a, field) <= getattr(b, field) for field in fields)
    strictly_better = any(getattr(a, field) < getattr(b, field) for field in fields)
    return no_worse and strictly_better


def pareto_plans(plans: tuple[JointPlan, ...]) -> tuple[JointPlan, ...]:
    feasible = tuple(plan for plan in plans if plan.feasible)
    return tuple(
        plan
        for plan in feasible
        if not any(
            _dominates(other, plan)
            for other in feasible
            if other != plan
        )
    )


def independently_selected_plan() -> tuple[int, str]:
    fastest_workers = min(WORKERS, key=lambda row: row.work_wall_ns).workers
    # On the isolated residency dimensions used here, KEEP_WARM has zero
    # requested transfer and zero resume penalty, so a separable latency/transfer
    # heuristic chooses it before considering the joint memory cap.
    residency = min(
        RESIDENCIES,
        key=lambda row: (row.resume_penalty_ns, row.requested_transfer_bytes),
    ).policy
    return fastest_workers, residency


def run_panel() -> dict[str, Any]:
    plans = enumerate_joint_plans()
    frontier = pareto_plans(plans)
    independent_workers, independent_residency = independently_selected_plan()
    independent = next(
        plan
        for plan in plans
        if plan.workers == independent_workers
        and plan.residency_policy == independent_residency
    )

    fastest_feasible = min(
        (plan for plan in plans if plan.feasible),
        key=lambda row: row.predicted_completion_ns,
    )
    lowest_pss_feasible = min(
        (plan for plan in plans if plan.feasible),
        key=lambda row: row.prestart_pss_kib,
    )

    frontier_ids = [f"N{plan.workers}:{plan.residency_policy}" for plan in frontier]
    checks = {
        "six_joint_candidates_enumerated": len(plans) == 6,
        "independent_fastest_workers_is_four": independent_workers == 4,
        "independent_residency_is_keep_warm": independent_residency == "KEEP_WARM",
        "independent_composition_is_infeasible": not independent.feasible,
        "joint_feasible_set_nonempty": any(plan.feasible for plan in plans),
        "joint_pareto_frontier_nonempty": bool(frontier),
        "four_worker_fault_in_remains_feasible": any(
            plan.workers == 4
            and plan.residency_policy == "FAULT_IN"
            and plan.feasible
            for plan in plans
        ),
        "two_worker_keep_warm_remains_feasible": any(
            plan.workers == 2
            and plan.residency_policy == "KEEP_WARM"
            and plan.feasible
            for plan in plans
        ),
        "no_scalar_gain_without_external_price": True,
        "authority_unchanged": True,
    }

    return {
        "schema": SCHEMA,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "classification": "SYNTHETIC_JOINT_RESIDENCY_CONCURRENCY_COMPOSITION_FALSIFIER",
        "memory_cap_kib": MEMORY_CAP_KIB,
        "source_evidence": {
            "worker_shape": "FR-P9-005 qualified hosted medians used as frozen evidence anchors",
            "residency_shape": "FR-P9-003 inspired synthetic 8 MiB warm/fault fixture",
            "comparability_boundary": "cross-proxy values are used only to construct this synthetic falsifier; no physical joint claim",
        },
        "plans": [asdict(plan) for plan in plans],
        "independent_selection": {
            "workers": independent_workers,
            "residency_policy": independent_residency,
            "composed_plan": asdict(independent),
        },
        "fastest_feasible": asdict(fastest_feasible),
        "lowest_pss_feasible": asdict(lowest_pss_feasible),
        "pareto_plan_ids": frontier_ids,
        "checks": checks,
        "decision": (
            "DO_NOT_COMPOSE_INDEPENDENT_CONCURRENCY_AND_RESIDENCY_OPTIMA;SOLVE_THE_JOINT_FEASIBLE_TYPED_FRONTIER"
        ),
        "typed_objectives": [
            "prestart_pss_kib",
            "requested_transfer_bytes",
            "predicted_completion_ns",
            "resident_byte_seconds",
        ],
        "scalar_gain": None,
        "authority_effect": "NONE",
        "invariants": [
            "individually attractive decisions can compose into an infeasible plan",
            "concurrency and residency share the same finite memory budget",
            "feasibility precedes optimization",
            "cross-proxy evidence must not be relabeled as a physical joint measurement",
            "resource feasibility != execution authority",
        ],
        "next_falsifier": (
            "run one hosted joint probe where KEEP_WARM and FAULT_IN are measured under the same payload, worker counts, and memory accounting surface"
        ),
        "claim_ceiling": (
            "SYNTHETIC_JOINT_COMPOSITION_USING_QUALIFIED_PROXY_SHAPES_ONLY_NO_PHYSICAL_JOINT_OPTIMUM_CLAIM"
        ),
    }


def main() -> int:
    result = run_panel()
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
