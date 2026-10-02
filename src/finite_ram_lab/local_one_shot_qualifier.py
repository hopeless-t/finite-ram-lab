from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import statistics
from typing import Any, Mapping

from finite_ram_lab.local_adapter_bootstrap import (
    CANDIDATE_Q,
    fingerprint_sha256,
    local_host_fingerprint,
    minimum_samples_for_rank_max_coverage,
)
from finite_ram_lab.local_calibration_explore import run_local_exploration
from finite_ram_lab.local_calibration_extend import (
    STATE_SCHEMA,
    _pareto,
    extend_local_calibration,
)
from finite_ram_lab.local_policy_adapter import promote_local_policy
from finite_ram_lab.repaired_q_frontier import _run_fresh_child


QUALIFICATION_SCHEMA = "finite-ram-lab.local-governor-qualification/v0.1"


def _canonical_sha256(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _values_from_state(
    state: Mapping[str, Any],
) -> dict[int, list[dict[str, Any]]]:
    digest = str(state["cross_q_output_sha256"])
    values: dict[int, list[dict[str, Any]]] = {
        q: [] for q in CANDIDATE_Q
    }
    for row in state["rows"]:
        q = int(row["q"])
        peaks = list(row["peak_samples_bytes"])
        times = list(row["work_samples_seconds"])
        if len(peaks) != len(times):
            raise RuntimeError(f"state_sample_vector_mismatch:q={q}")
        if len(peaks) != int(row["sample_count"]):
            raise RuntimeError(f"state_sample_count_invalid:q={q}")
        for peak, work in zip(peaks, times, strict=True):
            values[q].append(
                {
                    "q": q,
                    "normalized_peak_growth_bytes": int(peak),
                    "work_seconds": float(work),
                    "output_sha256": digest,
                }
            )
    return values


def _round_order(
    active_q: list[int],
    round_index: int,
) -> tuple[int, ...]:
    if not active_q:
        return ()
    shift = round_index % len(active_q)
    rotated = tuple(active_q[shift:] + active_q[:shift])
    if (round_index // len(active_q)) % 2:
        rotated = tuple(reversed(rotated))
    return rotated


def extend_calibration_state(
    state: Mapping[str, Any],
    *,
    sample_additions: Mapping[int, int],
    size: int,
    target_rank_coverage: float,
) -> dict[str, Any]:
    if state.get("schema") != STATE_SCHEMA:
        raise RuntimeError("local_state_schema_invalid")
    if state.get("implementation") != "TILED_WHERE":
        raise RuntimeError("local_state_implementation_invalid")
    if int(state["size"]) != size:
        raise RuntimeError(
            f"local_state_size_mismatch:state={state['size']}:requested={size}"
        )

    binding = state["host_binding"]
    expected_fp = str(binding["environment_fingerprint_sha256"])
    before = local_host_fingerprint()
    before_sha = fingerprint_sha256(before)
    if before_sha != expected_fp:
        raise RuntimeError(
            "local_environment_fingerprint_mismatch:"
            f"expected={expected_fp}:observed={before_sha}"
        )

    additions = {
        int(q): int(count)
        for q, count in sample_additions.items()
        if int(count) > 0
    }
    if not set(additions).issubset(set(CANDIDATE_Q)):
        raise RuntimeError("local_extension_q_invalid")

    values = _values_from_state(state)
    extension_blocks = []
    max_rounds = max(additions.values(), default=0)

    for round_index in range(max_rounds):
        active = sorted(
            q for q, count in additions.items()
            if round_index < count
        )
        order = _round_order(active, round_index)
        block = {
            "round_index": round_index,
            "execution_order": list(order),
            "results": [],
        }
        for q in order:
            result = _run_fresh_child(
                strategy="TILED_WHERE",
                q=q,
                size=size,
            )
            if not result["semantic_exact"]:
                raise RuntimeError(
                    f"semantic_gate_failed:round={round_index}:q={q}"
                )
            if result["output_sha256"] != state["cross_q_output_sha256"]:
                raise RuntimeError(
                    f"output_digest_mismatch:round={round_index}:q={q}"
                )
            row = {
                "q": q,
                "normalized_peak_growth_bytes": int(
                    result["normalized_peak_growth_bytes"]
                ),
                "work_seconds": float(result["work_seconds"]),
                "output_sha256": result["output_sha256"],
            }
            values[q].append(row)
            block["results"].append(row)
        extension_blocks.append(block)

    after = local_host_fingerprint()
    after_sha = fingerprint_sha256(after)
    if after_sha != expected_fp:
        raise RuntimeError("local_environment_fingerprint_changed_during_cycle")

    rows = []
    for q in CANDIDATE_Q:
        q_rows = values[q]
        peaks = [
            int(row["normalized_peak_growth_bytes"])
            for row in q_rows
        ]
        times = [float(row["work_seconds"]) for row in q_rows]
        n = len(q_rows)
        rows.append(
            {
                "q": q,
                "sample_count": n,
                "median_peak_bytes": statistics.median(peaks),
                "empirical_max_peak_bytes": max(peaks),
                "median_work_seconds": statistics.median(times),
                "rank_max_one_step_predictive_coverage_floor": n / (n + 1),
                "peak_samples_bytes": peaks,
                "work_samples_seconds": times,
            }
        )

    pareto_q = _pareto(rows)
    required_n = minimum_samples_for_rank_max_coverage(
        target_rank_coverage
    )
    rows_by_q = {int(row["q"]): row for row in rows}
    promotion_rows = []
    for q in pareto_q:
        n = int(rows_by_q[q]["sample_count"])
        promotion_rows.append(
            {
                "q": q,
                "current_sample_count": n,
                "required_sample_count": required_n,
                "additional_samples_required": max(0, required_n - n),
            }
        )

    return {
        "schema": STATE_SCHEMA,
        "status": "CALIBRATION_STATE_UPDATED",
        "claim_ceiling": "HOST_SCOPED_LOCAL_ADAPTIVE_CALIBRATION",
        "implementation": "TILED_WHERE",
        "host_binding": binding,
        "sample_unit": "fresh_local_process_on_bound_host",
        "size": size,
        "seed": 469,
        "candidate_q": list(CANDIDATE_Q),
        "rows": rows,
        "pareto_q": pareto_q,
        "promotion_target_rank_coverage": target_rank_coverage,
        "promotion_rows": promotion_rows,
        "policy_promotion_allowed": all(
            row["additional_samples_required"] == 0
            for row in promotion_rows
        ),
        "cross_q_output_sha256": state["cross_q_output_sha256"],
        "hosted_threshold_imported": False,
        "last_cycle_additions": additions,
        "last_cycle_physical_observations": sum(additions.values()),
        "last_cycle_blocks": extension_blocks,
        "assumption": (
            "Coverage is host-scoped and conditional on exchangeability of fresh "
            "process executions under the fingerprint-bound local environment."
        ),
    }


def qualify_local_governor(
    *,
    exploration_samples_per_q: int = 8,
    size: int = 2048,
    target_rank_coverage: float = 0.95,
    max_extension_cycles: int = 4,
) -> dict[str, Any]:
    if max_extension_cycles <= 0:
        raise ValueError("max_extension_cycles_invalid")

    exploration = run_local_exploration(
        samples_per_q=exploration_samples_per_q,
        size=size,
        target_rank_coverage=target_rank_coverage,
    )

    state = extend_local_calibration(
        exploration,
        additional_samples_per_q=0,
        size=size,
        target_rank_coverage=target_rank_coverage,
    )

    cycles = []
    cycle_index = 0
    while not state["policy_promotion_allowed"]:
        if cycle_index >= max_extension_cycles:
            raise RuntimeError("local_qualification_did_not_converge")

        deficits = {
            int(row["q"]): int(row["additional_samples_required"])
            for row in state["promotion_rows"]
            if int(row["additional_samples_required"]) > 0
        }
        if not deficits:
            raise RuntimeError("local_qualification_stalled_without_deficit")

        next_state = extend_calibration_state(
            state,
            sample_additions=deficits,
            size=size,
            target_rank_coverage=target_rank_coverage,
        )
        cycles.append(
            {
                "cycle_index": cycle_index,
                "input_pareto_q": list(state["pareto_q"]),
                "sample_additions": deficits,
                "physical_observations": sum(deficits.values()),
                "output_pareto_q": list(next_state["pareto_q"]),
                "promotion_allowed": bool(
                    next_state["policy_promotion_allowed"]
                ),
            }
        )
        state = next_state
        cycle_index += 1

    current_fp = local_host_fingerprint()
    policy = promote_local_policy(
        state,
        target_rank_coverage=target_rank_coverage,
        fingerprint=current_fp,
    )

    final_counts = {
        int(row["q"]): int(row["sample_count"])
        for row in state["rows"]
    }
    total_observations = sum(final_counts.values())
    max_possible = (
        minimum_samples_for_rank_max_coverage(target_rank_coverage)
        * len(CANDIDATE_Q)
    )
    if total_observations > max_possible:
        raise RuntimeError("local_qualification_observation_bound_exceeded")

    receipt = {
        "schema": QUALIFICATION_SCHEMA,
        "status": "QUALIFIED",
        "claim_ceiling": "HOST_BOUND_LOCAL_GOVERNOR_QUALIFICATION",
        "implementation": "TILED_WHERE",
        "environment_fingerprint_sha256": state["host_binding"][
            "environment_fingerprint_sha256"
        ],
        "exploration_samples_per_q": exploration_samples_per_q,
        "initial_physical_observations": int(
            exploration["physical_observations"]
        ),
        "extension_cycles": cycles,
        "extension_physical_observations": sum(
            int(row["physical_observations"])
            for row in cycles
        ),
        "total_physical_observations": total_observations,
        "maximum_possible_physical_observations_at_target": max_possible,
        "final_pareto_q": list(state["pareto_q"]),
        "target_rank_coverage": target_rank_coverage,
        "final_sample_counts": final_counts,
        "policy_id": policy["policy_id"],
        "policy_canonical_sha256": _canonical_sha256(policy),
        "calibration_state_canonical_sha256": _canonical_sha256(state),
        "hosted_threshold_imported": False,
    }

    return {
        "exploration": exploration,
        "calibration_state": state,
        "policy": policy,
        "qualification_receipt": receipt,
    }


def write_qualification_bundle(
    bundle: Mapping[str, Any],
    out_dir: str | Path,
) -> dict[str, Any]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)

    files = {
        "exploration": root / "local-exploration.json",
        "calibration_state": root / "local-calibration-state.json",
        "policy": root / "local-governor-policy.json",
        "qualification_receipt": root / "local-qualification-receipt.json",
    }
    for key, path in files.items():
        path.write_text(
            json.dumps(bundle[key], indent=2, sort_keys=True) + "\n"
        )

    manifest = {
        "schema": "finite-ram-lab.local-qualification-bundle/v0.1",
        "files": {
            key: {
                "path": path.name,
                "sha256": _file_sha256(path),
            }
            for key, path in files.items()
        },
        "policy_id": bundle["policy"]["policy_id"],
        "environment_fingerprint_sha256": bundle[
            "qualification_receipt"
        ]["environment_fingerprint_sha256"],
    }
    manifest_path = root / "bundle-manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )
    return {
        "root": str(root),
        "manifest": manifest,
        "manifest_path": str(manifest_path),
        "manifest_sha256": _file_sha256(manifest_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="finite-ram-local-qualify",
        description=(
            "Adaptively qualify and promote a fingerprint-bound local Governor "
            "policy in one command."
        ),
    )
    parser.add_argument("--exploration-samples-per-q", type=int, default=8)
    parser.add_argument("--size", type=int, default=2048)
    parser.add_argument("--target-rank-coverage", type=float, default=0.95)
    parser.add_argument("--max-extension-cycles", type=int, default=4)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()

    bundle = qualify_local_governor(
        exploration_samples_per_q=args.exploration_samples_per_q,
        size=args.size,
        target_rank_coverage=args.target_rank_coverage,
        max_extension_cycles=args.max_extension_cycles,
    )
    written = write_qualification_bundle(bundle, args.out_dir)
    print(json.dumps({
        "status": "QUALIFIED",
        "policy_id": bundle["policy"]["policy_id"],
        "final_pareto_q": bundle["qualification_receipt"]["final_pareto_q"],
        "total_physical_observations": bundle[
            "qualification_receipt"
        ]["total_physical_observations"],
        "environment_fingerprint_sha256": bundle[
            "qualification_receipt"
        ]["environment_fingerprint_sha256"],
        "bundle_manifest_sha256": written["manifest_sha256"],
        "out_dir": written["root"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
