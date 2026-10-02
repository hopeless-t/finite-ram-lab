from __future__ import annotations

import json
import math
from statistics import mean


SCHEMA = "finite-ram-lab.semantic-oom-event-time-daemon/v0.1"

HALF_LIFE_S = 60.0
ENTER_THRESHOLD = 1.6
EXIT_THRESHOLD = 0.6
MIN_PROTECTIVE_HOLD_S = 60.0
DEPENDENCE_EVIDENCE_DELTA = 1.0
IID_EVIDENCE_DELTA = -1.5

COOPERATIVE_OK_LOSS = 10
BACKGROUND_SACRIFICE_LOSS = 73
ACTIVE_TASK_LOSS = 290

REGIME_SHARED_START_S = 106
REGIME_RECOVERY_START_S = 240


EVIDENCE_EVENTS = (
    (0, "IID"),
    (17, "DEPENDENCE"),
    (23, "IID"),
    (103, "DEPENDENCE"),
    (113, "DEPENDENCE"),
    (131, "DEPENDENCE"),
    (150, "IID"),
    (167, "DEPENDENCE"),
    (310, "IID"),
    (470, "DEPENDENCE"),
    (480, "IID"),
)

PRESSURE_EVENTS = (
    (5, "IID"),
    (18, "IID"),
    (40, "IID"),
    (106, "SHARED"),
    (116, "SHARED"),
    (145, "SHARED"),
    (155, "SHARED"),
    (185, "SHARED"),
    (220, "SHARED"),
    (280, "IID"),
    (315, "IID"),
    (472, "IID"),
    (500, "IID"),
)


def _decay(
    confidence: float,
    delta_s: float,
) -> float:
    if delta_s <= 0:
        return confidence

    return confidence * math.exp(
        -math.log(2.0)
        * delta_s
        / HALF_LIFE_S
    )


def _score_pressure(
    mode: str,
    regime: str,
) -> dict:
    if mode == "PROTECTIVE":
        return {
            "semantic_loss": (
                BACKGROUND_SACRIFICE_LOSS
            ),
            "current_task_lost": False,
            "unnecessary_protection": (
                regime == "IID"
            ),
        }

    if regime == "SHARED":
        return {
            "semantic_loss": ACTIVE_TASK_LOSS,
            "current_task_lost": True,
            "unnecessary_protection": False,
        }

    return {
        "semantic_loss": COOPERATIVE_OK_LOSS,
        "current_task_lost": False,
        "unnecessary_protection": False,
    }


def _evaluate_modes(
    strategy: str,
    pressure_modes: dict[int, str],
    switches: list[dict],
    extra: dict | None = None,
) -> dict:
    rows = []
    semantic_losses = []
    current_task_losses = 0
    unnecessary_protection = 0

    for time_s, regime in PRESSURE_EVENTS:
        mode = pressure_modes[time_s]
        outcome = _score_pressure(
            mode,
            regime,
        )

        semantic_losses.append(
            outcome["semantic_loss"]
        )
        current_task_losses += int(
            outcome["current_task_lost"]
        )
        unnecessary_protection += int(
            outcome[
                "unnecessary_protection"
            ]
        )

        rows.append(
            {
                "time_s": time_s,
                "regime_for_harness_only": (
                    regime
                ),
                "mode": mode,
                **outcome,
            }
        )

    first_protective_after_shared = next(
        (
            time_s
            for time_s, mode
            in sorted(
                pressure_modes.items()
            )
            if (
                time_s
                >= REGIME_SHARED_START_S
                and mode == "PROTECTIVE"
            )
        ),
        None,
    )

    first_cooperative_after_recovery = next(
        (
            time_s
            for time_s, mode
            in sorted(
                pressure_modes.items()
            )
            if (
                time_s
                >= REGIME_RECOVERY_START_S
                and mode == "COOPERATIVE"
            )
        ),
        None,
    )

    detection_delay_s = (
        None
        if first_protective_after_shared
        is None
        else (
            first_protective_after_shared
            - REGIME_SHARED_START_S
        )
    )

    release_delay_s = (
        0
        if all(
            mode == "COOPERATIVE"
            for time_s, mode
            in pressure_modes.items()
            if time_s < REGIME_SHARED_START_S
        )
        and not any(
            mode == "PROTECTIVE"
            for time_s, mode
            in pressure_modes.items()
            if (
                REGIME_SHARED_START_S
                <= time_s
                < REGIME_RECOVERY_START_S
            )
        )
        else (
            None
            if first_cooperative_after_recovery
            is None
            else (
                first_cooperative_after_recovery
                - REGIME_RECOVERY_START_S
            )
        )
    )

    result = {
        "strategy": strategy,
        "pressure_rows": rows,
        "switches": switches,
        "switch_count": len(switches),
        "current_task_loss_count": (
            current_task_losses
        ),
        "unnecessary_protection_count": (
            unnecessary_protection
        ),
        "mean_semantic_loss": mean(
            semantic_losses
        ),
        "max_semantic_loss": max(
            semantic_losses
        ),
        "detection_delay_to_protected_pressure_s": (
            detection_delay_s
        ),
        "release_delay_to_cooperative_pressure_s": (
            release_delay_s
        ),
    }

    if extra:
        result.update(extra)

    return result


