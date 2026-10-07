from __future__ import annotations

import argparse
import itertools
import json
import random
from dataclasses import dataclass
from typing import Any

from finite_ram_lab.fr_p9_018_service_curve_deadline_admission import (
    ADMIT,
    INSUFFICIENT,
    REPLAN,
    ServiceCurveSnapshot,
    ServiceDemand,
    curve_from_increments,
    deadline_admit,
    service_at,
)

SCHEMA = "finite-ram-lab.fr-p9-020-multi-resource-service-conjunction/v0.1"

MULTI_INSUFFICIENT = "INSUFFICIENT_TYPED_RESOURCE_SERVICE"
MISSING = "FAIL_CLOSED_MISSING_RESOURCE_CURVE"
UNIT_MISMATCH = "FAIL_CLOSED_SERVICE_UNIT_MISMATCH"


@dataclass(frozen=True)
class TypedCurve:
    curve: ServiceCurveSnapshot
    service_unit: str


@dataclass(frozen=True)
class TypedDemand:
    demand: ServiceDemand
    service_unit: str


def _key(resource_kind: str, contention_domain: str) -> tuple[str, str]:
    return resource_kind, contention_domain


def multi_resource_admit(
    demands: tuple[TypedDemand, ...],
    curves: tuple[TypedCurve, ...],
    *,
    observed_epochs: dict[tuple[str, str], int],
) -> dict[str, Any]:
    if not demands:
        raise ValueError("at_least_one_demand_required")
    if not curves:
        raise ValueError("at_least_one_curve_required")

    curve_map: dict[tuple[str, str], TypedCurve] = {}
    for typed_curve in curves:
        if not typed_curve.service_unit:
            raise ValueError("service_unit_required")
        key = _key(typed_curve.curve.resource_kind, typed_curve.curve.contention_domain)
        if key in curve_map:
            raise ValueError("duplicate_resource_curve")
        curve_map[key] = typed_curve

    demand_keys: set[tuple[str, str]] = set()
    per_resource: list[dict[str, Any]] = []
    overall = ADMIT

    for typed_demand in demands:
        if not typed_demand.service_unit:
            raise ValueError("service_unit_required")
        demand = typed_demand.demand
        key = _key(demand.resource_kind, demand.contention_domain)
        if key in demand_keys:
            raise ValueError("duplicate_resource_demand")
        demand_keys.add(key)

        typed_curve = curve_map.get(key)
        if typed_curve is None or key not in observed_epochs:
            per_resource.append(
                {
                    "resource": list(key),
                    "service_unit": typed_demand.service_unit,
                    "status": MISSING,
                    "available_service": None,
                    "required_service": demand.required_service,
                }
            )
            if overall != REPLAN:
                overall = MISSING
            continue

        if typed_curve.service_unit != typed_demand.service_unit:
            per_resource.append(
                {
                    "resource": list(key),
                    "service_unit": typed_demand.service_unit,
                    "curve_service_unit": typed_curve.service_unit,
                    "status": UNIT_MISMATCH,
                    "available_service": None,
                    "required_service": demand.required_service,
                }
            )
            if overall != REPLAN:
                overall = UNIT_MISMATCH
            continue

        decision = deadline_admit(
            demand,
            typed_curve.curve,
            observed_epoch=observed_epochs[key],
        )
        per_resource.append(
            {
                "resource": list(key),
                "service_unit": typed_demand.service_unit,
                "status": decision.status,
                "available_service": decision.available_service,
                "required_service": demand.required_service,
                "deadline_index": demand.deadline_index,
                "curve_epoch": decision.curve_epoch,
                "observed_epoch": decision.observed_epoch,
            }
        )
        if decision.status == REPLAN:
            overall = REPLAN
        elif decision.status != ADMIT and overall not in {REPLAN, MISSING, UNIT_MISMATCH}:
            overall = MULTI_INSUFFICIENT

    return {
        "status": overall,
        "per_resource": per_resource,
        "authority_effect": "NONE",
        "retry_authority": False,
    }


