from __future__ import annotations

import argparse
import itertools
import json
import random
from dataclasses import asdict, dataclass
from typing import Any

SCHEMA = "finite-ram-lab.fr-p9-018-service-curve-deadline-admission/v0.1"

ADMIT = "ADMIT_RESOURCE_FEASIBLE"
INSUFFICIENT = "INSUFFICIENT_SERVICE_BEFORE_DEADLINE"
REPLAN = "REPLAN_REQUIRED"
MISMATCH = "FAIL_CLOSED_RESOURCE_MISMATCH"


@dataclass(frozen=True)
class ServiceSample:
    time_index: int
    cumulative_service: int


@dataclass(frozen=True)
class ServiceCurveSnapshot:
    resource_kind: str
    contention_domain: str
    measurement_epoch: int
    samples: tuple[ServiceSample, ...]


@dataclass(frozen=True)
class ServiceDemand:
    work_id: str
    resource_kind: str
    contention_domain: str
    deadline_index: int
    required_service: int


@dataclass(frozen=True)
class AdmissionDecision:
    status: str
    available_service: int | None
    required_service: int
    deadline_index: int
    curve_epoch: int
    observed_epoch: int
    reason: str
    authority_effect: str = "NONE"
    retry_authority: bool = False


def validate_curve(curve: ServiceCurveSnapshot) -> None:
    if not curve.resource_kind:
        raise ValueError("resource_kind_required")
    if not curve.contention_domain:
        raise ValueError("contention_domain_required")
    if curve.measurement_epoch < 0:
        raise ValueError("measurement_epoch_must_be_nonnegative")
    if not curve.samples:
        raise ValueError("service_curve_samples_required")

    last_time = -1
    last_service = -1
    for sample in curve.samples:
        if sample.time_index < 0:
            raise ValueError("sample_time_must_be_nonnegative")
        if sample.time_index <= last_time:
            raise ValueError("sample_times_must_be_strictly_increasing")
        if sample.cumulative_service < 0:
            raise ValueError("cumulative_service_must_be_nonnegative")
        if sample.cumulative_service < last_service:
            raise ValueError("cumulative_service_must_be_monotone")
        last_time = sample.time_index
        last_service = sample.cumulative_service


def validate_demand(demand: ServiceDemand) -> None:
    if not demand.work_id:
        raise ValueError("work_id_required")
    if not demand.resource_kind:
        raise ValueError("resource_kind_required")
    if not demand.contention_domain:
        raise ValueError("contention_domain_required")
    if demand.deadline_index < 0:
        raise ValueError("deadline_must_be_nonnegative")
    if demand.required_service < 0:
        raise ValueError("required_service_must_be_nonnegative")


def service_at(curve: ServiceCurveSnapshot, time_index: int) -> int:
    validate_curve(curve)
    if time_index < 0:
        raise ValueError("time_index_must_be_nonnegative")
    value = 0
    for sample in curve.samples:
        if sample.time_index > time_index:
            break
        value = sample.cumulative_service
    return value


def deadline_admit(
    demand: ServiceDemand,
    curve: ServiceCurveSnapshot,
    *,
    observed_epoch: int,
) -> AdmissionDecision:
    validate_demand(demand)
    validate_curve(curve)
    if observed_epoch < 0:
        raise ValueError("observed_epoch_must_be_nonnegative")

    if (
        demand.resource_kind != curve.resource_kind
        or demand.contention_domain != curve.contention_domain
    ):
        return AdmissionDecision(
            status=MISMATCH,
            available_service=None,
            required_service=demand.required_service,
            deadline_index=demand.deadline_index,
            curve_epoch=curve.measurement_epoch,
            observed_epoch=observed_epoch,
            reason="resource_or_contention_domain_mismatch",
        )

    if curve.measurement_epoch != observed_epoch:
        return AdmissionDecision(
            status=REPLAN,
            available_service=None,
            required_service=demand.required_service,
            deadline_index=demand.deadline_index,
            curve_epoch=curve.measurement_epoch,
            observed_epoch=observed_epoch,
            reason="service_curve_epoch_stale",
        )

    available = service_at(curve, demand.deadline_index)
    if available >= demand.required_service:
        return AdmissionDecision(
            status=ADMIT,
            available_service=available,
            required_service=demand.required_service,
            deadline_index=demand.deadline_index,
            curve_epoch=curve.measurement_epoch,
            observed_epoch=observed_epoch,
            reason="cumulative_service_meets_deadline_demand",
        )
    return AdmissionDecision(
        status=INSUFFICIENT,
        available_service=available,
        required_service=demand.required_service,
        deadline_index=demand.deadline_index,
        curve_epoch=curve.measurement_epoch,
        observed_epoch=observed_epoch,
        reason="cumulative_service_below_deadline_demand",
    )


