from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any


def _read_text(path: Path) -> dict[str, Any]:
    try:
        return {"state": "SUPPORTED", "value": path.read_text().strip()}
    except FileNotFoundError:
        return {"state": "UNAVAILABLE", "value": None}
    except Exception as exc:
        return {"state": "ERROR", "value": None, "error": f"{type(exc).__name__}: {exc}"}


def _self_cgroup_path() -> str | None:
    raw = Path("/proc/self/cgroup").read_text()
    for line in raw.splitlines():
        parts = line.split(":", 2)
        if len(parts) == 3 and parts[0] == "0":
            return parts[2] or "/"
    return None


def _parse_int(value: dict[str, Any]) -> int | None:
    if value.get("state") != "SUPPORTED":
        return None
    raw = value.get("value")
    if raw in (None, "", "max"):
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def _events(value: dict[str, Any]) -> dict[str, int]:
    out: dict[str, int] = {}
    if value.get("state") != "SUPPORTED":
        return out
    for line in str(value.get("value") or "").splitlines():
        parts = line.split()
        if len(parts) == 2:
            try:
                out[parts[0]] = int(parts[1])
            except ValueError:
                pass
    return out


def _snapshot(base: Path) -> dict[str, Any]:
    names = (
        "memory.current",
        "memory.peak",
        "memory.high",
        "memory.max",
        "memory.events",
        "memory.stat",
        "memory.pressure",
        "memory.swap.current",
        "memory.swap.max",
    )
    return {name: _read_text(base / name) for name in names}


def run(allocation_mib: int, expected_high: int, expected_max: int) -> dict[str, Any]:
    relpath = _self_cgroup_path()
    mount = Path("/sys/fs/cgroup")
    current = mount / (relpath or "/").lstrip("/")

    before = _snapshot(current)

    buf = bytearray(allocation_mib * 1024 * 1024)
    for i in range(0, len(buf), 4096):
        buf[i] = (i // 4096) & 0xFF

    time.sleep(0.15)
    after = _snapshot(current)

    before_current = _parse_int(before["memory.current"])
    after_current = _parse_int(after["memory.current"])
    high = _parse_int(after["memory.high"])
    maximum = _parse_int(after["memory.max"])
    events = _events(after["memory.events"])

    checks = {
        "cgroup_v2": (mount / "cgroup.controllers").exists() and relpath is not None,
        "memory_current_readable": after_current is not None,
        "memory_high_matches": high == expected_high,
        "memory_max_matches": maximum == expected_max,
        "usage_increases": (
            before_current is not None
            and after_current is not None
            and after_current > before_current
        ),
        "no_oom_event": events.get("oom", 0) == 0 and events.get("oom_kill", 0) == 0,
    }

    return {
        "experiment_id": "ENV-002",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "allocation_mib": allocation_mib,
        "expected": {
            "memory_high_bytes": expected_high,
            "memory_max_bytes": expected_max,
        },
        "cgroup_path": relpath,
        "cgroup_directory": str(current),
        "before": before,
        "after": after,
        "checks": checks,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--allocation-mib", type=int, required=True)
    parser.add_argument("--expected-high-bytes", type=int, required=True)
    parser.add_argument("--expected-max-bytes", type=int, required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    result = run(args.allocation_mib, args.expected_high_bytes, args.expected_max_bytes)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "checks": result["checks"]}, sort_keys=True))

    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
