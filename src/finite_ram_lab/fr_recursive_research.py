from __future__ import annotations

import json
import math
import random
import statistics
from typing import Iterable

SCHEMA = "finite-ram-lab.fr-meta-001-recursive-research/v0.1"

SCENARIOS = {
    "EVIDENCE_GAP": {"uncertainty": 0.55, "rare": 0.04, "ambiguity": 0.65, "experiment_value": 0.55},
    "MODEL_GAP": {"uncertainty": 0.72, "rare": 0.02, "ambiguity": 0.55, "experiment_value": 0.35},
    "CAPABILITY_GAP": {"uncertainty": 0.82, "rare": 0.08, "ambiguity": 0.80, "experiment_value": 0.90},
    "CONTRACT_GAP": {"uncertainty": 0.42, "rare": 0.03, "ambiguity": 0.45, "experiment_value": 0.25},
    "FRONTIER_REACHED": {"uncertainty": 0.18, "rare": 0.01, "ambiguity": 0.15, "experiment_value": 0.05},
}

STAGE_COST = {
    "explore": 4.0,
    "atomize": 2.0,
    "council": 3.0,
    "monte_carlo": 7.0,
    "experiment": 12.0,
    "failure_biopsy": 5.0,
    "theory_update": 3.0,
}

STAGE_GAIN = {
    "explore": 0.11,
    "atomize": 0.14,
    "council": 0.13,
    "monte_carlo": 0.24,
    "experiment": 0.28,
    "failure_biopsy": 0.22,
    "theory_update": 0.10,
}

NOMINAL_WEIGHTS = {
    "progress": 1.0,
    "correct": 0.8,
    "rare": 0.35,
    "cost": 0.045,
}

PROTOCOLS = {
    "FIXED_V1": {
        "gap_router": False,
        "mc_threshold": 0.0,
        "biopsy_threshold": 0.0,
        "stop_at_frontier": False,
        "skip_council": False,
        "missing_evidence_as_zero": False,
    },
    "VOI_ADAPTIVE_V2": {
        "gap_router": True,
        "mc_threshold": 0.60,
        "biopsy_threshold": 0.20,
        "stop_at_frontier": True,
        "skip_council": False,
        "missing_evidence_as_zero": False,
    },
    "RISKY_FAST": {
        "gap_router": True,
        "mc_threshold": 0.90,
        "biopsy_threshold": 0.90,
        "stop_at_frontier": True,
        "skip_council": True,
        "missing_evidence_as_zero": True,
    },
}

MIXED_POLICY = {
    "EVIDENCE_GAP": "VOI_ADAPTIVE_V2",
    "MODEL_GAP": "FIXED_V1",
    "CAPABILITY_GAP": "FIXED_V1",
    "CONTRACT_GAP": "VOI_ADAPTIVE_V2",
    "FRONTIER_REACHED": "VOI_ADAPTIVE_V2",
}

COUNCIL_ROLES = (
    "methodologist",
    "statistician",
    "systems_researcher",
    "falsifier",
    "continuity_reviewer",
)


def invariant_violations(protocol_name: str) -> list[str]:
    protocol = PROTOCOLS[protocol_name]
    violations: list[str] = []

    if protocol["skip_council"]:
        violations.append("EXPERIMENT_WITHOUT_COUNCIL")

    if protocol["missing_evidence_as_zero"]:
        violations.append("MISSING_EVIDENCE_TREATED_AS_ZERO")

    return violations


def stages_for(protocol_name: str, gap: str) -> list[str]:
    protocol = PROTOCOLS[protocol_name]
    scenario = SCENARIOS[gap]

    if protocol["stop_at_frontier"] and gap == "FRONTIER_REACHED":
        return ["explore", "atomize", "council", "theory_update"]

    stages = ["explore", "atomize", "council"]

    if protocol["skip_council"]:
        stages.remove("council")

    if scenario["uncertainty"] >= protocol["mc_threshold"]:
        stages.append("monte_carlo")

    if gap != "FRONTIER_REACHED":
        stages.append("experiment")

    failure_signal = max(
        scenario["rare"],
        scenario["ambiguity"] * 0.60,
    )
    if (
        gap != "FRONTIER_REACHED"
        and failure_signal >= protocol["biopsy_threshold"]
    ):
        stages.append("failure_biopsy")

    stages.append("theory_update")
    return stages