def static_cooperative() -> dict:
    pressure_modes = {
        time_s: "COOPERATIVE"
        for time_s, _ in PRESSURE_EVENTS
    }

    return _evaluate_modes(
        "STATIC_COOPERATIVE",
        pressure_modes,
        [],
    )


def sticky_ever_dependence() -> dict:
    pressure_modes = {}
    switches = []
    protective = False

    events = sorted(
        [
            (time_s, "EVIDENCE", label)
            for time_s, label
            in EVIDENCE_EVENTS
        ]
        + [
            (time_s, "PRESSURE", regime)
            for time_s, regime
            in PRESSURE_EVENTS
        ]
    )

    for time_s, kind, value in events:
        if (
            kind == "EVIDENCE"
            and value == "DEPENDENCE"
            and not protective
        ):
            protective = True
            switches.append(
                {
                    "time_s": time_s,
                    "to": "PROTECTIVE",
                    "reason": (
                        "FIRST_DEPENDENCE_EVIDENCE"
                    ),
                }
            )

        if kind == "PRESSURE":
            pressure_modes[time_s] = (
                "PROTECTIVE"
                if protective
                else "COOPERATIVE"
            )

    return _evaluate_modes(
        "STICKY_EVER_DEPENDENCE",
        pressure_modes,
        switches,
    )


def raw_last_evidence() -> dict:
    pressure_modes = {}
    switches = []
    mode = "COOPERATIVE"

    events = sorted(
        [
            (time_s, "EVIDENCE", label)
            for time_s, label
            in EVIDENCE_EVENTS
        ]
        + [
            (time_s, "PRESSURE", regime)
            for time_s, regime
            in PRESSURE_EVENTS
        ]
    )

    for time_s, kind, value in events:
        if kind == "EVIDENCE":
            desired = (
                "PROTECTIVE"
                if value == "DEPENDENCE"
                else "COOPERATIVE"
            )

            if desired != mode:
                mode = desired
                switches.append(
                    {
                        "time_s": time_s,
                        "to": mode,
                        "reason": (
                            "LATEST_EVIDENCE"
                        ),
                    }
                )

        if kind == "PRESSURE":
            pressure_modes[time_s] = mode

    return _evaluate_modes(
        "RAW_LAST_EVIDENCE",
        pressure_modes,
        switches,
    )


def decay_hysteresis_cooldown() -> dict:
    confidence = 0.0
    last_time_s = 0
    mode = "COOPERATIVE"
    entered_protective_at_s = None

    pressure_modes = {}
    switches = []
    trace = []
    cooldown_blocked_exit_events = 0

    events = sorted(
        [
            (time_s, "EVIDENCE", label)
            for time_s, label
            in EVIDENCE_EVENTS
        ]
        + [
            (time_s, "PRESSURE", regime)
            for time_s, regime
            in PRESSURE_EVENTS
        ]
    )

    def maybe_decay_exit(
        time_s: int,
        reason: str,
    ) -> None:
        nonlocal mode
        nonlocal entered_protective_at_s
        nonlocal cooldown_blocked_exit_events

        if (
            mode != "PROTECTIVE"
            or confidence > EXIT_THRESHOLD
        ):
            return

        held_s = (
            time_s
            - entered_protective_at_s
        )

        if held_s < MIN_PROTECTIVE_HOLD_S:
            cooldown_blocked_exit_events += 1
            return

        mode = "COOPERATIVE"
        switches.append(
            {
                "time_s": time_s,
                "to": mode,
                "reason": reason,
                "confidence": confidence,
            }
        )
        entered_protective_at_s = None

    for time_s, kind, value in events:
        confidence = _decay(
            confidence,
            time_s - last_time_s,
        )
        last_time_s = time_s

        maybe_decay_exit(
            time_s,
            "WALL_CLOCK_CONFIDENCE_DECAY",
        )

        if kind == "EVIDENCE":
            if value == "DEPENDENCE":
                confidence = min(
                    3.0,
                    confidence
                    + DEPENDENCE_EVIDENCE_DELTA,
                )
            else:
                confidence = max(
                    0.0,
                    confidence
                    + IID_EVIDENCE_DELTA,
                )

            if (
                mode == "COOPERATIVE"
                and confidence
                >= ENTER_THRESHOLD
            ):
                mode = "PROTECTIVE"
                entered_protective_at_s = (
                    time_s
                )
                switches.append(
                    {
                        "time_s": time_s,
                        "to": mode,
                        "reason": (
                            "CONFIDENCE_ENTER"
                        ),
                        "confidence": (
                            confidence
                        ),
                    }
                )
            else:
                maybe_decay_exit(
                    time_s,
                    "CONTRADICTORY_EVIDENCE",
                )

        if kind == "PRESSURE":
            pressure_modes[time_s] = mode

        trace.append(
            {
                "time_s": time_s,
                "kind": kind,
                "value": value,
                "confidence": confidence,
                "mode": mode,
            }
        )

    return _evaluate_modes(
        "DECAY_HYSTERESIS_COOLDOWN",
        pressure_modes,
        switches,
        {
            "confidence_trace": trace,
            "cooldown_blocked_exit_events": (
                cooldown_blocked_exit_events
            ),
            "half_life_s": HALF_LIFE_S,
            "enter_threshold": (
                ENTER_THRESHOLD
            ),
            "exit_threshold": EXIT_THRESHOLD,
            "minimum_protective_hold_s": (
                MIN_PROTECTIVE_HOLD_S
            ),
        },
    )


