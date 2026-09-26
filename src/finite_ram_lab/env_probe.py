from __future__ import annotations

import argparse
import json
import os
import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VMSTAT_KEYS = {
    "pgfault",
    "pgmajfault",
    "pgscan_kswapd",
    "pgscan_direct",
    "pgsteal_kswapd",
    "pgsteal_direct",
    "workingset_refault_anon",
    "workingset_refault_file",
    "pswpin",
    "pswpout",
    "oom_kill",
    "compact_stall",
}

CGROUP_MEMORY_FILES = (
    "memory.current",
    "memory.peak",
    "memory.min",
    "memory.low",
    "memory.high",
    "memory.max",
    "memory.events",
    "memory.events.local",
    "memory.stat",
    "memory.pressure",
    "memory.swap.current",
    "memory.swap.max",
    "memory.oom.group",
    "memory.reclaim",
)


def _read(path: str) -> dict[str, Any]:
    try:
        return {"state": "SUPPORTED", "value": Path(path).read_text()}
    except FileNotFoundError:
        return {"state": "UNAVAILABLE", "value": None}
    except Exception as exc:
        return {"state": "ERROR", "value": None, "error": f"{type(exc).__name__}: {exc}"}


def _parse_kv_lines(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        parts = line.split(None, 1)
        out[parts[0].rstrip(":")] = parts[1] if len(parts) == 2 else ""
    return out


def _current_cgroup_relpath() -> tuple[str | None, dict[str, Any]]:
    raw = _read("/proc/self/cgroup")
    if raw["state"] != "SUPPORTED":
        return None, raw
    for line in raw["value"].splitlines():
        parts = line.split(":", 2)
        if len(parts) == 3 and parts[0] == "0":
            return parts[2] or "/", raw
    return None, raw


def _memory_files(base: Path) -> dict[str, Any]:
    return {name: _read(str(base / name)) for name in CGROUP_MEMORY_FILES}


def _cgroup_snapshot() -> dict[str, Any]:
    mount = Path("/sys/fs/cgroup")
    controllers = _read(str(mount / "cgroup.controllers"))
    relpath, self_raw = _current_cgroup_relpath()

    current_dir = mount
    if relpath:
        current_dir = mount / relpath.lstrip("/")

    return {
        "v2": controllers["state"] == "SUPPORTED",
        "controllers": controllers,
        "self": self_raw,
        "current_path": relpath,
        "current_directory": str(current_dir),
        "root_files": _memory_files(mount),
        "current_files": _memory_files(current_dir),
    }


def snapshot() -> dict[str, Any]:
    meminfo_raw = _read("/proc/meminfo")
    vmstat_raw = _read("/proc/vmstat")

    meminfo = _parse_kv_lines(meminfo_raw["value"]) if meminfo_raw["state"] == "SUPPORTED" else {}
    vmstat_all = _parse_kv_lines(vmstat_raw["value"]) if vmstat_raw["state"] == "SUPPORTED" else {}
    vmstat = {k: vmstat_all[k] for k in sorted(VMSTAT_KEYS) if k in vmstat_all}

    return {
        "experiment_id": "ENV-001",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "platform": platform.platform(),
        "kernel": platform.release(),
        "machine": platform.machine(),
        "cpu_count": os.cpu_count(),
        "runner": {
            key: os.environ.get(key)
            for key in (
                "RUNNER_OS",
                "RUNNER_ARCH",
                "ImageOS",
                "ImageVersion",
                "GITHUB_SHA",
                "GITHUB_RUN_ID",
                "GITHUB_RUN_ATTEMPT",
                "GITHUB_JOB",
                "GITHUB_WORKFLOW",
            )
        },
        "meminfo": {
            "state": meminfo_raw["state"],
            "selected": {
                k: meminfo.get(k)
                for k in (
                    "MemTotal",
                    "MemAvailable",
                    "SwapTotal",
                    "SwapFree",
                    "AnonPages",
                    "Cached",
                    "Slab",
                )
            },
        },
        "vmstat": {"state": vmstat_raw["state"], "selected": vmstat},
        "psi_memory": _read("/proc/pressure/memory"),
        "swaps": _read("/proc/swaps"),
        "cgroup": _cgroup_snapshot(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    data = snapshot()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    print(json.dumps(data, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