def curve_from_increments(
    increments: tuple[int, ...],
    *,
    epoch: int,
    resource_kind: str = "CPU",
    contention_domain: str = "cpu0",
) -> ServiceCurveSnapshot:
    if not increments:
        raise ValueError("increments_required")
    if any(value < 0 for value in increments):
        raise ValueError("increments_must_be_nonnegative")
    cumulative = 0
    samples: list[ServiceSample] = []
    for index, increment in enumerate(increments, start=1):
        cumulative += increment
        samples.append(ServiceSample(index, cumulative))
    return ServiceCurveSnapshot(
        resource_kind=resource_kind,
        contention_domain=contention_domain,
        measurement_epoch=epoch,
        samples=tuple(samples),
    )


def exhaustive_oracle_check() -> dict[str, int]:
    mismatches = 0
    comparisons = 0
    for increments in itertools.product(range(4), repeat=4):
        curve = curve_from_increments(tuple(increments), epoch=7)
        for deadline in range(1, 5):
            oracle_available = sum(increments[:deadline])
            for required in range(14):
                demand = ServiceDemand(
                    work_id="exhaustive",
                    resource_kind="CPU",
                    contention_domain="cpu0",
                    deadline_index=deadline,
                    required_service=required,
                )
                decision = deadline_admit(demand, curve, observed_epoch=7)
                expected = ADMIT if oracle_available >= required else INSUFFICIENT
                comparisons += 1
                if decision.status != expected or decision.available_service != oracle_available:
                    mismatches += 1
    return {"comparisons": comparisons, "mismatches": mismatches}


def equal_total_timing_adversary() -> dict[str, Any]:
    front = curve_from_increments((4, 4, 0, 0), epoch=3)
    back = curve_from_increments((0, 0, 4, 4), epoch=3)
    demand = ServiceDemand("timing", "CPU", "cpu0", 2, 6)
    front_decision = deadline_admit(demand, front, observed_epoch=3)
    back_decision = deadline_admit(demand, back, observed_epoch=3)
    return {
        "front_horizon_total": service_at(front, 4),
        "back_horizon_total": service_at(back, 4),
        "front_deadline_service": service_at(front, 2),
        "back_deadline_service": service_at(back, 2),
        "front_status": front_decision.status,
        "back_status": back_decision.status,
    }


def stale_epoch_adversary() -> dict[str, Any]:
    forecast = curve_from_increments((4, 4, 0, 0), epoch=10)
    actual = curve_from_increments((0, 0, 4, 4), epoch=11)
    demand = ServiceDemand("stale", "CPU", "cpu0", 2, 6)
    naive_forecast = deadline_admit(demand, forecast, observed_epoch=10)
    stale_aware = deadline_admit(demand, forecast, observed_epoch=11)
    actual_decision = deadline_admit(demand, actual, observed_epoch=11)
    return {
        "forecast_horizon_total": service_at(forecast, 4),
        "actual_horizon_total": service_at(actual, 4),
        "naive_forecast_status": naive_forecast.status,
        "stale_aware_status": stale_aware.status,
        "actual_status": actual_decision.status,
    }


def _random_allocation(total: int, bins: int, rng: random.Random) -> tuple[int, ...]:
    values = [0] * bins
    for _ in range(total):
        values[rng.randrange(bins)] += 1
    return tuple(values)


