from __future__ import annotations

import argparse
import json
import math
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
from finite_ram_lab.fr_p9_015_cpu_contention_slack import _consume_cpu_for_ns, _pin_one_cpu

SCHEMA = "finite-ram-lab.fr-p9-016-cpu-service-fraction/v0.1"


def _duty_window(*, duration_ms: int, busy_percent: int, quantum_us: int = 2000) -> tuple[int, int]:
    if duration_ms <= 0:
        raise ValueError("duration_ms_must_be_positive")
    if not 0 <= busy_percent <= 100:
        raise ValueError("busy_percent_out_of_range")
    if quantum_us <= 0:
        raise ValueError("quantum_us_must_be_positive")
    started = time.monotonic_ns()
    deadline = started + duration_ms * 1_000_000
    busy_elapsed = 0
    quantum_ns = quantum_us * 1000
    while True:
        now = time.monotonic_ns()
        if now >= deadline:
            break
        segment_ns = min(quantum_ns, deadline - now)
        busy_ns = segment_ns * busy_percent // 100
        if busy_ns:
            elapsed, _ = _consume_cpu_for_ns(busy_ns)
            busy_elapsed += elapsed
        remaining = min(deadline, now + segment_ns) - time.monotonic_ns()
        if remaining > 0:
            time.sleep(remaining / 1_000_000_000)
    return time.monotonic_ns() - started, busy_elapsed


def _pearson(xs: list[float], ys: list[float]) -> float:
    if len(xs) != len(ys) or len(xs) < 2:
        raise ValueError("correlation_requires_equal_vectors")
    mx = statistics.fmean(xs)
    my = statistics.fmean(ys)
    dx = [x - mx for x in xs]
    dy = [y - my for y in ys]
    den = math.sqrt(sum(v * v for v in dx) * sum(v * v for v in dy))
    return 0.0 if den == 0 else sum(a * b for a, b in zip(dx, dy)) / den


def child(
    *, mode: str, busy_percent: int, slack_ms: int, compressed_path: Path, payload_bytes: int,
    expected_digest: str, workspace_mib: int, transitions: int, rounds: int,
    ready_path: Path, work_start_path: Path, result_path: Path,
) -> int:
    if mode not in {"KEEP_WARM", "FAULT_IN"}:
        raise ValueError(f"unknown_mode:{mode}")
    if not 0 <= busy_percent <= 100:
        raise ValueError("busy_percent_out_of_range")
    pinned_cpu = _pin_one_cpu()
    capability = None
    prestart_reconstruct_ns = 0
    if mode == "KEEP_WARM":
        started = time.monotonic_ns()
        capability, _ = _reconstruct_capability(
            compressed_path, payload_bytes=payload_bytes, expected_digest=expected_digest
        )
        prestart_reconstruct_ns = time.monotonic_ns() - started
    _atomic_json(ready_path, {"pid": os.getpid(), "mode": mode, "busy_percent": busy_percent, "pinned_cpu": pinned_cpu})
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
        reconstruct_ns = 0
        exposed_stall_ns = 0
        schedule_gap_ns = 0
        slack_elapsed_ns = 0
        busy_elapsed_ns = 0
        if mode == "FAULT_IN":
            reconstruction: dict[str, Any] = {}
            error: list[BaseException] = []

            def reconstruct() -> None:
                try:
                    reconstruction["start_ns"] = time.monotonic_ns()
                    cap, _ = _reconstruct_capability(
                        compressed_path, payload_bytes=payload_bytes, expected_digest=expected_digest
                    )
                    reconstruction["capability"] = cap
                    reconstruction["done_ns"] = time.monotonic_ns()
                except BaseException as exc:
                    error.append(exc)

            thread = threading.Thread(target=reconstruct, name=f"fault-in-{transition}")
            thread.start()
            slack_elapsed_ns, busy_elapsed_ns = _duty_window(duration_ms=slack_ms, busy_percent=busy_percent)
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

        work_started_ns = time.monotonic_ns()
        semantic_value = _stride_work(capability, transition=transition, rounds=rounds)
        work_ns = time.monotonic_ns() - work_started_ns
        rows.append({
            "transition": transition, "workspace_signature": workspace_sig, "semantic_value": semantic_value,
            "workspace_close_ns": workspace_close_ns, "schedule_gap_ns": schedule_gap_ns,
            "reconstruct_ns": reconstruct_ns, "exposed_stall_ns": exposed_stall_ns,
            "slack_elapsed_ns": slack_elapsed_ns, "busy_elapsed_ns": busy_elapsed_ns, "work_ns": work_ns,
        })
        if mode == "FAULT_IN":
            capability.close(); capability = None
    if capability is not None:
        capability.close()
    _atomic_json(result_path, {
        "mode": mode, "busy_percent": busy_percent, "slack_ms": slack_ms,
        "pinned_cpu": pinned_cpu, "affinity": sorted(os.sched_getaffinity(0)),
        "prestart_reconstruct_ns": prestart_reconstruct_ns, "rows": rows,
    })
    return 0


