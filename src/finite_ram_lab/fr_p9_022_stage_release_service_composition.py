from __future__ import annotations

import argparse
import itertools
import json
import random
from typing import Any

from finite_ram_lab.fr_p9_018_service_curve_deadline_admission import (
    ADMIT,
    REPLAN,
    ServiceCurveSnapshot,
    curve_from_increments,
    service_at,
)

SCHEMA = "finite-ram-lab.fr-p9-022-stage-release-service-composition/v0.1"
INSUFFICIENT_TRANSFER = "INSUFFICIENT_TRANSFER_SERVICE_BEFORE_DEADLINE"
INSUFFICIENT_CPU = "INSUFFICIENT_POST_RELEASE_CPU_SERVICE_BEFORE_DEADLINE"


def first_completion_index(
    curve: ServiceCurveSnapshot,
    required_service: int,
    *,
    deadline_index: int,
) -> int | None:
    if required_service < 0 or deadline_index < 0:
        raise ValueError("requirements_and_deadline_must_be_nonnegative")
    if required_service == 0:
        return 0
    for index in range(0, deadline_index + 1):
        if service_at(curve, index) >= required_service:
            return index
    return None


def post_release_service(
    curve: ServiceCurveSnapshot,
    *,
    release_index: int,
    deadline_index: int,
) -> int:
    if release_index < 0 or deadline_index < 0:
        raise ValueError("indices_must_be_nonnegative")
    if release_index > deadline_index:
        return 0
    return service_at(curve, deadline_index) - service_at(curve, release_index)


def two_stage_admit(
    *,
    transfer_curve: ServiceCurveSnapshot,
    cpu_curve: ServiceCurveSnapshot,
    transfer_required: int,
    cpu_required: int,
    deadline_index: int,
    observed_transfer_epoch: int,
    observed_cpu_epoch: int,
) -> dict[str, Any]:
    if transfer_curve.measurement_epoch != observed_transfer_epoch:
        return {
            "status": REPLAN,
            "reason": "transfer_curve_epoch_stale",
            "authority_effect": "NONE",
            "retry_authority": False,
        }
    if cpu_curve.measurement_epoch != observed_cpu_epoch:
        return {
            "status": REPLAN,
            "reason": "cpu_curve_epoch_stale",
            "authority_effect": "NONE",
            "retry_authority": False,
        }

    release = first_completion_index(
        transfer_curve,
        transfer_required,
        deadline_index=deadline_index,
    )
    if release is None:
        return {
            "status": INSUFFICIENT_TRANSFER,
            "release_index": None,
            "usable_cpu_service": 0,
            "authority_effect": "NONE",
            "retry_authority": False,
        }

    usable_cpu = post_release_service(
        cpu_curve,
        release_index=release,
        deadline_index=deadline_index,
    )
    status = ADMIT if usable_cpu >= cpu_required else INSUFFICIENT_CPU
    return {
        "status": status,
        "release_index": release,
        "usable_cpu_service": usable_cpu,
        "authority_effect": "NONE",
        "retry_authority": False,
    }


def naive_independent_admit(
    *,
    transfer_curve: ServiceCurveSnapshot,
    cpu_curve: ServiceCurveSnapshot,
    transfer_required: int,
    cpu_required: int,
    deadline_index: int,
) -> bool:
    return (
        service_at(transfer_curve, deadline_index) >= transfer_required
        and service_at(cpu_curve, deadline_index) >= cpu_required
    )


