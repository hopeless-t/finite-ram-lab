from __future__ import annotations

import hashlib
import itertools
import json
import math
from statistics import mean


SCHEMA = "finite-ram-lab.semantic-oom-regime-drift/v0.1"
SEED = "FR-SOOM-002H-v0.1"
WINDOWS = 12
EPISODES_PER_WINDOW = 2048
TAIL_COUNT_PER_ACTION = 20
PERMUTATIONS = 199
RELIEF_TARGET_MIB = 3000

ACTIONS = (
    "CHROME_CACHE",
    "MODEL_SHRINK",
    "INDEXER_EXIT",
)

REGIMES = (
    "IID",
    "IID",
    "BURST",
    "IID",
    "SHARED",
    "SHARED",
    "SHARED",
    "SHARED",
    "IID",
    "IID",
    "IID",
    "IID",
)

COOPERATIVE_SEMANTIC_LOSS = 10
BACKGROUND_SACRIFICE_SEMANTIC_LOSS = 73
EMERGENCY_ACTIVE_TASK_LOSS = 280


def _hash_rank(
    domain: str,
    episode: int,
) -> int:
    payload = f"{SEED}|{domain}|{episode}".encode("utf-8")
    return int.from_bytes(
        hashlib.sha256(payload).digest()[:8],
        "big",
    )


def _select_exact_tail_set(
    domain: str,
) -> set[int]:
    ranked = sorted(
        range(EPISODES_PER_WINDOW),
        key=lambda episode: _hash_rank(
            domain,
            episode,
        ),
    )
    return set(
        ranked[:TAIL_COUNT_PER_ACTION]
    )


def _window_sets(
    window: int,
    regime: str,
) -> dict[str, set[int]]:
    if regime in {
        "SHARED",
        "BURST",
    }:
        shared = _select_exact_tail_set(
            f"W{window}:SHARED"
        )
        return {
            action: set(shared)
            for action in ACTIONS
        }

    if regime == "IID":
        return {
            action: _select_exact_tail_set(
                f"W{window}:IID:{action}"
            )
            for action in ACTIONS
        }

    raise ValueError("unknown_regime")


def _pair_cofailure_total(
    sets: dict[str, set[int]],
) -> int:
    return sum(
        len(sets[left] & sets[right])
        for left, right
        in itertools.combinations(ACTIONS, 2)
    )


def _shift_for(
    window: int,
    permutation: int,
    action: str,
) -> int:
    payload = (
        f"{SEED}|W{window}|PERM|"
        f"{permutation}|{action}"
    ).encode("utf-8")

    return (
        int.from_bytes(
            hashlib.sha256(payload).digest()[:8],
            "big",
        )
        % EPISODES_PER_WINDOW
    )


def _shift_set(
    values: set[int],
    shift: int,
) -> set[int]:
    return {
        (
            episode + shift
        )
        % EPISODES_PER_WINDOW
        for episode in values
    }


def analyze_window(
    window: int,
    regime: str,
) -> dict:
    sets = _window_sets(
        window,
        regime,
    )

    observed = _pair_cofailure_total(
        sets
    )

    multi_action_episodes = sum(
        int(
            sum(
                episode in sets[action]
                for action in ACTIONS
            )
            >= 2
        )
        for episode in range(
            EPISODES_PER_WINDOW
        )
    )

    null_statistics: list[int] = []

    for permutation in range(PERMUTATIONS):
        shifted = {
            action: _shift_set(
                sets[action],
                _shift_for(
                    window,
                    permutation,
                    action,
                ),
            )
            for action in ACTIONS
        }

        null_statistics.append(
            _pair_cofailure_total(
                shifted
            )
        )

    null_ge = sum(
        statistic >= observed
        for statistic in null_statistics
    )

    permutation_p_upper = (
        1 + null_ge
    ) / (PERMUTATIONS + 1)

    classification = (
        "DEPENDENCE_EVIDENCE"
        if permutation_p_upper <= 0.01
        else "IID_COMPATIBLE"
    )

    return {
        "window": window,
        "regime_for_harness_only": (
            regime
        ),
        "marginal_tail_count": {
            action: len(
                sets[action]
            )
            for action in ACTIONS
        },
        "pair_cofailure_total": observed,
        "multi_action_tail_episodes": (
            multi_action_episodes
        ),
        "permutation_p_upper": (
            permutation_p_upper
        ),
        "classification": classification,
    }


def _static_plans(
    evidence: list[dict],
) -> list[str]:
    del evidence
    return [
        "COOPERATIVE"
        for _ in range(WINDOWS)
    ]


