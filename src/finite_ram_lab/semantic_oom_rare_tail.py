from __future__ import annotations

import hashlib
import json
import math
from statistics import mean


SCHEMA = "finite-ram-lab.semantic-oom-rare-tail/v0.1"
SEED = "FR-SOOM-002C-v0.1"
REPLICATES = 8192
DEADLINE_MS = 200
RELIEF_TARGET_MIB = 3000
RELIABILITY_TARGET = 0.99


ACTIONS = {
    "CHROME_TRIM_AND_IDLE_RENDERERS": {
        "draw_domain": "CHROME_RICH",
        "base_latency_ms": (160, 190),
        "tail_probability": 0.04,
        "tail_latency_ms": (420, 520),
        "relief_mib": 1500,
        "under_relief_probability": 0.01,
        "under_relief_mib": 1200,
        "semantic_loss": 8,
        "hard_kill": False,
        "current_task_damage": False,
    },
    "MODEL_SHRINK": {
        "draw_domain": "MODEL_SHRINK",
        "base_latency_ms": (130, 170),
        "tail_probability": 0.02,
        "tail_latency_ms": (260, 340),
        "relief_mib": 600,
        "under_relief_probability": 0.01,
        "under_relief_mib": 450,
        "semantic_loss": 0,
        "hard_kill": False,
        "current_task_damage": False,
    },
    "INDEXER_GRACEFUL_EXIT": {
        "draw_domain": "INDEXER_GRACEFUL",
        "base_latency_ms": (80, 120),
        "tail_probability": 0.001,
        "tail_latency_ms": (240, 300),
        "relief_mib": 900,
        "under_relief_probability": 0.001,
        "under_relief_mib": 800,
        "semantic_loss": 1,
        "hard_kill": False,
        "current_task_damage": False,
    },
    "CHROME_TRIM_CACHE": {
        "draw_domain": "CHROME_CACHE",
        "base_latency_ms": (60, 90),
        "tail_probability": 0.0015,
        "tail_latency_ms": (220, 280),
        "relief_mib": 900,
        "under_relief_probability": 0.001,
        "under_relief_mib": 750,
        "semantic_loss": 0,
        "hard_kill": False,
        "current_task_damage": False,
    },
    "BATCH_KILL": {
        "draw_domain": "BATCH_KILL",
        "base_latency_ms": (15, 25),
        "tail_probability": 0.0,
        "tail_latency_ms": (15, 25),
        "relief_mib": 1400,
        "under_relief_probability": 0.0,
        "under_relief_mib": 1400,
        "semantic_loss": 13,
        "hard_kill": True,
        "current_task_damage": False,
    },
    "CHROME_KILL": {
        "draw_domain": "CHROME_KILL",
        "base_latency_ms": (15, 25),
        "tail_probability": 0.0,
        "tail_latency_ms": (15, 25),
        "relief_mib": 3200,
        "under_relief_probability": 0.0,
        "under_relief_mib": 3200,
        "semantic_loss": 280,
        "hard_kill": True,
        "current_task_damage": True,
    },
}


PLANS = {
    "MEAN_COOPERATIVE": (
        "CHROME_TRIM_AND_IDLE_RENDERERS",
        "MODEL_SHRINK",
        "INDEXER_GRACEFUL_EXIT",
    ),
    "TAIL_AWARE_MIXED": (
        "CHROME_TRIM_CACHE",
        "BATCH_KILL",
        "INDEXER_GRACEFUL_EXIT",
    ),
    "KILL_FIRST": (
        "CHROME_KILL",
    ),
}


def _uniform(*parts: object) -> float:
    payload = "|".join(str(part) for part in parts).encode("utf-8")
    digest = hashlib.sha256(payload).digest()
    value = int.from_bytes(digest[:8], "big")
    return value / 2**64


def _draw_int(
    low: int,
    high: int,
    *,
    uniform: float,
) -> int:
    return low + int(uniform * (high - low + 1))


def _draw_action(
    *,
    plan_name: str,
    replicate: int,
    action_name: str,
) -> dict:
    action = ACTIONS[action_name]

    is_tail = (
        _uniform(
            SEED,
            plan_name,
            replicate,
            action["draw_domain"],
            "tail",
        )
        < action["tail_probability"]
    )

    latency_range = (
        action["tail_latency_ms"]
        if is_tail
        else action["base_latency_ms"]
    )

    latency_ms = _draw_int(
        latency_range[0],
        latency_range[1],
        uniform=_uniform(
            SEED,
            plan_name,
            replicate,
            action["draw_domain"],
            "lat",
        ),
    )

    under_relief = (
        _uniform(
            SEED,
            plan_name,
            replicate,
            action["draw_domain"],
            "under",
        )
        < action["under_relief_probability"]
    )

    relief_mib = (
        action["under_relief_mib"]
        if under_relief
        else action["relief_mib"]
    )

    return {
        "action": action_name,
        "latency_ms": latency_ms,
        "relief_mib": relief_mib,
        "tail_event": is_tail,
        "under_relief_event": under_relief,
    }


def _wilson95(successes: int, total: int) -> tuple[float, float]:
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


def _quantile(values: list[int], probability: float) -> int:
    ordered = sorted(values)
    index = max(
        0,
        math.ceil(probability * len(ordered)) - 1,
    )
    return ordered[index]