def run_panel() -> dict:
    strategies = {
        "STATIC_COOPERATIVE": (
            static_cooperative()
        ),
        "STICKY_EVER_DEPENDENCE": (
            sticky_ever_dependence()
        ),
        "RAW_LAST_EVIDENCE": (
            raw_last_evidence()
        ),
        "DECAY_HYSTERESIS_COOLDOWN": (
            decay_hysteresis_cooldown()
        ),
    }

    static = strategies[
        "STATIC_COOPERATIVE"
    ]
    sticky = strategies[
        "STICKY_EVER_DEPENDENCE"
    ]
    raw = strategies[
        "RAW_LAST_EVIDENCE"
    ]
    decay = strategies[
        "DECAY_HYSTERESIS_COOLDOWN"
    ]

    frozen = {
        "STATIC_COOPERATIVE": {
            "current_task_loss_count": 6,
            "unnecessary_protection_count": 0,
            "switch_count": 0,
        },
        "STICKY_EVER_DEPENDENCE": {
            "current_task_loss_count": 0,
            "unnecessary_protection_count": 6,
            "switch_count": 1,
        },
        "RAW_LAST_EVIDENCE": {
            "current_task_loss_count": 1,
            "unnecessary_protection_count": 3,
            "switch_count": 6,
        },
        "DECAY_HYSTERESIS_COOLDOWN": {
            "current_task_loss_count": 1,
            "unnecessary_protection_count": 0,
            "switch_count": 2,
        },
    }

    for name, expected in frozen.items():
        row = strategies[name]

        for field, value in expected.items():
            if row[field] != value:
                raise RuntimeError(
                    f"reference_changed:{name}:{field}"
                )

    if decay[
        "cooldown_blocked_exit_events"
    ] != 1:
        raise RuntimeError(
            "cooldown_block_reference_changed"
        )

    if decay[
        "detection_delay_to_protected_pressure_s"
    ] != 10:
        raise RuntimeError(
            "decay_detection_delay_changed"
        )

    if decay[
        "release_delay_to_cooperative_pressure_s"
    ] != 40:
        raise RuntimeError(
            "decay_release_delay_changed"
        )

    if raw[
        "release_delay_to_cooperative_pressure_s"
    ] != 75:
        raise RuntimeError(
            "raw_release_delay_changed"
        )

    if not (
        decay[
            "unnecessary_protection_count"
        ]
        < raw[
            "unnecessary_protection_count"
        ]
        < sticky[
            "unnecessary_protection_count"
        ]
    ):
        raise RuntimeError(
            "overprotection_order_changed"
        )

    if not (
        decay["switch_count"]
        < raw["switch_count"]
    ):
        raise RuntimeError(
            "churn_advantage_changed"
        )

    if not (
        decay["mean_semantic_loss"]
        < raw["mean_semantic_loss"]
        < static["mean_semantic_loss"]
    ):
        raise RuntimeError(
            "mean_loss_order_changed"
        )

    return {
        "schema": SCHEMA,
        "status": "PASS",
        "classification": (
            "SYNTHETIC_EVENT_TIME_DAEMON_STATE_MACHINE_VALIDATED"
        ),
        "synthetic_only": True,
        "live_control_claim": False,
        "evidence_events": [
            {
                "time_s": time_s,
                "label": label,
            }
            for time_s, label
            in EVIDENCE_EVENTS
        ],
        "pressure_events": [
            {
                "time_s": time_s,
                "regime_for_harness_only": (
                    regime
                ),
            }
            for time_s, regime
            in PRESSURE_EVENTS
        ],
        "strategies": strategies,
        "primary_finding": (
            "WALL_CLOCK_DECAY_PLUS_HYSTERESIS_CAN_REDUCE_STALE_PROTECTION_AND_CHURN_WITH_BOUNDED_DETECTION_DELAY"
        ),
        "claim_ceiling": (
            "SYNTHETIC_EVENT_TIME_DAEMON_STATE_MACHINE_ONLY"
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
