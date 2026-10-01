from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import statistics
from typing import Any, Mapping


EXPECTED_BLOCKS = 8
FAMILY_ALPHA = 0.05
PER_TEST_ALPHA = FAMILY_ALPHA / 4.0


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _condition_median(block: Mapping[str, Any], q: int, seed: int) -> float:
    row = next(
        item for item in block["condition_summaries"]
        if int(item["q"]) == q and int(item["seed"]) == seed
    )
    return float(row["median_peak_bytes"])


def _one_sided_sign_p(deltas: list[float], direction: str) -> dict[str, Any]:
    nonzero = [value for value in deltas if value != 0]
    n = len(nonzero)
    if n == 0:
        return {"n_nonzero": 0, "favorable": 0, "p": 1.0}
    if direction == "positive":
        favorable = sum(value > 0 for value in nonzero)
    elif direction == "negative":
        favorable = sum(value < 0 for value in nonzero)
    else:
        raise ValueError("direction_invalid")
    tail = sum(math.comb(n, k) for k in range(favorable, n + 1)) / (2**n)
    return {"n_nonzero": n, "favorable": favorable, "p": tail}


def _two_sided_sign_p(deltas: list[float]) -> dict[str, Any]:
    nonzero = [value for value in deltas if value != 0]
    n = len(nonzero)
    if n == 0:
        return {"n_nonzero": 0, "positive": 0, "p": 1.0}
    positive = sum(value > 0 for value in nonzero)
    lower = sum(math.comb(n, k) for k in range(0, positive + 1)) / (2**n)
    upper = sum(math.comb(n, k) for k in range(positive, n + 1)) / (2**n)
    return {
        "n_nonzero": n,
        "positive": positive,
        "p": min(1.0, 2.0 * min(lower, upper)),
    }


def analyze_runner_blocks(
    blocks: list[Mapping[str, Any]],
    reference_input: Mapping[str, Any],
) -> dict[str, Any]:
    if len(blocks) != EXPECTED_BLOCKS:
        raise RuntimeError("runner_block_count_invalid")
    ids = sorted(int(block["block_id"]) for block in blocks)
    if ids != list(range(EXPECTED_BLOCKS)):
        raise RuntimeError("runner_block_ids_invalid")
    if reference_input.get("schema") != "finite-ram-lab.location-shift-input/v0.1":
        raise RuntimeError("reference_input_schema_invalid")

    historical = {
        2: statistics.median(
            int(v) for v in reference_input["reference_batches"]["2"]
        ),
        4: statistics.median(
            int(v) for v in reference_input["reference_batches"]["4"]
        ),
    }

    block_rows = []
    q2_seed_deltas = []
    q4_seed_deltas = []
    q2_temporal_deltas = []
    q4_temporal_deltas = []

    for block in sorted(blocks, key=lambda item: int(item["block_id"])):
        q2_474 = _condition_median(block, 2, 474)
        q2_476 = _condition_median(block, 2, 476)
        q4_474 = _condition_median(block, 4, 474)
        q4_476 = _condition_median(block, 4, 476)

        q2_seed = q2_476 - q2_474
        q4_seed = q4_476 - q4_474
        q2_temporal = q2_474 - historical[2]
        q4_temporal = q4_474 - historical[4]

        q2_seed_deltas.append(q2_seed)
        q4_seed_deltas.append(q4_seed)
        q2_temporal_deltas.append(q2_temporal)
        q4_temporal_deltas.append(q4_temporal)

        block_rows.append(
            {
                "block_id": int(block["block_id"]),
                "runner_name": block["environment"].get("runner_name"),
                "image_os": block["environment"].get("image_os"),
                "image_version": block["environment"].get("image_version"),
                "cpu_model": block["environment"].get("cpu_model"),
                "mem_total": block["environment"].get("mem_total"),
                "q2_seed474_median_peak_bytes": q2_474,
                "q2_seed476_median_peak_bytes": q2_476,
                "q2_seed_delta_476_minus_474_bytes": q2_seed,
                "q2_temporal_delta_474_vs_historical_bytes": q2_temporal,
                "q4_seed474_median_peak_bytes": q4_474,
                "q4_seed476_median_peak_bytes": q4_476,
                "q4_seed_delta_476_minus_474_bytes": q4_seed,
                "q4_temporal_delta_474_vs_historical_bytes": q4_temporal,
            }
        )

    tests = {
        "q2_seed_negative": _one_sided_sign_p(q2_seed_deltas, "negative"),
        "q4_seed_negative": _one_sided_sign_p(q4_seed_deltas, "negative"),
        "q2_temporal_positive": _one_sided_sign_p(q2_temporal_deltas, "positive"),
        "q4_temporal_two_sided": _two_sided_sign_p(q4_temporal_deltas),
    }
    for value in tests.values():
        value["significant"] = value["p"] <= PER_TEST_ALPHA

    classifications = {
        "q2_seed_effect_replicated": tests["q2_seed_negative"]["significant"],
        "q4_seed_effect_replicated": tests["q4_seed_negative"]["significant"],
        "q2_temporal_shift_replicated": tests["q2_temporal_positive"]["significant"],
        "q4_temporal_shift_detected": tests["q4_temporal_two_sided"]["significant"],
    }

    return {
        "schema": "finite-ram-lab.runner-block-aggregate/v0.1",
        "claim_ceiling": "GITHUB_HOSTED_JOB_BLOCK_FACTORIAL_REPLICATION",
        "runner_block_count": EXPECTED_BLOCKS,
        "family_alpha": FAMILY_ALPHA,
        "per_test_bonferroni_alpha": PER_TEST_ALPHA,
        "historical_seed474_median_peak_bytes": {
            "q2": historical[2],
            "q4": historical[4],
        },
        "block_rows": block_rows,
        "delta_summaries": {
            "q2_seed_delta_median_bytes": statistics.median(q2_seed_deltas),
            "q4_seed_delta_median_bytes": statistics.median(q4_seed_deltas),
            "q2_temporal_delta_median_bytes": statistics.median(q2_temporal_deltas),
            "q4_temporal_delta_median_bytes": statistics.median(q4_temporal_deltas),
            "q2_seed474_block_median_range_bytes": (
                max(row["q2_seed474_median_peak_bytes"] for row in block_rows)
                - min(row["q2_seed474_median_peak_bytes"] for row in block_rows)
            ),
            "q4_seed474_block_median_range_bytes": (
                max(row["q4_seed474_median_peak_bytes"] for row in block_rows)
                - min(row["q4_seed474_median_peak_bytes"] for row in block_rows)
            ),
        },
        "tests": tests,
        "classifications": classifications,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--blocks-dir", type=Path, required=True)
    parser.add_argument("--reference-input", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    blocks = [
        json.loads(path.read_text())
        for path in sorted(args.blocks_dir.glob("block-*.json"))
    ]
    result = analyze_runner_blocks(blocks, _load(args.reference_input))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
