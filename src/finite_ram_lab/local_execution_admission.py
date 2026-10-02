from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping

from finite_ram_lab.local_adapter_bootstrap import (
    minimum_samples_for_rank_max_coverage,
)


SPEC_SCHEMA = "finite-ram-lab.local-execution-admission/v0.1"
REQUEST_SCHEMA = "finite-ram-lab.local-execution-request/v0.1"
RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


def _canonical_sha256(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_spec(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    validate_spec(payload)
    return payload


def validate_spec(spec: Mapping[str, Any]) -> None:
    if spec.get("schema") != SPEC_SCHEMA:
        raise RuntimeError("admission_schema_invalid")
    if spec.get("action_id") != "finite_ram.local_qualify_v1":
        raise RuntimeError("admission_action_id_invalid")
    if spec.get("authority_effect") != "NONE":
        raise RuntimeError("admission_authority_effect_invalid")

    execution = spec.get("execution")
    if not isinstance(execution, Mapping):
        raise RuntimeError("admission_execution_missing")
    if execution.get("network_allowed") is not False:
        raise RuntimeError("admission_network_must_be_false")
    if execution.get("external_effects_allowed") is not False:
        raise RuntimeError("admission_external_effects_must_be_false")
    if execution.get("working_tree_required_clean") is not True:
        raise RuntimeError("admission_clean_tree_required")
    if execution.get("exact_repo_commit_must_be_recorded") is not True:
        raise RuntimeError("admission_commit_binding_required")

    budget = spec.get("budget")
    if not isinstance(budget, Mapping):
        raise RuntimeError("admission_budget_missing")

    q = [int(x) for x in budget.get("candidate_q", [])]
    if q != [1, 2, 4, 7]:
        raise RuntimeError("admission_candidate_q_invalid")

    exploration = int(budget["exploration_samples_per_q"])
    initial = int(budget["initial_physical_observations"])
    if initial != exploration * len(q):
        raise RuntimeError("admission_initial_observation_count_invalid")

    target = float(budget["target_rank_coverage"])
    required_n = minimum_samples_for_rank_max_coverage(target)
    if int(budget["required_sample_count_per_promoted_q"]) != required_n:
        raise RuntimeError("admission_required_n_invalid")

    maximum = int(budget["maximum_total_physical_observations"])
    if maximum != required_n * len(q):
        raise RuntimeError("admission_maximum_observation_count_invalid")

    if int(budget["size"]) != 2048:
        raise RuntimeError("admission_size_invalid")
    if int(budget["max_extension_cycles"]) != 4:
        raise RuntimeError("admission_extension_cycle_invalid")

    retry = spec.get("retry")
    if not isinstance(retry, Mapping):
        raise RuntimeError("admission_retry_missing")
    if retry.get("unknown_delivery") != "DO_NOT_RETRY":
        raise RuntimeError("admission_unknown_delivery_policy_invalid")
    if retry.get("new_run_requires_new_run_id") is not True:
        raise RuntimeError("admission_new_run_id_required")

    output = spec.get("output")
    if not isinstance(output, Mapping):
        raise RuntimeError("admission_output_missing")
    if output.get("root_template") != "runs/local-governor/{run_id}":
        raise RuntimeError("admission_output_root_invalid")

    required_files = list(output.get("required_files", []))
    expected_files = [
        "local-exploration.json",
        "local-calibration-state.json",
        "local-governor-policy.json",
        "local-qualification-receipt.json",
        "bundle-manifest.json",
    ]
    if required_files != expected_files:
        raise RuntimeError("admission_required_files_invalid")

    argv = list(execution.get("python_argv_template", []))
    if not argv or argv[:3] != [
        "python",
        "-m",
        "finite_ram_lab.local_one_shot_qualifier",
    ]:
        raise RuntimeError("admission_command_invalid")
    if "{out_dir}" not in argv:
        raise RuntimeError("admission_command_out_dir_missing")


def build_request(
    spec: Mapping[str, Any],
    *,
    run_id: str,
    repo_commit: str,
) -> dict[str, Any]:
    validate_spec(spec)

    if not RUN_ID_RE.fullmatch(run_id):
        raise ValueError("run_id_invalid")
    if not COMMIT_RE.fullmatch(repo_commit):
        raise ValueError("repo_commit_invalid")

    out_dir = spec["output"]["root_template"].format(run_id=run_id)
    argv = [
        out_dir if token == "{out_dir}" else token
        for token in spec["execution"]["python_argv_template"]
    ]

    return {
        "schema": REQUEST_SCHEMA,
        "status": "READY_FOR_ADMISSION",
        "action_id": spec["action_id"],
        "run_id": run_id,
        "repository": "hopeless-t/finite-ram-lab",
        "repo_commit": repo_commit,
        "admission_spec_sha256": _canonical_sha256(spec),
        "authority_effect": "NONE",
        "network_allowed": False,
        "external_effects_allowed": False,
        "working_tree_required_clean": True,
        "maximum_total_physical_observations": int(
            spec["budget"]["maximum_total_physical_observations"]
        ),
        "retry_on_unknown_delivery": "DO_NOT_RETRY",
        "out_dir": out_dir,
        "argv": argv,
        "required_output_files": list(spec["output"]["required_files"]),
        "preconditions": list(spec["preconditions"]),
        "postconditions": list(spec["postconditions"]),
        "claim_ceiling": "LOCAL_EXECUTION_REQUEST_READY_NOT_EXECUTED",
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="finite-ram-local-admission",
        description="Build a bounded MVCA/LDC admission request for B500 local qualification.",
    )
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--repo-commit", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    request = build_request(
        load_spec(args.spec),
        run_id=args.run_id,
        repo_commit=args.repo_commit,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(request, indent=2, sort_keys=True) + "\n")
    print(json.dumps(request, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