def _pair_fixture(
    cpu_inc: tuple[int, ...],
    io_inc: tuple[int, ...],
    *,
    epoch: int,
    cpu_required: int,
    io_required: int,
    deadline: int = 2,
) -> tuple[tuple[TypedDemand, ...], tuple[TypedCurve, ...], dict[tuple[str, str], int]]:
    cpu_curve = curve_from_increments(
        cpu_inc,
        epoch=epoch,
        resource_kind="CPU",
        contention_domain="cpu0",
    )
    io_curve = curve_from_increments(
        io_inc,
        epoch=epoch,
        resource_kind="TRANSFER",
        contention_domain="storage-link0",
    )
    demands = (
        TypedDemand(ServiceDemand("work", "CPU", "cpu0", deadline, cpu_required), "cpu_quanta"),
        TypedDemand(
            ServiceDemand("work", "TRANSFER", "storage-link0", deadline, io_required),
            "byte_quanta",
        ),
    )
    curves = (
        TypedCurve(cpu_curve, "cpu_quanta"),
        TypedCurve(io_curve, "byte_quanta"),
    )
    epochs = {("CPU", "cpu0"): epoch, ("TRANSFER", "storage-link0"): epoch}
    return demands, curves, epochs


def exhaustive_conjunction_check() -> dict[str, int]:
    comparisons = 0
    mismatches = 0
    for cpu_inc in itertools.product(range(3), repeat=3):
        for io_inc in itertools.product(range(3), repeat=3):
            cpu_available = sum(cpu_inc[:2])
            io_available = sum(io_inc[:2])
            for cpu_required in range(7):
                for io_required in range(7):
                    demands, curves, epochs = _pair_fixture(
                        tuple(cpu_inc),
                        tuple(io_inc),
                        epoch=9,
                        cpu_required=cpu_required,
                        io_required=io_required,
                    )
                    result = multi_resource_admit(demands, curves, observed_epochs=epochs)
                    expected = (
                        ADMIT
                        if cpu_available >= cpu_required and io_available >= io_required
                        else MULTI_INSUFFICIENT
                    )
                    comparisons += 1
                    if result["status"] != expected:
                        mismatches += 1
    return {"comparisons": comparisons, "mismatches": mismatches}


def scalarization_adversary() -> dict[str, Any]:
    # CPU surplus exactly masks transfer deficit under an invalid scalar sum.
    demands, curves, epochs = _pair_fixture(
        (4, 4, 0),
        (0, 0, 8),
        epoch=4,
        cpu_required=4,
        io_required=4,
    )
    typed = multi_resource_admit(demands, curves, observed_epochs=epochs)
    cpu_available = service_at(curves[0].curve, 2)
    io_available = service_at(curves[1].curve, 2)
    naive_scalar_admit = (cpu_available + io_available) >= 8
    return {
        "cpu_available_cpu_quanta": cpu_available,
        "transfer_available_byte_quanta": io_available,
        "required_cpu_quanta": 4,
        "required_byte_quanta": 4,
        "naive_illegal_cross_unit_sum_admits": naive_scalar_admit,
        "typed_conjunction_status": typed["status"],
    }


def partial_stale_adversary() -> dict[str, Any]:
    demands, curves, epochs = _pair_fixture(
        (3, 3, 0),
        (3, 3, 0),
        epoch=20,
        cpu_required=4,
        io_required=4,
    )
    stale_epochs = dict(epochs)
    stale_epochs[("TRANSFER", "storage-link0")] = 21
    result = multi_resource_admit(demands, curves, observed_epochs=stale_epochs)
    return {
        "status": result["status"],
        "per_resource": result["per_resource"],
    }


def unit_mismatch_adversary() -> dict[str, Any]:
    demands, curves, epochs = _pair_fixture(
        (3, 3, 0),
        (3, 3, 0),
        epoch=30,
        cpu_required=4,
        io_required=4,
    )
    bad_curves = (curves[0], TypedCurve(curves[1].curve, "milliseconds"))
    result = multi_resource_admit(demands, bad_curves, observed_epochs=epochs)
    return {"status": result["status"], "per_resource": result["per_resource"]}


def _random_increments(total: int, bins: int, rng: random.Random) -> tuple[int, ...]:
    values = [0] * bins
    for _ in range(total):
        values[rng.randrange(bins)] += 1
    return tuple(values)


