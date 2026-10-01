from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def analyze_axis_leverage(
    b463: Mapping[str, Any],
    b465: Mapping[str, Any],
    b467: Mapping[str, Any],
) -> dict[str, Any]:
    if b463.get("schema") != "finite-ram-lab.b463-result/v0.1":
        raise RuntimeError("b463_schema_invalid")
    if b465.get("schema") != "finite-ram-lab.b465-result/v0.1":
        raise RuntimeError("b465_schema_invalid")
    if b467.get("schema") != "finite-ram-lab.b467-result/v0.1":
        raise RuntimeError("b467_schema_invalid")

    if int(b463.get("semantic_match_count", -1)) != int(b463.get("pair_count", -2)):
        raise RuntimeError("b463_semantic_incomplete")
    if int(b465.get("semantic_match_count", -1)) != int(b465.get("pair_count", -2)):
        raise RuntimeError("b465_semantic_incomplete")
    if int(b467.get("semantic_match_count", -1)) != int(b467.get("pair_count", -2)):
        raise RuntimeError("b467_semantic_incomplete")

    representation_peak = abs(int(b463["median_treatment_minus_reference_peak_bytes"]))
    tile32_peak = abs(int(b465["median_selected_minus_baseline_peak_bytes"]))
    tile128_peak = abs(int(b467["median_selected_minus_baseline_peak_bytes"]))
    tile_peak_max = max(tile32_peak, tile128_peak, 1)
    peak_leverage_ratio = representation_peak / tile_peak_max

    representation_latency = float(b463["median_latency_ratio_treatment_over_reference"])
    tile32_latency = float(b465["median_latency_ratio_selected_over_baseline"])
    tile128_latency = float(b467["median_latency_ratio_selected_over_baseline"])

    return {
        "schema": "finite-ram-lab.axis-leverage/v0.1",
        "status": "PROPOSAL_ONLY",
        "claim_ceiling": "OFFLINE_AXIS_LEVERAGE_ANALYSIS",
        "source_results": {
            "b463": {
                "workflow_run_id": b463["workflow_run_id"],
                "median_abs_peak_effect_bytes": representation_peak,
                "median_latency_ratio": representation_latency,
            },
            "b465_tile32": {
                "workflow_run_id": b465["workflow_run_id"],
                "median_abs_peak_effect_bytes": tile32_peak,
                "median_latency_ratio": tile32_latency,
            },
            "b467_tile128": {
                "workflow_run_id": b467["workflow_run_id"],
                "median_abs_peak_effect_bytes": tile128_peak,
                "median_latency_ratio": tile128_latency,
            },
        },
        "peak_leverage": {
            "representation_effect_bytes": representation_peak,
            "max_tested_tile_effect_bytes": tile_peak_max,
            "representation_over_tile_ratio": peak_leverage_ratio,
        },
        "axis_decision": {
            "deprioritize": "tile_rows_for_peak_memory",
            "next_axis": "residue_lane_concurrency_q",
            "reason": (
                "The representation-residency effect is orders of magnitude larger "
                "than the tested tile-row effects, while tile changes mainly expose "
                "small latency/peak exchanges."
            ),
        },
        "next_experiment": {
            "mode": "PROBE",
            "hypothesis_id": "H468_RESIDUE_LANE_CONCURRENCY_FRONTIER",
            "variable": "resident_lane_concurrency_q",
            "coarse_sweep": [1, 2, 4, 7],
            "interpretation": {
                "q=1": "stream one residue lane at a time",
                "q=7": "retain all seven residue lanes before folding",
                "intermediate_q": "produce and retain q lanes, fold/release as a group",
            },
            "hard_gates": [
                "exact numerical output equality",
                "fresh process per arm",
                "normalized peak growth",
                "latency accounting",
                "fixed lane_count=7",
                "fixed tile_rows=64",
            ],
            "execute_now": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--b463", type=Path, required=True)
    parser.add_argument("--b465", type=Path, required=True)
    parser.add_argument("--b467", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    payload = analyze_axis_leverage(
        _load(args.b463),
        _load(args.b465),
        _load(args.b467),
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