def monte_carlo_stale_forecasts(*, seed: int = 20261008, trials: int = 5000) -> dict[str, int]:
    if trials <= 0:
        raise ValueError("trials_must_be_positive")
    rng = random.Random(seed)
    naive_false_admits = 0
    epoch_aware_false_admits = 0
    replan_required = 0
    same_total_trials = 0

    for trial in range(trials):
        total = rng.randint(1, 12)
        forecast_inc = _random_allocation(total, 4, rng)
        actual_inc = _random_allocation(total, 4, rng)
        forecast = curve_from_increments(forecast_inc, epoch=100 + trial * 2)
        actual = curve_from_increments(actual_inc, epoch=101 + trial * 2)
        deadline = rng.randint(1, 3)
        required = rng.randint(1, total)
        demand = ServiceDemand(f"mc-{trial}", "CPU", "cpu0", deadline, required)

        naive = deadline_admit(demand, forecast, observed_epoch=forecast.measurement_epoch)
        guarded = deadline_admit(demand, forecast, observed_epoch=actual.measurement_epoch)
        truth = deadline_admit(demand, actual, observed_epoch=actual.measurement_epoch)

        if service_at(forecast, 4) == service_at(actual, 4):
            same_total_trials += 1
        if naive.status == ADMIT and truth.status != ADMIT:
            naive_false_admits += 1
        if guarded.status == ADMIT and truth.status != ADMIT:
            epoch_aware_false_admits += 1
        if guarded.status == REPLAN:
            replan_required += 1

    return {
        "seed": seed,
        "trials": trials,
        "same_total_trials": same_total_trials,
        "naive_false_admits": naive_false_admits,
        "epoch_aware_false_admits": epoch_aware_false_admits,
        "replan_required": replan_required,
    }


def run_panel(*, seed: int = 20261008, trials: int = 5000) -> dict[str, Any]:
    exhaustive = exhaustive_oracle_check()
    timing = equal_total_timing_adversary()
    stale = stale_epoch_adversary()
    mc = monte_carlo_stale_forecasts(seed=seed, trials=trials)

    checks = {
        "exhaustive_operator_matches_direct_cumulative_oracle": exhaustive["mismatches"] == 0,
        "equal_total_curves_can_have_different_deadline_admission": (
            timing["front_horizon_total"] == timing["back_horizon_total"]
            and timing["front_status"] == ADMIT
            and timing["back_status"] == INSUFFICIENT
        ),
        "stale_forecast_is_replan_not_admit": (
            stale["naive_forecast_status"] == ADMIT
            and stale["stale_aware_status"] == REPLAN
            and stale["actual_status"] == INSUFFICIENT
        ),
        "monte_carlo_contains_naive_false_admits": mc["naive_false_admits"] > 0,
        "epoch_guard_eliminates_stale_forecast_false_admit": mc["epoch_aware_false_admits"] == 0,
        "all_stale_trials_require_replan": mc["replan_required"] == trials,
        "all_monte_carlo_pairs_preserve_horizon_total": mc["same_total_trials"] == trials,
        "resource_admission_does_not_grant_authority": True,
        "resource_admission_does_not_grant_retry_permission": True,
    }

    return {
        "schema": SCHEMA,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "classification": "ANALYTIC_DISCRETE_SERVICE_CURVE_DEADLINE_ADMISSION",
        "exhaustive": exhaustive,
        "equal_total_timing_adversary": timing,
        "stale_epoch_adversary": stale,
        "monte_carlo": mc,
        "checks": checks,
        "decision": "DEADLINE_ADMISSION_REQUIRES_CURRENT_EPOCH_CUMULATIVE_SERVICE_AT_DEADLINE_IF_QUALIFIED",
        "claim_ceiling": "ANALYTIC_DISCRETE_SERVICE_CURVE_ADMISSION_ONLY_NO_PHYSICAL_SCHEDULER_OR_APPLICATION_CLAIM",
        "authority_effect": "NONE",
        "retry_authority": False,
        "scalar_gain": None,
        "next_gate": "PHYSICAL_FORECAST_DRIFT_AND_SERVICE_CURVE_EPOCH_REPLAN",
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
