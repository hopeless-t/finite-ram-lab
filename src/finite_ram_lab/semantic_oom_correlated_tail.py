from __future__ import annotations

import hashlib
import json
import math
from statistics import mean


SCHEMA = "finite-ram-lab.semantic-oom-correlated-tail/v0.1"
SEED = "FR-SOOM-002D-v0.1"
REPLICATES = 16384
TAIL_COUNT_PER_ACTION = 164
DEADLINE_MS = 200
RELIEF_TARGET_MIB = 3000


ACTIONS = (
    {
        "name": "CHROME_SHRINK",
        "relief_mib": 1500,
        "base_latency_ms": 120,
        "tail_latency_ms": 350,
    },
    {
        "name": "MODEL_SHRINK",
        "relief_mib": 600,
        "base_latency_ms": 140,
        "tail_latency_ms": 300,
    },
    {
        "name": "INDEXER_EXIT",
        "relief_mib": 900,
        "base_latency_ms": 100,
        "tail_latency_ms": 260,
    },
)


def _hash_rank(domain: str, replicate: int) -> int:
    payload = f"{SEED}|{domain}|{replicate}".encode("utf-8")
    return int.from_bytes(
        hashlib.sha256(payload).digest()[:8],
        "big",
    )


def _select_exact_tail_set(domain: str) -> set[int]:
    ranked = sorted(
        range(REPLICATES),
        key=lambda replicate: _hash_rank(
            domain,
            replicate,
        ),
    )
    return set(ranked[:TAIL_COUNT_PER_ACTION])


def _quantile(values: list[int], probability: float) -> int:
    ordered = sorted(values)
    index = max(
        0,
        math.ceil(probability * len(ordered)) - 1,
    )
    return ordered[index]


def _independent_tail_sets() -> dict[str, set[int]]:
    return {
        action["name"]: _select_exact_tail_set(
            f"IID:{action['name']}"
        )
        for action in ACTIONS
    }


def _shared_bad_set() -> set[int]:
    return _select_exact_tail_set("SHARED_BAD")


def evaluate_arm(arm: str) -> dict:
    if arm not in {"INDEPENDENT", "SHARED_BAD"}:
        raise ValueError("unknown_arm")

    independent = _independent_tail_sets()
    shared = _shared_bad_set()

    per_action_tail_count = {
        action["name"]: 0
        for action in ACTIONS
    }

    affected_replicates = 0
    deadline_successes = 0
    multi_action_tail_replicates = 0

    conditional_tail_action_counts: list[int] = []
    conditional_relief_deficits: list[int] = []

    first_affected: dict | None = None
    first_multi_action: dict | None = None

    for replicate in range(REPLICATES):
        draws: list[dict] = []

        for action in ACTIONS:
            if arm == "INDEPENDENT":
                tail = (
                    replicate
                    in independent[action["name"]]
                )
            else:
                tail = replicate in shared

            per_action_tail_count[action["name"]] += int(tail)

            latency_ms = (
                action["tail_latency_ms"]
                if tail
                else action["base_latency_ms"]
            )

            draws.append(
                {
                    "action": action["name"],
                    "tail_event": tail,
                    "latency_ms": latency_ms,
                    "relief_mib": action["relief_mib"],
                }
            )

        tail_action_count = sum(
            int(draw["tail_event"])
            for draw in draws
        )

        timely_relief_mib = sum(
            draw["relief_mib"]
            for draw in draws
            if draw["latency_ms"] <= DEADLINE_MS
        )

        relief_deficit_mib = max(
            0,
            RELIEF_TARGET_MIB - timely_relief_mib,
        )

        affected = tail_action_count > 0
        deadline_success = relief_deficit_mib == 0

        affected_replicates += int(affected)
        deadline_successes += int(deadline_success)

        if affected:
            conditional_tail_action_counts.append(
                tail_action_count
            )
            conditional_relief_deficits.append(
                relief_deficit_mib
            )

            if first_affected is None:
                first_affected = {
                    "replicate": replicate,
                    "tail_action_count": (
                        tail_action_count
                    ),
                    "relief_deficit_mib": (
                        relief_deficit_mib
                    ),
                    "draws": draws,
                }

        if tail_action_count >= 2:
            multi_action_tail_replicates += 1

            if first_multi_action is None:
                first_multi_action = {
                    "replicate": replicate,
                    "tail_action_count": (
                        tail_action_count
                    ),
                    "relief_deficit_mib": (
                        relief_deficit_mib
                    ),
                    "draws": draws,
                }

    return {
        "arm": arm,
        "replicates": REPLICATES,
        "tail_count_per_action_target": (
            TAIL_COUNT_PER_ACTION
        ),
        "per_action_tail_count": per_action_tail_count,
        "per_action_tail_rate": {
            name: count / REPLICATES
            for name, count
            in per_action_tail_count.items()
        },
        "affected_replicates": affected_replicates,
        "affected_rate": (
            affected_replicates / REPLICATES
        ),
        "deadline_successes": deadline_successes,
        "deadline_success_rate": (
            deadline_successes / REPLICATES
        ),
        "multi_action_tail_replicates": (
            multi_action_tail_replicates
        ),
        "multi_action_tail_rate": (
            multi_action_tail_replicates
            / REPLICATES
        ),
        "conditional_mean_tail_action_count": (
            mean(conditional_tail_action_counts)
        ),
        "conditional_p95_tail_action_count": (
            _quantile(
                conditional_tail_action_counts,
                0.95,
            )
        ),
        "conditional_mean_relief_deficit_mib": (
            mean(conditional_relief_deficits)
        ),
        "conditional_p95_relief_deficit_mib": (
            _quantile(
                conditional_relief_deficits,
                0.95,
            )
        ),
        "conditional_max_relief_deficit_mib": (
            max(conditional_relief_deficits)
        ),
        "first_affected": first_affected,
        "first_multi_action": first_multi_action,
    }


