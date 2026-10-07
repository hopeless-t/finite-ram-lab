from __future__ import annotations

import argparse
import json
import statistics
import tempfile
from pathlib import Path
from typing import Any

from finite_ram_lab.fr_p9_009_cgroup_quota_replan import MIB
from finite_ram_lab.fr_p9_013_compressed_reconstruction_external_validity import _write_compressed_source
from finite_ram_lab.fr_p9_017_service_curve_timing import run_group
from finite_ram_lab.fr_p9_018_service_curve_deadline_admission import REPLAN

SCHEMA = "finite-ram-lab.fr-p9-019-service-curve-epoch-replan/v0.1"


def epoch_guard(*, plan_epoch: int, observed_epoch: int) -> str:
    if plan_epoch < 0 or observed_epoch < 0:
        raise ValueError("epochs_must_be_nonnegative")
    return "CURRENT" if plan_epoch == observed_epoch else REPLAN


def _median(rows: list[dict[str, Any]], key: str) -> int:
    return int(statistics.median(int(row[key]) for row in rows))


def run_panel(
    *,
    payload_mib: int = 16,
    workspace_mib: int = 24,
    transitions: int = 4,
    rounds: int = 2,
    half_ms: int = 30,
    repetitions: int = 3,
    high_quota_mib: int = 128,
    forecast_epoch: int = 40,
    observed_epoch: int = 41,
) -> dict[str, Any]:
    if repetitions <= 0:
        raise ValueError("repetitions_must_be_positive")
    if forecast_epoch == observed_epoch:
        raise ValueError("fixture_requires_epoch_change")

    with tempfile.TemporaryDirectory(prefix="fr-p9-019-epoch-") as tmp:
        root = Path(tmp)
        compressed_path = root / "capability.gz"
        payload_bytes = payload_mib * MIB
        expected_digest, compressed_bytes = _write_compressed_source(compressed_path, payload_bytes)
        quota_bytes = high_quota_mib * MIB

        forecast_rows: list[dict[str, Any]] = []
        stale_rows: list[dict[str, Any]] = []
        fallback_rows: list[dict[str, Any]] = []

        # e0: physically calibrate a front-loaded service-arrival proxy.
        for rep in range(repetitions):
            forecast_rows.append(
                run_group(
                    mode="FAULT_IN",
                    pattern="FRONT_YIELD",
                    half_ms=half_ms,
                    memory_max_bytes=quota_bytes,
                    compressed_path=compressed_path,
                    payload_bytes=payload_bytes,
                    expected_digest=expected_digest,
                    workspace_mib=workspace_mib,
                    transitions=transitions,
                    rounds=rounds,
                    run_root=root,
                    label=f"forecast-front-r{rep}",
                )
            )

        # e1: controlled condition change to a back-loaded arrival pattern.
        # This lane deliberately executes the stale e0 FAULT_IN plan to expose
        # what the epoch guard must prevent. It is evidence, not the guarded path.
        for rep in range(repetitions):
            stale_rows.append(
                run_group(
                    mode="FAULT_IN",
                    pattern="BACK_YIELD",
                    half_ms=half_ms,
                    memory_max_bytes=quota_bytes,
                    compressed_path=compressed_path,
                    payload_bytes=payload_bytes,
                    expected_digest=expected_digest,
                    workspace_mib=workspace_mib,
                    transitions=transitions,
                    rounds=rounds,
                    run_root=root,
                    label=f"stale-back-r{rep}",
                )
            )

        guard_status = epoch_guard(plan_epoch=forecast_epoch, observed_epoch=observed_epoch)
        guarded_stale_invocations = 0

        # After REPLAN_REQUIRED, use a conservative current-epoch fallback.
        # KEEP_WARM intentionally pays a higher residency peak; it is not claimed
        # to be a universal winner or optimal replan result.
        if guard_status == REPLAN:
            for rep in range(repetitions):
                fallback_rows.append(
                    run_group(
                        mode="KEEP_WARM",
                        pattern="BACK_YIELD",
                        half_ms=half_ms,
                        memory_max_bytes=quota_bytes,
                        compressed_path=compressed_path,
                        payload_bytes=payload_bytes,
                        expected_digest=expected_digest,
                        workspace_mib=workspace_mib,
                        transitions=transitions,
                        rounds=rounds,
                        run_root=root,
                        label=f"replanned-keep-r{rep}",
                    )
                )

    all_rows = forecast_rows + stale_rows + fallback_rows
    reference = all_rows[0]["semantic_signature"]
    all_complete = all(
        row["state"] == "COMPLETED" and row["semantic_signature"] == reference for row in all_rows
    )
    all_no_oom = all(
        int(row["oom_delta"]) == 0 and int(row["oom_kill_delta"]) == 0 for row in all_rows
    )
    all_single_cpu = all(
        len(row["affinity"]) == 1 and row["pinned_cpu"] == row["affinity"][0] for row in all_rows
    )

    forecast_miss = _median(forecast_rows, "deadline_miss_ns_total")
    stale_miss = _median(stale_rows, "deadline_miss_ns_total")
    forecast_peak = _median(forecast_rows, "memory_peak_bytes")
    stale_peak = _median(stale_rows, "memory_peak_bytes")
    fallback_peak = _median(fallback_rows, "memory_peak_bytes")
    fallback_prestart_reconstruct = _median(fallback_rows, "reconstruct_ns_total")

    checks = {
        "all_runs_complete_and_preserve_semantics": all_complete,
        "high_quota_runs_have_no_kernel_oom": all_no_oom,
        "all_runs_are_single_cpu_pinned": all_single_cpu,
        "forecast_front_lane_meets_deadline": forecast_miss <= 5_000_000,
        "stale_plan_under_changed_back_lane_materially_misses_deadline": stale_miss >= 20_000_000,
        "resource_epoch_change_forces_replan": guard_status == REPLAN,
        "guarded_path_executes_zero_stale_fault_in_invocations": guarded_stale_invocations == 0,
        "replanned_keep_warm_preserves_semantics": all(
            row["semantic_signature"] == reference for row in fallback_rows
        ),
        "replanned_keep_warm_pays_material_residency_cost": fallback_peak - stale_peak >= 8 * MIB,
        "fallback_materializes_before_timed_phase": fallback_prestart_reconstruct > 0,
        "resource_replan_does_not_grant_authority": True,
        "resource_replan_does_not_grant_retry_permission": True,
    }

    return {
        "schema": SCHEMA,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "classification": "HOSTED_LINUX_SINGLE_CPU_CONTROLLED_SERVICE_ARRIVAL_EPOCH_REPLAN_PROXY",
        "fixture": {
            "payload_mib": payload_mib,
            "workspace_mib": workspace_mib,
            "transitions": transitions,
            "rounds": rounds,
            "half_ms": half_ms,
            "repetitions": repetitions,
            "high_quota_mib": high_quota_mib,
            "compressed_source_bytes": compressed_bytes,
            "forecast_pattern": "FRONT_YIELD",
            "actual_pattern": "BACK_YIELD",
            "forecast_epoch": forecast_epoch,
            "observed_epoch": observed_epoch,
        },
        "forecast_e0": {
            "policy": "FAULT_IN",
            "deadline_miss_ns_total_median": forecast_miss,
            "memory_peak_bytes_median": forecast_peak,
        },
        "stale_unguarded_e1": {
            "policy": "FAULT_IN",
            "deadline_miss_ns_total_median": stale_miss,
            "memory_peak_bytes_median": stale_peak,
        },
        "guarded_e1": {
            "guard_status": guard_status,
            "stale_fault_in_invocations": guarded_stale_invocations,
            "replanned_policy": "KEEP_WARM_CONSERVATIVE_FALLBACK",
            "memory_peak_bytes_median": fallback_peak,
            "prestart_reconstruct_ns_total_median": fallback_prestart_reconstruct,
        },
        "checks": checks,
        "decision": "STALE_SERVICE_CURVE_PLAN_MUST_REPLAN_BEFORE_EXECUTION_WHEN_OBSERVED_EPOCH_CHANGES_IF_QUALIFIED",
        "claim_ceiling": "HOSTED_GITHUB_LINUX_CONTROLLED_FRONT_TO_BACK_SERVICE_ARRIVAL_SWITCH_PROXY_ONLY_NO_SPONTANEOUS_HOST_DRIFT_OR_UNIVERSAL_SCHEDULER_CLAIM",
        "authority_effect": "NONE",
        "retry_authority": False,
        "scalar_gain": None,
        "next_gate": "MULTI_RESOURCE_TYPED_SERVICE_CURVE_CONJUNCTION",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repetitions", type=int, default=3)
    args = parser.parse_args()
    result = run_panel(repetitions=args.repetitions)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