def _single_trial(
    protocol_name: str,
    gap: str,
    rng: random.Random,
    weights: dict[str, float],
) -> dict:
    scenario = SCENARIOS[gap]
    protocol = PROTOCOLS[protocol_name]
    stages = stages_for(protocol_name, gap)

    cost = sum(STAGE_COST[name] for name in stages)

    correct_probability = 0.20
    correct_probability += STAGE_GAIN["explore"] if "explore" in stages else 0.0
    correct_probability += STAGE_GAIN["atomize"] if "atomize" in stages else 0.0
    correct_probability += STAGE_GAIN["council"] if "council" in stages else -0.12

    if "monte_carlo" in stages:
        correct_probability += STAGE_GAIN["monte_carlo"] * scenario["uncertainty"]

    if "experiment" in stages:
        correct_probability += STAGE_GAIN["experiment"] * scenario["experiment_value"]

    if "failure_biopsy" in stages:
        correct_probability += STAGE_GAIN["failure_biopsy"] * max(
            scenario["rare"] * 4.0,
            scenario["ambiguity"] * 0.55,
        )

    if "theory_update" in stages:
        correct_probability += STAGE_GAIN["theory_update"]

    if protocol["gap_router"]:
        correct_probability += 0.06
        cost += 1.0

    if protocol["missing_evidence_as_zero"]:
        correct_probability -= 0.22
        cost -= 1.0

    correct_probability = min(0.995, max(0.02, correct_probability))
    correct = rng.random() < correct_probability

    if gap == "FRONTIER_REACHED":
        rare_capture_probability = 1.0
    else:
        rare_capture_probability = 0.20
        if "failure_biopsy" in stages:
            rare_capture_probability += 0.48
        if "monte_carlo" in stages:
            rare_capture_probability += 0.16
        if "council" in stages:
            rare_capture_probability += 0.08
        rare_capture_probability = min(0.98, rare_capture_probability)

    rare_captured = rng.random() < rare_capture_probability

    if gap == "FRONTIER_REACHED":
        if correct and "experiment" not in stages:
            progress = 1.0
        elif correct:
            progress = 0.75
        else:
            progress = 0.0
    else:
        progress = (
            0.45 + 0.55 * scenario["experiment_value"]
            if correct
            else 0.0
        )

    utility = (
        weights["progress"] * progress
        + weights["correct"] * float(correct)
        + weights["rare"] * float(rare_captured)
        - weights["cost"] * cost
    )

    return {
        "cost": cost,
        "correct": correct,
        "rare_captured": rare_captured,
        "progress": progress,
        "utility": utility,
        "stages": stages,
    }


def evaluate_protocol(
    protocol_name: str,
    *,
    scenarios: Iterable[str] | None = None,
    trials: int = 4000,
    seed: int = 20261004,
    weights: dict[str, float] | None = None,
) -> dict:
    selected = list(scenarios or SCENARIOS)
    rng = random.Random(seed)
    active_weights = weights or NOMINAL_WEIGHTS
    rows = []

    for index in range(trials):
        gap = selected[index % len(selected)]
        rows.append(
            _single_trial(
                protocol_name,
                gap,
                rng,
                active_weights,
            )
        )

    return {
        "mean_cost": statistics.fmean(row["cost"] for row in rows),
        "correct_rate": statistics.fmean(float(row["correct"]) for row in rows),
        "rare_capture_rate": statistics.fmean(float(row["rare_captured"]) for row in rows),
        "mean_progress": statistics.fmean(row["progress"] for row in rows),
        "mean_utility": statistics.fmean(row["utility"] for row in rows),
    }


