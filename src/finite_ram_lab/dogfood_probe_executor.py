from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import statistics
from typing import Any, Mapping

from finite_ram_lab.coupled_numerical_residency import _run_fresh_child


ALLOWED_VARIABLES = ("lane_count", "strategy", "tile_rows")
ALLOWED_STRATEGIES = {"ALL_RESIDENT", "STREAMED_FOLD"}


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_frozen_decision(path: Path, expected_sha256: str) -> tuple[dict[str, Any], str]:
    raw = path.read_bytes()
    digest = _sha256_bytes(raw)
    if digest != expected_sha256:
        raise RuntimeError("decision_receipt_digest_mismatch")
    payload = json.loads(raw)
    return payload, digest


def _variables_from_receipt(
    receipt: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    baseline: dict[str, Any] = {}
    selected: dict[str, Any] = {}

    held = receipt.get("held_constant_variables")
    changed = receipt.get("changed_variables")
    if not isinstance(held, list) or not isinstance(changed, list):
        raise ValueError("decision_variable_receipts_missing")

    for item in held:
        if not isinstance(item, list) or len(item) != 2:
            raise ValueError("held_variable_shape_invalid")
        name, value = item
        baseline[str(name)] = value
        selected[str(name)] = value

    for item in changed:
        if not isinstance(item, list) or len(item) != 3:
            raise ValueError("changed_variable_shape_invalid")
        name, before, after = item
        key = str(name)
        baseline[key] = before
        selected[key] = after

    if set(baseline) != set(selected):
        raise AssertionError("decision_variable_schema_internal_mismatch")
    if set(baseline) != set(ALLOWED_VARIABLES):
        raise RuntimeError("decision_variable_surface_not_allowlisted")

    return baseline, selected


def validate_probe_decision(
    receipt: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    if receipt.get("schema") != "finite-ram-lab.runtime-decision/v0.1":
        raise RuntimeError("decision_schema_invalid")
    if receipt.get("mode") != "PROBE":
        raise RuntimeError("decision_mode_not_probe")
    if receipt.get("dataset_partition") != "EXPERIMENTAL_INTERVENTION":
        raise RuntimeError("decision_partition_invalid")
    if receipt.get("intervention") is not True:
        raise RuntimeError("decision_not_intervention")
    if not receipt.get("hypothesis_id"):
        raise RuntimeError("decision_hypothesis_missing")

    baseline, selected = _variables_from_receipt(receipt)

    changed_names = [
        str(item[0])
        for item in receipt["changed_variables"]
    ]
    if changed_names != ["tile_rows"]:
        raise RuntimeError("b465_requires_tile_rows_only_probe")

    for variables in (baseline, selected):
        strategy = variables["strategy"]
        if strategy not in ALLOWED_STRATEGIES:
            raise RuntimeError("strategy_not_allowlisted")
        lane_count = variables["lane_count"]
        tile_rows = variables["tile_rows"]
        if type(lane_count) is not int or not (2 <= lane_count <= 7):
            raise RuntimeError("lane_count_out_of_bounds")
        if type(tile_rows) is not int or tile_rows not in {32, 64, 128}:
            raise RuntimeError("tile_rows_not_allowlisted")

    if baseline["strategy"] != selected["strategy"]:
        raise RuntimeError("strategy_changed_unexpectedly")
    if baseline["lane_count"] != selected["lane_count"]:
        raise RuntimeError("lane_count_changed_unexpectedly")

    return baseline, selected


def _execute_condition(
    variables: Mapping[str, Any],
    *,
    size: int,
    seed: int,
    value_limit: int,
) -> dict[str, Any]:
    return _run_fresh_child(
        strategy=str(variables["strategy"]),
        size=size,
        lane_count=int(variables["lane_count"]),
        seed=seed,
        value_limit=value_limit,
        tile_rows=int(variables["tile_rows"]),
    )


def execute_probe(
    *,
    decision_receipt: Mapping[str, Any],
    decision_sha256: str,
    pairs: int,
    size: int,
    seed: int,
    value_limit: int,
) -> dict[str, Any]:
    if pairs <= 0:
        raise ValueError("pairs_invalid")
    if size <= 0:
        raise ValueError("size_invalid")

    baseline_vars, selected_vars = validate_probe_decision(decision_receipt)

    rows = []
    for repetition in range(pairs):
        order = (
            ("baseline", "selected")
            if repetition % 2 == 0
            else ("selected", "baseline")
        )
        observed: dict[str, dict[str, Any]] = {}
        for arm in order:
            variables = baseline_vars if arm == "baseline" else selected_vars
            observed[arm] = _execute_condition(
                variables,
                size=size,
                seed=seed,
                value_limit=value_limit,
            )

        baseline = observed["baseline"]
        selected = observed["selected"]
        semantic_match = (
            bool(baseline["semantic_exact"])
            and bool(selected["semantic_exact"])
            and baseline["output_sha256"] == selected["output_sha256"]
        )
        if not semantic_match:
            raise RuntimeError("dogfood_semantic_gate_failed")

        peak_delta = (
            int(selected["normalized_peak_growth_bytes"])
            - int(baseline["normalized_peak_growth_bytes"])
        )
        latency_ratio = (
            float(selected["work_seconds"])
            / float(baseline["work_seconds"])
        )
        rows.append(
            {
                "repetition": repetition,
                "order": list(order),
                "semantic_match": semantic_match,
                "baseline": baseline,
                "selected": selected,
                "selected_minus_baseline_peak_bytes": peak_delta,
                "latency_ratio_selected_over_baseline": latency_ratio,
            }
        )

    peak_deltas = [row["selected_minus_baseline_peak_bytes"] for row in rows]
    latency_ratios = [row["latency_ratio_selected_over_baseline"] for row in rows]

    return {
        "schema": "finite-ram-lab.dogfood-probe-telemetry/v0.1",
        "claim_ceiling": "BOUNDED_GITHUB_ACTIONS_DOGFOOD_PROBE",
        "dataset_partition": "EXPERIMENTAL_INTERVENTION",
        "mode": "PROBE",
        "hypothesis_id": decision_receipt["hypothesis_id"],
        "decision_receipt_sha256": decision_sha256,
        "decision_baseline_plan_id": decision_receipt["baseline_plan_id"],
        "decision_selected_plan_id": decision_receipt["selected_plan_id"],
        "decision_changed_variables": decision_receipt["changed_variables"],
        "decision_held_constant_variables": decision_receipt["held_constant_variables"],
        "same_run_model_update": False,
        "pairs": pairs,
        "size": size,
        "seed": seed,
        "value_limit": value_limit,
        "pair_rows": rows,
        "summary": {
            "semantic_match_count": sum(bool(row["semantic_match"]) for row in rows),
            "peak_deltas_bytes": peak_deltas,
            "median_selected_minus_baseline_peak_bytes": statistics.median(peak_deltas),
            "negative_peak_count": sum(value < 0 for value in peak_deltas),
            "positive_peak_count": sum(value > 0 for value in peak_deltas),
            "zero_peak_count": sum(value == 0 for value in peak_deltas),
            "latency_ratios_selected_over_baseline": latency_ratios,
            "median_latency_ratio_selected_over_baseline": statistics.median(latency_ratios),
        },
    }


def run_from_contract(contract: Mapping[str, Any]) -> dict[str, Any]:
    decision_path = Path(str(contract["decision_receipt_path"]))
    expected_sha = str(contract["expected_decision_sha256"])
    decision, digest = load_frozen_decision(decision_path, expected_sha)
    return execute_probe(
        decision_receipt=decision,
        decision_sha256=digest,
        pairs=int(contract["pairs"]),
        size=int(contract["size"]),
        seed=int(contract["seed"]),
        value_limit=int(contract["value_limit"]),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    contract = json.loads(args.contract.read_text())
    payload = run_from_contract(contract)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