def run_group(
    *, mode: str, busy_percent: int, slack_ms: int, memory_max_bytes: int,
    compressed_path: Path, payload_bytes: int, expected_digest: str, workspace_mib: int,
    transitions: int, rounds: int, run_root: Path, label: str,
) -> dict[str, Any]:
    cg = _create_cgroup(f"fr-p9-016-{os.getpid()}-{label}-{time.monotonic_ns()}", memory_max_bytes)
    run_dir = run_root / label; run_dir.mkdir()
    ready_path = run_dir / "ready.json"; result_path = run_dir / "result.json"; work_start_path = run_dir / "work-start.ns"
    args = [
        sys.executable, "-m", "finite_ram_lab.fr_p9_016_cpu_service_fraction", "--child",
        "--mode", mode, "--busy-percent", str(busy_percent), "--slack-ms", str(slack_ms),
        "--compressed-path", str(compressed_path), "--payload-bytes", str(payload_bytes),
        "--expected-digest", expected_digest, "--workspace-mib", str(workspace_mib),
        "--transitions", str(transitions), "--rounds", str(rounds), "--ready-path", str(ready_path),
        "--work-start-path", str(work_start_path), "--result-path", str(result_path),
    ]
    exec_line = " ".join(shlex.quote(v) for v in args)
    command = f"echo $$ > {shlex.quote(str(cg / 'cgroup.procs'))}; exec {exec_line}"
    before = _read_events(cg)
    process = subprocess.Popen(["sudo", "sh", "-c", command], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    state = "UNKNOWN"; wall_ns = 0
    try:
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if ready_path.exists(): state = "READY"; break
            if process.poll() is not None: state = "EARLY_EXIT"; break
            time.sleep(0.01)
        if state == "READY":
            started = time.monotonic_ns(); work_start_path.write_text(str(started))
            try:
                process.wait(timeout=120)
            except subprocess.TimeoutExpired:
                process.kill(); process.wait(timeout=5); state = "WORK_TIMEOUT"
            else:
                wall_ns = time.monotonic_ns() - started
                state = "COMPLETED" if process.returncode == 0 else "WORK_EXIT"
        if process.poll() is None:
            process.kill(); process.wait(timeout=5)
        after = _read_events(cg)
        peak = int((cg / "memory.peak").read_text().strip())
        receipt = json.loads(result_path.read_text()) if result_path.exists() else None
        semantic_signature: list[tuple[int, int, int]] = []
        reconstruct_ns_total = exposed_stall_ns_total = slack_elapsed_ns_total = busy_elapsed_ns_total = 0
        schedule_gaps: list[int] = []; pinned_cpu = None; affinity: list[int] = []
        if receipt:
            pinned_cpu = int(receipt["pinned_cpu"]); affinity = [int(v) for v in receipt["affinity"]]
            reconstruct_ns_total = int(receipt["prestart_reconstruct_ns"])
            for row in receipt["rows"]:
                semantic_signature.append((int(row["transition"]), int(row["workspace_signature"]), int(row["semantic_value"])))
                reconstruct_ns_total += int(row["reconstruct_ns"])
                exposed_stall_ns_total += int(row["exposed_stall_ns"])
                slack_elapsed_ns_total += int(row["slack_elapsed_ns"])
                busy_elapsed_ns_total += int(row["busy_elapsed_ns"])
                if mode == "FAULT_IN": schedule_gaps.append(int(row["schedule_gap_ns"]))
        return {
            "label": label, "mode": mode, "busy_percent": busy_percent, "state": state,
            "memory_peak_bytes": peak, "reconstruct_ns_total": reconstruct_ns_total,
            "exposed_stall_ns_total": exposed_stall_ns_total, "slack_elapsed_ns_total": slack_elapsed_ns_total,
            "busy_elapsed_ns_total": busy_elapsed_ns_total, "work_wall_ns": wall_ns,
            "semantic_signature": semantic_signature, "min_schedule_gap_ns": min(schedule_gaps) if schedule_gaps else None,
            "pinned_cpu": pinned_cpu, "affinity": affinity,
            "oom_delta": after.get("oom", 0) - before.get("oom", 0),
            "oom_kill_delta": after.get("oom_kill", 0) - before.get("oom_kill", 0),
            "returncode": process.returncode,
            "stderr": process.stderr.read() if process.stderr is not None else "",
        }
    finally:
        if process.poll() is None: process.kill(); process.wait(timeout=5)
        subprocess.run(["sudo", "rmdir", str(cg)], check=False)


def _median(rows: list[dict[str, Any]], key: str) -> int:
    return int(statistics.median(int(r[key]) for r in rows))


def service_budget(slack_ms: int, busy_percent: int) -> int:
    if slack_ms < 0 or not 0 <= busy_percent <= 100:
        raise ValueError("invalid_service_budget_input")
    return slack_ms * 1_000_000 * (100 - busy_percent) // 100


def run_panel(
    *, payload_mib: int = 16, workspace_mib: int = 24, transitions: int = 4, rounds: int = 2,
    slack_ms: int = 40, busy_percents: tuple[int, ...] = (0, 25, 50, 75, 100), repetitions: int = 3,
    high_quota_mib: int = 128,
) -> dict[str, Any]:
    if "memory" not in (Path("/sys/fs/cgroup") / "cgroup.controllers").read_text().split():
        raise RuntimeError("memory_controller_unavailable")
    if tuple(sorted(set(busy_percents))) != tuple(busy_percents) or busy_percents[0] != 0 or busy_percents[-1] != 100:
        raise ValueError("busy_percents_must_be_unique_sorted_and_span_0_to_100")
    with tempfile.TemporaryDirectory(prefix="fr-p9-016-service-") as tmp:
        root = Path(tmp); compressed_path = root / "capability.gz"; payload_bytes = payload_mib * MIB
        expected_digest, compressed_bytes = _write_compressed_source(compressed_path, payload_bytes)
        quota_bytes = high_quota_mib * MIB; runs: list[dict[str, Any]] = []
        for rep in range(repetitions):
            runs.append(run_group(mode="KEEP_WARM", busy_percent=0, slack_ms=slack_ms,
                memory_max_bytes=quota_bytes, compressed_path=compressed_path, payload_bytes=payload_bytes,
                expected_digest=expected_digest, workspace_mib=workspace_mib, transitions=transitions,
                rounds=rounds, run_root=root, label=f"keep-r{rep}"))
            order = busy_percents if rep % 2 == 0 else tuple(reversed(busy_percents))
            for duty in order:
                runs.append(run_group(mode="FAULT_IN", busy_percent=duty, slack_ms=slack_ms,
                    memory_max_bytes=quota_bytes, compressed_path=compressed_path, payload_bytes=payload_bytes,
                    expected_digest=expected_digest, workspace_mib=workspace_mib, transitions=transitions,
                    rounds=rounds, run_root=root, label=f"fault-b{duty}-r{rep}"))

    reference = runs[0]["semantic_signature"]
    all_complete = all(r["state"] == "COMPLETED" and r["semantic_signature"] == reference for r in runs)
    all_no_oom = all(int(r["oom_delta"]) == 0 and int(r["oom_kill_delta"]) == 0 for r in runs)
    all_single_cpu = all(len(r["affinity"]) == 1 and r["pinned_cpu"] == r["affinity"][0] for r in runs)
    keep_rows = [r for r in runs if r["mode"] == "KEEP_WARM"]; keep_peak = _median(keep_rows, "memory_peak_bytes")
    lanes: list[dict[str, Any]] = []
    for duty in busy_percents:
        rows = [r for r in runs if r["mode"] == "FAULT_IN" and int(r["busy_percent"]) == duty]
        slack_elapsed = _median(rows, "slack_elapsed_ns_total"); busy_elapsed = _median(rows, "busy_elapsed_ns_total")
        lanes.append({
            "busy_percent": duty, "nominal_yield_budget_ns_per_transition": service_budget(slack_ms, duty),
            "memory_peak_bytes": _median(rows, "memory_peak_bytes"),
            "reconstruct_ns_total": _median(rows, "reconstruct_ns_total"),
            "exposed_stall_ns_total": _median(rows, "exposed_stall_ns_total"),
            "slack_elapsed_ns_total": slack_elapsed, "busy_elapsed_ns_total": busy_elapsed,
            "observed_busy_fraction": (busy_elapsed / slack_elapsed) if slack_elapsed else 0.0,
            "work_wall_ns": _median(rows, "work_wall_ns"),
            "min_schedule_gap_ns": min(int(r["min_schedule_gap_ns"]) for r in rows),
        })
    duties = [float(l["busy_percent"]) for l in lanes]
    reconstruct = [float(l["reconstruct_ns_total"]) for l in lanes]
    stall = [float(l["exposed_stall_ns_total"]) for l in lanes]
    observed = [float(l["observed_busy_fraction"]) for l in lanes]
    r_reconstruct = _pearson(duties, reconstruct); r_stall = _pearson(duties, stall)
    first_material = next((int(l["busy_percent"]) for l in lanes if int(l["exposed_stall_ns_total"]) >= 5_000_000), None)
    interior = [l for l in lanes if 0 < int(l["busy_percent"]) < 100]
    endpoint_lo = int(lanes[0]["reconstruct_ns_total"]); endpoint_hi = int(lanes[-1]["reconstruct_ns_total"])
    checks = {
        "all_runs_complete_and_preserve_semantics": all_complete,
        "high_quota_runs_have_no_kernel_oom": all_no_oom,
        "all_runs_are_pinned_to_exactly_one_cpu": all_single_cpu,
        "reconstruction_starts_after_workspace_release": all(int(l["min_schedule_gap_ns"]) >= 0 for l in lanes),
        "all_fault_lanes_preserve_peak_saving": all(keep_peak - int(l["memory_peak_bytes"]) >= 8 * MIB for l in lanes),
        "observed_busy_fraction_increases_with_requested_duty": all(b >= a for a, b in zip(observed, observed[1:])),
        "zero_busy_hides_almost_all_stall": int(lanes[0]["exposed_stall_ns_total"]) <= 5_000_000,
        "full_busy_exposes_material_stall": int(lanes[-1]["exposed_stall_ns_total"]) >= 5_000_000,
        "full_busy_adds_at_least_50ms_reconstruction_elapsed": endpoint_hi - endpoint_lo >= 50_000_000,
        "reconstruction_elapsed_correlates_with_busy_fraction": r_reconstruct >= 0.80,
        "exposed_stall_correlates_with_busy_fraction": r_stall >= 0.70,
        "an_interior_duty_produces_intermediate_reconstruction_cost": any(
            endpoint_lo + 5_000_000 < int(l["reconstruct_ns_total"]) < endpoint_hi - 5_000_000 for l in interior
        ),
        "service_fraction_policy_does_not_grant_authority": True,
        "service_fraction_policy_does_not_grant_retry_permission": True,
    }
    return {
        "schema": SCHEMA, "status": "PASS" if all(checks.values()) else "FAIL",
        "classification": "HOSTED_LINUX_SINGLE_CPU_SERVICE_FRACTION_SWEEP_PROXY",
        "fixture": {"payload_mib": payload_mib, "workspace_mib": workspace_mib, "transitions": transitions,
                    "rounds": rounds, "slack_ms": slack_ms, "busy_percents": list(busy_percents),
                    "repetitions": repetitions, "high_quota_mib": high_quota_mib,
                    "compressed_source_bytes": compressed_bytes},
        "keep_warm": {"memory_peak_bytes": keep_peak}, "lanes": lanes,
        "correlation_busy_vs_reconstruct": r_reconstruct, "correlation_busy_vs_exposed_stall": r_stall,
        "first_material_stall_busy_percent": first_material, "checks": checks,
        "decision": "WALL_CLOCK_SLACK_SHOULD_COMPILE_TO_A_RESOURCE_SERVICE_BUDGET_NOT_DURATION_ALONE_IF_QUALIFIED",
        "claim_ceiling": "HOSTED_GITHUB_LINUX_SINGLE_CPU_DUTY_CYCLE_PYTHON_THREAD_GZIP_PROXY_ONLY_NO_UNIVERSAL_CPU_SHARE_OR_SCHEDULER_CLAIM",
        "authority_effect": "NONE", "retry_authority": False, "scalar_gain": None,
    }


def main() -> int:
    p = argparse.ArgumentParser(); p.add_argument("--child", action="store_true"); p.add_argument("--mode", default="FAULT_IN")
    p.add_argument("--busy-percent", type=int, default=0); p.add_argument("--busy-percents", default="0,25,50,75,100")
    p.add_argument("--slack-ms", type=int, default=40); p.add_argument("--compressed-path", type=Path); p.add_argument("--payload-bytes", type=int)
    p.add_argument("--expected-digest"); p.add_argument("--workspace-mib", type=int, default=24); p.add_argument("--transitions", type=int, default=4)
    p.add_argument("--rounds", type=int, default=2); p.add_argument("--ready-path", type=Path); p.add_argument("--work-start-path", type=Path)
    p.add_argument("--result-path", type=Path); p.add_argument("--payload-mib", type=int, default=16); p.add_argument("--repetitions", type=int, default=3)
    p.add_argument("--high-quota-mib", type=int, default=128); a = p.parse_args()
    if a.child:
        required = [a.compressed_path, a.payload_bytes, a.expected_digest, a.ready_path, a.work_start_path, a.result_path]
        if any(v is None for v in required): raise SystemExit("child arguments missing")
        return child(mode=a.mode, busy_percent=a.busy_percent, slack_ms=a.slack_ms, compressed_path=a.compressed_path,
            payload_bytes=a.payload_bytes, expected_digest=a.expected_digest, workspace_mib=a.workspace_mib,
            transitions=a.transitions, rounds=a.rounds, ready_path=a.ready_path, work_start_path=a.work_start_path, result_path=a.result_path)
    duties = tuple(int(v) for v in a.busy_percents.split(",") if v)
    result = run_panel(payload_mib=a.payload_mib, workspace_mib=a.workspace_mib, transitions=a.transitions, rounds=a.rounds,
        slack_ms=a.slack_ms, busy_percents=duties, repetitions=a.repetitions, high_quota_mib=a.high_quota_mib)
    json.dump(result, sys.stdout, sort_keys=True, indent=2); sys.stdout.write("\n")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