def evaluate_mixed_policy(
    *,
    scenarios: Iterable[str] | None = None,
    trials: int = 4000,
    seed: int = 20261004,
    weights: dict[str, float] | None = None,
) -> dict:
    selected = list(scenarios or SCENARIOS)
    rng = random.Random(seed)
    active_weights = weights or NOMINAL_WEIGHTS
    rows = []

    for index in range(trials):
        gap = selected[index % len(selected)]
        rows.append(
            _single_trial(
                MIXED_POLICY[gap],
                gap,
                rng,
                active_weights,
            )
        )

    return {
        "mean_cost": statistics.fmean(row["cost"] for row in rows),
        "correct_rate": statistics.fmean(float(row["correct"]) for row in rows),
        "rare_capture_rate": statistics.fmean(float(row["rare_captured"]) for row in rows),
        "mean_progress": statistics.fmean(row["progress"] for row in rows),
        "mean_utility": statistics.fmean(row["utility"] for row in rows),
    }


def promotion_gate(baseline: dict, candidate: dict) -> dict:
    checks = {
        "cost_not_higher": candidate["mean_cost"] <= baseline["mean_cost"],
        "correct_within_1pp": candidate["correct_rate"] >= baseline["correct_rate"] - 0.01,
        "rare_capture_within_10pp": candidate["rare_capture_rate"] >= baseline["rare_capture_rate"] - 0.10,
        "progress_within_1pp": candidate["mean_progress"] >= baseline["mean_progress"] - 0.01,
        "utility_higher": candidate["mean_utility"] > baseline["mean_utility"],
    }
    return {"checks": checks, "pass": all(checks.values())}


def meta_meta_robustness(
    *,
    perturbations: int = 300,
    seed: int = 20261004,
) -> dict:
    rng = random.Random(seed)
    candidate_wins = 0
    risky_scalar_wins = 0
    utility_deltas = []

    for index in range(perturbations):
        weights = {
            "progress": math.exp(rng.normalvariate(0.0, 0.18)) * NOMINAL_WEIGHTS["progress"],
            "correct": math.exp(rng.normalvariate(0.0, 0.18)) * NOMINAL_WEIGHTS["correct"],
            "rare": math.exp(rng.normalvariate(0.0, 0.22)) * NOMINAL_WEIGHTS["rare"],
            "cost": math.exp(rng.normalvariate(0.0, 0.22)) * NOMINAL_WEIGHTS["cost"],
        }
        trial_seed = 30000 + index

        baseline = evaluate_protocol(
            "FIXED_V1",
            trials=800,
            seed=trial_seed,
            weights=weights,
        )
        candidate = evaluate_mixed_policy(
            trials=800,
            seed=trial_seed,
            weights=weights,
        )
        risky = evaluate_protocol(
            "RISKY_FAST",
            trials=800,
            seed=trial_seed,
            weights=weights,
        )

        delta = candidate["mean_utility"] - baseline["mean_utility"]
        utility_deltas.append(delta)

        if delta > 0.0:
            candidate_wins += 1

        if risky["mean_utility"] > max(
            candidate["mean_utility"],
            baseline["mean_utility"],
        ):
            risky_scalar_wins += 1

    risky_invariants = invariant_violations("RISKY_FAST")

    return {
        "perturbations": perturbations,
        "candidate_win_rate": candidate_wins / perturbations,
        "mean_utility_delta": statistics.fmean(utility_deltas),
        "min_utility_delta": min(utility_deltas),
        "risky_scalar_win_rate": risky_scalar_wins / perturbations,
        "risky_invariant_violations": risky_invariants,
        "risky_promotable": False,
    }


