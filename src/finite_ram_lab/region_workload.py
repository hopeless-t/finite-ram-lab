from __future__ import annotations

import argparse
import ctypes
import json
import mmap
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .obs_workload import _self_cgroup_path, _snapshot, _touch


PAGE_SIZE = os.sysconf("SC_PAGE_SIZE")
LIBC = ctypes.CDLL(None, use_errno=True)
LIBC.mincore.argtypes = [
    ctypes.c_void_p,
    ctypes.c_size_t,
    ctypes.POINTER(ctypes.c_ubyte),
]
LIBC.mincore.restype = ctypes.c_int


def _mapping(size: int) -> mmap.mmap:
    return mmap.mmap(
        -1,
        size,
        flags=mmap.MAP_PRIVATE | mmap.MAP_ANONYMOUS,
        prot=mmap.PROT_READ | mmap.PROT_WRITE,
    )


def residency(mm: mmap.mmap, size: int) -> dict[str, Any]:
    pages = (size + PAGE_SIZE - 1) // PAGE_SIZE
    vec = (ctypes.c_ubyte * pages)()
    address = ctypes.addressof(ctypes.c_char.from_buffer(mm))

    if address % PAGE_SIZE:
        raise RuntimeError("anonymous mmap base address is not page aligned")

    start = time.perf_counter_ns()
    rc = LIBC.mincore(
        ctypes.c_void_p(address),
        ctypes.c_size_t(size),
        vec,
    )
    duration = time.perf_counter_ns() - start

    if rc != 0:
        err = ctypes.get_errno()
        raise OSError(err, os.strerror(err))

    resident = sum(1 for value in vec if value & 1)
    return {
        "supported": True,
        "page_size": PAGE_SIZE,
        "total_pages": pages,
        "resident_pages": resident,
        "missing_pages": pages - resident,
        "resident_fraction": resident / pages if pages else 0.0,
        "mincore_duration_ns": duration,
    }


def run(
    hotset_mib: int,
    burst_mib: int,
    expected_high: int,
    expected_max: int,
    mincore_mode: str = "full",
) -> dict[str, Any]:
    rel = _self_cgroup_path()
    base = Path("/sys/fs/cgroup") / rel.lstrip("/")
    timeline: list[dict[str, Any]] = []
    t0 = time.monotonic_ns()

    hot: mmap.mmap | None = None
    burst: mmap.mmap | None = None
    hot_size = hotset_mib * 1024 * 1024
    burst_size = burst_mib * 1024 * 1024

    if mincore_mode not in {"full", "none"}:
        raise ValueError("mincore_mode must be full or none")

    def region_state() -> dict[str, Any]:
        if mincore_mode == "none":
            return {}
        out: dict[str, Any] = {}
        if hot is not None:
            out["hotset"] = residency(hot, hot_size)
        if burst is not None:
            out["burst"] = residency(burst, burst_size)
        return out

    def mark(phase: str, **extra: Any) -> None:
        timeline.append(
            {
                "phase": phase,
                "monotonic_ns": time.monotonic_ns() - t0,
                "wall_time_utc": datetime.now(timezone.utc).isoformat(),
                "os": _snapshot(base),
                "regions": region_state(),
                **extra,
            }
        )

    mark("BASELINE", declared_live_mib=0)

    start = time.perf_counter_ns()
    hot = _mapping(hot_size)
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
    burst = _mapping(burst_size)
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
    burst.close()
    burst = None
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
    burst_event = next(e for e in timeline if e["phase"] == "BURST_ALLOC")
    mincore_ok = True
    if mincore_mode == "full":
        mincore_ok = (
            burst_event["regions"]["hotset"]["supported"]
            and burst_event["regions"]["burst"]["supported"]
        )

    checks = {
        "phase_sequence": phases == expected_phases,
        "timestamps_strictly_increase": all(
            b > a for a, b in zip(stamps, stamps[1:])
        ),
        "memory_high_matches": timeline[-1]["os"]["memory_high"] == expected_high,
        "memory_max_matches": timeline[-1]["os"]["memory_max"] == expected_max,
        "no_oom_event": (
            final_events.get("oom", 0) == 0
            and final_events.get("oom_kill", 0) == 0
        ),
        "mincore_supported": mincore_ok,
        "hotset_page_count": (
            mincore_mode == "none"
            or burst_event["regions"]["hotset"]["total_pages"]
            == hot_size // PAGE_SIZE
        ),
        "burst_page_count": (
            mincore_mode == "none"
            or burst_event["regions"]["burst"]["total_pages"]
            == burst_size // PAGE_SIZE
        ),
    }

    result = {
        "experiment_id": "OBS-002",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "cgroup_path": rel,
        "parameters": {
            "hotset_mib": hotset_mib,
            "burst_mib": burst_mib,
            "expected_high_bytes": expected_high,
            "expected_max_bytes": expected_max,
            "page_size": PAGE_SIZE,
            "mapping": "MAP_PRIVATE|MAP_ANONYMOUS",
            "mincore_mode": mincore_mode,
        },
        "checks": checks,
        "timeline": timeline,
    }

    hot.close()
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hotset-mib", type=int, required=True)
    parser.add_argument("--burst-mib", type=int, required=True)
    parser.add_argument("--expected-high-bytes", type=int, required=True)
    parser.add_argument("--expected-max-bytes", type=int, required=True)
    parser.add_argument("--mincore-mode", choices=("full", "none"), default="full")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    result = run(
        args.hotset_mib,
        args.burst_mib,
        args.expected_high_bytes,
        args.expected_max_bytes,
        args.mincore_mode,
    )
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    burst = next(e for e in result["timeline"] if e["phase"] == "BURST_ALLOC")
    retouch = next(e for e in result["timeline"] if e["phase"] == "HOTSET_RETOUCH")
    summary = {
        "status": result["status"],
        "mincore_mode": args.mincore_mode,
        "retouch_latency_ms": retouch.get("phase_latency_ns", 0) / 1e6,
    }
    if args.mincore_mode == "full":
        summary["hotset_resident_after_burst"] = burst["regions"]["hotset"]
        summary["burst_resident_after_burst"] = burst["regions"]["burst"]
    print(json.dumps(summary, indent=2, sort_keys=True))

    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
