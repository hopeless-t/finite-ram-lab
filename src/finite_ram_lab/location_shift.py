from __future__ import annotations

import argparse
from itertools import combinations
import json
from pathlib import Path
import statistics
from typing import Any, Iterable, Mapping


Q_VALUES = (1, 2, 4, 7)
FAMILY_ALPHA = 0.05
PER_Q_ALPHA = FAMILY_ALPHA / len(Q_VALUES)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def midranks(values: list[int]) -> list[float]:
    order = sorted(range(len(values)), key=values.__getitem__)
    ranks = [0.0] * len(values)
    cursor = 0
    while cursor < len(order):
        end = cursor + 1
        value = values[order[cursor]]
        while end < len(order) and values[order[end]] == value:
            end += 1
        # One-indexed average rank for positions cursor+1 .. end.
        rank = ((cursor + 1) + end) / 2.0
        for position in range(cursor, end):
            ranks[order[position]] = rank
        cursor = end
    return ranks


def exact_two_sided_rank_sum_p(
    reference: list[int],
    future: list[int],
) -> tuple[float, float, int]:
    if not reference or not future:
        raise ValueError("empty_group")

    pooled = reference + future
    ranks = midranks(pooled)
    future_size = len(future)
    future_start = len(reference)
    observed = sum(ranks[future_start:])

    expected = future_size * (len(pooled) + 1) / 2.0
    distance = abs(observed - expected)

    extreme = 0
    total = 0
    for indices in combinations(range(len(pooled)), future_size):
        statistic = sum(ranks[index] for index in indices)
        if abs(statistic - expected) >= distance - 1e-12:
            extreme += 1
        total += 1

    return extreme / total, observed, total


def analyze_location_shift(payload: Mapping[str, Any]) -> dict[str, Any]:
    if payload.get("schema") != "finite-ram-lab.location-shift-input/v0.1":
        raise RuntimeError("input_schema_invalid")

    refs = payload["reference_batches"]
    futures = payload["future_batches"]

    rows = []
    suspect_q = []

    for q in Q_VALUES:
        reference = [int(value) for value in refs[str(q)]]
        future = [int(value) for value in futures[str(q)]]
        p_value, rank_sum, permutation_count = exact_two_sided_rank_sum_p(
            reference,
            future,
        )
        ref_median = statistics.median(reference)
        future_median = statistics.median(future)
        median_delta = future_median - ref_median

        if p_value <= PER_Q_ALPHA:
            classification = (
                "LOCATION_SHIFT_UP_SUSPECT"
                if median_delta > 0
                else "LOCATION_SHIFT_DOWN_SUSPECT"
                if median_delta < 0
                else "LOCATION_SHAPE_SHIFT_SUSPECT"
            )
            suspect_q.append(q)
        else:
            classification = "LOCATION_COMPATIBLE"

        rows.append(
            {
                "q": q,
                "reference_sample_count": len(reference),
                "future_sample_count": len(future),
                "reference_median_peak_bytes": ref_median,
                "future_median_peak_bytes": future_median,
                "median_delta_bytes": median_delta,
                "future_rank_sum": rank_sum,
                "exact_permutation_count": permutation_count,
                "exact_two_sided_rank_sum_p": p_value,
                "family_alpha": FAMILY_ALPHA,
                "per_q_bonferroni_alpha": PER_Q_ALPHA,
                "classification": classification,
            }
        )

    overall = (
        "LOCATION_SHIFT_SUSPECT"
        if suspect_q
        else "NO_LOCATION_SHIFT_DETECTED"
    )

    return {
        "schema": "finite-ram-lab.location-shift-result/v0.1",
        "claim_ceiling": "SEED_CONFOUNDED_EXACT_PERMUTATION_LOCATION_DIAGNOSTIC",
        "overall": {
            "classification": overall,
            "suspect_q": suspect_q,
        },
        "rows": rows,
        "provenance": payload["provenance"],
        "caveat": payload["caveat"],
        "next_action": (
            "REPLAY_REFERENCE_AND_FUTURE_SEEDS_IN_CURRENT_ENVIRONMENT"
            if suspect_q
            else "CONTINUE_MONITORING"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    result = analyze_location_shift(_load(args.input))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
