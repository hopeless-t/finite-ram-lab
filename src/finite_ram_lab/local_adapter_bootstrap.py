from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import platform
from typing import Any, Mapping


CANDIDATE_Q = (1, 2, 4, 7)
BOOTSTRAP_SCHEMA = "finite-ram-lab.local-governor-bootstrap/v0.1"
FINGERPRINT_SCHEMA = "finite-ram-lab.local-host-fingerprint/v0.1"


def _read_first(prefix: str, path: str) -> str | None:
    try:
        for line in Path(path).read_text().splitlines():
            if line.startswith(prefix):
                return line.split(":", 1)[1].strip()
    except OSError:
        return None
    return None


def local_host_fingerprint() -> dict[str, Any]:
    page_size = os.sysconf("SC_PAGE_SIZE")
    libc_name, libc_version = platform.libc_ver()
    return {
        "schema": FINGERPRINT_SCHEMA,
        "system": platform.system(),
        "kernel_release": platform.release(),
        "machine": platform.machine(),
        "python_version": platform.python_version(),
        "page_size_bytes": int(page_size),
        "cpu_model": _read_first("model name", "/proc/cpuinfo"),
        "mem_total": _read_first("MemTotal", "/proc/meminfo"),
        "libc": {
            "name": libc_name or None,
            "version": libc_version or None,
        },
        "cgroup_v2_present": Path("/sys/fs/cgroup/cgroup.controllers").exists(),
    }


def fingerprint_sha256(fingerprint: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        fingerprint,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def minimum_samples_for_rank_max_coverage(target: float) -> int:
    if not (0.0 < target < 1.0):
        raise ValueError("target_coverage_invalid")
    return math.ceil(target / (1.0 - target))


def build_local_bootstrap_plan(
    *,
    target_coverage: float = 0.95,
    exploration_samples_per_q: int = 8,
    fingerprint: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if exploration_samples_per_q <= 0:
        raise ValueError("exploration_samples_invalid")

    fp = dict(fingerprint or local_host_fingerprint())
    if fp.get("schema") != FINGERPRINT_SCHEMA:
        raise RuntimeError("fingerprint_schema_invalid")

    target_n = minimum_samples_for_rank_max_coverage(target_coverage)
    expansion = max(0, target_n - exploration_samples_per_q)

    return {
        "schema": BOOTSTRAP_SCHEMA,
        "status": "CALIBRATION_REQUIRED",
        "implementation": "TILED_WHERE",
        "claim_ceiling": "HOST_SCOPED_LOCAL_CALIBRATION_BOOTSTRAP",
        "environment_fingerprint": fp,
        "environment_fingerprint_sha256": fingerprint_sha256(fp),
        "candidate_q": list(CANDIDATE_Q),
        "hosted_threshold_import_allowed": False,
        "application_contract": {
            "request_fields": [
                "peak_budget_bytes",
                "minimum_rank_coverage",
            ],
            "decision_receipt_schema": (
                "finite-ram-lab.governor-decision-receipt/v0.1"
            ),
            "application_execution_receipt_schema": (
                "finite-ram-lab.application-execution-receipt/v0.1"
            ),
        },
        "initial_exploration": {
            "sample_unit": "fresh_local_process_on_bound_host",
            "samples_per_q": exploration_samples_per_q,
            "q_count": len(CANDIDATE_Q),
            "physical_observations": exploration_samples_per_q * len(CANDIDATE_Q),
            "purpose": (
                "rebuild the local q frontier without importing hosted-runner "
                "dominance or peak thresholds"
            ),
        },
        "promotion_target": {
            "target_rank_max_coverage": target_coverage,
            "required_sample_count_per_promoted_q": target_n,
            "additional_samples_after_exploration_per_promoted_q": expansion,
            "pareto_q": "UNKNOWN_UNTIL_LOCAL_EXPLORATION",
            "sample_unit": "fresh_local_process_on_bound_host",
        },
        "guardrails": [
            "do_not_copy_github_hosted_peak_thresholds",
            "do_not_exclude_q1_before_local_frontier_measurement",
            "bind_promoted_policy_to_environment_fingerprint",
            "fail_closed_on_environment_fingerprint_mismatch",
            "do_not_claim_cross_host_coverage",
        ],
        "assumption": (
            "Any later local rank-coverage claim is conditional on exchangeability "
            "of fresh-process observations on the fingerprint-bound local host."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="finite-ram-local-bootstrap",
        description="Create a host-bound calibration plan for the local Governor adapter.",
    )
    parser.add_argument("--target-rank-coverage", type=float, default=0.95)
    parser.add_argument("--exploration-samples-per-q", type=int, default=8)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    payload = build_local_bootstrap_plan(
        target_coverage=args.target_rank_coverage,
        exploration_samples_per_q=args.exploration_samples_per_q,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