def _raw_sliding_plans(
    evidence: list[dict],
) -> list[str]:
    plans = ["COOPERATIVE"]

    for window in range(1, WINDOWS):
        previous = evidence[
            window - 1
        ]["classification"]

        plans.append(
            "BACKGROUND_SACRIFICE"
            if previous
            == "DEPENDENCE_EVIDENCE"
            else "COOPERATIVE"
        )

    return plans


def _hysteresis_plans(
    evidence: list[dict],
) -> list[str]:
    state = "COOPERATIVE"
    dependence_streak = 0
    plans: list[str] = []

    for row in evidence:
        plans.append(state)

        if row[
            "classification"
        ] == "DEPENDENCE_EVIDENCE":
            dependence_streak += 1

            if (
                state == "COOPERATIVE"
                and dependence_streak >= 2
            ):
                state = (
                    "BACKGROUND_SACRIFICE"
                )
        else:
            dependence_streak = 0

            if (
                state
                == "BACKGROUND_SACRIFICE"
            ):
                state = "COOPERATIVE"

    return plans


def _quantile(
    values: list[int],
    probability: float,
) -> int:
    ordered = sorted(values)
    index = max(
        0,
        math.ceil(
            probability * len(ordered)
        )
        - 1,
    )
    return ordered[index]


def _evaluate_strategy(
    name: str,
    plans: list[str],
    evidence: list[dict],
) -> dict:
    semantic_losses: list[int] = []
    current_task_losses = 0
    background_windows = 0
    unnecessary_background_windows = 0
    rows: list[dict] = []

    for window, plan in enumerate(
        plans
    ):
        regime = REGIMES[window]
        cooperative_failures = (
            evidence[window][
                "multi_action_tail_episodes"
            ]
        )

        if plan == "COOPERATIVE":
            deadline_failures = (
                cooperative_failures
            )
            current_task_losses += (
                deadline_failures
            )

            semantic_losses.extend(
                [
                    COOPERATIVE_SEMANTIC_LOSS
                ]
                * (
                    EPISODES_PER_WINDOW
                    - deadline_failures
                )
            )
            semantic_losses.extend(
                [
                    (
                        COOPERATIVE_SEMANTIC_LOSS
                        + EMERGENCY_ACTIVE_TASK_LOSS
                    )
                ]
                * deadline_failures
            )
        else:
            deadline_failures = 0
            background_windows += 1

            if regime == "IID":
                unnecessary_background_windows += 1

            semantic_losses.extend(
                [
                    BACKGROUND_SACRIFICE_SEMANTIC_LOSS
                ]
                * EPISODES_PER_WINDOW
            )

        rows.append(
            {
                "window": window,
                "regime_for_harness_only": (
                    regime
                ),
                "evidence": evidence[
                    window
                ]["classification"],
                "plan": plan,
                "cooperative_failure_count": (
                    cooperative_failures
                ),
                "realized_deadline_failures": (
                    deadline_failures
                ),
            }
        )

    plan_switches = sum(
        plans[index]
        != plans[index - 1]
        for index in range(
            1,
            len(plans),
        )
    )

    shared_start = 4
    recovery_start = 8

    first_background_after_shared = next(
        (
            index
            for index in range(
                shared_start,
                WINDOWS,
            )
            if plans[index]
            == "BACKGROUND_SACRIFICE"
        ),
        None,
    )

    first_cooperative_after_recovery = next(
        (
            index
            for index in range(
                recovery_start,
                WINDOWS,
            )
            if plans[index]
            == "COOPERATIVE"
        ),
        None,
    )

    detection_delay_windows = (
        None
        if first_background_after_shared
        is None
        else (
            first_background_after_shared
            - shared_start
        )
    )

    release_delay_windows = (
        0
        if all(
            plans[index]
            == "COOPERATIVE"
            for index in range(
                shared_start,
                recovery_start,
            )
        )
        else (
            None
            if first_cooperative_after_recovery
            is None
            else (
                first_cooperative_after_recovery
                - recovery_start
            )
        )
    )

    return {
        "strategy": name,
        "plans": plans,
        "window_rows": rows,
        "total_episodes": (
            WINDOWS
            * EPISODES_PER_WINDOW
        ),
        "current_task_loss_count": (
            current_task_losses
        ),
        "background_sacrifice_windows": (
            background_windows
        ),
        "unnecessary_background_sacrifice_windows": (
            unnecessary_background_windows
        ),
        "post_burst_stale_escalation": (
            plans[3]
            == "BACKGROUND_SACRIFICE"
        ),
        "plan_switches": plan_switches,
        "detection_delay_windows": (
            detection_delay_windows
        ),
        "release_delay_windows": (
            release_delay_windows
        ),
        "mean_semantic_loss": mean(
            semantic_losses
        ),
        "p99_semantic_loss": (
            _quantile(
                semantic_losses,
                0.99,
            )
        ),
        "p99_9_semantic_loss": (
            _quantile(
                semantic_losses,
                0.999,
            )
        ),
        "max_semantic_loss": max(
            semantic_losses
        ),
    }


