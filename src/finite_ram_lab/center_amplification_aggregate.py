from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics
from typing import Any, Mapping

from finite_ram_lab.center_amplification_probe import (
    BASE_DIFF,
    MULTIPLIERS,
    count_pair,
)
from finite_ram_lab.runner_block_aggregate import _one_sided_sign_p
from finite_ram_lab.three_phase_hwm_aggregate import holm_decisions


EXPECTED_BLOCKS = 8
FAMILY_ALPHA = 0.05


def _result(block: Mapping[str, Any], multiplier: int, side: str) -> Mapping[str, Any]:
    return next(
        item for item in block["results"]
        if int(item["multiplier"]) == multiplier and item["side"] == side
    )


def analyze(blocks: list[Mapping[str, Any]]) -> dict[str, Any]:
    if len(blocks) != EXPECTED_BLOCKS:
        raise RuntimeError("runner_block_count_invalid")
    blocks = sorted(blocks, key=lambda item: int(item["block_id"]))
    if [int(block["block_id"]) for block in blocks] != list(range(EXPECTED_BLOCKS)):
        raise RuntimeError("runner_block_ids_invalid")

    per_multiplier: dict[int, dict[str, Any]] = {}
    raw_tests = {}

    for multiplier in MULTIPLIERS:
        low_count, high_count = count_pair(multiplier)
        selected_delta = low_count - high_count
        expected_hwm_delta = selected_delta * 8

        block_deltas = []
        rss_deltas = []
        for block in blocks:
            low = _result(block, multiplier, "low")
            high = _result(block, multiplier, "high")
            block_deltas.append(
                float(low["hwm_growth_bytes"]) - float(high["hwm_growth_bytes"])
            )
            rss_deltas.append(
                float(low["rss_delta_bytes"]) - float(high["rss_delta_bytes"])
            )

        raw_tests[f"k{multiplier}_negative"] = _one_sided_sign_p(
            block_deltas, "negative"
        )
        median_delta = statistics.median(block_deltas)
        slope = median_delta / selected_delta
        rel_error = abs(median_delta - expected_hwm_delta) / abs(expected_hwm_delta)

        per_multiplier[multiplier] = {
            "multiplier": multiplier,
            "low_count": low_count,
            "high_count": high_count,
            "selected_count_delta": selected_delta,
            "expected_hwm_delta_bytes": expected_hwm_delta,
            "block_hwm_deltas_bytes": block_deltas,
            "median_hwm_delta_bytes": median_delta,
            "median_rss_delta_bytes": statistics.median(rss_deltas),
            "bytes_hwm_per_selected_element": slope,
            "relative_prediction_error": rel_error,
        }

    holm = holm_decisions(
        {name: float(result["p"]) for name, result in raw_tests.items()},
        FAMILY_ALPHA,
    )
    tests = {
        name: {**result, "holm_significant": holm[name]}
        for name, result in raw_tests.items()
    }

    median_effects = [
        abs(per_multiplier[m]["median_hwm_delta_bytes"])
        for m in MULTIPLIERS
    ]
    monotonic = all(
        later > earlier
        for earlier, later in zip(median_effects, median_effects[1:])
    )
    slopes = [
        float(per_multiplier[m]["bytes_hwm_per_selected_element"])
        for m in MULTIPLIERS
    ]
    all_directional = all(tests[f"k{m}_negative"]["holm_significant"] for m in MULTIPLIERS)
    all_slopes_close = all(6.0 <= slope <= 10.0 for slope in slopes)
    amplified_errors_close = all(
        per_multiplier[m]["relative_prediction_error"] <= 0.15
        for m in (2,4,8)
    )

    supported = (
        all_directional
        and monotonic
        and all_slopes_close
        and amplified_errors_close
    )

    return {
        "schema": "finite-ram-lab.center-amplification-aggregate/v0.1",
        "claim_ceiling": "ISOLATED_CENTER_SELECTED_COUNT_AMPLIFICATION",
        "runner_block_count": EXPECTED_BLOCKS,
        "family_alpha": FAMILY_ALPHA,
        "base_selected_count_difference": BASE_DIFF,
        "tests": tests,
        "series": [per_multiplier[m] for m in MULTIPLIERS],
        "summary": {
            "monotonic_effect_magnitude": monotonic,
            "median_slopes_bytes_per_selected_element": slopes,
            "median_slope_bytes_per_selected_element": statistics.median(slopes),
            "all_directional_tests_holm_significant": all_directional,
            "all_slopes_between_6_and_10": all_slopes_close,
            "k2_k4_k8_relative_error_le_15pct": amplified_errors_close,
            "mechanism_supported": supported,
        },
        "classification": (
            "BOOLEAN_INDEX_TEMPORARY_MECHANISM_CONFIRMED"
            if supported
            else "AMPLIFICATION_SERIES_INCONCLUSIVE"
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
