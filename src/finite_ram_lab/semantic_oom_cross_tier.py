from __future__ import annotations

import hashlib
import json
import math
from statistics import mean


SCHEMA = "finite-ram-lab.semantic-oom-cross-tier/v0.1"
SEED = "FR-SOOM-002K-v0.1"
EPISODES = 16384
RELIABILITY_TARGET = 0.999

VRAM_TOTAL_MIB = 16384
MODEL_FIXED_VRAM_MIB = 6000

HOST_RAM_TOTAL_MIB = 32768
MODEL_RAM_MIB = 19000
FOREGROUND_RAM_MIB = 4500

ACTIVE_TASK_LOSS = 280

POLICIES = {
    "TIER_LOCAL_GREEDY": {
        "model_cache_mib": 10000,
        "reaction": False,
        "base_semantic_cost": 0,
    },
    "CROSS_TIER_HEADROOM": {
        "model_cache_mib": 5200,
        "reaction": False,
        "base_semantic_cost": 12,
    },
    "REACTIVE_SHRINK": {
        "model_cache_mib": 10000,
        "reaction": True,
        "base_semantic_cost": 4,
        "shrink_mib": 4000,
        "reaction_survival_overage_mib": 1000,
    },
}


def _uniform(
    episode: int,
    field: str,
) -> float:
    payload = (
        f"{SEED}|{episode}|{field}"
    ).encode("utf-8")
    value = int.from_bytes(
        hashlib.sha256(payload).digest()[:8],
        "big",
    )
    return value / 2**64


def _desktop_vram_demand_mib(
    episode: int,
) -> float:
    if _uniform(episode, "spike") < 0.08:
        return (
            2800.0
            + 1700.0
            * _uniform(
                episode,
                "dv",
            )
        )

    return (
        600.0
        + 1600.0
        * _uniform(
            episode,
            "desktop_vram",
        )
    )


def _background_ram_mib(
    episode: int,
) -> float:
    value = (
        2500.0
        + 3000.0
        * _uniform(
            episode,
            "bg",
        )
    )

    if (
        _uniform(
            episode,
            "ramspike",
        )
        < 0.05
    ):
        value += (
            1500.0
            + 2000.0
            * _uniform(
                episode,
                "bgs",
            )
        )

    return value


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
    values: list[float | int],
    probability: float,
) -> float | int:
    ordered = sorted(values)
    index = max(
        0,
        math.ceil(
            probability * len(ordered)
        )
        - 1,
    )
    return ordered[index]


