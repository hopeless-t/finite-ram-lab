from __future__ import annotations

import hashlib
import itertools
import json
import math
from statistics import mean


SCHEMA = "finite-ram-lab.semantic-oom-observable-dependence/v0.1"
SEED = "FR-SOOM-002F-v0.1"
EPISODES = 16384
TAIL_COUNT_PER_ACTION = 164
PERMUTATIONS = 999
ACTIONS = (
    "CHROME_SHRINK",
    "MODEL_SHRINK",
    "INDEXER_EXIT",
)


def _hash_rank(domain: str, episode: int) -> int:
    payload = f"{SEED}|{domain}|{episode}".encode("utf-8")
    return int.from_bytes(
        hashlib.sha256(payload).digest()[:8],
        "big",
    )


def _select_exact_tail_set(domain: str) -> set[int]:
    ranked = sorted(
        range(EPISODES),
        key=lambda episode: _hash_rank(
            domain,
            episode,
        ),
    )
    return set(ranked[:TAIL_COUNT_PER_ACTION])


def generate_trace(arm: str) -> list[dict]:
    if arm == "INDEPENDENT":
        sets = {
            action: _select_exact_tail_set(
                f"IID:{action}"
            )
            for action in ACTIONS
        }
    elif arm == "SHARED_BAD":
        shared = _select_exact_tail_set(
            "SHARED_BAD"
        )
        sets = {
            action: set(shared)
            for action in ACTIONS
        }
    else:
        raise ValueError("unknown_arm")

    return [
        {
            "episode": episode,
            "late_actions": {
                action: episode in sets[action]
                for action in ACTIONS
            },
        }
        for episode in range(EPISODES)
    ]


def _sets_from_trace(
    trace: list[dict],
) -> dict[str, set[int]]:
    sets = {
        action: set()
        for action in ACTIONS
    }

    for row in trace:
        episode = int(row["episode"])
        late_actions = row["late_actions"]

        for action in ACTIONS:
            if bool(late_actions[action]):
                sets[action].add(episode)

    return sets


def _pair_cofailure_total(
    sets: dict[str, set[int]],
) -> int:
    return sum(
        len(sets[left] & sets[right])
        for left, right
        in itertools.combinations(ACTIONS, 2)
    )


def _pairwise_phi(
    sets: dict[str, set[int]],
) -> dict[str, float]:
    result: dict[str, float] = {}

    for left, right in itertools.combinations(
        ACTIONS,
        2,
    ):
        left_set = sets[left]
        right_set = sets[right]

        n11 = len(left_set & right_set)
        n10 = len(left_set - right_set)
        n01 = len(right_set - left_set)
        n00 = (
            EPISODES
            - n11
            - n10
            - n01
        )

        denominator = math.sqrt(
            (n11 + n10)
            * (n01 + n00)
            * (n11 + n01)
            * (n10 + n00)
        )

        phi = (
            (
                n11 * n00
                - n10 * n01
            )
            / denominator
            if denominator
            else 0.0
        )

        result[f"{left}|{right}"] = phi

    return result


def _shift_for(
    permutation: int,
    action: str,
) -> int:
    payload = (
        f"{SEED}|PERM|{permutation}|{action}"
    ).encode("utf-8")

    return (
        int.from_bytes(
            hashlib.sha256(payload).digest()[:8],
            "big",
        )
        % EPISODES
    )


def _shift_set(
    values: set[int],
    shift: int,
) -> set[int]:
    return {
        (episode + shift) % EPISODES
        for episode in values
    }


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


