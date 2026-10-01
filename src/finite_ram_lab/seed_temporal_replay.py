from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics
from typing import Any, Mapping

from finite_ram_lab.lane_concurrency_sweep import _run_fresh_child
from finite_ram_lab.location_shift import exact_two_sided_rank_sum_p


Q_VALUES = (2, 4)
SEEDS = (474, 476)
REPETITIONS_PER_CONDITION = 8
FAMILY_ALPHA = 0.05
PER_TEST_ALPHA = FAMILY_ALPHA / 4.0

# Four conditions:
# A=(q2,s474), B=(q2,s476), C=(q4,s474), D=(q4,s476)
BALANCED_ORDERS = (
    ((2,474),(2,476),(4,474),(4,476)),
    ((4,476),(4,474),(2,476),(2,474)),
    ((2,476),(2,474),(4,476),(4,474)),
    ((4,474),(4,476),(2,474),(2,476)),
    ((2,474),(2,476),(4,474),(4,476)),
    ((4,476),(4,474),(2,476),(2,474)),
    ((2,476),(2,474),(4,476),(4,474)),
    ((4,474),(4,476),(2,474),(2,476)),
)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _historical_seed474(reference_input: Mapping[str, Any], q: int) -> list[int]:
    if reference_input.get("schema") != "finite-ram-lab.location-shift-input/v0.1":
        raise RuntimeError("reference_input_schema_invalid")
    if q not in Q_VALUES:
        raise ValueError("q_invalid")
    return [int(value) for value in reference_input["reference_batches"][str(q)]]


def _classify_factor(
    *,
    temporal_p: float,
    seed_p: float,
    current_seed474_median: float,
    current_seed476_median: float,
    historical_seed474_median: float,
) -> str:
    temporal_sig = temporal_p <= PER_TEST_ALPHA
    seed_sig = seed_p <= PER_TEST_ALPHA

    if temporal_sig and seed_sig:
        return "MIXED_TEMPORAL_AND_SEED_SHIFT_SUSPECT"
    if temporal_sig:
        return "TEMPORAL_RUNNER_SHIFT_SUSPECT"
    if seed_sig:
        return "WORKLOAD_SEED_EFFECT_SUSPECT"
    return "NO_FACTOR_SHIFT_RESOLVED"


