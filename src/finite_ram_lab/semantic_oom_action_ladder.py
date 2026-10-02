from __future__ import annotations

from dataclasses import dataclass
from itertools import product
import json


SCHEMA = "finite-ram-lab.semantic-oom-action-ladder/v0.1"
RELIEF_TARGET_MIB = 3000
DEADLINES_MS = (25, 100, 200, 600)


@dataclass(frozen=True)
class Action:
    entity: str
    name: str
    relief_mib: int
    latency_ms: int
    semantic_loss: int
    current_task_damage: bool
    hard_kill: bool
    reversible: bool


def action_catalog() -> dict[str, tuple[Action | None, ...]]:
    return {
        "chrome-active": (
            None,
            Action(
                "chrome-active",
                "CHROME_TRIM_CACHE",
                900,
                80,
                0,
                False,
                False,
                True,
            ),
            Action(
                "chrome-active",
                "CHROME_TRIM_AND_IDLE_RENDERERS",
                1500,
                180,
                8,
                False,
                False,
                True,
            ),
            Action(
                "chrome-active",
                "CHROME_KILL",
                3200,
                20,
                280,
                True,
                True,
                False,
            ),
        ),
        "terminal-session": (
            None,
            Action(
                "terminal-session",
                "TERMINAL_TRIM",
                100,
                50,
                0,
                False,
                False,
                True,
            ),
            Action(
                "terminal-session",
                "TERMINAL_KILL",
                500,
                20,
                245,
                True,
                True,
                False,
            ),
        ),
        "model-worker": (
            None,
            Action(
                "model-worker",
                "MODEL_SHRINK",
                600,
                150,
                0,
                False,
                False,
                True,
            ),
            Action(
                "model-worker",
                "MODEL_GRACEFUL_STOP",
                1200,
                400,
                20,
                False,
                False,
                False,
            ),
            Action(
                "model-worker",
                "MODEL_KILL",
                1200,
                20,
                55,
                False,
                True,
                False,
            ),
        ),
        "batch-compressor": (
            None,
            Action(
                "batch-compressor",
                "BATCH_CHECKPOINT_EXIT",
                1400,
                500,
                3,
                False,
                False,
                False,
            ),
            Action(
                "batch-compressor",
                "BATCH_KILL",
                1400,
                20,
                13,
                False,
                True,
                False,
            ),
        ),
        "background-indexer": (
            None,
            Action(
                "background-indexer",
                "INDEXER_GRACEFUL_EXIT",
                900,
                100,
                1,
                False,
                False,
                False,
            ),
            Action(
                "background-indexer",
                "INDEXER_KILL",
                900,
                20,
                5,
                False,
                True,
                False,
            ),
        ),
    }


def _summarize(
    actions: tuple[Action, ...],
    *,
    deadline_ms: int,
) -> dict:
    relief = sum(action.relief_mib for action in actions)
    semantic_loss = sum(action.semantic_loss for action in actions)
    hard_kills = sum(action.hard_kill for action in actions)
    current_task_damage = sum(
        action.current_task_damage for action in actions
    )
    reversible_relief = sum(
        action.relief_mib for action in actions
        if action.reversible
    )

    return {
        "deadline_ms": deadline_ms,
        "relief_target_mib": RELIEF_TARGET_MIB,
        "actions": [action.name for action in actions],
        "relief_mib": relief,
        "relief_satisfied": relief >= RELIEF_TARGET_MIB,
        "excess_relief_mib": max(
            0,
            relief - RELIEF_TARGET_MIB,
        ),
        "response_latency_ms": max(
            (action.latency_ms for action in actions),
            default=0,
        ),
        "semantic_loss": semantic_loss,
        "current_task_damage_count": current_task_damage,
        "current_task_survives": current_task_damage == 0,
        "hard_kill_count": hard_kills,
        "reversible_relief_mib": reversible_relief,
    }


def earlyoom_like_kill_first() -> dict:
    chrome_kill = next(
        action
        for action in action_catalog()["chrome-active"]
        if action is not None and action.name == "CHROME_KILL"
    )
    return _summarize((chrome_kill,), deadline_ms=25)


