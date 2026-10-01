from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics
from typing import Any, Mapping

from finite_ram_lab.center_temporary_probe import (
    COUNT_HIGH,
    COUNT_LOW,
    COUNT_SEED474,
    COUNT_SEED476,
    EXPECTED_ACTUAL_PAIR_PAYLOAD_DELTA_BYTES,
)
from finite_ram_lab.runner_block_aggregate import _one_sided_sign_p
from finite_ram_lab.three_phase_hwm_aggregate import holm_decisions


EXPECTED_BLOCKS = 8
FAMILY_ALPHA = 0.05


def _condition(block: Mapping[str, Any], count: int) -> Mapping[str, Any]:
    return next(
        row for row in block["condition_summaries"]
        if int(row["selected_count"]) == count
    )


def analyze(blocks: list[Mapping[str, Any]]) -> dict[str, Any]:
    if len(blocks) != EXPECTED_BLOCKS:
        raise RuntimeError("runner_block_count_invalid")
    blocks = sorted(blocks, key=lambda item: int(item["block_id"]))
    if [int(block["block_id"]) for block in blocks] != list(range(EXPECTED_BLOCKS)):
        raise RuntimeError("runner_block_ids_invalid")

    actual_deltas = []
    span_deltas = []
    slopes = []
    rss_actual_deltas = []
    rows = []

    for block in blocks:
        low = _condition(block, COUNT_LOW)
        s476 = _condition(block, COUNT_SEED476)
        s474 = _condition(block, COUNT_SEED474)
        high = _condition(block, COUNT_HIGH)

        actual_delta = (
            float(s476["median_hwm_growth_bytes"])
            - float(s474["median_hwm_growth_bytes"])
        )
        span_delta = (
            float(high["median_hwm_growth_bytes"])
            - float(low["median_hwm_growth_bytes"])
        )
        slope = span_delta / (COUNT_HIGH - COUNT_LOW)
        rss_delta = (
            float(s476["median_rss_delta_bytes"])
            - float(s474["median_rss_delta_bytes"])
        )

        actual_deltas.append(actual_delta)
        span_deltas.append(span_delta)
        slopes.append(slope)
        rss_actual_deltas.append(rss_delta)

        rows.append({
            "block_id": int(block["block_id"]),
            "runner_name": block["environment"].get("runner_name"),
            "cpu_model": block["environment"].get("cpu_model"),
            "actual_pair_hwm_delta_bytes": actual_delta,
            "expected_actual_pair_payload_delta_bytes": EXPECTED_ACTUAL_PAIR_PAYLOAD_DELTA_BYTES,
            "actual_pair_prediction_error_bytes": (
                actual_delta - EXPECTED_ACTUAL_PAIR_PAYLOAD_DELTA_BYTES
            ),
            "low_high_hwm_delta_bytes": span_delta,
            "bytes_hwm_per_selected_element": slope,
            "actual_pair_rss_delta_bytes": rss_delta,
        })

    raw_tests = {
        "actual_pair_hwm_negative": _one_sided_sign_p(actual_deltas, "negative"),
        "span_hwm_positive": _one_sided_sign_p(span_deltas, "positive"),
    }
    holm = holm_decisions(
        {name: float(result["p"]) for name, result in raw_tests.items()},
        FAMILY_ALPHA,
    )
    tests = {
        name: {**result, "holm_significant": holm[name]}
        for name, result in raw_tests.items()
    }

    median_actual = statistics.median(actual_deltas)
    median_slope = statistics.median(slopes)
    median_abs_error = statistics.median(
        abs(value - EXPECTED_ACTUAL_PAIR_PAYLOAD_DELTA_BYTES)
        for value in actual_deltas
    )
    relative_payload_error = (
        median_abs_error / abs(EXPECTED_ACTUAL_PAIR_PAYLOAD_DELTA_BYTES)
    )

    mechanism_supported = (
        tests["actual_pair_hwm_negative"]["holm_significant"]
        and tests["span_hwm_positive"]["holm_significant"]
        and 6.0 <= median_slope <= 10.0
        and relative_payload_error <= 0.25
    )

    return {
        "schema": "finite-ram-lab.center-temporary-aggregate/v0.1",
        "claim_ceiling": "ISOLATED_NUMPY_BOOLEAN_INDEX_CENTERING",
        "runner_block_count": EXPECTED_BLOCKS,
        "family_alpha": FAMILY_ALPHA,
        "expected_actual_pair_payload_delta_bytes": EXPECTED_ACTUAL_PAIR_PAYLOAD_DELTA_BYTES,
        "block_rows": rows,
        "tests": tests,
        "summary": {
            "median_actual_pair_hwm_delta_bytes": median_actual,
            "median_actual_pair_rss_delta_bytes": statistics.median(rss_actual_deltas),
            "median_bytes_hwm_per_selected_element": median_slope,
            "median_abs_prediction_error_bytes": median_abs_error,
            "median_relative_payload_prediction_error": relative_payload_error,
            "mechanism_supported": mechanism_supported,
        },
        "classification": (
            "BOOLEAN_INDEX_TEMPORARY_MECHANISM_SUPPORTED"
            if mechanism_supported
            else "CENTERING_MECHANISM_NOT_YET_RESOLVED"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--blocks-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    blocks = [
        json.loads(path.read_text())
        for path in sorted(args.blocks_dir.glob("block-*.json"))
    ]
    result = analyze(blocks)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
