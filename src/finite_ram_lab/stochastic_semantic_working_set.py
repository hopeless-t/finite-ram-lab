from __future__ import annotations

from collections import Counter
import hashlib
import json
import math

from finite_ram_lab.semantic_working_set import (
    BUDGETS,
    Case,
    append_truncate_indices,
    corpus,
    evaluate_case,
    key_aware_indices,
)


SCHEMA = "finite-ram-lab.stochastic-semantic-working-set/v0.1"
SEED = 20261002
REPLICATES = 512
OMISSION_PROBABILITY = 0.005
WILSON_Z_95 = 1.959963984540054
KNEE_EXACT_RATE = 0.95
KNEE_WILSON_LOWER = 0.95
MAX_BIOPSIES = 16


def _uniform01(*parts: object) -> float:
    payload = "|".join(str(part) for part in parts).encode("utf-8")
    digest = hashlib.sha256(payload).digest()
    return int.from_bytes(digest[:8], "big") / 2**64


def _required_latest_indices(case: Case) -> dict[str, int]:
    out: dict[str, int] = {}
    for key in case.query_keys:
        for index in range(len(case.events) - 1, -1, -1):
            if case.events[index].key == key:
                out[key] = index
                break
    return out


def noisy_key_aware_indices(
    case: Case,
    budget: int,
    *,
    replicate: int,
    omission_probability: float = OMISSION_PROBABILITY,
    seed: int = SEED,
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    """Inject a deterministic rare omission into KEY_AWARE.

    The omitted required event is blocked from immediate re-selection and the
    resident set is back-filled with the newest available non-blocked event.
    This keeps resident size fixed while changing semantic sufficiency.
    """
    base = list(key_aware_indices(case, budget))
    required = set(_required_latest_indices(case).values())

    omitted = {
        index
        for index in base
        if (
            index in required
            and _uniform01(
                seed,
                "NOISY_KEY_AWARE",
                budget,
                replicate,
                case.name,
                index,
            )
            < omission_probability
        )
    }

    selected = [index for index in base if index not in omitted]
    selected_set = set(selected)

    for index in range(len(case.events) - 1, -1, -1):
        if len(selected) >= min(budget, len(case.events)):
            break
        if index in selected_set or index in omitted:
            continue
        selected.append(index)
        selected_set.add(index)

    return tuple(sorted(selected)), tuple(sorted(omitted))


def wilson_interval(
    successes: int,
    trials: int,
    *,
    z: float = WILSON_Z_95,
) -> tuple[float, float]:
    if trials <= 0:
        raise ValueError("trials_must_be_positive")
    if successes < 0 or successes > trials:
        raise ValueError("successes_out_of_range")

    p = successes / trials
    denominator = 1.0 + z * z / trials
    center = (p + z * z / (2.0 * trials)) / denominator
    half = (
        z
        * math.sqrt(
            p * (1.0 - p) / trials
            + z * z / (4.0 * trials * trials)
        )
        / denominator
    )
    return center - half, center + half


def _failure_signature(row: dict) -> str:
    missing = ",".join(row["missing_required_keys"]) or "-"
    stale = ",".join(row["stale_required_keys"]) or "-"
    return f"missing={missing}|stale={stale}"


def evaluate_replicated_policy(
    policy: str,
    budget: int,
    *,
    replicates: int = REPLICATES,
    omission_probability: float = OMISSION_PROBABILITY,
    seed: int = SEED,
) -> dict:
    if policy not in {"APPEND_TRUNCATE", "NOISY_KEY_AWARE"}:
        raise ValueError(f"unknown_policy:{policy}")
    if replicates <= 0:
        raise ValueError("replicates_must_be_positive")
    if not 0.0 <= omission_probability <= 1.0:
        raise ValueError("omission_probability_out_of_range")

    successes = 0
    observations = 0
    failure_count = 0
    biopsies: list[dict] = []
    signatures: Counter[str] = Counter()

    for replicate in range(replicates):
        for case in corpus():
            if policy == "APPEND_TRUNCATE":
                indices = append_truncate_indices(case, budget)
                omitted: tuple[int, ...] = ()
            else:
                indices, omitted = noisy_key_aware_indices(
                    case,
                    budget,
                    replicate=replicate,
                    omission_probability=omission_probability,
                    seed=seed,
                )

            row = evaluate_case(case, indices)
            observations += 1
            successes += int(row["success"])

            if row["success"]:
                continue

            failure_count += 1
            signatures[_failure_signature(row)] += 1
            if len(biopsies) < MAX_BIOPSIES:
                biopsies.append(
                    {
                        "replicate": replicate,
                        "case": case.name,
                        "resident_indices": row["resident_indices"],
                        "omitted_required_indices": list(omitted),
                        "missing_required_keys": row["missing_required_keys"],
                        "stale_required_keys": row["stale_required_keys"],
                        "interference_events": row["interference_events"],
                    }
                )

    lower, upper = wilson_interval(successes, observations)
    exact_rate = successes / observations

    return {
        "policy": policy,
        "budget": budget,
        "replicates": replicates,
        "case_count": len(corpus()),
        "observations": observations,
        "success_count": successes,
        "failure_count": failure_count,
        "exact_rate": exact_rate,
        "wilson95": {
            "lower": lower,
            "upper": upper,
        },
        "knee_qualified": (
            exact_rate >= KNEE_EXACT_RATE
            and lower >= KNEE_WILSON_LOWER
        ),
        "failure_signatures": dict(sorted(signatures.items())),
        "failure_biopsies": biopsies,
    }


def first_qualified_budget(policy: str) -> int | None:
    for budget in BUDGETS:
        row = evaluate_replicated_policy(policy, budget)
        if row["knee_qualified"]:
            return budget
    return None


def run_panel() -> dict:
    rows = [
        evaluate_replicated_policy(policy, budget)
        for policy in ("APPEND_TRUNCATE", "NOISY_KEY_AWARE")
        for budget in BUDGETS
    ]

    knees = {
        "APPEND_TRUNCATE": first_qualified_budget("APPEND_TRUNCATE"),
        "NOISY_KEY_AWARE": first_qualified_budget("NOISY_KEY_AWARE"),
    }

    noisy_budget_two = next(
        row
        for row in rows
        if (
            row["policy"] == "NOISY_KEY_AWARE"
            and row["budget"] == 2
        )
    )

    result = {
        "schema": SCHEMA,
        "status": "PASS",
        "classification": (
            "STOCHASTIC_SEMANTIC_WORKING_SET_RARE_EVENT_HARNESS_VALIDATED"
        ),
        "synthetic_only": True,
        "empirical_model_claim": False,
        "seed": SEED,
        "replicates": REPLICATES,
        "omission_probability": OMISSION_PROBABILITY,
        "budgets": list(BUDGETS),
        "knee_rule": {
            "exact_rate_at_least": KNEE_EXACT_RATE,
            "wilson95_lower_at_least": KNEE_WILSON_LOWER,
        },
        "rows": rows,
        "qualified_knees": knees,
        "rare_event_probe": {
            "policy": "NOISY_KEY_AWARE",
            "budget": 2,
            "failure_count": noisy_budget_two["failure_count"],
            "observations": noisy_budget_two["observations"],
            "failure_rate": 1.0 - noisy_budget_two["exact_rate"],
            "captured_biopsy_count": len(
                noisy_budget_two["failure_biopsies"]
            ),
        },
        "claim_ceiling": (
            "SYNTHETIC_STOCHASTIC_SEMANTIC_WORKING_SET_ONLY"
        ),
    }

    if knees["APPEND_TRUNCATE"] != 8:
        raise RuntimeError("append_truncate_qualified_knee_unexpected")
    if knees["NOISY_KEY_AWARE"] != 2:
        raise RuntimeError("noisy_key_aware_qualified_knee_unexpected")
    if noisy_budget_two["failure_count"] <= 0:
        raise RuntimeError("rare_event_not_captured")
    if noisy_budget_two["failure_count"] >= (
        noisy_budget_two["observations"] * 0.05
    ):
        raise RuntimeError("rare_event_rate_too_high_for_fixture")

    return result


def main() -> int:
    print(json.dumps(run_panel(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
