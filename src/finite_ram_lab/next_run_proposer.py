from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


def _sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def propose_next_run(result: Mapping[str, Any], source_sha256: str) -> dict[str, Any]:
    if result.get("schema") != "finite-ram-lab.b465-result/v0.1":
        raise RuntimeError("unsupported_source_schema")
    if result.get("status") != "PASS":
        raise RuntimeError("source_result_not_pass")
    if result.get("mode") != "PROBE":
        raise RuntimeError("source_mode_not_probe")
    if result.get("dataset_partition") != "EXPERIMENTAL_INTERVENTION":
        raise RuntimeError("source_partition_invalid")
    if result.get("same_run_model_update") is not False:
        raise RuntimeError("source_same_run_update_invalid")
    if int(result.get("semantic_match_count", -1)) != int(result.get("pair_count", -2)):
        raise RuntimeError("source_semantic_gate_incomplete")

    changed = result.get("changed_variables")
    if changed != [["tile_rows", 64, 32]]:
        raise RuntimeError("unsupported_probe_geometry")

    classification = str(result.get("effect_classification"))
    median_peak = int(result.get("median_selected_minus_baseline_peak_bytes"))
    median_latency = float(result.get("median_latency_ratio_selected_over_baseline"))

    if (
        classification == "PEAK_EFFECT_UNRESOLVED_WITH_LATENCY_COST"
        and abs(median_peak) <= 1024 * 1024
        and median_latency > 1.0
    ):
        action = "PROBE_OPPOSITE_TILE_DIRECTION"
        selected_tile_rows = 128
        hypothesis_id = "H466_TILE_GRANULARITY_OTHER_SIDE"
        rationale = (
            "The smaller-tile probe produced no robust peak reduction and a positive "
            "median latency cost. Probe the opposite side of the frozen tile envelope "
            "while keeping strategy and lane count fixed."
        )
    else:
        action = "HOLD_FOR_MANUAL_REVIEW"
        selected_tile_rows = 64
        hypothesis_id = "H466_MANUAL_REVIEW"
        rationale = (
            "The source result does not match the bounded automatic proposal rule. "
            "Do not widen or execute automatically."
        )

    return {
        "schema": "finite-ram-lab.next-run-proposal/v0.1",
        "status": "PROPOSAL_ONLY",
        "execute_now": False,
        "requires_new_frozen_decision": True,
        "source_result_sha256": source_sha256,
        "source_telemetry_sha256": result["telemetry_sha256"],
        "source_workflow_run_id": result["workflow_run_id"],
        "source_effect_classification": classification,
        "proposal_action": action,
        "mode": "PROBE",
        "dataset_partition": "EXPERIMENTAL_INTERVENTION",
        "hypothesis_id": hypothesis_id,
        "baseline_variables": {
            "strategy": "STREAMED_FOLD",
            "lane_count": 7,
            "tile_rows": 64
        },
        "selected_variables": {
            "strategy": "STREAMED_FOLD",
            "lane_count": 7,
            "tile_rows": selected_tile_rows
        },
        "changed_variables": (
            [["tile_rows", 64, selected_tile_rows]]
            if selected_tile_rows != 64
            else []
        ),
        "held_constant_variables": [
            ["lane_count", 7],
            ["strategy", "STREAMED_FOLD"]
        ],
        "probe_envelope": {
            "allowed_variables": ["tile_rows"],
            "allowed_values": {"tile_rows": [32, 64, 128]},
            "numeric_bounds": {"tile_rows": [32, 128]}
        },
        "rationale": rationale,
        "claim_ceiling": "OFFLINE_NEXT_RUN_PROPOSAL_ONLY"
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    source_sha = _sha256_path(args.source)
    result = json.loads(args.source.read_text())
    proposal = propose_next_run(result, source_sha)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(proposal, indent=2, sort_keys=True) + "\n")
    print(json.dumps(proposal, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