def run_panel() -> dict:
    independent = evaluate_arm("INDEPENDENT")
    shared = evaluate_arm("SHARED_BAD")

    for arm in (independent, shared):
        if set(
            arm["per_action_tail_count"].values()
        ) != {TAIL_COUNT_PER_ACTION}:
            raise RuntimeError(
                f"marginal_tail_count_changed:{arm['arm']}"
            )

    if independent["affected_replicates"] != 484:
        raise RuntimeError(
            "independent_affected_reference_changed"
        )

    if shared["affected_replicates"] != 164:
        raise RuntimeError(
            "shared_affected_reference_changed"
        )

    if not (
        shared["affected_rate"]
        < independent["affected_rate"]
    ):
        raise RuntimeError(
            "shared_prevalence_not_lower"
        )

    if not (
        shared["conditional_mean_tail_action_count"]
        > independent["conditional_mean_tail_action_count"]
    ):
        raise RuntimeError(
            "shared_conditional_tail_depth_not_higher"
        )

    if not (
        shared["conditional_p95_relief_deficit_mib"]
        > independent["conditional_p95_relief_deficit_mib"]
    ):
        raise RuntimeError(
            "shared_conditional_deficit_tail_not_higher"
        )

    if independent[
        "conditional_p95_relief_deficit_mib"
    ] != 1500:
        raise RuntimeError(
            "independent_deficit_reference_changed"
        )

    if shared[
        "conditional_p95_relief_deficit_mib"
    ] != 3000:
        raise RuntimeError(
            "shared_deficit_reference_changed"
        )

    return {
        "schema": SCHEMA,
        "status": "PASS",
        "classification": (
            "SYNTHETIC_CORRELATED_TAIL_RISK_SHAPE_VALIDATED"
        ),
        "synthetic_only": True,
        "live_control_claim": False,
        "seed": SEED,
        "replicates": REPLICATES,
        "tail_count_per_action": (
            TAIL_COUNT_PER_ACTION
        ),
        "per_action_tail_rate": (
            TAIL_COUNT_PER_ACTION / REPLICATES
        ),
        "deadline_ms": DEADLINE_MS,
        "relief_target_mib": RELIEF_TARGET_MIB,
        "arms": {
            "INDEPENDENT": independent,
            "SHARED_BAD": shared,
        },
        "primary_finding": (
            "MATCHED_MARGINAL_TAILS_DO_NOT_IMPLY_MATCHED_CONTROLLER_RISK"
        ),
        "claim_ceiling": (
            "SYNTHETIC_CORRELATED_TAIL_RISK_SHAPE_ONLY"
        ),
    }


def main() -> int:
    print(json.dumps(run_panel(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
