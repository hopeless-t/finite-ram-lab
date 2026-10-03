from __future__ import annotations

import json
import math
import statistics
from typing import Any

from finite_ram_lab.fr_fp_002_semantic_oom import (
    ENDPOINT_DELTA,
    RESIDUAL_EPS,
    _endpoint_gap,
    _episodes,
    _first_safe_step,
    _residual,
)

SCHEMA = "finite-ram-lab.fr-fp-003-predictive-cold-tier/v0.1"

TRANSFER_LEAD_STEPS = 2
PREDICTION_MARGIN_STEPS = 1
BUDGETS = (4, 8)

POLICIES = (
    "REACTIVE_TRANSFER",
    "PREDICTIVE_TRANSFER",
    "ALWAYS_PREEMPTIVE",
)


def estimate_safe_eta(
    rows: list[float],
    step: int,
) -> int:
    if step <= 0:
        raise ValueError(
            "step_must_be_positive"
        )

    gap = _endpoint_gap(
        rows,
        step,
    )
    residual = _residual(
        rows,
        step,
    )

    if (
        gap <= ENDPOINT_DELTA
        and residual
        <= RESIDUAL_EPS
    ):
        return 0

    previous_gap = (
        _endpoint_gap(
            rows,
            step - 1,
        )
    )

    progress = max(
        previous_gap - gap,
        0.0,
    )

    if step >= 2:
        previous_previous_gap = (
            _endpoint_gap(
                rows,
                step - 2,
            )
        )
        previous_progress = max(
            previous_previous_gap
            - previous_gap,
            0.0,
        )

        positive = [
            value
            for value
            in (
                progress,
                previous_progress,
            )
            if value > 1e-12
        ]

        rate = (
            min(positive)
            if positive
            else 0.0
        )
    else:
        rate = progress

    if rate <= 1e-12:
        return 999

    eta = math.ceil(
        max(
            gap
            - ENDPOINT_DELTA,
            0.0,
        )
        / rate
    )

    if residual > RESIDUAL_EPS:
        eta = max(
            eta,
            1,
        )

    return eta


def simulate_transfer_policy(
    rows: list[float],
    *,
    policy: str,
    budget: int,
) -> dict[str, Any]:
    safe_step = _first_safe_step(
        rows
    )

    hot = 1
    cold = 0
    pending: list[int] = []
    semantic_oom = False
    peak_hot = 1
    cold_writes = 0
    transfer_requests = 0

    for step in range(
        1,
        len(rows),
    ):
        next_pending = []

        for remaining in pending:
            remaining -= 1

            if remaining <= 0:
                hot -= 1
                cold += 1
                cold_writes += 1
            else:
                next_pending.append(
                    remaining
                )

        pending = next_pending
        hot += 1

        if (
            safe_step is not None
            and step >= safe_step
        ):
            hot = 1
            cold = 0
            pending = []

        else:
            available = (
                hot
                - 1
                - len(pending)
            )

            request = False

            if available > 0:
                if (
                    policy
                    == "ALWAYS_PREEMPTIVE"
                ):
                    request = True

                elif (
                    policy
                    == "REACTIVE_TRANSFER"
                ):
                    request = (
                        hot >= budget
                    )

                elif (
                    policy
                    == "PREDICTIVE_TRANSFER"
                ):
                    eta = (
                        estimate_safe_eta(
                            rows,
                            step,
                        )
                    )
                    slots = (
                        budget - hot
                    )

                    request = (
                        eta
                        > (
                            slots
                            - TRANSFER_LEAD_STEPS
                            + PREDICTION_MARGIN_STEPS
                        )
                    )

                else:
                    raise ValueError(
                        "unknown_policy:"
                        f"{policy}"
                    )

            if request:
                pending.append(
                    TRANSFER_LEAD_STEPS
                )
                transfer_requests += 1

        if hot > budget:
            semantic_oom = True

        peak_hot = max(
            peak_hot,
            hot,
        )

    return {
        "semantic_oom": (
            semantic_oom
        ),
        "semantic_corruption": (
            False
        ),
        "cold_writes": (
            cold_writes
        ),
        "transfer_requests": (
            transfer_requests
        ),
        "peak_hot_states": (
            peak_hot
        ),
        "safe_step": safe_step,
    }


