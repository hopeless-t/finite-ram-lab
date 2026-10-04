from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA = "catfood.improvement-receipt/v0.1"


class CrossRepoReceiptError(ValueError):
    pass


def load_receipt(path: Path) -> dict[str, Any]:
    doc = json.loads(path.read_text(encoding="utf-8"))
    validate_receipt(doc)
    return doc


def validate_receipt(doc: Any) -> None:
    if not isinstance(doc, dict) or doc.get("schema") != SCHEMA:
        raise CrossRepoReceiptError("receipt_schema_invalid")
    if doc.get("producer_repository") != "hopeless-t/finite-ram-lab":
        raise CrossRepoReceiptError("producer_repository_invalid")
    if doc.get("loop_id") != "decision-relevance-pruning":
        raise CrossRepoReceiptError("loop_id_invalid")
    if doc.get("scalar_gain") is not None:
        raise CrossRepoReceiptError("heterogeneous_costs_must_not_be_scalarized")
    if not isinstance(doc.get("scalar_gain_reason"), str):
        raise CrossRepoReceiptError("scalar_gain_reason_missing")

    invariant = doc.get("decision_invariant")
    if not isinstance(invariant, dict):
        raise CrossRepoReceiptError("decision_invariant_missing")
    if invariant.get("id") != "PRUNE_PROVEN_DECISION_IRRELEVANT_WORK":
        raise CrossRepoReceiptError("decision_invariant_id_invalid")
    if invariant.get("decision_irrelevance_proven_required") is not True:
        raise CrossRepoReceiptError("decision_irrelevance_proof_missing")
    if invariant.get("skip_preserves_admissible_decision_required") is not True:
        raise CrossRepoReceiptError("decision_equivalence_proof_missing")
    if invariant.get("fail_closed_when_proof_absent") is not True:
        raise CrossRepoReceiptError("fail_closed_missing")
    if invariant.get("authority_effect") != "NONE":
        raise CrossRepoReceiptError("authority_effect_invalid")

    planes = doc.get("evidence_planes")
    if not isinstance(planes, list) or len(planes) != 3:
        raise CrossRepoReceiptError("evidence_planes_invalid")
    ids = [row.get("plane_id") for row in planes if isinstance(row, dict)]
    if len(ids) != 3 or len(set(ids)) != 3:
        raise CrossRepoReceiptError("evidence_plane_identity_invalid")

    for row in planes:
        if not isinstance(row, dict):
            raise CrossRepoReceiptError("evidence_plane_invalid")
        if row.get("independent_plane") is not True:
            raise CrossRepoReceiptError("evidence_plane_independence_missing")
        if row.get("decision_equivalence_verified") is not True:
            raise CrossRepoReceiptError("decision_equivalence_unverified")
        if not isinstance(row.get("qualification_run"), int):
            raise CrossRepoReceiptError("qualification_run_invalid")
        if not isinstance(row.get("cost_delta"), dict) or not row["cost_delta"]:
            raise CrossRepoReceiptError("cost_delta_missing")
        if not isinstance(row.get("comparator"), dict) or not row["comparator"]:
            raise CrossRepoReceiptError("comparator_missing")

    meta = doc.get("meta_compilation")
    if not isinstance(meta, dict):
        raise CrossRepoReceiptError("meta_compilation_missing")
    if meta.get("resident_skill") != "PRUNE_PROVEN_DECISION_IRRELEVANT_WORK":
        raise CrossRepoReceiptError("resident_skill_invalid")
    if meta.get("resident_skill_count") != 17:
        raise CrossRepoReceiptError("resident_skill_count_invalid")
    if meta.get("skill_count_growth") != 0:
        raise CrossRepoReceiptError("skill_count_growth_invalid")
    if meta.get("catalog_budget_gate") != "PASS":
        raise CrossRepoReceiptError("catalog_budget_gate_invalid")
    ceiling = meta.get("catalog_budget_fraction_ceiling")
    if not isinstance(ceiling, (int, float)) or ceiling != 0.30:
        raise CrossRepoReceiptError("catalog_budget_ceiling_invalid")

    if doc.get("no_new_physical_run_for_export") is not True:
        raise CrossRepoReceiptError("export_physical_run_boundary_invalid")
    if doc.get("authority_effect") != "NONE":
        raise CrossRepoReceiptError("receipt_authority_invalid")
    if doc.get("canonical_write") is not False or doc.get("promotion") is not False:
        raise CrossRepoReceiptError("receipt_write_boundary_invalid")


def receipt_summary(doc: dict[str, Any]) -> dict[str, Any]:
    validate_receipt(doc)
    return {
        "receipt_id": doc["receipt_id"],
        "producer_repository": doc["producer_repository"],
        "loop_id": doc["loop_id"],
        "independent_evidence_planes": len(doc["evidence_planes"]),
        "cost_dimensions": sorted({
            key
            for row in doc["evidence_planes"]
            for key in row["cost_delta"]
        }),
        "scalar_gain": None,
        "resident_skill": doc["meta_compilation"]["resident_skill"],
        "skill_count_growth": doc["meta_compilation"]["skill_count_growth"],
        "authority_effect": doc["authority_effect"],
        "claim_ceiling": doc["claim_ceiling"],
    }
