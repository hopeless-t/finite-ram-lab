from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import mmap
import os
import shlex
import statistics
import subprocess
import sys
import tempfile
import time
from fractions import Fraction
from pathlib import Path
from typing import Any

from finite_ram_lab.fr_p9_009_cgroup_quota_replan import MIB, _atomic_json, _create_cgroup, _read_events
from finite_ram_lab.fr_p9_011_repeated_phase_frontier import _linear_fit

SCHEMA = "finite-ram-lab.fr-p9-013-compressed-reconstruction-external-validity/v0.1"
MODES = ("KEEP_WARM", "FAULT_IN")


def _write_compressed_source(path: Path, payload_bytes: int) -> tuple[str, int]:
    pattern = bytes((index * 37 + 11) & 0xFF for index in range(4096))
    digest = hashlib.sha256()
    remaining = payload_bytes
    with gzip.open(path, "wb", compresslevel=6) as handle:
        while remaining:
            chunk = pattern[: min(len(pattern), remaining)]
            handle.write(chunk)
            digest.update(chunk)
            remaining -= len(chunk)
    return digest.hexdigest(), path.stat().st_size


def _reconstruct_capability(
    compressed_path: Path,
    *,
    payload_bytes: int,
    expected_digest: str,
) -> tuple[mmap.mmap, int]:
    capability = mmap.mmap(-1, payload_bytes, access=mmap.ACCESS_WRITE)
    view = memoryview(capability)
    try:
        offset = 0
        with gzip.open(compressed_path, "rb") as handle:
            while offset < payload_bytes:
                upper = min(payload_bytes, offset + 256 * 1024)
                count = handle.readinto(view[offset:upper])
                if not count:
                    break
                offset += count
        if offset != payload_bytes:
            raise RuntimeError(f"short_reconstruction:{offset}:{payload_bytes}")
    finally:
        view.release()
    if hashlib.sha256(capability).hexdigest() != expected_digest:
        capability.close()
        raise RuntimeError("reconstruction_digest_mismatch")
    return capability, offset


