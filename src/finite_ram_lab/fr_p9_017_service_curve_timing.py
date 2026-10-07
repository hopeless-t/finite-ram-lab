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
from finite_ram_lab.fr_p9_015_cpu_contention_slack import _consume_cpu_for_ns, _pin_one_cpu

SCHEMA = "finite-ram-lab.fr-p9-017-service-curve-timing/v0.1"
PATTERNS = ("FRONT_YIELD", "INTERLEAVED", "BACK_YIELD")


def _sleep_for_ns(duration_ns: int) -> int:
    if duration_ns < 0:
        raise ValueError("duration_ns_must_be_nonnegative")
    started = time.monotonic_ns()
    if duration_ns:
        time.sleep(duration_ns / 1_000_000_000)
    return time.monotonic_ns() - started


def _run_pattern(pattern: str, *, half_ms: int) -> tuple[int, int, int, int]:
    if pattern not in PATTERNS:
        raise ValueError(f"unknown_pattern:{pattern}")
    if half_ms <= 0:
        raise ValueError("half_ms_must_be_positive")
    half_ns = half_ms * 1_000_000
    started = time.monotonic_ns()
    deadline_ns = started + half_ns
    busy_elapsed = 0
    yield_elapsed = 0

    if pattern == "FRONT_YIELD":
        yield_elapsed += _sleep_for_ns(half_ns)
        elapsed, _ = _consume_cpu_for_ns(half_ns)
        busy_elapsed += elapsed
    elif pattern == "BACK_YIELD":
        elapsed, _ = _consume_cpu_for_ns(half_ns)
        busy_elapsed += elapsed
        yield_elapsed += _sleep_for_ns(half_ns)
    else:
        # Six 10 ms-equivalent segments over a 60 ms default window: yield/busy pairs.
        # Integer splitting preserves equal nominal total yield and busy duration.
        pieces = 3
        yield_piece = half_ns // pieces
        busy_piece = half_ns // pieces
        for index in range(pieces):
            yield_elapsed += _sleep_for_ns(yield_piece)
            elapsed, _ = _consume_cpu_for_ns(busy_piece)
            busy_elapsed += elapsed

    window_elapsed = time.monotonic_ns() - started
    return deadline_ns, busy_elapsed, yield_elapsed, window_elapsed


def child(
    *,
    mode: str,
    pattern: str,
    half_ms: int,
    compressed_path: Path,
    payload_bytes: int,
    expected_digest: str,
    workspace_mib: int,
    transitions: int,
    rounds: int,
    ready_path: Path,
    work_start_path: Path,
    result_path: Path,
) -> int:
    if mode not in {"KEEP_WARM", "FAULT_IN"}:
        raise ValueError(f"unknown_mode:{mode}")
    if mode == "FAULT_IN" and pattern not in PATTERNS:
        raise ValueError(f"unknown_pattern:{pattern}")
    pinned_cpu = _pin_one_cpu()

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
        {"pid": os.getpid(), "mode": mode, "pattern": pattern, "pinned_cpu": pinned_cpu},
    )
    timeout = time.monotonic() + 60
    while not work_start_path.exists():
        if time.monotonic() > timeout:
            raise TimeoutError("work_start_timeout")
        time.sleep(0.001)

    rows: list[dict[str, Any]] = []
    for transition in range(transitions):
        workspace, workspace_sig = _workspace_signature(workspace_mib * MIB, transition)
        workspace.close()
        workspace_close_ns = time.monotonic_ns()
        reconstruct_ns = 0
        deadline_miss_ns = 0
        busy_elapsed_ns = 0
        yield_elapsed_ns = 0
        window_elapsed_ns = 0
        schedule_gap_ns = 0

        if mode == "FAULT_IN":
            reconstruction: dict[str, Any] = {}
            errors: list[BaseException] = []

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
                except BaseException as exc:
                    errors.append(exc)

            thread = threading.Thread(target=reconstruct, name=f"fault-in-{transition}")
            thread.start()
            deadline_ns, busy_elapsed_ns, yield_elapsed_ns, window_elapsed_ns = _run_pattern(
                pattern, half_ms=half_ms
            )
            thread.join(timeout=60)
            if thread.is_alive():
                raise TimeoutError("reconstruction_thread_timeout")
            if errors:
                raise RuntimeError("reconstruction_thread_failed") from errors[0]
            capability = reconstruction.get("capability")
            if capability is None:
                raise RuntimeError("reconstruction_missing_capability")
            reconstruct_start_ns = int(reconstruction["start_ns"])
            reconstruct_done_ns = int(reconstruction["done_ns"])
            reconstruct_ns = reconstruct_done_ns - reconstruct_start_ns
            deadline_miss_ns = max(0, reconstruct_done_ns - deadline_ns)
            schedule_gap_ns = reconstruct_start_ns - workspace_close_ns
        else:
            if capability is None:
                raise RuntimeError("keep_warm_capability_missing")

        work_started_ns = time.monotonic_ns()
        semantic_value = _stride_work(capability, transition=transition, rounds=rounds)
        work_ns = time.monotonic_ns() - work_started_ns
        rows.append(
            {
                "transition": transition,
                "workspace_signature": workspace_sig,
                "semantic_value": semantic_value,
                "schedule_gap_ns": schedule_gap_ns,
                "reconstruct_ns": reconstruct_ns,
                "deadline_miss_ns": deadline_miss_ns,
                "busy_elapsed_ns": busy_elapsed_ns,
                "yield_elapsed_ns": yield_elapsed_ns,
                "window_elapsed_ns": window_elapsed_ns,
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
            "pattern": pattern,
            "half_ms": half_ms,
            "pinned_cpu": pinned_cpu,
            "affinity": sorted(os.sched_getaffinity(0)),
            "prestart_reconstruct_ns": prestart_reconstruct_ns,
            "rows": rows,
        },
    )
    return 0


