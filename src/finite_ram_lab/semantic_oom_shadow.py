from __future__ import annotations

from itertools import combinations
import json
from pathlib import Path
from typing import Any


SCHEMA = "finite-ram-lab.semantic-oom-shadow/v0.1"


def _semantic_loss(process: dict[str, Any]) -> int:
    semantic = process["semantic"]
    return (
        int(semantic["task_value"])
        + int(semantic["reconstruction_cost"])
        + 100 * int(semantic["unsaved_state"])
    )


def _eligible(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        process
        for process in snapshot["processes"]
        if not process["semantic"].get("hard_protected", False)
    ]


def _receipt(
    *,
    policy: str,
    selected: list[dict[str, Any]],
    deficit_mib: int,
) -> dict[str, Any]:
    freed = sum(int(process["rss_mib"]) for process in selected)
    semantic_loss = sum(_semantic_loss(process) for process in selected)
    current_task_killed = any(
        bool(process["semantic"]["current_task"])
        for process in selected
    )

    return {
        "policy": policy,
        "victims": [
            {
                "pid": process["pid"],
                "name": process["name"],
                "rss_mib": process["rss_mib"],
                "oom_score": process["oom_score"],
                "semantic_loss": _semantic_loss(process),
                "current_task": process["semantic"]["current_task"],
            }
            for process in selected
        ],
        "freed_mib": freed,
        "relief_target_mib": deficit_mib,
        "relief_satisfied": freed >= deficit_mib,
        "semantic_loss": semantic_loss,
        "current_task_survives": not current_task_killed,
    }


def earlyoom_like(snapshot: dict[str, Any], deficit_mib: int) -> dict[str, Any]:
    ranked = sorted(
        _eligible(snapshot),
        key=lambda process: (
            int(process["oom_score"]),
            int(process["rss_mib"]),
            str(process["name"]),
        ),
        reverse=True,
    )

    selected: list[dict[str, Any]] = []
    freed = 0
    for process in ranked:
        if freed >= deficit_mib:
            break
        selected.append(process)
        freed += int(process["rss_mib"])

    return _receipt(
        policy="EARLYOOM_LIKE_OOM_SCORE",
        selected=selected,
        deficit_mib=deficit_mib,
    )


def rss_first(snapshot: dict[str, Any], deficit_mib: int) -> dict[str, Any]:
    ranked = sorted(
        _eligible(snapshot),
        key=lambda process: (
            int(process["rss_mib"]),
            int(process["oom_score"]),
            str(process["name"]),
        ),
        reverse=True,
    )

    selected: list[dict[str, Any]] = []
    freed = 0
    for process in ranked:
        if freed >= deficit_mib:
            break
        selected.append(process)
        freed += int(process["rss_mib"])

    return _receipt(
        policy="RSS_FIRST",
        selected=selected,
        deficit_mib=deficit_mib,
    )


def semantic_min_loss(
    snapshot: dict[str, Any],
    deficit_mib: int,
) -> dict[str, Any]:
    eligible = _eligible(snapshot)
    candidates: list[
        tuple[
            tuple[int, int, int, tuple[str, ...]],
            tuple[dict[str, Any], ...],
        ]
    ] = []

    for count in range(1, len(eligible) + 1):
        for subset in combinations(eligible, count):
            freed = sum(int(process["rss_mib"]) for process in subset)
            if freed < deficit_mib:
                continue

            current_task_kills = sum(
                bool(process["semantic"]["current_task"])
                for process in subset
            )
            loss = sum(_semantic_loss(process) for process in subset)
            excess = freed - deficit_mib
            names = tuple(sorted(str(process["name"]) for process in subset))
            objective = (
                current_task_kills,
                loss,
                excess,
                names,
            )
            candidates.append((objective, subset))

    if not candidates:
        selected = eligible
    else:
        selected = list(min(candidates, key=lambda item: item[0])[1])

    return _receipt(
        policy="SEMANTIC_MIN_LOSS",
        selected=selected,
        deficit_mib=deficit_mib,
    )


def compare_snapshot(
    snapshot: dict[str, Any],
    deficit_mib: int,
) -> dict[str, Any]:
    if snapshot.get("schema") != "finite-ram-lab.semantic-oom-snapshot/v0.1":
        raise ValueError("snapshot_schema_mismatch")
    if deficit_mib <= 0:
        raise ValueError("relief_target_must_be_positive")

    policies = {
        row["policy"]: row
        for row in (
            earlyoom_like(snapshot, deficit_mib),
            rss_first(snapshot, deficit_mib),
            semantic_min_loss(snapshot, deficit_mib),
        )
    }

    baseline = policies["EARLYOOM_LIKE_OOM_SCORE"]
    semantic = policies["SEMANTIC_MIN_LOSS"]

    baseline_pids = {
        victim["pid"]
        for victim in baseline["victims"]
    }
    semantic_pids = {
        victim["pid"]
        for victim in semantic["victims"]
    }

    disagreement = baseline_pids != semantic_pids

    return {
        "schema": SCHEMA,
        "status": "PASS",
        "observation_only": True,
        "signals_sent": 0,
        "control_changes": 0,
        "authority_effect": "NONE",
        "snapshot_id": snapshot["snapshot_id"],
        "captured_at": snapshot["captured_at"],
        "host_fingerprint": snapshot["host_fingerprint"],
        "pressure": snapshot["pressure"],
        "relief_target_mib": deficit_mib,
        "policies": policies,
        "ranking_disagreement": disagreement,
        "semantic_loss_delta_vs_oom_score": (
            baseline["semantic_loss"]
            - semantic["semantic_loss"]
        ),
        "current_task_survival_changed": (
            baseline["current_task_survives"]
            != semantic["current_task_survives"]
        ),
        "claim_ceiling": "READ_ONLY_SHADOW_RANKING_ONLY",
    }


def run_file(
    snapshot_path: str | Path,
    *,
    deficit_mib: int,
) -> dict[str, Any]:
    snapshot = json.loads(Path(snapshot_path).read_text(encoding="utf-8"))
    return compare_snapshot(snapshot, deficit_mib)


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("snapshot")
    parser.add_argument("--relief-target-mib", type=int, required=True)
    args = parser.parse_args()

    print(
        json.dumps(
            run_file(
                args.snapshot,
                deficit_mib=args.relief_target_mib,
            ),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
