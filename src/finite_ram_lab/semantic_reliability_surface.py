from __future__ import annotations

from collections import Counter
import hashlib
import json
import math

from finite_ram_lab.semantic_working_set import (
    BUDGETS,
    Case,
    corpus,
    evaluate_case,
)


SCHEMA = "finite-ram-lab.semantic-reliability-surface/v0.1"
SEED = 20261002
REPLICATES = 2048
ERROR_PROBABILITIES = (
    0.0,
    0.001,
    0.0025,
    0.005,
    0.01,
    0.02,
    0.03,
    0.05,
    0.10,
    0.20,
)
WILSON_Z_95 = 1.959963984540054
KNEE_EXACT_RATE = 0.95
KNEE_WILSON_LOWER = 0.95
MAX_BIOPSIES = 8


def _uniform01(*parts: object) -> float:
    payload = "|".join(str(part) for part in parts).encode("utf-8")
    digest = hashlib.sha256(payload).digest()
    return int.from_bytes(digest[:8], "big") / 2**64


def _required_latest_indices(case: Case) -> set[int]:
    out: set[int] = set()
    for key in case.query_keys:
        for index in range(len(case.events) - 1, -1, -1):
            if case.events[index].key == key:
                out.add(index)
                break
    return out


def noisy_relevance_indices(
    case: Case,
    budget: int,
    *,
    replicate: int,
    error_probability: float,
    seed: int = SEED,
) -> tuple[tuple[int, ...], dict]:
    """Select a finite semantic working set with symmetric label noise.

    Ground-truth relevant events are the latest values for the query keys.
    Every event's relevant/irrelevant label is independently flipped with the
    frozen error probability. Predicted-relevant events rank first; recency is
    the deterministic tie-breaker.

    Unlike FR-CLM-001B's hard omission fixture, a larger resident budget can
    recover from ranking mistakes by admitting additional events.
    """
    if budget <= 0:
        return (), {
            "required_latest_indices": [],
            "false_negative_required_indices": [],
            "false_positive_distractor_indices": [],
        }
    if not 0.0 <= error_probability <= 1.0:
        raise ValueError("error_probability_out_of_range")

    required = _required_latest_indices(case)
    ranked: list[tuple[int, int]] = []
    false_negatives: list[int] = []
    false_positives: list[int] = []

    for index in range(len(case.events)):
        true_relevant = index in required
        flip = (
            _uniform01(
                seed,
                "SCORE_FLIP",
                error_probability,
                budget,
                replicate,
                case.name,
                index,
            )
            < error_probability
        )
        predicted_relevant = (
            not true_relevant if flip else true_relevant
        )

        if true_relevant and not predicted_relevant:
            false_negatives.append(index)
        elif not true_relevant and predicted_relevant:
            false_positives.append(index)

        ranked.append((1 if predicted_relevant else 0, index))

    ranked.sort(key=lambda item: (item[0], item[1]), reverse=True)
    selected = tuple(
        sorted(index for _, index in ranked[: min(budget, len(ranked))])
    )

    diagnostics = {
        "required_latest_indices": sorted(required),
        "false_negative_required_indices": false_negatives,
        "false_positive_distractor_indices": false_positives,
    }
    return selected, diagnostics


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