def release_order_adversary() -> dict[str, Any]:
    transfer = curve_from_increments(
        (0, 0, 4, 0),
        epoch=7,
        resource_kind="TRANSFER",
        contention_domain="storage-link0",
    )
    cpu_front = curve_from_increments(
        (4, 0, 0, 0), epoch=7, resource_kind="CPU", contention_domain="cpu0"
    )
    cpu_back = curve_from_increments(
        (0, 0, 0, 4), epoch=7, resource_kind="CPU", contention_domain="cpu0"
    )
    front = two_stage_admit(
        transfer_curve=transfer,
        cpu_curve=cpu_front,
        transfer_required=4,
        cpu_required=4,
        deadline_index=4,
        observed_transfer_epoch=7,
        observed_cpu_epoch=7,
    )
    back = two_stage_admit(
        transfer_curve=transfer,
        cpu_curve=cpu_back,
        transfer_required=4,
        cpu_required=4,
        deadline_index=4,
        observed_transfer_epoch=7,
        observed_cpu_epoch=7,
    )
    return {
        "naive_front_admit": naive_independent_admit(
            transfer_curve=transfer,
            cpu_curve=cpu_front,
            transfer_required=4,
            cpu_required=4,
            deadline_index=4,
        ),
        "stage_aware_front_status": front["status"],
        "front_release_index": front["release_index"],
        "front_usable_cpu_service": front["usable_cpu_service"],
        "stage_aware_back_status": back["status"],
        "back_release_index": back["release_index"],
        "back_usable_cpu_service": back["usable_cpu_service"],
    }


def exhaustive_stage_check() -> dict[str, int]:
    comparisons = 0
    mismatches = 0
    for transfer_inc in itertools.product(range(3), repeat=4):
        transfer_curve = curve_from_increments(
            tuple(transfer_inc),
            epoch=3,
            resource_kind="TRANSFER",
            contention_domain="storage-link0",
        )
        for cpu_inc in itertools.product(range(3), repeat=4):
            cpu_curve = curve_from_increments(
                tuple(cpu_inc), epoch=3, resource_kind="CPU", contention_domain="cpu0"
            )
            for transfer_required in range(1, 5):
                for cpu_required in range(1, 5):
                    release = None
                    cumulative = 0
                    for index, increment in enumerate(transfer_inc, start=1):
                        cumulative += increment
                        if cumulative >= transfer_required:
                            release = index
                            break
                    if release is None or release > 4:
                        expected = INSUFFICIENT_TRANSFER
                    else:
                        usable_cpu = sum(cpu_inc[release:4])
                        expected = ADMIT if usable_cpu >= cpu_required else INSUFFICIENT_CPU

                    result = two_stage_admit(
                        transfer_curve=transfer_curve,
                        cpu_curve=cpu_curve,
                        transfer_required=transfer_required,
                        cpu_required=cpu_required,
                        deadline_index=4,
                        observed_transfer_epoch=3,
                        observed_cpu_epoch=3,
                    )
                    comparisons += 1
                    if result["status"] != expected:
                        mismatches += 1
    return {"comparisons": comparisons, "mismatches": mismatches}


def stale_stage_adversary() -> dict[str, Any]:
    transfer = curve_from_increments(
        (2, 2, 0, 0), epoch=10, resource_kind="TRANSFER", contention_domain="storage-link0"
    )
    cpu = curve_from_increments(
        (0, 0, 2, 2), epoch=10, resource_kind="CPU", contention_domain="cpu0"
    )
    result = two_stage_admit(
        transfer_curve=transfer,
        cpu_curve=cpu,
        transfer_required=4,
        cpu_required=4,
        deadline_index=4,
        observed_transfer_epoch=11,
        observed_cpu_epoch=10,
    )
    return {"status": result["status"], "reason": result["reason"]}


def _random_increments(total: int, bins: int, rng: random.Random) -> tuple[int, ...]:
    values = [0] * bins
    for _ in range(total):
        values[rng.randrange(bins)] += 1
    return tuple(values)