def evaluate_plan(plan_name: str) -> dict:
    action_names = PLANS[plan_name]

    latencies: list[int] = []
    reliefs: list[int] = []

    deadline_misses = 0
    relief_misses = 0
    successes = 0
    tail_event_replicates = 0
    under_relief_replicates = 0

    first_deadline_miss: dict | None = None
    first_relief_miss: dict | None = None

    for replicate in range(REPLICATES):
        draws = [
            _draw_action(
                plan_name=plan_name,
                replicate=replicate,
                action_name=action_name,
            )
            for action_name in action_names
        ]

        completion_latency_ms = max(
            draw["latency_ms"]
            for draw in draws
        )
        relief_mib = sum(
            draw["relief_mib"]
            for draw in draws
        )

        deadline_miss = (
            completion_latency_ms > DEADLINE_MS
        )
        relief_miss = relief_mib < RELIEF_TARGET_MIB
        success = not deadline_miss and not relief_miss

        latencies.append(completion_latency_ms)
        reliefs.append(relief_mib)

        deadline_misses += int(deadline_miss)
        relief_misses += int(relief_miss)
        successes += int(success)

        if any(draw["tail_event"] for draw in draws):
            tail_event_replicates += 1

        if any(
            draw["under_relief_event"]
            for draw in draws
        ):
            under_relief_replicates += 1

        if deadline_miss and first_deadline_miss is None:
            first_deadline_miss = {
                "replicate": replicate,
                "completion_latency_ms": (
                    completion_latency_ms
                ),
                "relief_mib": relief_mib,
                "draws": draws,
            }

        if relief_miss and first_relief_miss is None:
            first_relief_miss = {
                "replicate": replicate,
                "completion_latency_ms": (
                    completion_latency_ms
                ),
                "relief_mib": relief_mib,
                "draws": draws,
            }

    lower, upper = _wilson95(
        successes,
        REPLICATES,
    )

    semantic_loss = sum(
        ACTIONS[action]["semantic_loss"]
        for action in action_names
    )
    hard_kill_count = sum(
        int(ACTIONS[action]["hard_kill"])
        for action in action_names
    )
    current_task_damage_count = sum(
        int(ACTIONS[action]["current_task_damage"])
        for action in action_names
    )

    return {
        "plan": plan_name,
        "actions": list(action_names),
        "replicates": REPLICATES,
        "deadline_ms": DEADLINE_MS,
        "relief_target_mib": RELIEF_TARGET_MIB,
        "deadline_successes": successes,
        "deadline_success_rate": (
            successes / REPLICATES
        ),
        "deadline_success_wilson95": [
            lower,
            upper,
        ],
        "reliability_target": RELIABILITY_TARGET,
        "reliability_qualified": (
            successes / REPLICATES >= RELIABILITY_TARGET
            and lower >= RELIABILITY_TARGET
        ),
        "deadline_miss_count": deadline_misses,
        "relief_miss_count": relief_misses,
        "tail_event_replicate_count": (
            tail_event_replicates
        ),
        "under_relief_replicate_count": (
            under_relief_replicates
        ),
        "mean_completion_latency_ms": mean(latencies),
        "p95_completion_latency_ms": _quantile(
            latencies,
            0.95,
        ),
        "p99_completion_latency_ms": _quantile(
            latencies,
            0.99,
        ),
        "max_completion_latency_ms": max(latencies),
        "mean_relief_mib": mean(reliefs),
        "semantic_loss": semantic_loss,
        "hard_kill_count": hard_kill_count,
        "current_task_survives": (
            current_task_damage_count == 0
        ),
        "first_deadline_miss": first_deadline_miss,
        "first_relief_miss": first_relief_miss,
    }


def run_panel() -> dict:
    rows = {
        plan_name: evaluate_plan(plan_name)
        for plan_name in PLANS
    }

    mean_plan = rows["MEAN_COOPERATIVE"]
    tail_plan = rows["TAIL_AWARE_MIXED"]
    kill_plan = rows["KILL_FIRST"]

    if not (
        mean_plan["mean_completion_latency_ms"]
        < DEADLINE_MS
    ):
        raise RuntimeError(
            "mean_cooperative_not_mean_fast"
        )

    if mean_plan["reliability_qualified"]:
        raise RuntimeError(
            "mean_cooperative_unexpectedly_tail_safe"
        )

    if not tail_plan["reliability_qualified"]:
        raise RuntimeError(
            "tail_aware_plan_not_qualified"
        )

    if not (
        tail_plan["semantic_loss"]
        < kill_plan["semantic_loss"]
    ):
        raise RuntimeError(
            "tail_aware_semantic_advantage_lost"
        )

    if not tail_plan["current_task_survives"]:
        raise RuntimeError(
            "tail_aware_current_task_lost"
        )

    if kill_plan["current_task_survives"]:
        raise RuntimeError(
            "kill_first_current_task_unexpectedly_survives"
        )

    if not (
        mean_plan["p95_completion_latency_ms"]
        > DEADLINE_MS
    ):
        raise RuntimeError(
            "rare_tail_not_visible_in_p95"
        )

    if not (
        tail_plan["p99_completion_latency_ms"]
        <= DEADLINE_MS
    ):
        raise RuntimeError(
            "tail_aware_p99_exceeds_deadline"
        )

    return {
        "schema": SCHEMA,
        "status": "PASS",
        "classification": (
            "SYNTHETIC_RARE_TAIL_POLICY_DIVERGENCE_VALIDATED"
        ),
        "synthetic_only": True,
        "live_control_claim": False,
        "seed": SEED,
        "replicates_per_plan": REPLICATES,
        "deadline_ms": DEADLINE_MS,
        "relief_target_mib": RELIEF_TARGET_MIB,
        "reliability_target": RELIABILITY_TARGET,
        "plans": rows,
        "primary_finding": (
            "MEAN_FAST_DOES_NOT_IMPLY_TAIL_SAFE"
        ),
        "claim_ceiling": (
            "SYNTHETIC_RARE_TAIL_POLICY_ONLY"
        ),
    }


def main() -> int:
    print(
        json.dumps(
            run_panel(),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