def evaluate_surface_cell(
    error_probability: float,
    budget: int,
    *,
    replicates: int = REPLICATES,
    seed: int = SEED,
) -> dict:
    if error_probability not in ERROR_PROBABILITIES:
        raise ValueError("unfrozen_error_probability")
    if budget not in BUDGETS:
        raise ValueError("unfrozen_budget")
    if replicates <= 0:
        raise ValueError("replicates_must_be_positive")

    successes = 0
    observations = 0
    false_negative_events = 0
    false_positive_events = 0
    biopsies: list[dict] = []
    signatures: Counter[str] = Counter()

    for replicate in range(replicates):
        for case in corpus():
            indices, diagnostics = noisy_relevance_indices(
                case,
                budget,
                replicate=replicate,
                error_probability=error_probability,
                seed=seed,
            )
            row = evaluate_case(case, indices)
            observations += 1
            successes += int(row["success"])
            false_negative_events += len(
                diagnostics["false_negative_required_indices"]
            )
            false_positive_events += len(
                diagnostics["false_positive_distractor_indices"]
            )

            if row["success"]:
                continue

            signatures[_failure_signature(row)] += 1
            if len(biopsies) < MAX_BIOPSIES:
                biopsies.append(
                    {
                        "replicate": replicate,
                        "case": case.name,
                        "resident_indices": row["resident_indices"],
                        "required_latest_indices": diagnostics[
                            "required_latest_indices"
                        ],
                        "false_negative_required_indices": diagnostics[
                            "false_negative_required_indices"
                        ],
                        "false_positive_distractor_indices": diagnostics[
                            "false_positive_distractor_indices"
                        ],
                        "missing_required_keys": row[
                            "missing_required_keys"
                        ],
                        "stale_required_keys": row[
                            "stale_required_keys"
                        ],
                        "interference_events": row[
                            "interference_events"
                        ],
                    }
                )

    lower, upper = wilson_interval(successes, observations)
    exact_rate = successes / observations

    return {
        "error_probability": error_probability,
        "selector_reliability": 1.0 - error_probability,
        "budget": budget,
        "replicates": replicates,
        "case_count": len(corpus()),
        "observations": observations,
        "success_count": successes,
        "failure_count": observations - successes,
        "exact_rate": exact_rate,
        "wilson95": {
            "lower": lower,
            "upper": upper,
        },
        "qualified": (
            exact_rate >= KNEE_EXACT_RATE
            and lower >= KNEE_WILSON_LOWER
        ),
        "false_negative_required_events": false_negative_events,
        "false_positive_distractor_events": false_positive_events,
        "failure_signatures": dict(sorted(signatures.items())),
        "failure_biopsies": biopsies,
    }


def run_surface() -> dict:
    rows = [
        evaluate_surface_cell(error_probability, budget)
        for error_probability in ERROR_PROBABILITIES
        for budget in BUDGETS
    ]

    frontier: dict[str, int | None] = {}
    for error_probability in ERROR_PROBABILITIES:
        qualified_budget = next(
            (
                row["budget"]
                for row in rows
                if (
                    row["error_probability"] == error_probability
                    and row["qualified"]
                )
            ),
            None,
        )
        frontier[str(error_probability)] = qualified_budget

    expected_frontier = {
        "0.0": 2,
        "0.001": 2,
        "0.0025": 2,
        "0.005": 2,
        "0.01": 2,
        "0.02": 4,
        "0.03": 4,
        "0.05": 6,
        "0.1": 8,
        "0.2": 8,
    }

    sentinel = next(
        row
        for row in rows
        if (
            row["error_probability"] == 0.001
            and row["budget"] == 2
        )
    )

    full_budget_rows = [
        row for row in rows if row["budget"] == max(BUDGETS)
    ]

    result = {
        "schema": SCHEMA,
        "status": "PASS",
        "classification": (
            "SYNTHETIC_RELIABILITY_RESIDENCY_SURFACE_VALIDATED"
        ),
        "synthetic_only": True,
        "empirical_model_claim": False,
        "seed": SEED,
        "replicates": REPLICATES,
        "error_probabilities": list(ERROR_PROBABILITIES),
        "budgets": list(BUDGETS),
        "observations_per_cell": REPLICATES * len(corpus()),
        "qualified_rule": {
            "exact_rate_at_least": KNEE_EXACT_RATE,
            "wilson95_lower_at_least": KNEE_WILSON_LOWER,
        },
        "rows": rows,
        "minimum_qualified_budget_by_error": frontier,
        "rare_event_sentinel": {
            "error_probability": 0.001,
            "budget": 2,
            "failure_count": sentinel["failure_count"],
            "exact_rate": sentinel["exact_rate"],
            "wilson95_lower": sentinel["wilson95"]["lower"],
            "captured_biopsy_count": len(
                sentinel["failure_biopsies"]
            ),
        },
        "claim_ceiling": (
            "SYNTHETIC_RELIABILITY_RESIDENCY_SURFACE_ONLY"
        ),
    }

    if frontier != expected_frontier:
        raise RuntimeError("reliability_residency_frontier_unexpected")
    if sentinel["failure_count"] != 30:
        raise RuntimeError("rare_event_sentinel_count_unexpected")
    if sentinel["wilson95"]["lower"] < KNEE_WILSON_LOWER:
        raise RuntimeError("rare_event_sentinel_not_qualified")
    if any(row["exact_rate"] != 1.0 for row in full_budget_rows):
        raise RuntimeError("full_residency_reference_failed")

    return result


def main() -> int:
    print(json.dumps(run_surface(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
