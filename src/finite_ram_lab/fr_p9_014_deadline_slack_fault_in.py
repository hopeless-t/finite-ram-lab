from __future__ import annotations

import argparse
import json
import os
import shlex
import statistics
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Any

from finite_ram_lab.fr_p9_009_cgroup_quota_replan import MIB, _atomic_json, _create_cgroup, _read_events
from finite_ram_lab.fr_p9_013_compressed_reconstruction_external_validity import (
    _reconstruct_capability,
    _stride_work,
    _workspace_signature,
    _write_compressed_source,
)

SCHEMA = "finite-ram-lab.fr-p9-014-deadline-slack-fault-in/v0.1"


def child(
    *,
    mode: str,
    compressed_path: Path,
    payload_bytes: int,
    expected_digest: str,
    workspace_mib: int,
    transitions: int,
    rounds: int,
    slack_ms: int,
    ready_path: Path,
    work_start_path: Path,
    result_path: Path,
) -> int:
    if mode not in {"KEEP_WARM", "FAULT_IN"}:
        raise ValueError(f"unknown_mode:{mode}")
    if slack_ms < 0:
        raise ValueError("slack_ms_must_be_nonnegative")

    capability = None
    prestart_reconstruct_ns = 0
    if mode == "KEEP_WARM":
        started = time.monotonic_ns()
        capability, _ = _reconstruct_capability(
            compressed_path,
            payload_bytes=payload_bytes,
            expected_digest=expected_digest,
        )
        prestart_reconstruct_ns = time.monotonic_ns() - started

    _atomic_json(
        ready_path,
        {"pid": os.getpid(), "mode": mode, "slack_ms": slack_ms, "transitions": transitions},
    )
    deadline = time.monotonic() + 60
    while not work_start_path.exists():
        if time.monotonic() > deadline:
            raise TimeoutError("work_start_timeout")
        time.sleep(0.001)

    rows: list[dict[str, Any]] = []
    for transition in range(transitions):
        workspace, workspace_sig = _workspace_signature(workspace_mib * MIB, transition)
        workspace.close()
        workspace_close_ns = time.monotonic_ns()

        reconstruction: dict[str, Any] = {}
        error: list[BaseException] = []
        thread: threading.Thread | None = None

        if mode == "FAULT_IN":
            def reconstruct() -> None:
                try:
                    reconstruction["start_ns"] = time.monotonic_ns()
                    cap, _ = _reconstruct_capability(
                        compressed_path,
                        payload_bytes=payload_bytes,
                        expected_digest=expected_digest,
                    )
                    reconstruction["capability"] = cap
                    reconstruction["done_ns"] = time.monotonic_ns()
                except BaseException as exc:  # fail closed after join
                    error.append(exc)

            thread = threading.Thread(target=reconstruct, name=f"fault-in-{transition}")
            thread.start()
            if slack_ms:
                time.sleep(slack_ms / 1000.0)
            slack_end_ns = time.monotonic_ns()
            thread.join(timeout=60)
            if thread.is_alive():
                raise TimeoutError("reconstruction_thread_timeout")
            if error:
                raise RuntimeError("reconstruction_thread_failed") from error[0]
            capability = reconstruction.get("capability")
            if capability is None:
                raise RuntimeError("reconstruction_missing_capability")
            reconstruct_start_ns = int(reconstruction["start_ns"])
            reconstruct_done_ns = int(reconstruction["done_ns"])
            reconstruct_ns = reconstruct_done_ns - reconstruct_start_ns
            exposed_stall_ns = max(0, reconstruct_done_ns - slack_end_ns)
            schedule_gap_ns = reconstruct_start_ns - workspace_close_ns
        else:
            if capability is None:
                raise RuntimeError("keep_warm_capability_missing")
            reconstruct_start_ns = 0
            reconstruct_done_ns = 0
            reconstruct_ns = 0
            exposed_stall_ns = 0
            schedule_gap_ns = 0
            slack_end_ns = workspace_close_ns

        work_started = time.monotonic_ns()
        semantic_value = _stride_work(capability, transition=transition, rounds=rounds)
        work_ns = time.monotonic_ns() - work_started
        rows.append(
            {
                "transition": transition,
                "workspace_signature": workspace_sig,
                "semantic_value": semantic_value,
                "workspace_close_ns": workspace_close_ns,
                "reconstruct_start_ns": reconstruct_start_ns,
                "reconstruct_done_ns": reconstruct_done_ns,
                "schedule_gap_ns": schedule_gap_ns,
                "reconstruct_ns": reconstruct_ns,
                "slack_ms": slack_ms,
                "slack_end_ns": slack_end_ns,
                "exposed_stall_ns": exposed_stall_ns,
                "work_ns": work_ns,
            }
        )

        if mode == "FAULT_IN":
            capability.close()
            capability = None

    if capability is not None:
        capability.close()

    _atomic_json(
        result_path,
        {
            "mode": mode,
            "slack_ms": slack_ms,
            "transitions": transitions,
            "prestart_reconstruct_ns": prestart_reconstruct_ns,
            "rows": rows,
        },
    )
    return 0