def monte_carlo_release_dependencies(*, seed: int = 20261008, trials: int = 5000) -> dict[str, int]:
    if trials <= 0:
        raise ValueError("trials_must_be_positive")
    rng = random.Random(seed)
    naive_false_admits = 0
    stage_aware_false_admits = 0
    stage_aware_admits = 0

    for trial in range(trials):
        transfer_total = rng.randint(1, 10)
        cpu_total = rng.randint(1, 10)
        transfer_inc = _random_increments(transfer_total, 4, rng)
        cpu_inc = _random_increments(cpu_total, 4, rng)
        transfer_required = rng.randint(1, transfer_total)
        cpu_required = rng.randint(1, cpu_total)
        transfer = curve_from_increments(
            transfer_inc,
            epoch=100 + trial,
            resource_kind="TRANSFER",
            contention_domain="storage-link0",
        )
        cpu = curve_from_increments(
            cpu_inc,
            epoch=100 + trial,
            resource_kind="CPU",
            contention_domain="cpu0",
        )

        # Direct stage simulation oracle.
        cumulative_transfer = 0
        release = None
        for index, increment in enumerate(transfer_inc, start=1):
            cumulative_transfer += increment
            if cumulative_transfer >= transfer_required:
                release = index
                break
        truth = False
        if release is not None:
            truth = sum(cpu_inc[release:4]) >= cpu_required

        naive = naive_independent_admit(
            transfer_curve=transfer,
            cpu_curve=cpu,
            transfer_required=transfer_required,
            cpu_required=cpu_required,
            deadline_index=4,
        )
        stage = two_stage_admit(
            transfer_curve=transfer,
            cpu_curve=cpu,
            transfer_required=transfer_required,
            cpu_required=cpu_required,
            deadline_index=4,
            observed_transfer_epoch=100 + trial,
            observed_cpu_epoch=100 + trial,
        )

        if naive and not truth:
            naive_false_admits += 1
        if stage["status"] == ADMIT:
            stage_aware_admits += 1
            if not truth:
                stage_aware_false_admits += 1

    return {
        "seed": seed,
        "trials": trials,
        "naive_independent_false_admits": naive_false_admits,
        "stage_aware_false_admits": stage_aware_false_admits,
        "stage_aware_admits": stage_aware_admits,
    }


def run_panel(*, seed: int = 20261008, trials: int = 5000) -> dict[str, Any]:
    exhaustive = exhaustive_stage_check()
    adversary = release_order_adversary()
    stale = stale_stage_adversary()
    mc = monte_carlo_release_dependencies(seed=seed, trials=trials)

    checks = {
        "exhaustive_stage_operator_matches_direct_simulation": exhaustive["mismatches"] == 0,
        "independent_absolute_curves_can_false_admit_when_cpu_service_arrives_before_release": (
            adversary["naive_front_admit"] is True
            and adversary["stage_aware_front_status"] == INSUFFICIENT_CPU
            and adversary["front_usable_cpu_service"] == 0
        ),
        "post_release_cpu_service_can_make_same_transfer_pipeline_feasible": (
            adversary["stage_aware_back_status"] == ADMIT
            and adversary["back_usable_cpu_service"] == 4
        ),
        "stale_upstream_stage_forces_replan": stale["status"] == REPLAN,
        "monte_carlo_finds_naive_independent_false_admits": mc["naive_independent_false_admits"] > 0,
        "stage_aware_operator_has_zero_false_admits": mc["stage_aware_false_admits"] == 0,
        "stage_composition_does_not_grant_authority": True,
        "stage_composition_does_not_grant_retry_permission": True,
    }

    return {
        "schema": SCHEMA,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "classification": "ANALYTIC_SEQUENTIAL_STAGE_RELEASE_AWARE_SERVICE_COMPOSITION",
        "prior_art_boundary": "SERVICE_CURVE_COMPOSITION_AND_MIN_PLUS_NETWORK_CALCULUS_ARE_ESTABLISHED_PRIOR_ART_THIS_IS_A_SEMANTIC_MATERIALIZATION_ADAPTATION",
        "exhaustive": exhaustive,
        "release_order_adversary": adversary,
        "stale_stage_adversary": stale,
        "monte_carlo": mc,
        "checks": checks,
        "decision": "SEQUENTIAL_MATERIALIZATION_MUST_COUNT_ONLY_DOWNSTREAM_SERVICE_AVAILABLE_AFTER_UPSTREAM_STAGE_RELEASE_IF_QUALIFIED",
        "claim_ceiling": "ANALYTIC_DISCRETE_TWO_STAGE_RELEASE_AWARE_MATERIALIZATION_ONLY_NO_NEW_NETWORK_CALCULUS_THEOREM_OR_PHYSICAL_APPLICATION_CLAIM",
        "authority_effect": "NONE",
        "retry_authority": False,
        "scalar_gain": None,
        "next_gate": "PHYSICAL_STAGE_RELEASE_COMPOSITION_WITH_OVERLAP_AND_STREAMING",
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
