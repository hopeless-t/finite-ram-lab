from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from finite_ram_lab.app_surface import (
    load_policy,
    select_configuration,
    write_receipt,
)
from finite_ram_lab.local_adapter_bootstrap import (
    CANDIDATE_Q,
    fingerprint_sha256,
    local_host_fingerprint,
    minimum_samples_for_rank_max_coverage,
)


CALIBRATION_STATE_SCHEMA = "finite-ram-lab.local-calibration-state/v0.1"
EXPLORATION_SCHEMA = "finite-ram-lab.local-calibration-exploration/v0.1"


def _canonical_sha256(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _normalize_calibration_state(
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    schema = payload.get("schema")
    if schema == EXPLORATION_SCHEMA:
        return {
            "schema": CALIBRATION_STATE_SCHEMA,
            "implementation": payload["implementation"],
            "host_binding": payload["host_binding"],
            "sample_unit": payload["sample_unit"],
            "pareto_q": list(payload["local_pareto_q"]),
            "rows": [
                {
                    "q": int(row["q"]),
                    "sample_count": int(row["sample_count"]),
                    "empirical_max_peak_bytes": int(
                        row["empirical_max_peak_bytes"]
                    ),
                    "median_work_seconds": float(
                        row["median_work_seconds"]
                    ),
                    "rank_max_one_step_predictive_coverage_floor": float(
                        row[
                            "rank_max_one_step_predictive_coverage_floor"
                        ]
                    ),
                }
                for row in payload["frontier_rows"]
            ],
            "source_schema": schema,
        }
    if schema == CALIBRATION_STATE_SCHEMA:
        return dict(payload)
    raise RuntimeError("local_calibration_schema_invalid")


def validate_host_binding(
    state_or_policy: Mapping[str, Any],
    *,
    fingerprint: Mapping[str, Any] | None = None,
) -> str:
    binding = state_or_policy.get("host_binding") or state_or_policy.get(
        "environment_binding"
    )
    if not isinstance(binding, Mapping):
        raise RuntimeError("local_environment_binding_missing")

    expected = str(binding["environment_fingerprint_sha256"])
    current = dict(fingerprint or local_host_fingerprint())
    observed = fingerprint_sha256(current)
    if observed != expected:
        raise RuntimeError(
            "local_environment_fingerprint_mismatch:"
            f"expected={expected}:observed={observed}"
        )
    return observed


def promote_local_policy(
    calibration: Mapping[str, Any],
    *,
    target_rank_coverage: float = 0.95,
    fingerprint: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    state = _normalize_calibration_state(calibration)

    if state.get("implementation") != "TILED_WHERE":
        raise RuntimeError("local_implementation_invalid")
    validate_host_binding(state, fingerprint=fingerprint)

    pareto_q = sorted(int(q) for q in state["pareto_q"])
    if not pareto_q:
        raise RuntimeError("local_pareto_empty")
    if not set(pareto_q).issubset(set(CANDIDATE_Q)):
        raise RuntimeError("local_pareto_q_invalid")

    required_n = minimum_samples_for_rank_max_coverage(
        target_rank_coverage
    )
    rows_by_q = {
        int(row["q"]): row for row in state["rows"]
    }

    points = []
    for q in pareto_q:
        if q not in rows_by_q:
            raise RuntimeError(f"local_pareto_row_missing:q={q}")
        row = rows_by_q[q]
        n = int(row["sample_count"])
        coverage = float(
            row["rank_max_one_step_predictive_coverage_floor"]
        )
        expected_coverage = n / (n + 1)
        if abs(coverage - expected_coverage) > 1e-12:
            raise RuntimeError(f"local_coverage_inconsistent:q={q}")
        if n < required_n or coverage < target_rank_coverage:
            raise RuntimeError(
                f"local_evidence_insufficient:q={q}:"
                f"n={n}:required={required_n}:"
                f"coverage={coverage}:target={target_rank_coverage}"
            )

        points.append(
            {
                "q": q,
                "minimum_peak_budget_bytes": int(
                    row["empirical_max_peak_bytes"]
                ),
                "sample_count": n,
                "rank_max_one_step_predictive_coverage_floor": coverage,
                "median_latency_seconds": float(
                    row["median_work_seconds"]
                ),
            }
        )

    binding = state["host_binding"]
    fp_sha = str(binding["environment_fingerprint_sha256"])
    state_sha = _canonical_sha256(state)

    return {
        "schema": "finite-ram-lab.governor-policy/v0.1",
        "policy_id": f"local-governor-{fp_sha[:12]}-v1",
        "policy_version": "local-v1",
        "scope": "LOCAL_HOST_BOUND",
        "implementation": "TILED_WHERE",
        "claim_ceiling": "HOST_BOUND_LOCAL_GOVERNOR",
        "environment_binding": {
            "environment_fingerprint_sha256": fp_sha,
            "environment_fingerprint": binding[
                "environment_fingerprint"
            ],
        },
        "evidence_state": {
            "source_result": "LOCAL_CALIBRATION",
            "source_result_schema": state["schema"],
            "governor_sha256": state_sha,
            "sample_unit": state["sample_unit"],
            "exchangeability_required": True,
        },
        "pareto_q": pareto_q,
        "dominated_q_excluded": sorted(
            set(CANDIDATE_Q) - set(pareto_q)
        ),
        "points": points,
        "assumption": (
            "This policy is valid only for the fingerprint-bound local host and "
            "is conditional on exchangeability of comparable fresh-process "
            "executions on that host."
        ),
    }


def select_local_configuration(
    policy: Mapping[str, Any],
    *,
    peak_budget_bytes: int,
    minimum_rank_coverage: float,
    fingerprint: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if policy.get("scope") != "LOCAL_HOST_BOUND":
        raise RuntimeError("local_policy_scope_invalid")
    observed_fp = validate_host_binding(
        policy,
        fingerprint=fingerprint,
    )
    receipt = select_configuration(
        policy,
        peak_budget_bytes=peak_budget_bytes,
        minimum_rank_coverage=minimum_rank_coverage,
    )
    receipt["environment_binding"] = {
        "validated": True,
        "environment_fingerprint_sha256": observed_fp,
    }
    receipt["claim_ceiling"] = "HOST_BOUND_LOCAL_GOVERNOR_DECISION"
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("promote")
    p.add_argument("--calibration", type=Path, required=True)
    p.add_argument("--target-rank-coverage", type=float, default=0.95)
    p.add_argument("--out", type=Path, required=True)

    p = sub.add_parser("select")
    p.add_argument("--policy", type=Path, required=True)
    p.add_argument("--peak-budget-bytes", type=int, required=True)
    p.add_argument("--minimum-rank-coverage", type=float, default=0.95)
    p.add_argument("--out", type=Path, required=True)

    args = parser.parse_args()

    if args.command == "promote":
        payload = promote_local_policy(
            json.loads(args.calibration.read_text()),
            target_rank_coverage=args.target_rank_coverage,
        )
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n"
        )
        print(json.dumps(payload, sort_keys=True))
        return 0

    policy = load_policy(args.policy)
    receipt = select_local_configuration(
        policy,
        peak_budget_bytes=args.peak_budget_bytes,
        minimum_rank_coverage=args.minimum_rank_coverage,
    )
    write_receipt(receipt, args.out)
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