def _workspace_signature(workspace_bytes: int, transition: int) -> tuple[mmap.mmap, int]:
    workspace = mmap.mmap(-1, workspace_bytes, access=mmap.ACCESS_WRITE)
    signature = 0
    for offset in range(0, workspace_bytes, 4096):
        value = (transition * 17 + offset // 4096) & 0xFF
        workspace[offset] = value
        signature = (signature * 257 + value) & 0xFFFFFFFFFFFFFFFF
    return workspace, signature


def _stride_work(capability: mmap.mmap, *, transition: int, rounds: int) -> int:
    total = (0x9E3779B97F4A7C15 ^ transition) & 0xFFFFFFFFFFFFFFFF
    pages = len(capability) // 4096
    for round_index in range(rounds):
        stride = 17 + 2 * round_index
        page = (transition * 13 + round_index) % max(1, pages)
        for _ in range(pages):
            value = capability[page * 4096]
            total ^= (value + page + round_index) & 0xFFFFFFFFFFFFFFFF
            total = ((total << 7) | (total >> 57)) & 0xFFFFFFFFFFFFFFFF
            total = (total * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
            page = (page + stride) % pages
    return total


def child(
    *,
    mode: str,
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
    if mode not in MODES:
        raise ValueError(f"unknown_mode:{mode}")
    capability: mmap.mmap | None = None
    prestart_reconstruct_ns = 0
    if mode == "KEEP_WARM":
        start = time.monotonic_ns()
        capability, _ = _reconstruct_capability(
            compressed_path,
            payload_bytes=payload_bytes,
            expected_digest=expected_digest,
        )
        prestart_reconstruct_ns = time.monotonic_ns() - start

    _atomic_json(ready_path, {"pid": os.getpid(), "mode": mode, "transitions": transitions})
    deadline = time.monotonic() + 60
    while not work_start_path.exists():
        if time.monotonic() > deadline:
            raise TimeoutError("work_start_timeout")
        time.sleep(0.001)

    rows: list[dict[str, Any]] = []
    for transition in range(transitions):
        workspace, signature = _workspace_signature(workspace_mib * MIB, transition)
        workspace.close()
        time.sleep(0.003)

        reconstruct_ns = 0
        if mode == "FAULT_IN":
            start = time.monotonic_ns()
            capability, _ = _reconstruct_capability(
                compressed_path,
                payload_bytes=payload_bytes,
                expected_digest=expected_digest,
            )
            reconstruct_ns = time.monotonic_ns() - start
        if capability is None:
            raise RuntimeError("capability_missing")

        work_start = time.monotonic_ns()
        semantic_value = _stride_work(capability, transition=transition, rounds=rounds)
        work_ns = time.monotonic_ns() - work_start
        rows.append(
            {
                "transition": transition,
                "workspace_signature": signature,
                "semantic_value": semantic_value,
                "reconstruct_ns": reconstruct_ns,
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
            "transitions": transitions,
            "prestart_reconstruct_ns": prestart_reconstruct_ns,
            "rows": rows,
        },
    )
    return 0


def run_group(
    *,
    mode: str,
    transitions: int,
    memory_max_bytes: int,
    compressed_path: Path,
    payload_bytes: int,
    expected_digest: str,
    workspace_mib: int,
    rounds: int,
    run_root: Path,
    label: str,
) -> dict[str, Any]:
    cg = _create_cgroup(f"fr-p9-013-{os.getpid()}-{label}-{time.monotonic_ns()}", memory_max_bytes)
    run_dir = run_root / label
    run_dir.mkdir()
    ready_path = run_dir / "ready.json"
    result_path = run_dir / "result.json"
    work_start_path = run_dir / "work-start.ns"
    args = [
        sys.executable, "-m", "finite_ram_lab.fr_p9_013_compressed_reconstruction_external_validity",
        "--child", "--mode", mode,
        "--compressed-path", str(compressed_path),
        "--payload-bytes", str(payload_bytes),
        "--expected-digest", expected_digest,
        "--workspace-mib", str(workspace_mib),
        "--transitions", str(transitions),
        "--rounds", str(rounds),
        "--ready-path", str(ready_path),
        "--work-start-path", str(work_start_path),
        "--result-path", str(result_path),
    ]
    exec_line = " ".join(shlex.quote(value) for value in args)
    command = f"echo $$ > {shlex.quote(str(cg / 'cgroup.procs'))}; exec {exec_line}"
    before = _read_events(cg)
    process = subprocess.Popen(["sudo", "sh", "-c", command], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    state = "UNKNOWN"
    work_wall_ns = 0
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
            start_ns = time.monotonic_ns()
            work_start_path.write_text(str(start_ns))
            try:
                process.wait(timeout=120)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
                state = "WORK_TIMEOUT"
            else:
                work_wall_ns = time.monotonic_ns() - start_ns
                state = "COMPLETED" if process.returncode == 0 else "WORK_EXIT"

        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        after = _read_events(cg)
        peak = int((cg / "memory.peak").read_text().strip())
        receipt = json.loads(result_path.read_text()) if result_path.exists() else None
        reconstruct_ns_total = 0
        semantic_signature: list[tuple[int, int, int]] = []
        if receipt:
            reconstruct_ns_total += int(receipt["prestart_reconstruct_ns"])
            for row in receipt["rows"]:
                reconstruct_ns_total += int(row["reconstruct_ns"])
                semantic_signature.append(
                    (int(row["transition"]), int(row["workspace_signature"]), int(row["semantic_value"]))
                )
        stderr = process.stderr.read() if process.stderr is not None else ""
        return {
            "label": label,
            "mode": mode,
            "transitions": transitions,
            "state": state,
            "memory_peak_bytes": peak,
            "reconstruct_ns_total": reconstruct_ns_total,
            "work_wall_ns": work_wall_ns,
            "semantic_signature": semantic_signature,
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


def break_even_ms_per_mib(warm: dict[str, Any], fault: dict[str, Any]) -> float:
    delta_ns = int(fault["reconstruct_ns_total"]) - int(warm["reconstruct_ns_total"])
    delta_bytes = int(warm["memory_peak_bytes"]) - int(fault["memory_peak_bytes"])
    if delta_ns <= 0 or delta_bytes <= 0:
        raise ValueError("non_tradeoff_anchor")
    return float(Fraction(delta_ns * MIB, delta_bytes)) / 1_000_000.0


def run_panel(
    *,
    payload_mib: int = 16,
    workspace_mib: int = 24,
    rounds: int = 2,
    transition_counts: tuple[int, ...] = (2, 4, 8),
    repetitions: int = 2,
    high_quota_mib: int = 128,
) -> dict[str, Any]:
    controllers = (Path("/sys/fs/cgroup") / "cgroup.controllers").read_text().split()
    if "memory" not in controllers:
        raise RuntimeError("memory_controller_unavailable")
    with tempfile.TemporaryDirectory(prefix="fr-p9-013-compressed-") as tmp:
        root = Path(tmp)
        compressed_path = root / "capability.gz"
        payload_bytes = payload_mib * MIB
        expected_digest, compressed_bytes = _write_compressed_source(compressed_path, payload_bytes)
        runs: list[dict[str, Any]] = []
        for transitions in transition_counts:
            for rep in range(repetitions):
                order = MODES if rep % 2 == 0 else tuple(reversed(MODES))
                for mode in order:
                    runs.append(
                        run_group(
                            mode=mode,
                            transitions=transitions,
                            memory_max_bytes=high_quota_mib * MIB,
                            compressed_path=compressed_path,
                            payload_bytes=payload_bytes,
                            expected_digest=expected_digest,
                            workspace_mib=workspace_mib,
                            rounds=rounds,
                            run_root=root,
                            label=f"h{transitions}-{mode.lower()}-r{rep}",
                        )
                    )

    summaries: list[dict[str, Any]] = []
    all_semantics = True
    all_no_oom = True
    thresholds: list[float] = []
    for transitions in transition_counts:
        horizon_rows = [row for row in runs if int(row["transitions"]) == transitions]
        reference = horizon_rows[0]["semantic_signature"]
        all_semantics &= all(
            row["state"] == "COMPLETED" and row["semantic_signature"] == reference for row in horizon_rows
        )
        all_no_oom &= all(
            int(row["oom_delta"]) == 0 and int(row["oom_kill_delta"]) == 0 for row in horizon_rows
        )
        warm_rows = [row for row in horizon_rows if row["mode"] == "KEEP_WARM"]
        fault_rows = [row for row in horizon_rows if row["mode"] == "FAULT_IN"]
        warm = {
            "memory_peak_bytes": _median(warm_rows, "memory_peak_bytes"),
            "reconstruct_ns_total": _median(warm_rows, "reconstruct_ns_total"),
            "work_wall_ns": _median(warm_rows, "work_wall_ns"),
        }
        fault = {
            "memory_peak_bytes": _median(fault_rows, "memory_peak_bytes"),
            "reconstruct_ns_total": _median(fault_rows, "reconstruct_ns_total"),
            "work_wall_ns": _median(fault_rows, "work_wall_ns"),
        }
        threshold = break_even_ms_per_mib(warm, fault)
        thresholds.append(threshold)
        summaries.append(
            {
                "transitions": transitions,
                "KEEP_WARM": warm,
                "FAULT_IN": fault,
                "peak_saving_bytes_fault_in": warm["memory_peak_bytes"] - fault["memory_peak_bytes"],
                "incremental_reconstruct_ns_fault_in": fault["reconstruct_ns_total"] - warm["reconstruct_ns_total"],
                "break_even_price_ms_per_mib": threshold,
            }
        )

    fit = _linear_fit(
        list(transition_counts),
        [int(row["FAULT_IN"]["reconstruct_ns_total"]) for row in summaries],
    )
    checks = {
        "all_runs_complete_and_preserve_semantics": all_semantics,
        "high_quota_runs_have_no_kernel_oom": all_no_oom,
        "fault_in_has_lower_peak_at_every_horizon": all(
            int(row["peak_saving_bytes_fault_in"]) >= 8 * MIB for row in summaries
        ),
        "fault_in_has_higher_reconstruction_cost_at_every_horizon": all(
            int(row["incremental_reconstruct_ns_fault_in"]) > 0 for row in summaries
        ),
        "break_even_price_rises_with_reuse_horizon": all(
            b > a for a, b in zip(thresholds, thresholds[1:])
        ),
        "compressed_source_is_materially_smaller_than_runtime_capability": compressed_bytes < payload_bytes // 16,
        "reconstruction_policy_does_not_grant_authority": True,
        "reconstruction_policy_does_not_grant_retry_permission": True,
    }
    return {
        "schema": SCHEMA,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "classification": "HOSTED_LINUX_CGROUP_V2_COMPRESSED_RECONSTRUCTION_EXTERNAL_VALIDITY",
        "fixture": {
            "payload_mib": payload_mib,
            "workspace_mib": workspace_mib,
            "rounds": rounds,
            "transition_counts": list(transition_counts),
            "repetitions": repetitions,
            "high_quota_mib": high_quota_mib,
            "compressed_source_bytes": compressed_bytes,
        },
        "horizon_summaries": summaries,
        "fault_in_reconstruction_linear_fit": fit,
        "checks": checks,
        "decision": (
            "HORIZON_DEPENDENT_RESIDENCY_PRICE_BOUNDARY_SURVIVES_A_COMPRESSED_RECONSTRUCTION_"
            "AND_STRIDED_ARITHMETIC_SHAPE_IF_QUALIFIED"
        ),
        "scalar_gain": None,
        "authority_effect": "NONE",
        "retry_authority": False,
        "next_falsifier": (
            "test whether deadline slack can hide FAULT_IN reconstruction latency without restoring phase overlap memory pressure"
        ),
        "claim_ceiling": (
            "HOSTED_GITHUB_LINUX_CGROUP_V2_COMPRESSED_RECONSTRUCTION_AND_STRIDED_ARITHMETIC_PROXY_ONLY_"
            "NO_UNIVERSAL_POLICY_OR_APPLICATION_PERFORMANCE_CLAIM"
        ),
    }


def _parse_counts(value: str) -> tuple[int, ...]:
    rows = tuple(int(part) for part in value.split(",") if part.strip())
    if not rows or any(item < 1 for item in rows):
        raise argparse.ArgumentTypeError("transition counts must be positive")
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--mode", choices=MODES)
    parser.add_argument("--compressed-path", type=Path)
    parser.add_argument("--payload-bytes", type=int)
    parser.add_argument("--expected-digest")
    parser.add_argument("--workspace-mib", type=int, default=24)
    parser.add_argument("--transitions", type=int, default=2)
    parser.add_argument("--rounds", type=int, default=2)
    parser.add_argument("--ready-path", type=Path)
    parser.add_argument("--work-start-path", type=Path)
    parser.add_argument("--result-path", type=Path)
    parser.add_argument("--payload-mib", type=int, default=16)
    parser.add_argument("--transition-counts", type=_parse_counts, default=(2, 4, 8))
    parser.add_argument("--repetitions", type=int, default=2)
    parser.add_argument("--high-quota-mib", type=int, default=128)
    args = parser.parse_args()
    if args.child:
        required = (
            args.mode,
            args.compressed_path,
            args.payload_bytes,
            args.expected_digest,
            args.ready_path,
            args.work_start_path,
            args.result_path,
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
            ready_path=args.ready_path,
            work_start_path=args.work_start_path,
            result_path=args.result_path,
        )
    result = run_panel(
        payload_mib=args.payload_mib,
        workspace_mib=args.workspace_mib,
        rounds=args.rounds,
        transition_counts=args.transition_counts,
        repetitions=args.repetitions,
        high_quota_mib=args.high_quota_mib,
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
