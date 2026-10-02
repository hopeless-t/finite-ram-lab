from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


POLICY_SCHEMA = "finite-ram-lab.governor-policy/v0.1"
RECEIPT_SCHEMA = "finite-ram-lab.governor-decision-receipt/v0.1"


class NoEligibleConfiguration(RuntimeError):
    pass


def _canonical_sha256(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_policy(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    validate_policy(payload)
    return payload


def validate_policy(policy: Mapping[str, Any]) -> None:
    if policy.get("schema") != POLICY_SCHEMA:
        raise RuntimeError("policy_schema_invalid")
    if policy.get("implementation") != "TILED_WHERE":
        raise RuntimeError("policy_implementation_invalid")

    points = list(policy.get("points", []))
    if not points:
        raise RuntimeError("policy_points_missing")

    q_values = [int(row["q"]) for row in points]
    if q_values != sorted(q_values):
        raise RuntimeError("policy_q_order_invalid")
    if len(set(q_values)) != len(q_values):
        raise RuntimeError("policy_q_duplicate")

    budgets = [int(row["minimum_peak_budget_bytes"]) for row in points]

    for row in points:
        if int(row["minimum_peak_budget_bytes"]) < 0:
            raise RuntimeError("policy_budget_invalid")
        n = int(row["sample_count"])
        coverage = float(row["rank_max_one_step_predictive_coverage_floor"])
        if n <= 0:
            raise RuntimeError("policy_sample_count_invalid")
        expected = n / (n + 1)
        if abs(coverage - expected) > 1e-12:
            raise RuntimeError("policy_coverage_inconsistent")


def select_configuration(
    policy: Mapping[str, Any],
    *,
    peak_budget_bytes: int,
    minimum_rank_coverage: float,
    environment_binding_validated: bool = False,
) -> dict[str, Any]:
    validate_policy(policy)

    if (
        policy.get("scope") == "LOCAL_HOST_BOUND"
        and not environment_binding_validated
    ):
        raise RuntimeError("local_policy_requires_bound_selector")

    if peak_budget_bytes < 0:
        raise ValueError("peak_budget_invalid")
    if not (0.0 < minimum_rank_coverage < 1.0):
        raise ValueError("minimum_rank_coverage_invalid")

    eligible = [
        row
        for row in policy["points"]
        if int(row["minimum_peak_budget_bytes"]) <= peak_budget_bytes
        and float(row["rank_max_one_step_predictive_coverage_floor"])
        >= minimum_rank_coverage
    ]
    if not eligible:
        raise NoEligibleConfiguration(
            "no_coverage_qualified_configuration_fits_budget"
        )

    selected = min(
        eligible,
        key=lambda row: (
            float(row["median_latency_seconds"]),
            int(row["minimum_peak_budget_bytes"]),
            int(row["q"]),
        ),
    )
    boundary = int(selected["minimum_peak_budget_bytes"])
    coverage = float(
        selected["rank_max_one_step_predictive_coverage_floor"]
    )

    return {
        "schema": RECEIPT_SCHEMA,
        "status": "SELECTED",
        "policy_id": policy["policy_id"],
        "policy_version": policy["policy_version"],
        "policy_manifest_sha256": _canonical_sha256(policy),
        "implementation": policy["implementation"],
        "claim_ceiling": policy["claim_ceiling"],
        "request": {
            "peak_budget_bytes": peak_budget_bytes,
            "minimum_rank_coverage": minimum_rank_coverage,
        },
        "decision": {
            "selected_q": int(selected["q"]),
            "selected_empirical_max_peak_bytes": boundary,
            "budget_slack_bytes": peak_budget_bytes - boundary,
            "sample_count": int(selected["sample_count"]),
            "rank_max_one_step_predictive_coverage_floor": coverage,
            "median_latency_seconds": float(selected["median_latency_seconds"]),
        },
        "evidence": {
            "source_result": policy["evidence_state"]["source_result"],
            "source_result_schema": policy["evidence_state"]["source_result_schema"],
            "source_governor_sha256": policy["evidence_state"]["governor_sha256"],
            "sample_unit": policy["evidence_state"]["sample_unit"],
            "exchangeability_required": bool(
                policy["evidence_state"]["exchangeability_required"]
            ),
        },
        "assumption": policy["assumption"],
    }


def select_from_policy_path(
    policy_path: str | Path,
    *,
    peak_budget_bytes: int,
    minimum_rank_coverage: float,
) -> dict[str, Any]:
    return select_configuration(
        load_policy(policy_path),
        peak_budget_bytes=peak_budget_bytes,
        minimum_rank_coverage=minimum_rank_coverage,
    )


def write_receipt(receipt: Mapping[str, Any], out: str | Path) -> None:
    path = Path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="finite-ram-governor",
        description="Select a repaired Finite RAM execution point from a frozen policy.",
    )
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--peak-budget-bytes", type=int, required=True)
    parser.add_argument("--minimum-rank-coverage", type=float, default=0.95)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    try:
        receipt = select_from_policy_path(
            args.policy,
            peak_budget_bytes=args.peak_budget_bytes,
            minimum_rank_coverage=args.minimum_rank_coverage,
        )
    except NoEligibleConfiguration as exc:
        print(json.dumps({
            "schema": RECEIPT_SCHEMA,
            "status": "NO_ELIGIBLE_CONFIGURATION",
            "error": str(exc),
            "request": {
                "peak_budget_bytes": args.peak_budget_bytes,
                "minimum_rank_coverage": args.minimum_rank_coverage,
            },
        }, sort_keys=True))
        return 2

    write_receipt(receipt, args.out)
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