def analyze_trace(
    trace: list[dict],
) -> dict:
    sets = _sets_from_trace(trace)

    marginal_counts = {
        action: len(sets[action])
        for action in ACTIONS
    }

    observed_pair_cofailures = (
        _pair_cofailure_total(sets)
    )

    pairwise_phi = _pairwise_phi(sets)
    mean_pairwise_phi = mean(
        pairwise_phi.values()
    )

    multi_action_episodes = sum(
        int(
            sum(
                episode in sets[action]
                for action in ACTIONS
            )
            >= 2
        )
        for episode in range(EPISODES)
    )

    affected_episodes = sum(
        int(
            any(
                episode in sets[action]
                for action in ACTIONS
            )
        )
        for episode in range(EPISODES)
    )

    null_statistics: list[int] = []

    for permutation in range(PERMUTATIONS):
        shifted = {
            action: _shift_set(
                sets[action],
                _shift_for(
                    permutation,
                    action,
                ),
            )
            for action in ACTIONS
        }

        null_statistics.append(
            _pair_cofailure_total(shifted)
        )

    null_ge_observed = sum(
        statistic >= observed_pair_cofailures
        for statistic in null_statistics
    )

    permutation_p_upper = (
        1 + null_ge_observed
    ) / (PERMUTATIONS + 1)

    if (
        permutation_p_upper <= 0.01
        and mean_pairwise_phi >= 0.10
    ):
        classification = (
            "CROSS_ACTION_DEPENDENCE_EVIDENCE"
        )
    elif permutation_p_upper > 0.05:
        classification = "IID_COMPATIBLE"
    else:
        classification = "INCONCLUSIVE"

    return {
        "trace_episodes": len(trace),
        "latent_labels_used": False,
        "marginal_tail_count": marginal_counts,
        "observed_pair_cofailure_total": (
            observed_pair_cofailures
        ),
        "pairwise_phi": pairwise_phi,
        "mean_pairwise_phi": mean_pairwise_phi,
        "multi_action_tail_episodes": (
            multi_action_episodes
        ),
        "affected_episodes": affected_episodes,
        "permutation_count": PERMUTATIONS,
        "permutation_p_upper": (
            permutation_p_upper
        ),
        "null_pair_cofailure_mean": mean(
            null_statistics
        ),
        "null_pair_cofailure_p95": _quantile(
            null_statistics,
            0.95,
        ),
        "null_pair_cofailure_p99": _quantile(
            null_statistics,
            0.99,
        ),
        "null_pair_cofailure_max": max(
            null_statistics
        ),
        "classification": classification,
    }


def run_panel() -> dict:
    results = {}

    for arm in (
        "INDEPENDENT",
        "SHARED_BAD",
    ):
        trace = generate_trace(arm)
        analysis = analyze_trace(trace)

        if set(
            analysis[
                "marginal_tail_count"
            ].values()
        ) != {TAIL_COUNT_PER_ACTION}:
            raise RuntimeError(
                f"marginal_count_changed:{arm}"
            )

        results[arm] = analysis

    independent = results["INDEPENDENT"]
    shared = results["SHARED_BAD"]

    if independent[
        "observed_pair_cofailure_total"
    ] != 5:
        raise RuntimeError(
            "independent_pair_cofailure_reference_changed"
        )

    if shared[
        "observed_pair_cofailure_total"
    ] != 492:
        raise RuntimeError(
            "shared_pair_cofailure_reference_changed"
        )

    if independent[
        "multi_action_tail_episodes"
    ] != 5:
        raise RuntimeError(
            "independent_multi_action_reference_changed"
        )

    if shared[
        "multi_action_tail_episodes"
    ] != 164:
        raise RuntimeError(
            "shared_multi_action_reference_changed"
        )

    if independent[
        "permutation_p_upper"
    ] != 0.587:
        raise RuntimeError(
            "independent_p_reference_changed"
        )

    if shared[
        "permutation_p_upper"
    ] != 0.001:
        raise RuntimeError(
            "shared_p_reference_changed"
        )

    if independent[
        "classification"
    ] != "IID_COMPATIBLE":
        raise RuntimeError(
            "independent_classification_changed"
        )

    if shared[
        "classification"
    ] != "CROSS_ACTION_DEPENDENCE_EVIDENCE":
        raise RuntimeError(
            "shared_classification_changed"
        )

    return {
        "schema": SCHEMA,
        "status": "PASS",
        "classification": (
            "SYNTHETIC_OBSERVABLE_DEPENDENCE_INFERENCE_VALIDATED"
        ),
        "synthetic_only": True,
        "live_control_claim": False,
        "latent_labels_used_by_analyzer": False,
        "seed": SEED,
        "episodes": EPISODES,
        "tail_count_per_action": (
            TAIL_COUNT_PER_ACTION
        ),
        "permutations": PERMUTATIONS,
        "arms": results,
        "primary_finding": (
            "SHARED_FAILURE_DOMAIN_CAN_BE_DETECTED_FROM_OBSERVABLE_COFAILURE_TRACE"
        ),
        "claim_ceiling": (
            "SYNTHETIC_OBSERVABLE_DEPENDENCE_INFERENCE_ONLY"
        ),
    }


def main() -> int:
    print(json.dumps(run_panel(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
