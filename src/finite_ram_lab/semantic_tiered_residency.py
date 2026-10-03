from __future__ import annotations

import itertools
import json
from dataclasses import dataclass
from typing import Iterable


SCHEMA = "finite-ram-lab.semantic-tiered-residency/v0.1"
RELIEF_TARGET_MIB = 4096

EXPECTED_WEIGHT = 0.01
CVAR95_WEIGHT = 0.02
SSD_WRITE_WEIGHT = 0.001


@dataclass(frozen=True)
class Choice:
    name: str
    relief_mib: int
    semantic_loss: float
    apply_ms: float
    ssd_write_mib: int
    restore_ms: float


GROUPS: dict[str, tuple[Choice, ...]] = {
    "KV": (
        Choice("KEEP", 0, 0, 0, 0, 0),
        Choice("Q8", 1024, 6, 12, 0, 20),
        Choice("Q4", 1536, 15, 20, 0, 35),
        Choice("SSD_COLD", 2048, 4, 5, 2048, 160),
    ),
    "PREFIX": (
        Choice("KEEP", 0, 0, 0, 0, 0),
        Choice("SSD", 1024, 1, 3, 1024, 70),
        Choice("DROP", 1024, 10, 8, 0, 300),
    ),
    "AUX_EXPERTS": (
        Choice("KEEP", 0, 0, 0, 0, 0),
        Choice("SSD", 3072, 6, 4, 3072, 240),
    ),
    "BROWSER_CACHE": (
        Choice("KEEP", 0, 0, 0, 0, 0),
        Choice("DROP", 1536, 20, 10, 0, 180),
    ),
    "BACKGROUND_JOB": (
        Choice("KEEP", 0, 0, 0, 0, 0),
        Choice("EXIT", 2048, 70, 15, 0, 1200),
    ),
    "ACTIVE_TASK": (
        Choice("KEEP", 0, 0, 0, 0, 0),
        Choice("KILL", 4096, 280, 5, 0, 5000),
    ),
}


REFAULT_SCENARIOS: tuple[tuple[float, tuple[str, ...]], ...] = (
    (0.80, ()),
    (0.05, ("KV",)),
    (0.05, ("PREFIX",)),
    (0.05, ("AUX_EXPERTS",)),
    (0.03, ("KV", "AUX_EXPERTS")),
    (0.02, ("KV", "PREFIX", "AUX_EXPERTS")),
)


def _cvar(
    values: list[float],
    probabilities: list[float],
    alpha: float = 0.95,
) -> float:
    tail_mass = 1.0 - alpha
    ranked = sorted(
        zip(values, probabilities),
        key=lambda pair: pair[0],
        reverse=True,
    )
    used = 0.0
    weighted = 0.0
    for value, probability in ranked:
        take = min(probability, tail_mass - used)
        if take > 0:
            weighted += value * take
            used += take
        if used >= tail_mass - 1e-12:
            break
    if used <= 0:
        return 0.0
    return weighted / used


def _scenario_restore_ms(
    plan: dict[str, Choice],
    affected: Iterable[str],
) -> float:
    return sum(
        plan[group].restore_ms
        for group in affected
        if plan[group].name != "KEEP"
    )


def evaluate_plan(
    plan: dict[str, Choice],
    *,
    ssd_enabled: bool,
    ssd_p05_write_mib_s: float,
    deadline_ms: float,
    max_ssd_write_mib: int,
) -> dict | None:
    relief_mib = sum(choice.relief_mib for choice in plan.values())
    semantic_loss = sum(choice.semantic_loss for choice in plan.values())
    non_ssd_apply_ms = sum(choice.apply_ms for choice in plan.values())
    ssd_write_mib = sum(choice.ssd_write_mib for choice in plan.values())

    if relief_mib < RELIEF_TARGET_MIB:
        return None
    if not ssd_enabled and ssd_write_mib:
        return None
    if ssd_write_mib > max_ssd_write_mib:
        return None
    if ssd_write_mib and ssd_p05_write_mib_s <= 0:
        return None

    migration_ms = non_ssd_apply_ms
    if ssd_write_mib:
        migration_ms += (
            ssd_write_mib / ssd_p05_write_mib_s
        ) * 1000.0

    if migration_ms > deadline_ms:
        return None

    restore_values: list[float] = []
    probabilities: list[float] = []
    for probability, affected in REFAULT_SCENARIOS:
        probabilities.append(probability)
        restore_values.append(
            _scenario_restore_ms(plan, affected)
        )

    expected_restore_ms = sum(
        value * probability
        for value, probability
        in zip(restore_values, probabilities)
    )
    cvar95_restore_ms = _cvar(
        restore_values,
        probabilities,
        0.95,
    )

    objective = (
        semantic_loss
        + EXPECTED_WEIGHT * expected_restore_ms
        + CVAR95_WEIGHT * cvar95_restore_ms
        + SSD_WRITE_WEIGHT * ssd_write_mib
    )

    return {
        "objective": objective,
        "relief_mib": relief_mib,
        "semantic_loss": semantic_loss,
        "ssd_write_mib": ssd_write_mib,
        "non_ssd_apply_ms": non_ssd_apply_ms,
        "migration_ms_at_p05_bandwidth": migration_ms,
        "expected_restore_ms": expected_restore_ms,
        "cvar95_restore_ms": cvar95_restore_ms,
        "choices": {
            group: choice.name
            for group, choice in plan.items()
        },
    }