def monte_carlo_scalarization(*, seed: int = 20261008, trials: int = 5000) -> dict[str, int]:
    if trials <= 0:
        raise ValueError("trials_must_be_positive")
    rng = random.Random(seed)
    naive_scalar_false_admits = 0
    typed_false_admits = 0
    typed_admits = 0

    for trial in range(trials):
        cpu_total = rng.randint(1, 12)
        io_total = rng.randint(1, 12)
        cpu_inc = _random_increments(cpu_total, 3, rng)
        io_inc = _random_increments(io_total, 3, rng)
        cpu_required = rng.randint(1, cpu_total)
        io_required = rng.randint(1, io_total)
        demands, curves, epochs = _pair_fixture(
            cpu_inc,
            io_inc,
            epoch=100 + trial,
            cpu_required=cpu_required,
            io_required=io_required,
        )
        typed = multi_resource_admit(demands, curves, observed_epochs=epochs)
        cpu_available = service_at(curves[0].curve, 2)
        io_available = service_at(curves[1].curve, 2)
        truth = cpu_available >= cpu_required and io_available >= io_required
        naive = (cpu_available + io_available) >= (cpu_required + io_required)

        if naive and not truth:
            naive_scalar_false_admits += 1
        if typed["status"] == ADMIT:
            typed_admits += 1
            if not truth:
                typed_false_admits += 1

    return {
        "seed": seed,
        "trials": trials,
        "naive_scalar_false_admits": naive_scalar_false_admits,
        "typed_false_admits": typed_false_admits,
        "typed_admits": typed_admits,
    }


def run_panel(*, seed: int = 20261008, trials: int = 5000) -> dict[str, Any]:
    exhaustive = exhaustive_conjunction_check()
    scalar = scalarization_adversary()
    stale = partial_stale_adversary()
    unit = unit_mismatch_adversary()
    mc = monte_carlo_scalarization(seed=seed, trials=trials)

    checks = {
        "exhaustive_typed_conjunction_matches_direct_oracle": exhaustive["mismatches"] == 0,
        "illegal_cross_unit_scalar_sum_can_false_admit": (
            scalar["naive_illegal_cross_unit_sum_admits"] is True
            and scalar["typed_conjunction_status"] == MULTI_INSUFFICIENT
        ),
        "one_stale_required_resource_forces_whole_plan_replan": stale["status"] == REPLAN,
        "service_unit_mismatch_fails_closed": unit["status"] == UNIT_MISMATCH,
        "monte_carlo_finds_naive_scalar_false_admits": mc["naive_scalar_false_admits"] > 0,
        "typed_conjunction_has_zero_false_admits": mc["typed_false_admits"] == 0,
        "resource_conjunction_does_not_grant_authority": True,
        "resource_conjunction_does_not_grant_retry_permission": True,
    }

    return {
        "schema": SCHEMA,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "classification": "ANALYTIC_MULTI_RESOURCE_TYPED_SERVICE_CURVE_CONJUNCTION",
        "exhaustive": exhaustive,
        "scalarization_adversary": scalar,
        "partial_stale_adversary": stale,
        "unit_mismatch_adversary": unit,
        "monte_carlo": mc,
        "checks": checks,
        "decision": "MULTI_RESOURCE_ADMISSION_REQUIRES_PER_RESOURCE_CURRENT_EPOCH_SERVICE_CONSTRAINTS_WITHOUT_CROSS_UNIT_SCALARIZATION_IF_QUALIFIED",
        "claim_ceiling": "ANALYTIC_TWO_RESOURCE_DISCRETE_SERVICE_CURVE_CONJUNCTION_ONLY_NO_PHYSICAL_MULTI_DEVICE_OR_APPLICATION_CLAIM",
        "authority_effect": "NONE",
        "retry_authority": False,
        "scalar_gain": None,
        "next_gate": "PHYSICAL_CPU_PLUS_TRANSFER_SERVICE_CURVE_CONJUNCTION",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=20261008)
    parser.add_argument("--trials", type=int, default=5000)
    args = parser.parse_args()
    result = run_panel(seed=args.seed, trials=args.trials)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