def run_panel() -> dict:
    evidence = [
        analyze_window(
            window,
            regime,
        )
        for window, regime
        in enumerate(REGIMES)
    ]

    expected_evidence = (
        "IID_COMPATIBLE",
        "IID_COMPATIBLE",
        "DEPENDENCE_EVIDENCE",
        "IID_COMPATIBLE",
        "DEPENDENCE_EVIDENCE",
        "DEPENDENCE_EVIDENCE",
        "DEPENDENCE_EVIDENCE",
        "DEPENDENCE_EVIDENCE",
        "IID_COMPATIBLE",
        "IID_COMPATIBLE",
        "IID_COMPATIBLE",
        "IID_COMPATIBLE",
    )

    observed_evidence = tuple(
        row["classification"]
        for row in evidence
    )

    if observed_evidence != (
        expected_evidence
    ):
        raise RuntimeError(
            "window_evidence_reference_changed"
        )

    strategies = {
        "STATIC_INITIAL": _evaluate_strategy(
            "STATIC_INITIAL",
            _static_plans(evidence),
            evidence,
        ),
        "RAW_SLIDING": _evaluate_strategy(
            "RAW_SLIDING",
            _raw_sliding_plans(
                evidence
            ),
            evidence,
        ),
        "HYSTERESIS_2_ENTER_1_EXIT": (
            _evaluate_strategy(
                "HYSTERESIS_2_ENTER_1_EXIT",
                _hysteresis_plans(
                    evidence
                ),
                evidence,
            )
        ),
    }

    static = strategies[
        "STATIC_INITIAL"
    ]
    raw = strategies["RAW_SLIDING"]
    hysteresis = strategies[
        "HYSTERESIS_2_ENTER_1_EXIT"
    ]

    if static[
        "current_task_loss_count"
    ] != 101:
        raise RuntimeError(
            "static_loss_reference_changed"
        )

    if raw[
        "current_task_loss_count"
    ] != 41:
        raise RuntimeError(
            "raw_loss_reference_changed"
        )

    if hysteresis[
        "current_task_loss_count"
    ] != 61:
        raise RuntimeError(
            "hysteresis_loss_reference_changed"
        )

    if raw[
        "unnecessary_background_sacrifice_windows"
    ] != 2:
        raise RuntimeError(
            "raw_overreaction_reference_changed"
        )

    if hysteresis[
        "unnecessary_background_sacrifice_windows"
    ] != 1:
        raise RuntimeError(
            "hysteresis_overreaction_reference_changed"
        )

    if raw["plan_switches"] != 4:
        raise RuntimeError(
            "raw_switch_reference_changed"
        )

    if hysteresis[
        "plan_switches"
    ] != 2:
        raise RuntimeError(
            "hysteresis_switch_reference_changed"
        )

    if raw[
        "detection_delay_windows"
    ] != 1:
        raise RuntimeError(
            "raw_detection_delay_changed"
        )

    if hysteresis[
        "detection_delay_windows"
    ] != 2:
        raise RuntimeError(
            "hysteresis_detection_delay_changed"
        )

    if not raw[
        "post_burst_stale_escalation"
    ]:
        raise RuntimeError(
            "raw_burst_spillover_missing"
        )

    if hysteresis[
        "post_burst_stale_escalation"
    ]:
        raise RuntimeError(
            "hysteresis_burst_spillover_present"
        )

    return {
        "schema": SCHEMA,
        "status": "PASS",
        "classification": (
            "SYNTHETIC_REGIME_DRIFT_CONTROL_VALIDATED"
        ),
        "synthetic_only": True,
        "live_control_claim": False,
        "windows": WINDOWS,
        "episodes_per_window": (
            EPISODES_PER_WINDOW
        ),
        "regimes": list(REGIMES),
        "window_evidence": evidence,
        "strategies": strategies,
        "primary_finding": (
            "HYSTERESIS_REDUCES_STALE_ESCALATION_AND_CHURN_AT_COST_OF_DETECTION_DELAY"
        ),
        "claim_ceiling": (
            "SYNTHETIC_REGIME_DRIFT_CONTROL_ONLY"
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
