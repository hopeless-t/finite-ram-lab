from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

SCHEMA = "finite-ram-lab.fr-p9-009-cgroup-capability-probe/v0.1"


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, sort_keys=True))
    os.replace(tmp, path)


def _read_kv(path: Path) -> dict[str, int]:
    result: dict[str, int] = {}
    for line in path.read_text().splitlines():
        key, value = line.split()
        result[key] = int(value)
    return result


def child(payload_mib: int, receipt: Path, release: Path) -> int:
    payload = bytearray(payload_mib * 1024 * 1024)
    checksum = 0
    for offset in range(0, len(payload), 4096):
        payload[offset] = (offset // 4096) & 0xFF
        checksum ^= payload[offset]
    _atomic_json(
        receipt,
        {
            "pid": os.getpid(),
            "payload_mib": payload_mib,
            "checksum": checksum,
        },
    )
    deadline = time.monotonic() + 30
    while not release.exists():
        if time.monotonic() > deadline:
            raise TimeoutError("release_timeout")
        time.sleep(0.01)
    if checksum < 0:
        raise RuntimeError("checksum_impossible")
    return 0


def _sudo_write(path: Path, value: str) -> None:
    subprocess.run(
        ["sudo", "sh", "-c", f"printf '%s\\n' {json.dumps(value)} > {json.dumps(str(path))}"],
        check=True,
    )


def run_probe(*, payload_mib: int = 16, memory_max_mib: int = 128) -> dict[str, Any]:
    root = Path("/sys/fs/cgroup")
    controllers_path = root / "cgroup.controllers"
    if not controllers_path.exists():
        return {
            "schema": SCHEMA,
            "status": "UNSUPPORTED",
            "reason": "cgroup_v2_root_missing",
            "authority_effect": "NONE",
        }
    controllers = controllers_path.read_text().split()
    if "memory" not in controllers:
        return {
            "schema": SCHEMA,
            "status": "UNSUPPORTED",
            "reason": "memory_controller_missing",
            "controllers": controllers,
            "authority_effect": "NONE",
        }

    name = f"fr-p9-009-{os.getpid()}-{time.monotonic_ns()}"
    cg = root / name
    memory_max_bytes = memory_max_mib * 1024 * 1024

    with tempfile.TemporaryDirectory(prefix="fr-p9-009-") as tmp:
        tmpdir = Path(tmp)
        receipt = tmpdir / "child.json"
        release = tmpdir / "release"
        process: subprocess.Popen[str] | None = None
        before_events: dict[str, int] = {}
        during_events: dict[str, int] = {}
        try:
            subprocess.run(["sudo", "mkdir", str(cg)], check=True)
            _sudo_write(cg / "memory.max", str(memory_max_bytes))
            if (cg / "memory.swap.max").exists():
                _sudo_write(cg / "memory.swap.max", "0")
            before_events = _read_kv(cg / "memory.events")

            python = sys.executable
            command = (
                f"echo $$ > {json.dumps(str(cg / 'cgroup.procs'))}; "
                f"exec {json.dumps(python)} -m finite_ram_lab.fr_p9_009_cgroup_capability_probe "
                f"--child --payload-mib {payload_mib} "
                f"--receipt {json.dumps(str(receipt))} --release {json.dumps(str(release))}"
            )
            process = subprocess.Popen(
                ["sudo", "sh", "-c", command],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            deadline = time.monotonic() + 20
            while not receipt.exists():
                if process.poll() is not None:
                    stderr = process.stderr.read() if process.stderr is not None else ""
                    raise RuntimeError(f"child_exited_before_receipt:{process.returncode}:{stderr}")
                if time.monotonic() > deadline:
                    raise TimeoutError("receipt_timeout")
                time.sleep(0.01)

            child_receipt = json.loads(receipt.read_text())
            child_pid = int(child_receipt["pid"])
            cgroup_pids = [int(value) for value in (cg / "cgroup.procs").read_text().split()]
            memory_current = int((cg / "memory.current").read_text().strip())
            memory_peak = (
                int((cg / "memory.peak").read_text().strip())
                if (cg / "memory.peak").exists()
                else None
            )
            during_events = _read_kv(cg / "memory.events")

            release.write_text("release\n")
            process.wait(timeout=20)
            stderr = process.stderr.read() if process.stderr is not None else ""
            if process.returncode != 0:
                raise RuntimeError(f"child_failed:{process.returncode}:{stderr}")

            after_events = _read_kv(cg / "memory.events")
            checks = {
                "cgroup_v2_memory_controller_present": "memory" in controllers,
                "memory_max_applied": int((cg / "memory.max").read_text().strip()) == memory_max_bytes,
                "child_is_inside_isolated_cgroup": child_pid in cgroup_pids,
                "physical_memory_current_observed": memory_current > 0,
                "payload_is_smaller_than_quota": payload_mib < memory_max_mib,
                "no_oom_during_capability_probe": after_events.get("oom", 0) == before_events.get("oom", 0),
                "child_completed": process.returncode == 0,
            }
            return {
                "schema": SCHEMA,
                "status": "PASS" if all(checks.values()) else "FAIL",
                "classification": "HOSTED_LINUX_CGROUP_V2_MEMORY_DOMAIN_CAPABILITY_PROBE",
                "controllers": controllers,
                "cgroup_name": name,
                "memory_max_bytes": memory_max_bytes,
                "payload_mib": payload_mib,
                "child_receipt": child_receipt,
                "cgroup_pids_during_probe": cgroup_pids,
                "memory_current_bytes": memory_current,
                "memory_peak_bytes": memory_peak,
                "memory_events_before": before_events,
                "memory_events_during": during_events,
                "memory_events_after": after_events,
                "checks": checks,
                "decision": "CGROUP_V2_MEMORY_DOMAIN_AVAILABLE_FOR_BOUNDED_PHYSICAL_QUOTA_FALSIFIERS",
                "authority_effect": "NONE",
                "claim_ceiling": "HOSTED_GITHUB_LINUX_CGROUP_V2_CAPABILITY_PROBE_ONLY_NO_REPLAN_OR_APPLICATION_PERFORMANCE_CLAIM",
            }
        finally:
            if process is not None and process.poll() is None:
                process.kill()
                process.wait(timeout=5)
            if cg.exists():
                subprocess.run(["sudo", "rmdir", str(cg)], check=False)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--payload-mib", type=int, default=16)
    parser.add_argument("--memory-max-mib", type=int, default=128)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--release", type=Path)
    args = parser.parse_args()

    if args.child:
        if args.receipt is None or args.release is None:
            raise SystemExit("child_requires_receipt_and_release")
        return child(args.payload_mib, args.receipt, args.release)

    result = run_probe(payload_mib=args.payload_mib, memory_max_mib=args.memory_max_mib)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