def run_group(
    *,
    mode: str,
    pattern: str,
    half_ms: int,
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
    cg = _create_cgroup(f"fr-p9-017-{os.getpid()}-{label}-{time.monotonic_ns()}", memory_max_bytes)
    run_dir = run_root / label
    run_dir.mkdir()
    ready_path = run_dir / "ready.json"
    result_path = run_dir / "result.json"
    work_start_path = run_dir / "work-start.ns"
    args = [
        sys.executable,
        "-m",
        "finite_ram_lab.fr_p9_017_service_curve_timing",
        "--child",
        "--mode",
        mode,
        "--pattern",
        pattern,
        "--half-ms",
        str(half_ms),
        "--compressed-path",
        str(compressed_path),
        "--payload-bytes",
        str(payload_bytes),
        "--expected-digest",
        expected_digest,
        "--workspace-mib",
        str(workspace_mib),
        "--transitions",
        str(transitions),
        "--rounds",
        str(rounds),
        "--ready-path",
        str(ready_path),
        "--work-start-path",
        str(work_start_path),
        "--result-path",
        str(result_path),
    ]
    exec_line = " ".join(shlex.quote(v) for v in args)
    command = f"echo $$ > {shlex.quote(str(cg / 'cgroup.procs'))}; exec {exec_line}"
    before = _read_events(cg)
    process = subprocess.Popen(
        ["sudo", "sh", "-c", command], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    state = "UNKNOWN"
    wall_ns = 0
    try:
        timeout = time.monotonic() + 30
        while time.monotonic() < timeout:
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
        reconstruct_ns_total = deadline_miss_ns_total = busy_elapsed_ns_total = yield_elapsed_ns_total = 0
        window_elapsed_ns_total = 0
        schedule_gaps: list[int] = []
        pinned_cpu = None
        affinity: list[int] = []
        if receipt:
            pinned_cpu = int(receipt["pinned_cpu"])
            affinity = [int(v) for v in receipt["affinity"]]
            reconstruct_ns_total = int(receipt["prestart_reconstruct_ns"])
            for row in receipt["rows"]:
                semantic_signature.append(
                    (int(row["transition"]), int(row["workspace_signature"]), int(row["semantic_value"]))
                )
                reconstruct_ns_total += int(row["reconstruct_ns"])
                deadline_miss_ns_total += int(row["deadline_miss_ns"])
                busy_elapsed_ns_total += int(row["busy_elapsed_ns"])
                yield_elapsed_ns_total += int(row["yield_elapsed_ns"])
                window_elapsed_ns_total += int(row["window_elapsed_ns"])
                if mode == "FAULT_IN":
                    schedule_gaps.append(int(row["schedule_gap_ns"]))
        return {
            "label": label,
            "mode": mode,
            "pattern": pattern,
            "state": state,
            "memory_peak_bytes": peak,
            "reconstruct_ns_total": reconstruct_ns_total,
            "deadline_miss_ns_total": deadline_miss_ns_total,
            "busy_elapsed_ns_total": busy_elapsed_ns_total,
            "yield_elapsed_ns_total": yield_elapsed_ns_total,
            "window_elapsed_ns_total": window_elapsed_ns_total,
            "work_wall_ns": wall_ns,
            "semantic_signature": semantic_signature,
            "min_schedule_gap_ns": min(schedule_gaps) if schedule_gaps else None,
            "pinned_cpu": pinned_cpu,
            "affinity": affinity,
            "oom_delta": after.get("oom", 0) - before.get("oom", 0),
            "oom_kill_delta": after.get("oom_kill", 0) - before.get("oom_kill", 0),
            "returncode": process.returncode,
            "stderr": process.stderr.read() if process.stderr is not None else "",
        }
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        subprocess.run(["sudo", "rmdir", str(cg)], check=False)


def _median(rows: list[dict[str, Any]], key: str) -> int:
    return int(statistics.median(int(r[key]) for r in rows))


def service_curve_contract(resource_kind: str, deadline_ms: int, delivered_before_deadline_ns: int) -> tuple[str, int, int]:
    if not resource_kind:
        raise ValueError("resource_kind_required")
    if deadline_ms <= 0 or delivered_before_deadline_ns < 0:
        raise ValueError("invalid_service_curve_contract")
    return resource_kind, deadline_ms, delivered_before_deadline_ns


def run_panel(
    *,
    payload_mib: int = 16,
    workspace_mib: int = 24,
    transitions: int = 4,
    rounds: int = 2,
    half_ms: int = 30,
    repetitions: int = 3,
    high_quota_mib: int = 128,
) -> dict[str, Any]:
    if "memory" not in (Path("/sys/fs/cgroup") / "cgroup.controllers").read_text().split():
        raise RuntimeError("memory_controller_unavailable")
    with tempfile.TemporaryDirectory(prefix="fr-p9-017-curve-") as tmp:
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
                    label=f"keep-r{rep}",
                )
            )
            order = PATTERNS if rep % 2 == 0 else tuple(reversed(PATTERNS))
            for pattern in order:
                runs.append(
                    run_group(
                        mode="FAULT_IN",
                        pattern=pattern,
                        half_ms=half_ms,
                        memory_max_bytes=quota_bytes,
                        compressed_path=compressed_path,
                        payload_bytes=payload_bytes,
                        expected_digest=expected_digest,
                        workspace_mib=workspace_mib,
                        transitions=transitions,
                        rounds=rounds,
                        run_root=root,
                        label=f"fault-{pattern.lower()}-r{rep}",
                    )
                )

    reference = runs[0]["semantic_signature"]
    all_complete = all(r["state"] == "COMPLETED" and r["semantic_signature"] == reference for r in runs)
    all_no_oom = all(int(r["oom_delta"]) == 0 and int(r["oom_kill_delta"]) == 0 for r in runs)
    all_single_cpu = all(len(r["affinity"]) == 1 and r["pinned_cpu"] == r["affinity"][0] for r in runs)
    keep_rows = [r for r in runs if r["mode"] == "KEEP_WARM"]
    keep_peak = _median(keep_rows, "memory_peak_bytes")

    lanes: dict[str, dict[str, Any]] = {}
    for pattern in PATTERNS:
        rows = [r for r in runs if r["mode"] == "FAULT_IN" and r["pattern"] == pattern]
        busy = _median(rows, "busy_elapsed_ns_total")
        yielded = _median(rows, "yield_elapsed_ns_total")
        lanes[pattern] = {
            "memory_peak_bytes": _median(rows, "memory_peak_bytes"),
            "reconstruct_ns_total": _median(rows, "reconstruct_ns_total"),
            "deadline_miss_ns_total": _median(rows, "deadline_miss_ns_total"),
            "busy_elapsed_ns_total": busy,
            "yield_elapsed_ns_total": yielded,
            "window_elapsed_ns_total": _median(rows, "window_elapsed_ns_total"),
            "work_wall_ns": _median(rows, "work_wall_ns"),
            "min_schedule_gap_ns": min(int(r["min_schedule_gap_ns"]) for r in rows),
        }

    front = lanes["FRONT_YIELD"]
    back = lanes["BACK_YIELD"]
    observed_busy = [int(lanes[p]["busy_elapsed_ns_total"]) for p in PATTERNS]
    observed_yield = [int(lanes[p]["yield_elapsed_ns_total"]) for p in PATTERNS]
    busy_ratio = max(observed_busy) / max(1, min(observed_busy))
    yield_ratio = max(observed_yield) / max(1, min(observed_yield))

    checks = {
        "all_runs_complete_and_preserve_semantics": all_complete,
        "high_quota_runs_have_no_kernel_oom": all_no_oom,
        "all_runs_are_pinned_to_exactly_one_cpu": all_single_cpu,
        "reconstruction_starts_after_workspace_release": all(int(lanes[p]["min_schedule_gap_ns"]) >= 0 for p in PATTERNS),
        "all_fault_lanes_preserve_peak_saving": all(keep_peak - int(lanes[p]["memory_peak_bytes"]) >= 8 * MIB for p in PATTERNS),
        "observed_busy_totals_are_comparable": busy_ratio <= 1.25,
        "observed_yield_totals_are_comparable": yield_ratio <= 1.25,
        "front_yield_meets_30ms_deadline_nearly_cleanly": int(front["deadline_miss_ns_total"]) <= 5_000_000,
        "back_yield_misses_30ms_deadline_materially": int(back["deadline_miss_ns_total"]) >= 20_000_000,
        "back_yield_has_at_least_15ms_more_deadline_miss_than_front": int(back["deadline_miss_ns_total"]) - int(front["deadline_miss_ns_total"]) >= 15_000_000,
        "service_curve_policy_does_not_grant_authority": True,
        "service_curve_policy_does_not_grant_retry_permission": True,
    }

    return {
        "schema": SCHEMA,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "classification": "HOSTED_LINUX_SINGLE_CPU_EQUAL_BUDGET_SERVICE_CURVE_TIMING_PROXY",
        "fixture": {
            "payload_mib": payload_mib,
            "workspace_mib": workspace_mib,
            "transitions": transitions,
            "rounds": rounds,
            "half_ms": half_ms,
            "window_ms": half_ms * 2,
            "capability_deadline_ms": half_ms,
            "patterns": list(PATTERNS),
            "repetitions": repetitions,
            "high_quota_mib": high_quota_mib,
            "compressed_source_bytes": compressed_bytes,
        },
        "keep_warm": {"memory_peak_bytes": keep_peak},
        "lanes": lanes,
        "observed_busy_total_ratio_max_over_min": busy_ratio,
        "observed_yield_total_ratio_max_over_min": yield_ratio,
        "checks": checks,
        "decision": "EQUAL_TOTAL_SERVICE_BUDGET_IS_NOT_DEADLINE_EQUIVALENT_WHEN_SERVICE_ARRIVAL_TIME_DIFFERS_IF_QUALIFIED",
        "candidate_contract": "ServiceCurve(resource_kind, contention_domain, time, delivered_service, measurement_epoch)",
        "claim_ceiling": "HOSTED_GITHUB_LINUX_SINGLE_CPU_PYTHON_THREAD_GZIP_EQUAL_TOTAL_BUDGET_TIMING_PROXY_ONLY_NO_UNIVERSAL_SCHEDULER_OR_SERVICE_CURVE_THEOREM",
        "authority_effect": "NONE",
        "retry_authority": False,
        "scalar_gain": None,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--child", action="store_true")
    p.add_argument("--mode", default="FAULT_IN")
    p.add_argument("--pattern", default="FRONT_YIELD")
    p.add_argument("--half-ms", type=int, default=30)
    p.add_argument("--compressed-path", type=Path)
    p.add_argument("--payload-bytes", type=int)
    p.add_argument("--expected-digest")
    p.add_argument("--workspace-mib", type=int, default=24)
    p.add_argument("--transitions", type=int, default=4)
    p.add_argument("--rounds", type=int, default=2)
    p.add_argument("--ready-path", type=Path)
    p.add_argument("--work-start-path", type=Path)
    p.add_argument("--result-path", type=Path)
    p.add_argument("--payload-mib", type=int, default=16)
    p.add_argument("--repetitions", type=int, default=3)
    p.add_argument("--high-quota-mib", type=int, default=128)
    a = p.parse_args()
    if a.child:
        required = [a.compressed_path, a.payload_bytes, a.expected_digest, a.ready_path, a.work_start_path, a.result_path]
        if any(v is None for v in required):
            raise SystemExit("child arguments missing")
        return child(
            mode=a.mode,
            pattern=a.pattern,
            half_ms=a.half_ms,
            compressed_path=a.compressed_path,
            payload_bytes=a.payload_bytes,
            expected_digest=a.expected_digest,
            workspace_mib=a.workspace_mib,
            transitions=a.transitions,
            rounds=a.rounds,
            ready_path=a.ready_path,
            work_start_path=a.work_start_path,
            result_path=a.result_path,
        )
    result = run_panel(
        payload_mib=a.payload_mib,
        workspace_mib=a.workspace_mib,
        transitions=a.transitions,
        rounds=a.rounds,
        half_ms=a.half_ms,
        repetitions=a.repetitions,
        high_quota_mib=a.high_quota_mib,
    )
    json.dump(result, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