def _episode(
    episode: int,
    *,
    policy_name: str,
) -> dict:
    policy = POLICIES[policy_name]

    desktop_vram_mib = (
        _desktop_vram_demand_mib(
            episode
        )
    )

    background_ram_mib = (
        _background_ram_mib(
            episode
        )
    )

    initial_cache_mib = int(
        policy["model_cache_mib"]
    )

    initial_free_vram_mib = (
        VRAM_TOTAL_MIB
        - MODEL_FIXED_VRAM_MIB
        - initial_cache_mib
    )

    initial_gtt_spill_mib = max(
        0.0,
        desktop_vram_mib
        - initial_free_vram_mib,
    )

    initial_host_ram_mib = (
        MODEL_RAM_MIB
        + FOREGROUND_RAM_MIB
        + background_ram_mib
        + initial_gtt_spill_mib
    )

    initial_overage_mib = max(
        0.0,
        initial_host_ram_mib
        - HOST_RAM_TOTAL_MIB,
    )

    final_cache_mib = initial_cache_mib
    final_gtt_spill_mib = (
        initial_gtt_spill_mib
    )

    if (
        bool(policy["reaction"])
        and initial_gtt_spill_mib > 0
    ):
        final_cache_mib = max(
            0,
            initial_cache_mib
            - int(policy["shrink_mib"]),
        )

        final_free_vram_mib = (
            VRAM_TOTAL_MIB
            - MODEL_FIXED_VRAM_MIB
            - final_cache_mib
        )

        final_gtt_spill_mib = max(
            0.0,
            desktop_vram_mib
            - final_free_vram_mib,
        )

        final_host_ram_mib = (
            MODEL_RAM_MIB
            + FOREGROUND_RAM_MIB
            + background_ram_mib
            + final_gtt_spill_mib
        )

        current_task_lost = (
            initial_overage_mib
            > float(
                policy[
                    "reaction_survival_overage_mib"
                ]
            )
            or final_host_ram_mib
            > HOST_RAM_TOTAL_MIB
        )
    else:
        final_host_ram_mib = (
            initial_host_ram_mib
        )

        current_task_lost = (
            final_host_ram_mib
            > HOST_RAM_TOTAL_MIB
        )

    semantic_loss = (
        int(policy["base_semantic_cost"])
        + (
            ACTIVE_TASK_LOSS
            if current_task_lost
            else 0
        )
    )

    return {
        "episode": episode,
        "policy": policy_name,
        "desktop_vram_demand_mib": (
            desktop_vram_mib
        ),
        "background_ram_mib": (
            background_ram_mib
        ),
        "initial_model_cache_mib": (
            initial_cache_mib
        ),
        "final_model_cache_mib": (
            final_cache_mib
        ),
        "initial_free_vram_mib": (
            initial_free_vram_mib
        ),
        "initial_gtt_spill_mib": (
            initial_gtt_spill_mib
        ),
        "final_gtt_spill_mib": (
            final_gtt_spill_mib
        ),
        "initial_host_ram_mib": (
            initial_host_ram_mib
        ),
        "final_host_ram_mib": (
            final_host_ram_mib
        ),
        "initial_overage_mib": (
            initial_overage_mib
        ),
        "current_task_lost": (
            current_task_lost
        ),
        "semantic_loss": semantic_loss,
    }


def evaluate_policy(
    policy_name: str,
) -> dict:
    rows = [
        _episode(
            episode,
            policy_name=policy_name,
        )
        for episode in range(EPISODES)
    ]

    current_task_losses = sum(
        int(row["current_task_lost"])
        for row in rows
    )

    successes = (
        EPISODES - current_task_losses
    )

    lower, upper = _wilson95(
        successes,
        EPISODES,
    )

    semantic_losses = [
        int(row["semantic_loss"])
        for row in rows
    ]

    initial_spills = [
        float(
            row[
                "initial_gtt_spill_mib"
            ]
        )
        for row in rows
    ]

    final_spills = [
        float(
            row[
                "final_gtt_spill_mib"
            ]
        )
        for row in rows
    ]

    return {
        "policy": policy_name,
        "episodes": EPISODES,
        "initial_model_cache_mib": int(
            POLICIES[policy_name][
                "model_cache_mib"
            ]
        ),
        "mean_final_model_cache_mib": mean(
            [
                row["final_model_cache_mib"]
                for row in rows
            ]
        ),
        "current_task_loss_count": (
            current_task_losses
        ),
        "current_task_survival_rate": (
            successes / EPISODES
        ),
        "current_task_survival_wilson95": [
            lower,
            upper,
        ],
        "reliability_target": (
            RELIABILITY_TARGET
        ),
        "reliability_qualified": (
            successes / EPISODES
            >= RELIABILITY_TARGET
            and lower
            >= RELIABILITY_TARGET
        ),
        "mean_initial_gtt_spill_mib": (
            mean(initial_spills)
        ),
        "p95_initial_gtt_spill_mib": (
            _quantile(
                initial_spills,
                0.95,
            )
        ),
        "p99_initial_gtt_spill_mib": (
            _quantile(
                initial_spills,
                0.99,
            )
        ),
        "mean_final_gtt_spill_mib": (
            mean(final_spills)
        ),
        "p99_final_gtt_spill_mib": (
            _quantile(
                final_spills,
                0.99,
            )
        ),
        "mean_semantic_loss": mean(
            semantic_losses
        ),
        "p99_semantic_loss": _quantile(
            semantic_losses,
            0.99,
        ),
        "p999_semantic_loss": _quantile(
            semantic_losses,
            0.999,
        ),
        "max_semantic_loss": max(
            semantic_losses
        ),
        "first_current_task_loss": next(
            (
                row
                for row in rows
                if row[
                    "current_task_lost"
                ]
            ),
            None,
        ),
    }