def solve(
    *,
    ssd_enabled: bool,
    ssd_p05_write_mib_s: float,
    deadline_ms: float,
    max_ssd_write_mib: int,
) -> dict:
    names = tuple(GROUPS)
    best: dict | None = None
    feasible_count = 0

    for choices in itertools.product(
        *(GROUPS[name] for name in names)
    ):
        plan = dict(zip(names, choices))
        row = evaluate_plan(
            plan,
            ssd_enabled=ssd_enabled,
            ssd_p05_write_mib_s=ssd_p05_write_mib_s,
            deadline_ms=deadline_ms,
            max_ssd_write_mib=max_ssd_write_mib,
        )
        if row is None:
            continue
        feasible_count += 1

        if (
            best is None
            or row["objective"] < best["objective"]
            or (
                row["objective"] == best["objective"]
                and row["semantic_loss"]
                < best["semantic_loss"]
            )
        ):
            best = row

    if best is None:
        raise RuntimeError("no_feasible_plan")

    return {
        "feasible_plan_count": feasible_count,
        **best,
    }


def run_panel() -> dict:
    arms = {
        "RAM_ONLY": solve(
            ssd_enabled=False,
            ssd_p05_write_mib_s=2500,
            deadline_ms=1600,
            max_ssd_write_mib=4096,
        ),
        "FAST_SSD_TIERED": solve(
            ssd_enabled=True,
            ssd_p05_write_mib_s=2500,
            deadline_ms=1600,
            max_ssd_write_mib=4096,
        ),
        "WRITE_BUDGET_2G": solve(
            ssd_enabled=True,
            ssd_p05_write_mib_s=2500,
            deadline_ms=1600,
            max_ssd_write_mib=2048,
        ),
        "SLOW_SSD_TIERED": solve(
            ssd_enabled=True,
            ssd_p05_write_mib_s=1000,
            deadline_ms=800,
            max_ssd_write_mib=4096,
        ),
        "EMERGENCY_SHORT_DEADLINE": solve(
            ssd_enabled=True,
            ssd_p05_write_mib_s=2500,
            deadline_ms=150,
            max_ssd_write_mib=4096,
        ),
    }

    fast = arms["FAST_SSD_TIERED"]
    ram = arms["RAM_ONLY"]
    write_limited = arms["WRITE_BUDGET_2G"]
    slow = arms["SLOW_SSD_TIERED"]
    emergency = arms["EMERGENCY_SHORT_DEADLINE"]

    if fast["choices"] != {
        "KV": "Q8",
        "PREFIX": "KEEP",
        "AUX_EXPERTS": "SSD",
        "BROWSER_CACHE": "KEEP",
        "BACKGROUND_JOB": "KEEP",
        "ACTIVE_TASK": "KEEP",
    }:
        raise RuntimeError("fast_ssd_reference_changed")

    if ram["choices"] != {
        "KV": "Q4",
        "PREFIX": "DROP",
        "AUX_EXPERTS": "KEEP",
        "BROWSER_CACHE": "DROP",
        "BACKGROUND_JOB": "KEEP",
        "ACTIVE_TASK": "KEEP",
    }:
        raise RuntimeError("ram_only_reference_changed")

    if write_limited["choices"] != {
        "KV": "Q4",
        "PREFIX": "SSD",
        "AUX_EXPERTS": "KEEP",
        "BROWSER_CACHE": "DROP",
        "BACKGROUND_JOB": "KEEP",
        "ACTIVE_TASK": "KEEP",
    }:
        raise RuntimeError("write_budget_reference_changed")

    if slow["choices"] != ram["choices"]:
        raise RuntimeError("slow_ssd_should_fall_back_to_ram_plan")

    if emergency["choices"] != ram["choices"]:
        raise RuntimeError("short_deadline_should_fall_back_to_ram_plan")

    if not fast["objective"] < ram["objective"]:
        raise RuntimeError("tiered_plan_has_no_modeled_advantage")

    if fast["choices"]["ACTIVE_TASK"] != "KEEP":
        raise RuntimeError("fast_tiered_plan_killed_active_task")

    fast_min_p05_write_mib_s = (
        fast["ssd_write_mib"]
        / (
            (1600.0 - fast["non_ssd_apply_ms"])
            / 1000.0
        )
    )
    if not 1900 < fast_min_p05_write_mib_s < 2000:
        raise RuntimeError("analytic_bandwidth_knee_changed")

    return {
        "schema": SCHEMA,
        "status": "PASS",
        "classification": (
            "SYNTHETIC_TIERED_RESIDENCY_SHADOW_PLANNER_VALIDATED"
        ),
        "synthetic_only": True,
        "live_control_claim": False,
        "relief_target_mib": RELIEF_TARGET_MIB,
        "objective_weights": {
            "expected_restore_ms": EXPECTED_WEIGHT,
            "cvar95_restore_ms": CVAR95_WEIGHT,
            "ssd_write_mib": SSD_WRITE_WEIGHT,
        },
        "analytic_boundaries": {
            "fast_hybrid_min_p05_write_mib_s_at_1600ms": (
                fast_min_p05_write_mib_s
            ),
            "fast_hybrid_min_write_budget_mib": (
                fast["ssd_write_mib"]
            ),
        },
        "refault_scenarios": [
            {
                "probability": probability,
                "affected": list(affected),
            }
            for probability, affected
            in REFAULT_SCENARIOS
        ],
        "arms": arms,
        "primary_finding": (
            "SSD_IS_USEFUL_AS_A_SEMANTIC_TIER_ONLY_WHEN_ITS_TAIL_BANDWIDTH_AND_DEADLINE_CONSTRAINTS_QUALIFY"
        ),
        "claim_ceiling": (
            "SYNTHETIC_TIERED_RESIDENCY_SHADOW_PLANNER_ONLY"
        ),
    }


def main() -> int:
    print(json.dumps(run_panel(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
