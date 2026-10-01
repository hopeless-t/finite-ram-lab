from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics
from typing import Any, Mapping

from finite_ram_lab.center_repair import (
    COUNT_HIGH,
    COUNT_SEED474,
    COUNT_SEED476,
)
from finite_ram_lab.runner_block_aggregate import _one_sided_sign_p
from finite_ram_lab.three_phase_hwm_aggregate import holm_decisions


EXPECTED_BLOCKS = 8
FAMILY_ALPHA = 0.05


def _result(
    block: Mapping[str, Any],
    strategy: str,
    count: int,
) -> Mapping[str, Any]:
    return next(
        item for item in block["results"]
        if item["strategy"] == strategy and int(item["selected_count"]) == count
    )


def analyze(blocks: list[Mapping[str, Any]]) -> dict[str, Any]:
    if len(blocks) != EXPECTED_BLOCKS:
        raise RuntimeError("runner_block_count_invalid")
    blocks = sorted(blocks, key=lambda item: int(item["block_id"]))
    if [int(block["block_id"]) for block in blocks] != list(range(EXPECTED_BLOCKS)):
        raise RuntimeError("runner_block_ids_invalid")

    repair_peak_savings_high = []
    repair_peak_savings_474 = []
    old_content_delta = []
    new_content_delta = []
    latency_ratios_high = []
    new_span_delta = []
    block_rows = []

    for block in blocks:
        old476 = _result(block, "BOOLEAN_INDEX", COUNT_SEED476)
        old474 = _result(block, "BOOLEAN_INDEX", COUNT_SEED474)
        oldhigh = _result(block, "BOOLEAN_INDEX", COUNT_HIGH)
        new476 = _result(block, "TILED_WHERE", COUNT_SEED476)
        new474 = _result(block, "TILED_WHERE", COUNT_SEED474)
        newhigh = _result(block, "TILED_WHERE", COUNT_HIGH)

        old_pair = float(old476["hwm_growth_bytes"]) - float(old474["hwm_growth_bytes"])
        new_pair = float(new476["hwm_growth_bytes"]) - float(new474["hwm_growth_bytes"])
        save_high = float(oldhigh["hwm_growth_bytes"]) - float(newhigh["hwm_growth_bytes"])
        save_474 = float(old474["hwm_growth_bytes"]) - float(new474["hwm_growth_bytes"])
        ratio_high = float(newhigh["elapsed_seconds"]) / max(float(oldhigh["elapsed_seconds"]), 1e-12)
        new_span = float(newhigh["hwm_growth_bytes"]) - float(new476["hwm_growth_bytes"])

        old_content_delta.append(old_pair)
        new_content_delta.append(new_pair)
        repair_peak_savings_high.append(save_high)
        repair_peak_savings_474.append(save_474)
        latency_ratios_high.append(ratio_high)
        new_span_delta.append(new_span)

        block_rows.append({
            "block_id": int(block["block_id"]),
            "runner_name": block["environment"].get("runner_name"),
            "cpu_model": block["environment"].get("cpu_model"),
            "old_content_pair_hwm_delta_bytes": old_pair,
            "new_content_pair_hwm_delta_bytes": new_pair,
            "peak_savings_at_seed474_count_bytes": save_474,
            "peak_savings_at_high_count_bytes": save_high,
            "new_high_over_476_hwm_delta_bytes": new_span,
            "latency_ratio_tiled_over_old_high_count": ratio_high,
            "old_high_elapsed_seconds": float(oldhigh["elapsed_seconds"]),
            "new_high_elapsed_seconds": float(newhigh["elapsed_seconds"]),
            "old_high_rss_delta_bytes": int(oldhigh["rss_delta_bytes"]),
            "new_high_rss_delta_bytes": int(newhigh["rss_delta_bytes"]),
        })

    raw_tests = {
        "repair_saves_peak_high": _one_sided_sign_p(repair_peak_savings_high, "positive"),
        "repair_saves_peak_474": _one_sided_sign_p(repair_peak_savings_474, "positive"),
        "old_content_pair_negative": _one_sided_sign_p(old_content_delta, "negative"),
    }
    holm = holm_decisions(
        {name: float(result["p"]) for name, result in raw_tests.items()},
        FAMILY_ALPHA,
    )
    tests = {
        name: {**result, "holm_significant": holm[name]}
        for name, result in raw_tests.items()
    }

    median_new_content_abs = abs(statistics.median(new_content_delta))
    median_new_span_abs = abs(statistics.median(new_span_delta))
    median_saving_high = statistics.median(repair_peak_savings_high)
    median_saving_474 = statistics.median(repair_peak_savings_474)
    median_latency_ratio = statistics.median(latency_ratios_high)

    qualified = (
        tests["repair_saves_peak_high"]["holm_significant"]
        and tests["repair_saves_peak_474"]["holm_significant"]
        and median_saving_high >= 16 * 1024 * 1024
        and median_saving_474 >= 12 * 1024 * 1024
        and median_new_content_abs <= 128 * 1024
        and median_new_span_abs <= 1024 * 1024
        and median_latency_ratio <= 2.0
    )

    return {
        "schema": "finite-ram-lab.center-repair-aggregate/v0.1",
        "claim_ceiling": "ISOLATED_EXACT_CENTER_REPAIR",
        "runner_block_count": EXPECTED_BLOCKS,
        "family_alpha": FAMILY_ALPHA,
        "block_rows": block_rows,
        "tests": tests,
        "summary": {
            "median_old_content_pair_hwm_delta_bytes": statistics.median(old_content_delta),
            "median_new_content_pair_hwm_delta_bytes": statistics.median(new_content_delta),
            "median_peak_savings_at_seed474_count_bytes": median_saving_474,
            "median_peak_savings_at_high_count_bytes": median_saving_high,
            "median_new_high_over_476_hwm_delta_bytes": statistics.median(new_span_delta),
            "median_latency_ratio_tiled_over_old_high_count": median_latency_ratio,
            "repair_qualified": qualified,
        },
        "classification": (
            "EXACT_TILED_CENTER_REPAIR_QUALIFIED"
            if qualified
            else "CENTER_REPAIR_HOLD"
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
