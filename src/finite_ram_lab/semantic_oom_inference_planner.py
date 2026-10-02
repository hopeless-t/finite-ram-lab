from __future__ import annotations

import hashlib
import json
import math
from statistics import mean

from finite_ram_lab.semantic_oom_observable_dependence import (
    analyze_trace,
    generate_trace,
)


SCHEMA = "finite-ram-lab.semantic-oom-inference-planner/v0.1"
SEED = "FR-SOOM-002G-v0.1"
FUTURE_EPISODES = 8192
FUTURE_TAIL_COUNT_PER_CLUSTER_ACTION = 82
RELIEF_TARGET_MIB = 3000
RELIABILITY_TARGET = 0.999

CLUSTER_ACTIONS = (
    "CHROME_CACHE",
    "MODEL_SHRINK",
    "INDEXER_EXIT",
)

COOPERATIVE_ACTIONS = (
    "CHROME_CACHE",
    "MODEL_SHRINK",
    "INDEXER_EXIT",
    "DISTINCT_SPARE",
)

COOPERATIVE_RELIEF_MIB = {
    "CHROME_CACHE": 1000,
    "MODEL_SHRINK": 1000,
    "INDEXER_EXIT": 1000,
    "DISTINCT_SPARE": 1000,
}

COOPERATIVE_SEMANTIC_LOSS = 10
BACKGROUND_SACRIFICE_SEMANTIC_LOSS = 73
KILL_FIRST_SEMANTIC_LOSS = 280
EMERGENCY_ACTIVE_TASK_LOSS = 280


def _hash_rank(domain: str, episode: int) -> int:
    payload = f"{SEED}|{domain}|{episode}".encode("utf-8")
    return int.from_bytes(
        hashlib.sha256(payload).digest()[:8],
        "big",
    )


def _select_exact_tail_set(domain: str) -> set[int]:
    ranked = sorted(
        range(FUTURE_EPISODES),
        key=lambda episode: _hash_rank(
            domain,
            episode,
        ),
    )
    return set(
        ranked[
            :FUTURE_TAIL_COUNT_PER_CLUSTER_ACTION
        ]
    )


def _future_tail_sets(
    regime: str,
) -> dict[str, set[int]]:
    if regime == "INDEPENDENT":
        return {
            action: _select_exact_tail_set(
                f"FUTURE:IID:{action}"
            )
            for action in CLUSTER_ACTIONS
        }

    if regime == "SHARED_BAD":
        shared = _select_exact_tail_set(
            "FUTURE:SHARED"
        )
        return {
            action: set(shared)
            for action in CLUSTER_ACTIONS
        }

    raise ValueError("unknown_regime")


def _wilson95(
    successes: int,
    total: int,
) -> tuple[float, float]:
    z = 1.959963984540054
    p = successes / total
    denominator = 1.0 + z * z / total
    center = (
        p + z * z / (2.0 * total)
    ) / denominator
    half = (
        z
        * math.sqrt(
            (
                p * (1.0 - p)
                + z * z / (4.0 * total)
            )
            / total
        )
        / denominator
    )
    return center - half, center + half


def _quantile(
    values: list[int],
    probability: float,
) -> int:
    ordered = sorted(values)
    index = max(
        0,
        math.ceil(probability * len(ordered)) - 1,
    )
    return ordered[index]


def _cooperative_episode(
    episode: int,
    *,
    tail_sets: dict[str, set[int]],
) -> dict:
    late_actions = {
        action
        for action in CLUSTER_ACTIONS
        if episode in tail_sets[action]
    }

    timely_relief_mib = (
        COOPERATIVE_RELIEF_MIB[
            "DISTINCT_SPARE"
        ]
        + sum(
            COOPERATIVE_RELIEF_MIB[action]
            for action in CLUSTER_ACTIONS
            if action not in late_actions
        )
    )

    deadline_success = (
        timely_relief_mib
        >= RELIEF_TARGET_MIB
    )

    if deadline_success:
        semantic_loss = (
            COOPERATIVE_SEMANTIC_LOSS
        )
        current_task_lost = False
    else:
        semantic_loss = (
            COOPERATIVE_SEMANTIC_LOSS
            + EMERGENCY_ACTIVE_TASK_LOSS
        )
        current_task_lost = True

    return {
        "deadline_success": deadline_success,
        "semantic_loss": semantic_loss,
        "current_task_lost": current_task_lost,
        "late_action_count": len(late_actions),
        "timely_relief_mib": timely_relief_mib,
    }