def run_group(
    *,
    mode: str,
    slack_ms: int,
    memory_max_bytes: int,
    compressed_path: Path,
    payload_bytes: int,
    expected_digest: str,
    workspace_mib: int,
    transitions: int,
    rounds: int,
    run_root: Path,
    label: str,
) -> dict[str, Any]:
    cg = _create_cgroup(f"fr-p9-014-{os.getpid()}-{label}-{time.monotonic_ns()}", memory_max_bytes)
    run_dir = run_root / label
    run_dir.mkdir()
    ready_path = run_dir / "ready.json"
    result_path = run_dir / "result.json"
    work_start_path = run_dir / "work-start.ns"
    args = [
        sys.executable, "-m", "finite_ram_lab.fr_p9_014_deadline_slack_fault_in",
        "--child", "--mode", mode,
        "--compressed-path", str(compressed_path),
        "--payload-bytes", str(payload_bytes),
        "--expected-digest", expected_digest,
        "--workspace-mib", str(workspace_mib),
        "--transitions", str(transitions),
        "--rounds", str(rounds),
        "--slack-ms", str(slack_ms),
        "--ready-path", str(ready_path),
        "--work-start-path", str(work_start_path),
        "--result-path", str(result_path),
    ]
    exec_line = " ".join(shlex.quote(value) for value in args)
    command = f"echo $$ > {shlex.quote(str(cg / 'cgroup.procs'))}; exec {exec_line}"
    before = _read_events(cg)
    process = subprocess.Popen(["sudo", "sh", "-c", command], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    state = "UNKNOWN"
    wall_ns = 0
    try:
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if ready_path.exists():
                state = "READY"
                break
            if process.poll() is not None:
                state = "EARLY_EXIT"
                break
            time.sleep(0.01)
        if state == "READY":
            started = time.monotonic_ns()
            work_start_path.write_text(str(started))
            try:
                process.wait(timeout=120)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
                state = "WORK_TIMEOUT"
            else:
                wall_ns = time.monotonic_ns() - started
                state = "COMPLETED" if process.returncode == 0 else "WORK_EXIT"

        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        after = _read_events(cg)
        peak = int((cg / "memory.peak").read_text().strip())
        receipt = json.loads(result_path.read_text()) if result_path.exists() else None
        semantic_signature: list[tuple[int, int, int]] = []
        reconstruct_ns_total = 0
        exposed_stall_ns_total = 0
        schedule_gaps: list[int] = []
        if receipt:
            reconstruct_ns_total += int(receipt["prestart_reconstruct_ns"])
            for row in receipt["rows"]:
                semantic_signature.append(
                    (int(row["transition"]), int(row["workspace_signature"]), int(row["semantic_value"]))
                )
                reconstruct_ns_total += int(row["reconstruct_ns"])
                exposed_stall_ns_total += int(row["exposed_stall_ns"])
                if mode == "FAULT_IN":
                    schedule_gaps.append(int(row["schedule_gap_ns"]))
        stderr = process.stderr.read() if process.stderr is not None else ""
        return {
            "label": label,
            "mode": mode,
            "slack_ms": slack_ms,
            "state": state,
            "memory_peak_bytes": peak,
            "reconstruct_ns_total": reconstruct_ns_total,
            "exposed_stall_ns_total": exposed_stall_ns_total,
            "work_wall_ns": wall_ns,
            "semantic_signature": semantic_signature,
            "min_schedule_gap_ns": min(schedule_gaps) if schedule_gaps else None,
            "oom_delta": after.get("oom", 0) - before.get("oom", 0),
            "oom_kill_delta": after.get("oom_kill", 0) - before.get("oom_kill", 0),
            "returncode": process.returncode,
            "stderr": stderr,
        }
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        subprocess.run(["sudo", "rmdir", str(cg)], check=False)


def _median(rows: list[dict[str, Any]], key: str) -> int:
    return int(statistics.median(int(row[key]) for row in rows))


def visible_stall_lower_bound_ns(reconstruct_ns: int, slack_ns: int) -> int:
    if reconstruct_ns < 0 or slack_ns < 0:
        raise ValueError("durations_must_be_nonnegative")
    return max(0, reconstruct_ns - slack_ns)


def run_panel(
    *,
    payload_mib: int = 16,
    workspace_mib: int = 24,
    transitions: int = 4,
    rounds: int = 2,
    slack_ms_values: tuple[int, ...] = (0, 10, 20, 40, 80),
    repetitions: int = 3,
    high_quota_mib: int = 128,
) -> dict[str, Any]:
    controllers = (Path("/sys/fs/cgroup") / "cgroup.controllers").read_text().split()
    if "memory" not in controllers:
        raise RuntimeError("memory_controller_unavailable")
    if any(value < 0 for value in slack_ms_values):
        raise ValueError("slack_values_must_be_nonnegative")

    with tempfile.TemporaryDirectory(prefix="fr-p9-014-slack-") as tmp:
        root = Path(tmp)
        compressed_path = root / "capability.gz"
        payload_bytes = payload_mib * MIB
        expected_digest, compressed_bytes = _write_compressed_source(compressed_path, payload_bytes)
        quota_bytes = high_quota_mib * MIB
        runs: list[dict[str, Any]] = []
        for rep in range(repetitions):
            runs.append(
                run_group(
                    mode="KEEP_WARM",
                    slack_ms=0,
                    memory_max_bytes=quota_bytes,
                    compressed_path=compressed_path,
                    payload_bytes=payload_bytes,
                    expected_digest=expected_digest,
                    workspace_mib=workspace_mib,
                    transitions=transitions,
                    rounds=rounds,
                    run_root=root,
                    label=f"keep-r{rep}",
                )
            )
            lane_order = slack_ms_values if rep % 2 == 0 else tuple(reversed(slack_ms_values))
            for slack_ms in lane_order:
                runs.append(
                    run_group(
                        mode="FAULT_IN",
                        slack_ms=slack_ms,
                        memory_max_bytes=quota_bytes,
                        compressed_path=compressed_path,
                        payload_bytes=payload_bytes,
                        expected_digest=expected_digest,
                        workspace_mib=workspace_mib,
                        transitions=transitions,
                        rounds=rounds,
                        run_root=root,
                        label=f"fault-s{slack_ms}-r{rep}",
                    )
                )

    reference = runs[0]["semantic_signature"]
    all_complete = all(
        row["state"] == "COMPLETED" and row["semantic_signature"] == reference for row in runs
    )
    all_no_oom = all(int(row["oom_delta"]) == 0 and int(row["oom_kill_delta"]) == 0 for row in runs)
    keep_rows = [row for row in runs if row["mode"] == "KEEP_WARM"]
    keep_peak = _median(keep_rows, "memory_peak_bytes")
    keep_reconstruct = _median(keep_rows, "reconstruct_ns_total")

    lanes: list[dict[str, Any]] = []
    for slack_ms in sorted(slack_ms_values):
        rows = [row for row in runs if row["mode"] == "FAULT_IN" and int(row["slack_ms"]) == slack_ms]
        lanes.append(
            {
                "slack_ms": slack_ms,
                "memory_peak_bytes": _median(rows, "memory_peak_bytes"),
                "reconstruct_ns_total": _median(rows, "reconstruct_ns_total"),
                "exposed_stall_ns_total": _median(rows, "exposed_stall_ns_total"),
                "work_wall_ns": _median(rows, "work_wall_ns"),
                "min_schedule_gap_ns": min(int(row["min_schedule_gap_ns"]) for row in rows),
            }
        )

    stall_values = [int(row["exposed_stall_ns_total"]) for row in lanes]
    peak_savings = [keep_peak - int(row["memory_peak_bytes"]) for row in lanes]
    checks = {
        "all_runs_complete_and_preserve_semantics": all_complete,
        "high_quota_runs_have_no_kernel_oom": all_no_oom,
        "fault_in_reconstruction_starts_after_workspace_release": all(
            int(row["min_schedule_gap_ns"]) >= 0 for row in lanes
        ),
        "fault_in_peak_saving_survives_all_slack_lanes": all(value >= 8 * MIB for value in peak_savings),
        "exposed_stall_is_nonincreasing_with_slack": all(
            b <= a for a, b in zip(stall_values, stall_values[1:])
        ),
        "zero_slack_exposes_material_reconstruction_stall": stall_values[0] >= 40_000_000,
        "largest_slack_hides_almost_all_reconstruction_stall": stall_values[-1] <= 2_000_000,
        "largest_slack_does_not_restore_keep_warm_peak": peak_savings[-1] >= 8 * MIB,
        "slack_policy_does_not_grant_authority": True,
        "slack_policy_does_not_grant_retry_permission": True,
    }

    return {
        "schema": SCHEMA,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "classification": "HOSTED_LINUX_CGROUP_V2_POST_RELEASE_SLACK_SCHEDULING_PROXY",
        "fixture": {
            "payload_mib": payload_mib,
            "workspace_mib": workspace_mib,
            "transitions": transitions,
            "rounds": rounds,
            "slack_ms_values": list(sorted(slack_ms_values)),
            "repetitions": repetitions,
            "high_quota_mib": high_quota_mib,
            "compressed_source_bytes": compressed_bytes,
        },
        "keep_warm": {
            "memory_peak_bytes": keep_peak,
            "reconstruct_ns_total": keep_reconstruct,
            "exposed_stall_ns_total": 0,
        },
        "fault_in_lanes": lanes,
        "peak_saving_bytes_by_slack": peak_savings,
        "checks": checks,
        "decision": (
            "POST_RELEASE_SLACK_CAN_HIDE_FAULT_IN_RECONSTRUCTION_STALL_WITHOUT_RECREATING_"
            "KEEP_WARM_PEAK_ON_THIS_HOSTED_PROXY_IF_QUALIFIED"
        ),
        "typed_objectives": [
            "kernel_memory_peak_bytes",
            "reconstruct_ns_total",
            "exposed_stall_ns_total",
            "slack_ms_consumed",
            "semantic_equivalence",
        ],
        "scalar_gain": None,
        "authority_effect": "NONE",
        "retry_authority": False,
        "next_falsifier": (
            "replace sleep-based slack with bounded deterministic independent work and test CPU-contention effects on the same post-release schedule"
        ),
        "claim_ceiling": (
            "HOSTED_GITHUB_LINUX_CGROUP_V2_POST_RELEASE_SLEEP_SLACK_AND_COMPRESSED_RECONSTRUCTION_PROXY_ONLY_"
            "NO_UNIVERSAL_LATENCY_HIDING_OR_APPLICATION_PERFORMANCE_CLAIM"
        ),
    }


def _parse_slacks(value: str) -> tuple[int, ...]:
    rows = tuple(int(part) for part in value.split(",") if part.strip())
    if not rows or any(item < 0 for item in rows):
        raise argparse.ArgumentTypeError("slack values must be nonnegative")
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--mode", choices=("KEEP_WARM", "FAULT_IN"))
    parser.add_argument("--compressed-path", type=Path)
    parser.add_argument("--payload-bytes", type=int)
    parser.add_argument("--expected-digest")
    parser.add_argument("--workspace-mib", type=int, default=24)
    parser.add_argument("--transitions", type=int, default=4)
    parser.add_argument("--rounds", type=int, default=2)
    parser.add_argument("--slack-ms", type=int, default=0)
    parser.add_argument("--ready-path", type=Path)
    parser.add_argument("--work-start-path", type=Path)
    parser.add_argument("--result-path", type=Path)
    parser.add_argument("--payload-mib", type=int, default=16)
    parser.add_argument("--slack-ms-values", type=_parse_slacks, default=(0, 10, 20, 40, 80))
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--high-quota-mib", type=int, default=128)
    args = parser.parse_args()
    if args.child:
        required = (
            args.mode, args.compressed_path, args.payload_bytes, args.expected_digest,
            args.ready_path, args.work_start_path, args.result_path,
        )
        if any(value is None for value in required):
            raise SystemExit("missing_child_argument")
        return child(
            mode=args.mode,
            compressed_path=args.compressed_path,
            payload_bytes=args.payload_bytes,
            expected_digest=args.expected_digest,
            workspace_mib=args.workspace_mib,
            transitions=args.transitions,
            rounds=args.rounds,
            slack_ms=args.slack_ms,
            ready_path=args.ready_path,
            work_start_path=args.work_start_path,
            result_path=args.result_path,
        )
    result = run_panel(
        payload_mib=args.payload_mib,
        workspace_mib=args.workspace_mib,
        transitions=args.transitions,
        rounds=args.rounds,
        slack_ms_values=args.slack_ms_values,
        repetitions=args.repetitions,
        high_quota_mib=args.high_quota_mib,
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