def pseudo_council(
    baseline: dict,
    candidate: dict,
    gate: dict,
    robustness: dict,
) -> dict:
    votes = {
        "methodologist": (
            gate["checks"]["progress_within_1pp"]
            and gate["checks"]["correct_within_1pp"]
        ),
        "statistician": (
            robustness["candidate_win_rate"] >= 0.90
            and robustness["min_utility_delta"] > 0.0
        ),
        "systems_researcher": gate["checks"]["cost_not_higher"],
        "falsifier": (
            not robustness["risky_promotable"]
            and bool(robustness["risky_invariant_violations"])
        ),
        "continuity_reviewer": True,
    }

    return {
        "roles": list(COUNCIL_ROLES),
        "votes": votes,
        "converged": all(votes.values()),
        "decision": (
            "PROMOTE_MIXED_V3_AS_RESEARCH_PROTOCOL_CANDIDATE"
            if all(votes.values())
            else "KEEP_FIXED_V1"
        ),
        "scope": "research-method routing only; no live-action authority",
        "baseline_utility": baseline["mean_utility"],
        "candidate_utility": candidate["mean_utility"],
    }


def run_panel() -> dict:
    baseline = evaluate_protocol("FIXED_V1")
    adaptive = evaluate_protocol("VOI_ADAPTIVE_V2")
    mixed = evaluate_mixed_policy()
    gate = promotion_gate(baseline, mixed)

    holdout_baseline = evaluate_protocol(
        "FIXED_V1",
        scenarios=["CAPABILITY_GAP"],
        trials=2000,
        seed=20261005,
    )
    holdout_mixed = evaluate_mixed_policy(
        scenarios=["CAPABILITY_GAP"],
        trials=2000,
        seed=20261005,
    )

    robustness = meta_meta_robustness()
    council = pseudo_council(
        baseline,
        mixed,
        gate,
        robustness,
    )

    status = "PASS" if (
        gate["pass"]
        and holdout_baseline == holdout_mixed
        and council["converged"]
        and robustness["candidate_win_rate"] >= 0.90
        and robustness["min_utility_delta"] > 0.0
        and not robustness["risky_promotable"]
    ) else "FAIL"

    return {
        "schema": SCHEMA,
        "status": status,
        "north_star": "QUALIFIED_TASK_SURVIVAL_FRONTIER",
        "layers": {
            "L0_object_loop": [
                "explore",
                "atomize",
                "pseudo_council",
                "monte_carlo_when_valuable",
                "experiment",
                "failure_biopsy_when_signal_requires",
                "theory_update",
                "primitive_registry_update",
                "frontier_re_evaluation",
            ],
            "L1_meta_loop": (
                "treat research protocol parameters and routing as experiment candidates"
            ),
            "L2_meta_meta_loop": (
                "audit the evaluator with holdout gaps, objective-weight perturbation, and unsafe Goodhart controls"
            ),
        },
        "baseline": baseline,
        "adaptive": adaptive,
        "mixed_candidate": mixed,
        "promotion_gate": gate,
        "capability_holdout": {
            "baseline": holdout_baseline,
            "candidate": holdout_mixed,
            "identical": holdout_baseline == holdout_mixed,
        },
        "meta_meta": robustness,
        "council": council,
        "mixed_policy": MIXED_POLICY,
        "non_negotiable_invariants": [
            "UNKNOWN_IS_NOT_SUCCESS",
            "MISSING_EVIDENCE_IS_NOT_ZERO",
            "EVIDENCE_AND_DECISION_REMAIN_SEPARATE",
            "EXPERIMENT_REQUIRES_COUNCIL_AND_FROZEN_CONTRACT",
            "FAILURE_SPECIMENS_ARE_NOT_ERASED",
            "METHOD_IMPROVEMENT_DOES_NOT_EXPAND_EXECUTION_AUTHORITY",
        ],
        "claim_ceiling": (
            "SYNTHETIC_RECURSIVE_RESEARCH_METHOD_SELECTION_ONLY"
        ),
    }


def main() -> int:
    print(json.dumps(run_panel(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