def _evaluate_policy(
    *,
    policy: str,
    regime: str,
    inference_classification: str,
) -> dict:
    tail_sets = _future_tail_sets(regime)

    if policy == "NAIVE_COOPERATIVE":
        selected_plan = "COOPERATIVE_REDUNDANCY"
    elif policy == "DEPENDENCE_AWARE":
        selected_plan = (
            "BACKGROUND_SACRIFICE"
            if inference_classification
            == "CROSS_ACTION_DEPENDENCE_EVIDENCE"
            else "COOPERATIVE_REDUNDANCY"
        )
    elif policy == "KILL_FIRST":
        selected_plan = "ACTIVE_TASK_KILL"
    else:
        raise ValueError("unknown_policy")

    rows: list[dict] = []

    for episode in range(FUTURE_EPISODES):
        if selected_plan == "COOPERATIVE_REDUNDANCY":
            row = _cooperative_episode(
                episode,
                tail_sets=tail_sets,
            )
        elif selected_plan == "BACKGROUND_SACRIFICE":
            row = {
                "deadline_success": True,
                "semantic_loss": (
                    BACKGROUND_SACRIFICE_SEMANTIC_LOSS
                ),
                "current_task_lost": False,
                "late_action_count": 0,
                "timely_relief_mib": 3500,
            }
        else:
            row = {
                "deadline_success": True,
                "semantic_loss": (
                    KILL_FIRST_SEMANTIC_LOSS
                ),
                "current_task_lost": True,
                "late_action_count": 0,
                "timely_relief_mib": 3200,
            }

        rows.append(row)

    successes = sum(
        int(row["deadline_success"])
        for row in rows
    )
    current_task_losses = sum(
        int(row["current_task_lost"])
        for row in rows
    )
    semantic_losses = [
        int(row["semantic_loss"])
        for row in rows
    ]
    lower, upper = _wilson95(
        successes,
        FUTURE_EPISODES,
    )

    reliability_qualified = (
        successes / FUTURE_EPISODES
        >= RELIABILITY_TARGET
        and lower >= RELIABILITY_TARGET
    )

    return {
        "policy": policy,
        "selected_plan": selected_plan,
        "regime": regime,
        "inference_classification": (
            inference_classification
        ),
        "episodes": FUTURE_EPISODES,
        "deadline_successes": successes,
        "deadline_failures": (
            FUTURE_EPISODES - successes
        ),
        "deadline_success_rate": (
            successes / FUTURE_EPISODES
        ),
        "deadline_success_wilson95": [
            lower,
            upper,
        ],
        "reliability_target": (
            RELIABILITY_TARGET
        ),
        "reliability_qualified": (
            reliability_qualified
        ),
        "current_task_loss_count": (
            current_task_losses
        ),
        "current_task_survival_rate": (
            1.0
            - current_task_losses
            / FUTURE_EPISODES
        ),
        "mean_semantic_loss": mean(
            semantic_losses
        ),
        "p95_semantic_loss": _quantile(
            semantic_losses,
            0.95,
        ),
        "p99_semantic_loss": _quantile(
            semantic_losses,
            0.99,
        ),
        "max_semantic_loss": max(
            semantic_losses
        ),
    }


def _history_inference(regime: str) -> dict:
    trace = generate_trace(regime)
    return analyze_trace(trace)