def run_panel() -> dict:
    results = {
        name: evaluate_policy(name)
        for name in POLICIES
    }

    greedy = results[
        "TIER_LOCAL_GREEDY"
    ]
    headroom = results[
        "CROSS_TIER_HEADROOM"
    ]
    reactive = results[
        "REACTIVE_SHRINK"
    ]

    if greedy[
        "current_task_loss_count"
    ] != 106:
        raise RuntimeError(
            "greedy_loss_reference_changed"
        )

    if reactive[
        "current_task_loss_count"
    ] != 17:
        raise RuntimeError(
            "reactive_loss_reference_changed"
        )

    if headroom[
        "current_task_loss_count"
    ] != 0:
        raise RuntimeError(
            "headroom_loss_reference_changed"
        )

    if greedy[
        "reliability_qualified"
    ]:
        raise RuntimeError(
            "greedy_unexpectedly_qualified"
        )

    if reactive[
        "reliability_qualified"
    ]:
        raise RuntimeError(
            "reactive_unexpectedly_qualified"
        )

    if not headroom[
        "reliability_qualified"
    ]:
        raise RuntimeError(
            "headroom_not_qualified"
        )

    if not (
        greedy[
            "mean_semantic_loss"
        ]
        < reactive[
            "mean_semantic_loss"
        ]
        < headroom[
            "mean_semantic_loss"
        ]
    ):
        raise RuntimeError(
            "expected_cost_order_changed"
        )

    if not (
        headroom[
            "p999_semantic_loss"
        ]
        < greedy[
            "p999_semantic_loss"
        ]
    ):
        raise RuntimeError(
            "tail_task_protection_disappeared"
        )

    if not (
        reactive[
            "mean_final_gtt_spill_mib"
        ]
        < greedy[
            "mean_final_gtt_spill_mib"
        ]
    ):
        raise RuntimeError(
            "reactive_shrink_not_reducing_spill"
        )

    return {
        "schema": SCHEMA,
        "status": "PASS",
        "classification": (
            "SYNTHETIC_CROSS_TIER_PRESSURE_COUPLING_VALIDATED"
        ),
        "synthetic_only": True,
        "live_control_claim": False,
        "source_inspiration": {
            "repository": "Niko1221/Strata",
            "commit": (
                "b48aad2a9d96eceb749b4f06ffd6607f9b00be7f"
            ),
            "evidence_role": (
                "architectural motivation only"
            ),
        },
        "fixture": {
            "episodes": EPISODES,
            "vram_total_mib": (
                VRAM_TOTAL_MIB
            ),
            "model_fixed_vram_mib": (
                MODEL_FIXED_VRAM_MIB
            ),
            "host_ram_total_mib": (
                HOST_RAM_TOTAL_MIB
            ),
            "model_ram_mib": MODEL_RAM_MIB,
            "foreground_ram_mib": (
                FOREGROUND_RAM_MIB
            ),
            "reliability_target": (
                RELIABILITY_TARGET
            ),
        },
        "policies": results,
        "primary_finding": (
            "TIER_LOCAL_RELIEF_DOES_NOT_IMPLY_GLOBAL_SEMANTIC_RELIEF"
        ),
        "control_implication": (
            "CROSS_TIER_HEADROOM_IS_A_CONSTRAINT_NOT_A_PER_TIER_HEURISTIC"
        ),
        "claim_ceiling": (
            "SYNTHETIC_CROSS_TIER_PRESSURE_COUPLING_ONLY"
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
