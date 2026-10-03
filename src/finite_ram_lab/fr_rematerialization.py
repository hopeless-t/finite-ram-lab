from __future__ import annotations

import itertools
import json


SCHEMA = "finite-ram-lab.fr-remat-001-retain-recompute-offload/v0.1"

FAST_BUDGET_MIB = 256
SLOW_BUDGET_MIB = 256
STAGING_MIB = 8

OBJECTS = (
    {
        "name": "POINTWISE_A",
        "size_mib": 96,
        "recompute_ms_per_use": 1.5,
        "offload_ms_per_use": 8.0,
        "future_uses": 2,
        "rebuildable": True,
    },
    {
        "name": "MATMUL_B",
        "size_mib": 128,
        "recompute_ms_per_use": 14.0,
        "offload_ms_per_use": 10.0,
        "future_uses": 2,
        "rebuildable": True,
    },
    {
        "name": "ATTN_C",
        "size_mib": 160,
        "recompute_ms_per_use": 32.0,
        "offload_ms_per_use": 13.0,
        "future_uses": 2,
        "rebuildable": True,
    },
    {
        "name": "NORM_D",
        "size_mib": 48,
        "recompute_ms_per_use": 1.0,
        "offload_ms_per_use": 5.0,
        "future_uses": 3,
        "rebuildable": True,
    },
    {
        "name": "EMBED_E",
        "size_mib": 80,
        "recompute_ms_per_use": 5.0,
        "offload_ms_per_use": 7.0,
        "future_uses": 1,
        "rebuildable": True,
    },
    {
        "name": "ROUTER_F",
        "size_mib": 64,
        "recompute_ms_per_use": 3.0,
        "offload_ms_per_use": 6.0,
        "future_uses": 4,
        "rebuildable": True,
    },
    {
        "name": "EXTERNAL_RESULT_G",
        "size_mib": 72,
        "recompute_ms_per_use": None,
        "offload_ms_per_use": 9.0,
        "future_uses": 1,
        "rebuildable": False,
    },
)

ACTIONS = (
    "KEEP",
    "RECOMPUTE",
    "OFFLOAD",
)


def evaluate(
    choices: tuple[str, ...],
) -> dict | None:
    fast_mib = 0
    slow_mib = 0
    mean_overhead_ms = 0.0
    tail_proxy_ms = 0.0
    transfer_mib = 0

    details = []

    for obj, action in zip(
        OBJECTS,
        choices,
        strict=True,
    ):
        size = int(
            obj["size_mib"]
        )

        uses = int(
            obj["future_uses"]
        )

        row = {
            "name": obj["name"],
            "action": action,
        }

        if action == "KEEP":
            fast_mib += size

        elif action == "RECOMPUTE":
            if not obj[
                "rebuildable"
            ]:
                return None

            cost = (
                float(
                    obj[
                        "recompute_ms_per_use"
                    ]
                )
                * uses
            )

            mean_overhead_ms += cost
            tail_proxy_ms += (
                1.25 * cost
            )

        elif action == "OFFLOAD":
            fast_mib += STAGING_MIB
            slow_mib += size

            cost = (
                float(
                    obj[
                        "offload_ms_per_use"
                    ]
                )
                * uses
            )

            mean_overhead_ms += cost
            tail_proxy_ms += (
                1.80 * cost
            )

            transfer_mib += (
                2
                * size
                * uses
            )

        else:
            raise ValueError(
                f"unknown_action:{action}"
            )

        details.append(row)

    if (
        fast_mib
        > FAST_BUDGET_MIB
        or slow_mib
        > SLOW_BUDGET_MIB
    ):
        return None

    objective = (
        mean_overhead_ms
        + 0.15
        * tail_proxy_ms
        + 0.002
        * transfer_mib
    )

    return {
        "fast_mib": fast_mib,
        "slow_mib": slow_mib,
        "mean_overhead_ms": (
            mean_overhead_ms
        ),
        "tail_proxy_ms": (
            tail_proxy_ms
        ),
        "transfer_mib": (
            transfer_mib
        ),
        "objective": objective,
        "details": details,
    }


def solve_optimal() -> dict:
    best = None

    for choices in itertools.product(
        ACTIONS,
        repeat=len(OBJECTS),
    ):
        result = evaluate(
            choices
        )

        if result is None:
            continue

        candidate = (
            result[
                "objective"
            ],
            choices,
            result,
        )

        if (
            best is None
            or candidate[0]
            < best[0]
        ):
            best = candidate

    if best is None:
        raise RuntimeError(
            "no_feasible_policy"
        )

    objective, choices, result = (
        best
    )

    return {
        "choices": list(
            choices
        ),
        **result,
    }