def run_panel() -> dict:
    arms: dict[str, dict] = {}

    for regime in (
        "INDEPENDENT",
        "SHARED_BAD",
    ):
        inference = _history_inference(
            regime
        )

        policies = {
            policy: _evaluate_policy(
                policy=policy,
                regime=regime,
                inference_classification=(
                    inference[
                        "classification"
                    ]
                ),
            )
            for policy in (
                "NAIVE_COOPERATIVE",
                "DEPENDENCE_AWARE",
                "KILL_FIRST",
            )
        }

        arms[regime] = {
            "history_inference": inference,
            "future_policies": policies,
        }

    independent = arms["INDEPENDENT"]
    shared = arms["SHARED_BAD"]

    iid_naive = independent[
        "future_policies"
    ]["NAIVE_COOPERATIVE"]
    iid_aware = independent[
        "future_policies"
    ]["DEPENDENCE_AWARE"]
    shared_naive = shared[
        "future_policies"
    ]["NAIVE_COOPERATIVE"]
    shared_aware = shared[
        "future_policies"
    ]["DEPENDENCE_AWARE"]
    shared_kill = shared[
        "future_policies"
    ]["KILL_FIRST"]

    if independent[
        "history_inference"
    ]["classification"] != "IID_COMPATIBLE":
        raise RuntimeError(
            "iid_history_classification_changed"
        )

    if shared[
        "history_inference"
    ]["classification"] != (
        "CROSS_ACTION_DEPENDENCE_EVIDENCE"
    ):
        raise RuntimeError(
            "shared_history_classification_changed"
        )

    if iid_naive[
        "deadline_failures"
    ] != 1:
        raise RuntimeError(
            "iid_future_failure_reference_changed"
        )

    if iid_aware[
        "selected_plan"
    ] != "COOPERATIVE_REDUNDANCY":
        raise RuntimeError(
            "iid_aware_unnecessary_escalation"
        )

    if not iid_aware[
        "reliability_qualified"
    ]:
        raise RuntimeError(
            "iid_aware_reliability_changed"
        )

    if shared_naive[
        "deadline_failures"
    ] != 82:
        raise RuntimeError(
            "shared_naive_failure_reference_changed"
        )

    if shared_naive[
        "reliability_qualified"
    ]:
        raise RuntimeError(
            "shared_naive_unexpectedly_qualified"
        )

    if shared_aware[
        "selected_plan"
    ] != "BACKGROUND_SACRIFICE":
        raise RuntimeError(
            "shared_aware_plan_changed"
        )

    if not shared_aware[
        "reliability_qualified"
    ]:
        raise RuntimeError(
            "shared_aware_not_qualified"
        )

    if shared_aware[
        "current_task_loss_count"
    ] != 0:
        raise RuntimeError(
            "shared_aware_current_task_loss"
        )

    if shared_aware[
        "p99_semantic_loss"
    ] >= shared_naive[
        "p99_semantic_loss"
    ]:
        raise RuntimeError(
            "shared_aware_tail_loss_not_better"
        )

    if shared_aware[
        "mean_semantic_loss"
    ] <= shared_naive[
        "mean_semantic_loss"
    ]:
        raise RuntimeError(
            "expected_cost_tradeoff_disappeared"
        )

    if shared_aware[
        "mean_semantic_loss"
    ] >= shared_kill[
        "mean_semantic_loss"
    ]:
        raise RuntimeError(
            "background_sacrifice_not_better_than_kill_first"
        )

    return {
        "schema": SCHEMA,
        "status": "PASS",
        "classification": (
            "SYNTHETIC_INFERENCE_INFORMED_PLANNING_VALIDATED"
        ),
        "synthetic_only": True,
        "live_control_claim": False,
        "history_analyzer_uses_latent_labels": False,
        "future_episodes_per_regime": (
            FUTURE_EPISODES
        ),
        "future_tail_count_per_cluster_action": (
            FUTURE_TAIL_COUNT_PER_CLUSTER_ACTION
        ),
        "relief_target_mib": RELIEF_TARGET_MIB,
        "reliability_target": (
            RELIABILITY_TARGET
        ),
        "arms": arms,
        "primary_finding": (
            "DEPENDENCE_INFERENCE_CAN_TRADE_MEAN_COST_FOR_TAIL_TASK_SURVIVAL"
        ),
        "claim_ceiling": (
            "SYNTHETIC_INFERENCE_INFORMED_PLANNING_ONLY"
        ),
    }


def main() -> int:
    print(json.dumps(run_panel(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