def run_seed_temporal_replay(
    reference_input: Mapping[str, Any],
    *,
    repetitions: int = REPETITIONS_PER_CONDITION,
    size: int = 2048,
    value_limit: int = 50,
    tile_rows: int = 64,
) -> dict[str, Any]:
    if repetitions != REPETITIONS_PER_CONDITION:
        raise ValueError("b478_requires_eight_per_condition")

    observations: dict[tuple[int,int], list[dict[str, Any]]] = {
        (q, seed): [] for q in Q_VALUES for seed in SEEDS
    }
    execution_rows = []

    for repetition, order in enumerate(BALANCED_ORDERS):
        row = {
            "repetition": repetition,
            "order": [
                {"q": q, "seed": seed}
                for q, seed in order
            ],
            "results": [],
        }
        for q, seed in order:
            result = _run_fresh_child(
                q=q,
                size=size,
                lane_count=7,
                seed=seed,
                value_limit=value_limit,
                tile_rows=tile_rows,
            )
            if not result["semantic_exact"]:
                raise RuntimeError(
                    f"semantic_gate_failed:q={q}:seed={seed}:rep={repetition}"
                )
            item = {
                "q": q,
                "seed": seed,
                "repetition": repetition,
                "observed_peak_bytes": int(result["normalized_peak_growth_bytes"]),
                "work_seconds": float(result["work_seconds"]),
                "output_sha256": result["output_sha256"],
            }
            observations[(q,seed)].append(item)
            row["results"].append(item)
        execution_rows.append(row)

    # Different seeds intentionally produce different exact numerical outputs.
    # Within each (q,seed), output must remain deterministic across repetitions.
    digest_by_condition = {}
    for condition, values in observations.items():
        digests = {item["output_sha256"] for item in values}
        if len(digests) != 1:
            raise RuntimeError(f"condition_output_digest_mismatch:{condition}")
        digest_by_condition[f"q{condition[0]}_seed{condition[1]}"] = next(iter(digests))

    rows = []
    suspect_q = []
    for q in Q_VALUES:
        historical = _historical_seed474(reference_input, q)
        current474 = [
            item["observed_peak_bytes"] for item in observations[(q,474)]
        ]
        current476 = [
            item["observed_peak_bytes"] for item in observations[(q,476)]
        ]

        temporal_p, _, temporal_permutations = exact_two_sided_rank_sum_p(
            historical,
            current474,
        )
        seed_p, _, seed_permutations = exact_two_sided_rank_sum_p(
            current474,
            current476,
        )

        historical_median = statistics.median(historical)
        current474_median = statistics.median(current474)
        current476_median = statistics.median(current476)

        classification = _classify_factor(
            temporal_p=temporal_p,
            seed_p=seed_p,
            current_seed474_median=current474_median,
            current_seed476_median=current476_median,
            historical_seed474_median=historical_median,
        )
        if classification != "NO_FACTOR_SHIFT_RESOLVED":
            suspect_q.append(q)

        rows.append(
            {
                "q": q,
                "historical_seed474_sample_count": len(historical),
                "current_seed474_sample_count": len(current474),
                "current_seed476_sample_count": len(current476),
                "historical_seed474_median_peak_bytes": historical_median,
                "current_seed474_median_peak_bytes": current474_median,
                "current_seed476_median_peak_bytes": current476_median,
                "temporal_delta_current474_minus_historical474_bytes": (
                    current474_median - historical_median
                ),
                "seed_delta_current476_minus_current474_bytes": (
                    current476_median - current474_median
                ),
                "temporal_exact_two_sided_p": temporal_p,
                "seed_exact_two_sided_p": seed_p,
                "temporal_permutation_count": temporal_permutations,
                "seed_permutation_count": seed_permutations,
                "family_alpha": FAMILY_ALPHA,
                "per_test_bonferroni_alpha": PER_TEST_ALPHA,
                "classification": classification,
                "current_seed474_peak_bytes": current474,
                "current_seed476_peak_bytes": current476,
            }
        )

    if suspect_q:
        overall = "FACTOR_SHIFT_SUSPECT"
    else:
        overall = "NO_FACTOR_SHIFT_RESOLVED"

    return {
        "schema": "finite-ram-lab.seed-temporal-replay/v0.1",
        "claim_ceiling": "TWO_FACTOR_BOUNDED_REPLAY_DIAGNOSTIC",
        "q_values": list(Q_VALUES),
        "seeds": list(SEEDS),
        "repetitions_per_condition": repetitions,
        "total_new_observations": repetitions * len(Q_VALUES) * len(SEEDS),
        "balanced_orders": [
            [{"q": q, "seed": seed} for q, seed in order]
            for order in BALANCED_ORDERS
        ],
        "family_alpha": FAMILY_ALPHA,
        "per_test_bonferroni_alpha": PER_TEST_ALPHA,
        "size": size,
        "value_limit": value_limit,
        "tile_rows": tile_rows,
        "digest_by_condition": digest_by_condition,
        "execution_rows": execution_rows,
        "rows": rows,
        "overall": {
            "classification": overall,
            "suspect_q": suspect_q,
        },
        "interpretation_rule": {
            "temporal_only": "TEMPORAL_RUNNER_SHIFT_SUSPECT",
            "seed_only": "WORKLOAD_SEED_EFFECT_SUSPECT",
            "both": "MIXED_TEMPORAL_AND_SEED_SHIFT_SUSPECT",
            "neither": "NO_FACTOR_SHIFT_RESOLVED"
        }
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference-input", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--repetitions", type=int, default=REPETITIONS_PER_CONDITION)
    parser.add_argument("--size", type=int, default=2048)
    args = parser.parse_args()

    payload = run_seed_temporal_replay(
        _load(args.reference_input),
        repetitions=args.repetitions,
        size=args.size,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"overall": payload["overall"], "rows": payload["rows"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