def run_panel() -> dict:
    keep_all_fast_mib = sum(
        int(
            row[
                "size_mib"
            ]
        )
        for row in OBJECTS
    )

    largest_first = (
        "RECOMPUTE",
        "RECOMPUTE",
        "RECOMPUTE",
        "RECOMPUTE",
        "KEEP",
        "KEEP",
        "KEEP",
    )

    cheap_recompute_first = (
        "RECOMPUTE",
        "RECOMPUTE",
        "KEEP",
        "RECOMPUTE",
        "RECOMPUTE",
        "RECOMPUTE",
        "KEEP",
    )

    largest = evaluate(
        largest_first
    )

    cheap = evaluate(
        cheap_recompute_first
    )

    optimal = solve_optimal()

    if (
        largest is None
        or cheap is None
    ):
        raise RuntimeError(
            "frozen_baseline_infeasible"
        )

    frozen = {
        "keep_all_fast_mib": 648,
        "largest_objective": (
            116.375
        ),
        "cheap_objective": (
            60.5625
        ),
        "optimal_objective": (
            51.204499999999996
        ),
        "optimal_fast_mib": 240,
        "optimal_slow_mib": 200,
        "optimal_mean_overhead_ms": 40.0,
        "optimal_tail_proxy_ms": (
            65.95
        ),
        "optimal_transfer_mib": 656,
        "optimal_choices": [
            "RECOMPUTE",
            "OFFLOAD",
            "KEEP",
            "RECOMPUTE",
            "RECOMPUTE",
            "KEEP",
            "OFFLOAD",
        ],
    }

    actual = {
        "keep_all_fast_mib": (
            keep_all_fast_mib
        ),
        "largest_objective": (
            largest[
                "objective"
            ]
        ),
        "cheap_objective": (
            cheap[
                "objective"
            ]
        ),
        "optimal_objective": (
            optimal[
                "objective"
            ]
        ),
        "optimal_fast_mib": (
            optimal[
                "fast_mib"
            ]
        ),
        "optimal_slow_mib": (
            optimal[
                "slow_mib"
            ]
        ),
        "optimal_mean_overhead_ms": (
            optimal[
                "mean_overhead_ms"
            ]
        ),
        "optimal_tail_proxy_ms": (
            optimal[
                "tail_proxy_ms"
            ]
        ),
        "optimal_transfer_mib": (
            optimal[
                "transfer_mib"
            ]
        ),
        "optimal_choices": (
            optimal[
                "choices"
            ]
        ),
    }

    if actual != frozen:
        raise RuntimeError(
            "frozen_remat_surface_changed:"
            f"{actual}"
        )

    if (
        optimal[
            "objective"
        ]
        >= cheap[
            "objective"
        ]
    ):
        raise RuntimeError(
            "mixed_policy_not_better"
        )

    if (
        optimal[
            "choices"
        ][6]
        == "RECOMPUTE"
    ):
        raise RuntimeError(
            "nonrebuildable_state_recomputed"
        )

    return {
        "schema": SCHEMA,
        "status": "PASS",
        "classification": (
            "SYNTHETIC_RETAIN_RECOMPUTE_OFFLOAD_PLANNER_VALIDATED"
        ),
        "budgets": {
            "fast_mib": (
                FAST_BUDGET_MIB
            ),
            "slow_mib": (
                SLOW_BUDGET_MIB
            ),
            "offload_staging_mib_per_object": (
                STAGING_MIB
            ),
        },
        "objects": list(
            OBJECTS
        ),
        "baselines": {
            "KEEP_ALL": {
                "fast_mib": (
                    keep_all_fast_mib
                ),
                "feasible": (
                    keep_all_fast_mib
                    <= FAST_BUDGET_MIB
                ),
            },
            "DROP_LARGEST_RECOMPUTE": {
                "choices": list(
                    largest_first
                ),
                **largest,
            },
            "CHEAP_RECOMPUTE_FIRST": {
                "choices": list(
                    cheap_recompute_first
                ),
                **cheap,
            },
        },
        "optimal_mixed": optimal,
        "derived": {
            "optimal_objective_reduction_vs_cheap_recompute": (
                1.0
                - optimal[
                    "objective"
                ]
                / cheap[
                    "objective"
                ]
            ),
            "optimal_fast_memory_reduction_vs_keep_all": (
                1.0
                - optimal[
                    "fast_mib"
                ]
                / keep_all_fast_mib
            ),
        },
        "objective": (
            "mean_overhead_ms + 0.15*tail_proxy_ms + 0.002*transfer_mib"
        ),
        "source_boundaries": {
            "checkpointing": (
                "Activation checkpointing motivates trading saved tensors for recomputation."
            ),
            "checkmate": (
                "Checkmate motivates treating rematerialization scheduling as an optimization problem."
            ),
            "offload": (
                "Recent PyTorch/TorchTitan work motivates offload as a third resource-spending choice beside retain and recompute."
            ),
            "fixture": (
                "All object sizes, latency proxies, tail multipliers, and objective weights are synthetic controls."
            ),
        },
        "primary_findings": [
            "STORAGE_VS_RECOMPUTE_IS_NOT_A_BINARY_DECISION",
            "RECOMPUTE_VALUE_DENSITY_BEATS_DROP_LARGEST_IN_THE_FROZEN_FIXTURE",
            "OFFLOAD_CREATES_A_THIRD_RESOURCE_AXIS_BANDWIDTH",
            "NONREBUILDABLE_STATE_MUST_FAIL_CLOSED_FOR_RECOMPUTE",
            "THE_OPTIMAL_POLICY_CAN_MIX_KEEP_RECOMPUTE_AND_OFFLOAD",
            "REMATERIALIZATION_MUST_BE_OPTIMIZED_JOINTLY_WITH_PLACEMENT_AND_TAIL_RISK",
        ],
        "claim_ceiling": (
            "SOURCE_GROUNDED_SYNTHETIC_REMATERIALIZATION_PLANNER_ONLY"
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
    raise SystemExit(
        main()
    )