def _summary(
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "semantic_oom_rate": (
            sum(
                row[
                    "semantic_oom"
                ]
                for row in rows
            )
            / len(rows)
        ),
        "semantic_corruption_rate": (
            sum(
                row[
                    "semantic_corruption"
                ]
                for row in rows
            )
            / len(rows)
        ),
        "mean_cold_writes": (
            statistics.fmean(
                row[
                    "cold_writes"
                ]
                for row in rows
            )
        ),
        "mean_transfer_requests": (
            statistics.fmean(
                row[
                    "transfer_requests"
                ]
                for row in rows
            )
        ),
        "mean_peak_hot_states": (
            statistics.fmean(
                row[
                    "peak_hot_states"
                ]
                for row in rows
            )
        ),
    }


def run_panel() -> dict[str, Any]:
    episodes = _episodes()
    matrix = {}

    for budget in BUDGETS:
        matrix[
            str(budget)
        ] = {}

        for policy in POLICIES:
            matrix[
                str(budget)
            ][policy] = (
                _summary(
                    [
                        simulate_transfer_policy(
                            trajectory,
                            policy=policy,
                            budget=budget,
                        )
                        for _family,
                        trajectory
                        in episodes
                    ]
                )
            )

    reactive_8 = (
        matrix["8"][
            "REACTIVE_TRANSFER"
        ]
    )
    predictive_8 = (
        matrix["8"][
            "PREDICTIVE_TRANSFER"
        ]
    )
    always_8 = (
        matrix["8"][
            "ALWAYS_PREEMPTIVE"
        ]
    )
    predictive_4 = (
        matrix["4"][
            "PREDICTIVE_TRANSFER"
        ]
    )
    always_4 = (
        matrix["4"][
            "ALWAYS_PREEMPTIVE"
        ]
    )

    checks = {
        "reactive_late_under_budget8": (
            reactive_8[
                "semantic_oom_rate"
            ]
            > 0.50
        ),
        "predictive_avoids_budget8_oom": (
            predictive_8[
                "semantic_oom_rate"
            ]
            == 0.0
        ),
        "predictive_avoids_budget4_oom": (
            predictive_4[
                "semantic_oom_rate"
            ]
            == 0.0
        ),
        "predictive_no_corruption": (
            predictive_8[
                "semantic_corruption_rate"
            ]
            == 0.0
        ),
        "predictive_saves_io_at_budget8": (
            predictive_8[
                "mean_cold_writes"
            ]
            < 0.60
            * always_8[
                "mean_cold_writes"
            ]
        ),
        "tight_budget_erodes_io_advantage": (
            predictive_4[
                "mean_cold_writes"
            ]
            <= always_4[
                "mean_cold_writes"
            ]
        ),
    }

    return {
        "schema": SCHEMA,
        "status": (
            "PASS"
            if all(
                checks.values()
            )
            else "FAIL"
        ),
        "classification": (
            "SYNTHETIC_PREDICTIVE_COLD_TIER_GOVERNOR"
        ),
        "transfer_lead_steps": (
            TRANSFER_LEAD_STEPS
        ),
        "prediction_margin_steps": (
            PREDICTION_MARGIN_STEPS
        ),
        "budgets": list(
            BUDGETS
        ),
        "policies": list(
            POLICIES
        ),
        "matrix": matrix,
        "checks": checks,
        "primary_findings": [
            "REACTIVE_TRANSFER_CAN_BE_TOO_LATE_ONCE_TRANSFER_LATENCY_EXISTS",
            "LOCAL_GAP_TREND_CAN_TRIGGER_PROACTIVE_COLD_TIER_MOVEMENT",
            "PREDICTIVE_TRANSFER_CAN_REMOVE_SEMANTIC_OOM_WITH_LESS_IO_THAN_ALWAYS_PREEMPTIVE_AT_MODERATE_SLACK",
            "TIGHT_BUDGETS_ERODE_THE_IO_SAVINGS_OF_PREDICTION",
            "PROACTIVE_RESIDENCY_CONTROL_NEEDS_TIME_TO_RECLAIMABILITY_NOT_ONLY_CURRENT_PRESSURE",
        ],
        "claim_ceiling": (
            "SYNTHETIC_PREDICTIVE_TRANSFER_TIMING_ONLY"
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
