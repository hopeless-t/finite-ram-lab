from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


EXPECTED_PROPOSAL_SHA256 = "64672a290dc46e40f5db021baeb9e02b86303da61100d0bc2fc90d6f8b97463f"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_json(path: Path, payload: Mapping[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()
    path.write_bytes(raw)
    return _sha256_bytes(raw)


def load_and_validate_proposal(path: Path, expected_sha256: str) -> tuple[dict[str, Any], str]:
    raw = path.read_bytes()
    digest = _sha256_bytes(raw)
    if digest != expected_sha256:
        raise RuntimeError("proposal_digest_mismatch")

    proposal = json.loads(raw)
    if proposal.get("schema") != "finite-ram-lab.next-run-proposal/v0.1":
        raise RuntimeError("proposal_schema_invalid")
    if proposal.get("status") != "PROPOSAL_ONLY":
        raise RuntimeError("proposal_status_invalid")
    if proposal.get("execute_now") is not False:
        raise RuntimeError("proposal_execute_now_must_be_false")
    if proposal.get("requires_new_frozen_decision") is not True:
        raise RuntimeError("proposal_requires_new_decision_missing")
    if proposal.get("proposal_action") != "PROBE_OPPOSITE_TILE_DIRECTION":
        raise RuntimeError("proposal_action_invalid")
    if proposal.get("changed_variables") != [["tile_rows", 64, 128]]:
        raise RuntimeError("proposal_geometry_invalid")
    if proposal.get("held_constant_variables") != [
        ["lane_count", 7],
        ["strategy", "STREAMED_FOLD"],
    ]:
        raise RuntimeError("proposal_held_constants_invalid")

    return proposal, digest


def freeze_decision(
    proposal: Mapping[str, Any],
    proposal_sha256: str,
) -> dict[str, Any]:
    baseline = proposal["baseline_variables"]
    selected = proposal["selected_variables"]

    if baseline != {
        "strategy": "STREAMED_FOLD",
        "lane_count": 7,
        "tile_rows": 64,
    }:
        raise RuntimeError("proposal_baseline_invalid")
    if selected != {
        "strategy": "STREAMED_FOLD",
        "lane_count": 7,
        "tile_rows": 128,
    }:
        raise RuntimeError("proposal_selected_invalid")

    return {
        "schema": "finite-ram-lab.runtime-decision/v0.1",
        "mode": "PROBE",
        "dataset_partition": "EXPERIMENTAL_INTERVENTION",
        "baseline_plan_id": "streamed_7_t64",
        "selected_plan_id": "streamed_7_t128",
        "intervention": True,
        "hypothesis_id": proposal["hypothesis_id"],
        "changed_variables": [["tile_rows", 64, 128]],
        "held_constant_variables": [
            ["lane_count", 7],
            ["strategy", "STREAMED_FOLD"],
        ],
        "selection_rule": "frozen_from_b466_offline_proposal",
        "claim_ceiling": "FROZEN_NEXT_RUN_DECISION",
        "source_proposal_sha256": proposal_sha256,
        "source_telemetry_sha256": proposal["source_telemetry_sha256"],
        "source_workflow_run_id": proposal["source_workflow_run_id"],
    }


def freeze_binding(
    *,
    decision_path: Path,
    decision_sha256: str,
    proposal_sha256: str,
    source_telemetry_sha256: str,
) -> dict[str, Any]:
    return {
        "schema": "finite-ram-lab.dogfood-probe-contract/v0.2",
        "id": "TX-DOGFOOD-PROBE-B467-v0.1",
        "decision_receipt_path": str(decision_path),
        "expected_decision_sha256": decision_sha256,
        "pairs": 4,
        "size": 2048,
        "seed": 467,
        "value_limit": 50,
        "allowlisted_executor": "finite_ram_lab.dogfood_probe_executor",
        "same_run_model_update": False,
        "source_proposal_sha256": proposal_sha256,
        "source_telemetry_sha256": source_telemetry_sha256,
        "claim_ceiling": "BOUNDED_CROSS_RUN_FEEDBACK_EXECUTION",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--proposal", type=Path, required=True)
    parser.add_argument("--expected-proposal-sha256", default=EXPECTED_PROPOSAL_SHA256)
    parser.add_argument("--decision-out", type=Path, required=True)
    parser.add_argument("--contract-out", type=Path, required=True)
    args = parser.parse_args()

    proposal, proposal_sha = load_and_validate_proposal(
        args.proposal,
        args.expected_proposal_sha256,
    )
    decision = freeze_decision(proposal, proposal_sha)
    decision_sha = _write_json(args.decision_out, decision)
    contract = freeze_binding(
        decision_path=args.decision_out,
        decision_sha256=decision_sha,
        proposal_sha256=proposal_sha,
        source_telemetry_sha256=proposal["source_telemetry_sha256"],
    )
    contract_sha = _write_json(args.contract_out, contract)

    print(
        json.dumps(
            {
                "proposal_sha256": proposal_sha,
                "decision_sha256": decision_sha,
                "contract_sha256": contract_sha,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