def semantic_action_plan(deadline_ms: int) -> dict:
    if deadline_ms not in DEADLINES_MS:
        raise ValueError("unfrozen_deadline")

    catalog = action_catalog()
    entities = tuple(catalog)

    candidates: list[
        tuple[
            tuple[
                int,
                int,
                int,
                int,
                int,
                tuple[str, ...],
            ],
            tuple[Action, ...],
        ]
    ] = []

    for choices in product(
        *(catalog[entity] for entity in entities)
    ):
        selected = tuple(
            action
            for action in choices
            if action is not None
        )
        if not selected:
            continue

        if max(action.latency_ms for action in selected) > deadline_ms:
            continue

        relief = sum(action.relief_mib for action in selected)
        if relief < RELIEF_TARGET_MIB:
            continue

        objective = (
            sum(action.current_task_damage for action in selected),
            sum(action.semantic_loss for action in selected),
            sum(action.hard_kill for action in selected),
            relief - RELIEF_TARGET_MIB,
            len(selected),
            tuple(action.name for action in selected),
        )
        candidates.append((objective, selected))

    if not candidates:
        raise RuntimeError("no_feasible_plan")

    selected = min(candidates, key=lambda item: item[0])[1]
    return _summarize(selected, deadline_ms=deadline_ms)


def run_panel() -> dict:
    baseline = earlyoom_like_kill_first()
    rows = [
        semantic_action_plan(deadline)
        for deadline in DEADLINES_MS
    ]

    expected = {
        25: (
            "MODEL_KILL",
            "BATCH_KILL",
            "INDEXER_KILL",
        ),
        100: (
            "CHROME_TRIM_CACHE",
            "BATCH_KILL",
            "INDEXER_GRACEFUL_EXIT",
        ),
        200: (
            "CHROME_TRIM_AND_IDLE_RENDERERS",
            "MODEL_SHRINK",
            "INDEXER_GRACEFUL_EXIT",
        ),
        600: (
            "CHROME_TRIM_CACHE",
            "TERMINAL_TRIM",
            "MODEL_SHRINK",
            "BATCH_CHECKPOINT_EXIT",
        ),
    }

    for row in rows:
        deadline = row["deadline_ms"]
        if tuple(row["actions"]) != expected[deadline]:
            raise RuntimeError(
                f"frozen_plan_changed:{deadline}"
            )
        if not row["relief_satisfied"]:
            raise RuntimeError(
                f"relief_not_satisfied:{deadline}"
            )
        if not row["current_task_survives"]:
            raise RuntimeError(
                f"current_task_damaged:{deadline}"
            )

    semantic_losses = [
        row["semantic_loss"] for row in rows
    ]
    if semantic_losses != sorted(
        semantic_losses,
        reverse=True,
    ):
        raise RuntimeError(
            "semantic_loss_not_monotone_with_deadline"
        )

    hard_kills = [
        row["hard_kill_count"] for row in rows
    ]
    if hard_kills != sorted(
        hard_kills,
        reverse=True,
    ):
        raise RuntimeError(
            "hard_kills_not_monotone_with_deadline"
        )

    if rows[-1]["semantic_loss"] != 3:
        raise RuntimeError(
            "long_deadline_loss_unexpected"
        )
    if rows[-1]["hard_kill_count"] != 0:
        raise RuntimeError(
            "long_deadline_still_kills"
        )

    return {
        "schema": SCHEMA,
        "status": "PASS",
        "classification": (
            "SYNTHETIC_DEADLINE_ACTION_LADDER_VALIDATED"
        ),
        "synthetic_only": True,
        "live_control_claim": False,
        "relief_target_mib": RELIEF_TARGET_MIB,
        "deadlines_ms": list(DEADLINES_MS),
        "kill_first_baseline": baseline,
        "semantic_plans": rows,
        "claim_ceiling": (
            "SYNTHETIC_DEADLINE_ACTION_LADDER_ONLY"
        ),
    }


def main() -> int:
    print(json.dumps(run_panel(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
