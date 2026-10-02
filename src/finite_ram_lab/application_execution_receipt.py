from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping


RECEIPT_SCHEMA = "finite-ram-lab.application-execution-receipt/v0.1"


def _load(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def build_execution_receipt(
    decision: Mapping[str, Any],
    execution: Mapping[str, Any],
) -> dict[str, Any]:
    if decision.get("schema") != "finite-ram-lab.governor-decision-receipt/v0.1":
        raise RuntimeError("decision_schema_invalid")
    if decision.get("status") != "SELECTED":
        raise RuntimeError("decision_not_selected")
    if execution.get("schema") != "finite-ram-lab.repaired-q-child/v0.1":
        raise RuntimeError("execution_schema_invalid")
    if not execution.get("semantic_exact"):
        raise RuntimeError("execution_semantic_gate_failed")
    if decision.get("implementation") != "TILED_WHERE":
        raise RuntimeError("decision_implementation_invalid")
    if execution.get("strategy") != "TILED_WHERE":
        raise RuntimeError("execution_implementation_invalid")

    selected_q = int(decision["decision"]["selected_q"])
    executed_q = int(execution["q"])
    if selected_q != executed_q:
        raise RuntimeError(
            f"selected_q_execution_q_mismatch:selected={selected_q}:executed={executed_q}"
        )

    boundary = int(
        decision["decision"]["selected_empirical_max_peak_bytes"]
    )
    observed = int(execution["normalized_peak_growth_bytes"])
    relation = (
        "WITHIN_CALIBRATED_BOUNDARY"
        if observed <= boundary
        else "EXCEEDS_CALIBRATED_BOUNDARY"
    )

    return {
        "schema": RECEIPT_SCHEMA,
        "status": "EXECUTED",
        "contract_consistent": True,
        "policy": {
            "policy_id": decision["policy_id"],
            "policy_version": decision["policy_version"],
            "policy_manifest_sha256": decision["policy_manifest_sha256"],
            "implementation": decision["implementation"],
        },
        "request": decision["request"],
        "decision": decision["decision"],
        "execution": {
            "executed_q": executed_q,
            "semantic_exact": True,
            "output_sha256": execution["output_sha256"],
            "observed_peak_bytes": observed,
            "work_seconds": float(execution["work_seconds"]),
        },
        "boundary_check": {
            "declared_empirical_max_peak_bytes": boundary,
            "observed_peak_bytes": observed,
            "overrun_bytes": max(0, observed - boundary),
            "headroom_bytes": max(0, boundary - observed),
            "classification": relation,
        },
        "evidence": decision["evidence"],
        "claim_ceiling": "APPLICATION_LEVEL_REPAIRED_GOVERNOR_DOGFOOD",
        "assumption": decision["assumption"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--decision", type=Path, required=True)
    parser.add_argument("--execution", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    receipt = build_execution_receipt(
        _load(args.decision),
        _load(args.execution),
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
