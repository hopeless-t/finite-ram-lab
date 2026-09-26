from __future__ import annotations

import argparse
import json
import mmap
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .obs_workload import _self_cgroup_path, _snapshot, _touch


def _mapping(size: int) -> mmap.mmap:
    return mmap.mmap(
        -1,
        size,
        flags=mmap.MAP_PRIVATE | mmap.MAP_ANONYMOUS,
        prot=mmap.PROT_READ | mmap.PROT_WRITE,
    )


def run(
    region_a_mib: int,
    region_b_mib: int,
    burst_mib: int,
    expected_high: int,
    expected_max: int,
    arm: str,
    recent_identity: str,
) -> dict[str, Any]:
    if arm not in {"aligned", "misaligned", "control"}:
        raise ValueError("arm must be aligned, misaligned, or control")
    if recent_identity not in {"A", "B"}:
        raise ValueError("recent_identity must be A or B")

    rel = _self_cgroup_path()
    base = Path("/sys/fs/cgroup") / rel.lstrip("/")
    t0 = time.monotonic_ns()
    timeline: list[dict[str, Any]] = []

    a_size = region_a_mib * 1024 * 1024
    b_size = region_b_mib * 1024 * 1024
    burst_size = burst_mib * 1024 * 1024

    region_a: mmap.mmap | None = None
    region_b: mmap.mmap | None = None
    burst: mmap.mmap | None = None

    def mark(phase: str, **extra: Any) -> None:
        timeline.append(
            {
                "phase": phase,
                "monotonic_ns": time.monotonic_ns() - t0,
                "wall_time_utc": datetime.now(timezone.utc).isoformat(),
                "os": _snapshot(base),
                **extra,
            }
        )

    mark("BASELINE", declared_live_mib=0)

    start = time.perf_counter_ns()
    region_a = _mapping(a_size)
    region_b = _mapping(b_size)
    _touch(region_a)
    _touch(region_b)
    mark(
        "REGIONS_ALLOC",
        declared_live_mib=region_a_mib + region_b_mib,
        phase_latency_ns=time.perf_counter_ns() - start,
    )

    # Equal access counts; only the final order differs.
    older_identity = "B" if recent_identity == "A" else "A"
    regions = {"A": region_a, "B": region_b}

    start = time.perf_counter_ns()
    _touch(regions[older_identity], rounds=2)
    _touch(regions[recent_identity], rounds=2)
    mark(
        "PREBURST_RECENCY",
        declared_live_mib=region_a_mib + region_b_mib,
        phase_latency_ns=time.perf_counter_ns() - start,
        recent_identity=recent_identity,
        older_identity=older_identity,
        touches_per_region=2,
    )

    start = time.perf_counter_ns()
    burst = _mapping(burst_size)
    _touch(burst)
    mark(
        "BURST_ALLOC",
        declared_live_mib=region_a_mib + region_b_mib + burst_mib,
        phase_latency_ns=time.perf_counter_ns() - start,
    )

    if arm in {"aligned", "control"}:
        target_identity = recent_identity
    else:
        target_identity = older_identity

    start = time.perf_counter_ns()
    _touch(regions[target_identity], rounds=3)
    mark(
        "TARGET_RETOUCH",
        declared_live_mib=region_a_mib + region_b_mib + burst_mib,
        phase_latency_ns=time.perf_counter_ns() - start,
        target_identity=target_identity,
        recent_identity=recent_identity,
        arm=arm,
    )

    start = time.perf_counter_ns()
    burst.close()
    burst = None
    time.sleep(0.10)
    mark(
        "BURST_RELEASE",
        declared_live_mib=region_a_mib + region_b_mib,
        phase_latency_ns=time.perf_counter_ns() - start,
    )
    mark("COMPLETE", declared_live_mib=region_a_mib + region_b_mib)

    expected_phases = [
        "BASELINE",
        "REGIONS_ALLOC",
        "PREBURST_RECENCY",
        "BURST_ALLOC",
        "TARGET_RETOUCH",
        "BURST_RELEASE",
        "COMPLETE",
    ]
    phases = [e["phase"] for e in timeline]
    stamps = [e["monotonic_ns"] for e in timeline]
    final_events = timeline[-1]["os"]["memory_events"]

    checks = {
        "phase_sequence": phases == expected_phases,
        "timestamps_strictly_increase": all(b > a for a, b in zip(stamps, stamps[1:])),
        "memory_high_matches": timeline[-1]["os"]["memory_high"] == expected_high,
        "memory_max_matches": timeline[-1]["os"]["memory_max"] == expected_max,
        "no_oom_event": final_events.get("oom", 0) == 0 and final_events.get("oom_kill", 0) == 0,
        "matched_region_sizes": region_a_mib == region_b_mib,
    }

    result = {
        "experiment_id": "HYP-001",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "cgroup_path": rel,
        "parameters": {
            "region_a_mib": region_a_mib,
            "region_b_mib": region_b_mib,
            "burst_mib": burst_mib,
            "expected_high_bytes": expected_high,
            "expected_max_bytes": expected_max,
            "arm": arm,
            "recent_identity": recent_identity,
        },
        "checks": checks,
        "timeline": timeline,
    }

    region_a.close()
    region_b.close()
    return result


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--region-a-mib", type=int, required=True)
    p.add_argument("--region-b-mib", type=int, required=True)
    p.add_argument("--burst-mib", type=int, required=True)
    p.add_argument("--expected-high-bytes", type=int, required=True)
    p.add_argument("--expected-max-bytes", type=int, required=True)
    p.add_argument("--arm", choices=("aligned", "misaligned", "control"), required=True)
    p.add_argument("--recent-identity", choices=("A", "B"), required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    result = run(
        args.region_a_mib,
        args.region_b_mib,
        args.burst_mib,
        args.expected_high_bytes,
        args.expected_max_bytes,
        args.arm,
        args.recent_identity,
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    retouch = next(e for e in result["timeline"] if e["phase"] == "TARGET_RETOUCH")
    print(json.dumps({
        "status": result["status"],
        "arm": args.arm,
        "recent_identity": args.recent_identity,
        "target_identity": retouch["target_identity"],
        "retouch_latency_ms": retouch["phase_latency_ns"] / 1e6,
    }, indent=2, sort_keys=True))

    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
