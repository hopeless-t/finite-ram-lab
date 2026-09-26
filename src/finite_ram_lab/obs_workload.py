from __future__ import annotations

import argparse
import gc
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STAT_KEYS = (
    "anon",
    "file",
    "kernel",
    "anon_thp",
    "inactive_anon",
    "active_anon",
    "inactive_file",
    "active_file",
    "workingset_refault_anon",
    "workingset_refault_file",
    "pgscan",
    "pgsteal",
    "pswpin",
    "pswpout",
    "pgfault",
    "pgmajfault",
)


def _self_cgroup_path() -> str:
    raw = Path("/proc/self/cgroup").read_text()
    for line in raw.splitlines():
        parts = line.split(":", 2)
        if len(parts) == 3 and parts[0] == "0":
            return parts[2] or "/"
    raise RuntimeError("cgroup v2 path not found")


def _read(path: Path) -> str:
    return path.read_text().strip()


def _kv_int(text: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) == 2:
            try:
                out[parts[0]] = int(parts[1])
            except ValueError:
                pass
    return out


def _scalar(path: Path) -> int | str:
    raw = _read(path)
    if raw == "max":
        return raw
    return int(raw)


def _snapshot(base: Path) -> dict[str, Any]:
    stat_all = _kv_int(_read(base / "memory.stat"))
    return {
        "memory_current": int(_read(base / "memory.current")),
        "memory_peak": int(_read(base / "memory.peak")),
        "memory_high": _scalar(base / "memory.high"),
        "memory_max": _scalar(base / "memory.max"),
        "memory_events": _kv_int(_read(base / "memory.events")),
        "memory_stat": {k: stat_all.get(k, 0) for k in STAT_KEYS},
        "memory_pressure": _read(base / "memory.pressure"),
        "memory_swap_current": int(_read(base / "memory.swap.current")),
    }


def _touch(buf: bytearray, rounds: int = 1) -> None:
    for r in range(rounds):
        for i in range(0, len(buf), 4096):
            buf[i] = (buf[i] + r + 1) & 0xFF


def run(hotset_mib: int, burst_mib: int, expected_high: int, expected_max: int) -> dict[str, Any]:
    rel = _self_cgroup_path()
    base = Path("/sys/fs/cgroup") / rel.lstrip("/")
    timeline: list[dict[str, Any]] = []
    t0 = time.monotonic_ns()

    def mark(phase: str, **extra: Any) -> None:
        timeline.append({
            "phase": phase,
            "monotonic_ns": time.monotonic_ns() - t0,
            "wall_time_utc": datetime.now(timezone.utc).isoformat(),
            "os": _snapshot(base),
            **extra,
        })

    mark("BASELINE", declared_live_mib=0)

    start = time.perf_counter_ns()
    hot = bytearray(hotset_mib * 1024 * 1024)
    _touch(hot)
    mark(
        "HOTSET_ALLOC",
        declared_live_mib=hotset_mib,
        phase_latency_ns=time.perf_counter_ns() - start,
    )

    start = time.perf_counter_ns()
    _touch(hot, rounds=3)
    mark(
        "HOTSET_TOUCH",
        declared_live_mib=hotset_mib,
        phase_latency_ns=time.perf_counter_ns() - start,
    )

    start = time.perf_counter_ns()
    burst = bytearray(burst_mib * 1024 * 1024)
    _touch(burst)
    mark(
        "BURST_ALLOC",
        declared_live_mib=hotset_mib + burst_mib,
        phase_latency_ns=time.perf_counter_ns() - start,
    )

    start = time.perf_counter_ns()
    _touch(hot, rounds=3)
    mark(
        "HOTSET_RETOUCH",
        declared_live_mib=hotset_mib + burst_mib,
        phase_latency_ns=time.perf_counter_ns() - start,
    )

    start = time.perf_counter_ns()
    del burst
    gc.collect()
    time.sleep(0.15)
    mark(
        "BURST_RELEASE",
        declared_live_mib=hotset_mib,
        phase_latency_ns=time.perf_counter_ns() - start,
    )

    mark("COMPLETE", declared_live_mib=hotset_mib)

    phases = [e["phase"] for e in timeline]
    expected_phases = [
        "BASELINE",
        "HOTSET_ALLOC",
        "HOTSET_TOUCH",
        "BURST_ALLOC",
        "HOTSET_RETOUCH",
        "BURST_RELEASE",
        "COMPLETE",
    ]
    stamps = [e["monotonic_ns"] for e in timeline]
    final_events = timeline[-1]["os"]["memory_events"]

    checks = {
        "phase_sequence": phases == expected_phases,
        "timestamps_strictly_increase": all(b > a for a, b in zip(stamps, stamps[1:])),
        "memory_high_matches": timeline[-1]["os"]["memory_high"] == expected_high,
        "memory_max_matches": timeline[-1]["os"]["memory_max"] == expected_max,
        "no_oom_event": final_events.get("oom", 0) == 0 and final_events.get("oom_kill", 0) == 0,
    }

    return {
        "experiment_id": "OBS-001",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "cgroup_path": rel,
        "parameters": {
            "hotset_mib": hotset_mib,
            "burst_mib": burst_mib,
            "expected_high_bytes": expected_high,
            "expected_max_bytes": expected_max,
        },
        "checks": checks,
        "timeline": timeline,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hotset-mib", type=int, required=True)
    parser.add_argument("--burst-mib", type=int, required=True)
    parser.add_argument("--expected-high-bytes", type=int, required=True)
    parser.add_argument("--expected-max-bytes", type=int, required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    result = run(
        args.hotset_mib,
        args.burst_mib,
        args.expected_high_bytes,
        args.expected_max_bytes,
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    summary = {
        "status": result["status"],
        "checks": result["checks"],
        "phases": [
            {
                "phase": e["phase"],
                "latency_ns": e.get("phase_latency_ns"),
                "memory_current": e["os"]["memory_current"],
                "swap_current": e["os"]["memory_swap_current"],
                "events": e["os"]["memory_events"],
            }
            for e in result["timeline"]
        ],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))

    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
