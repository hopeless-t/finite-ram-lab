from __future__ import annotations

import argparse
import hashlib
import json
import mmap
import time
from pathlib import Path
from typing import Any

from .obs_workload import _self_cgroup_path, _snapshot, _touch
from .region_workload import PAGE_SIZE, _mapping, residency


MADV_COLD = 20


def _digest(mm: mmap.mmap, size: int) -> str:
    h = hashlib.sha256()
    for i in range(0, size, PAGE_SIZE):
        h.update(bytes([mm[i]]))
    return h.hexdigest()


def run(target_identity: str, region_mib: int, burst_mib: int) -> dict[str, Any]:
    if target_identity not in {"A", "B"}:
        raise ValueError("target_identity must be A or B")
    control_identity = "B" if target_identity == "A" else "A"
    region_size = region_mib * 1024 * 1024
    burst_size = burst_mib * 1024 * 1024

    a = _mapping(region_size)
    b = _mapping(region_size)
    regions = {"A": a, "B": b}
    _touch(a)
    _touch(b)
    target = regions[target_identity]
    control = regions[control_identity]

    digest_before = {"A": _digest(a, region_size), "B": _digest(b, region_size)}
    cg = Path("/sys/fs/cgroup") / _self_cgroup_path().lstrip("/")
    os_before = _snapshot(cg)
    residency_before = {
        "target": residency(target, region_size),
        "control": residency(control, region_size),
    }

    call_success = False
    call_error = None
    start = time.perf_counter_ns()
    try:
        target.madvise(getattr(mmap, "MADV_COLD", MADV_COLD), 0, region_size)
        call_success = True
    except Exception as exc:
        call_error = f"{type(exc).__name__}: {exc}"
    call_ns = time.perf_counter_ns() - start

    burst = _mapping(burst_size)
    start = time.perf_counter_ns()
    _touch(burst)
    burst_touch_ns = time.perf_counter_ns() - start

    os_after_burst = _snapshot(cg)
    residency_after_burst = {
        "target": residency(target, region_size),
        "control": residency(control, region_size),
    }

    # Integrity verification intentionally occurs after the primary residency snapshot.
    digest_after = {"A": _digest(a, region_size), "B": _digest(b, region_size)}
    content_match = digest_before == digest_after
    events = os_after_burst["memory_events"]
    no_oom = events.get("oom", 0) == 0 and events.get("oom_kill", 0) == 0

    result = {
        "experiment_id": "ENV-005",
        "target_identity": target_identity,
        "control_identity": control_identity,
        "region_mib": region_mib,
        "burst_mib": burst_mib,
        "madv_cold": {
            "success": call_success,
            "error": call_error,
            "duration_ns": call_ns,
        },
        "burst_touch_ns": burst_touch_ns,
        "residency_before": residency_before,
        "residency_after_burst": residency_after_burst,
        "derived": {
            "target_minus_control_fraction": (
                residency_after_burst["target"]["resident_fraction"]
                - residency_after_burst["control"]["resident_fraction"]
            ),
            "swap_growth_mib": (
                os_after_burst["memory_swap_current"]
                - os_before["memory_swap_current"]
            ) / (1024 * 1024),
        },
        "content_match": content_match,
        "no_oom": no_oom,
        "os_before": os_before,
        "os_after_burst": os_after_burst,
    }

    burst.close()
    a.close()
    b.close()
    return result


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--target-identity", choices=("A", "B"), required=True)
    p.add_argument("--region-mib", type=int, required=True)
    p.add_argument("--burst-mib", type=int, required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()
    result = run(args.target_identity, args.region_mib, args.burst_mib)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "target_identity": result["target_identity"],
        "call_success": result["madv_cold"]["success"],
        "target_fraction": result["residency_after_burst"]["target"]["resident_fraction"],
        "control_fraction": result["residency_after_burst"]["control"]["resident_fraction"],
        "difference": result["derived"]["target_minus_control_fraction"],
        "swap_growth_mib": result["derived"]["swap_growth_mib"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
