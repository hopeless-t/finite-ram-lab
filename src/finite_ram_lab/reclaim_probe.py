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


def _digest(mm: mmap.mmap, size: int) -> str:
    h = hashlib.sha256()
    for i in range(0, size, PAGE_SIZE):
        h.update(bytes([mm[i]]))
    return h.hexdigest()


def _retouch(mm: mmap.mmap, size: int) -> int:
    start = time.perf_counter_ns()
    for i in range(0, size, PAGE_SIZE):
        value = mm[i]
        mm[i] = value
    return time.perf_counter_ns() - start


def _reclaim(path: Path, request: str) -> dict[str, Any]:
    start = time.perf_counter_ns()
    try:
        with path.open("w") as fh:
            fh.write(request)
        return {
            "success": True,
            "duration_ns": time.perf_counter_ns() - start,
            "errno": None,
            "error": None,
        }
    except OSError as exc:
        return {
            "success": False,
            "duration_ns": time.perf_counter_ns() - start,
            "errno": exc.errno,
            "error": f"{type(exc).__name__}: {exc}",
        }


def run(
    target_identity: str,
    region_mib: int,
    reclaim_mib: int,
    post_pageout_wait_ms: int,
    post_reclaim_wait_ms: int,
) -> dict[str, Any]:
    if target_identity not in {"A", "B"}:
        raise ValueError("target_identity must be A or B")

    size = region_mib * 1024 * 1024
    a = _mapping(size)
    b = _mapping(size)
    regions = {"A": a, "B": b}
    control_identity = "B" if target_identity == "A" else "A"
    target = regions[target_identity]
    control = regions[control_identity]

    _touch(a)
    _touch(b)

    cg = Path("/sys/fs/cgroup") / _self_cgroup_path().lstrip("/")
    reclaim_path = cg / "memory.reclaim"

    digest_before = {
        "A": _digest(a, size),
        "B": _digest(b, size),
    }
    os_before = _snapshot(cg)
    resident_before = {
        "target": residency(target, size),
        "control": residency(control, size),
    }

    advice = getattr(mmap, "MADV_PAGEOUT", 21)
    pageout_error = None
    pageout_ns = None
    pageout_success = False
    try:
        start = time.perf_counter_ns()
        target.madvise(advice, 0, size)
        pageout_ns = time.perf_counter_ns() - start
        pageout_success = True
    except Exception as exc:
        pageout_error = f"{type(exc).__name__}: {exc}"

    time.sleep(post_pageout_wait_ms / 1000.0)
    os_after_pageout = _snapshot(cg)
    resident_after_pageout = {
        "target": residency(target, size),
        "control": residency(control, size),
    }

    reclaim_request = f"{reclaim_mib}M swappiness=max"
    reclaim_result = _reclaim(reclaim_path, reclaim_request)
    time.sleep(post_reclaim_wait_ms / 1000.0)
    os_after_reclaim = _snapshot(cg)
    resident_after_reclaim = {
        "target": residency(target, size),
        "control": residency(control, size),
    }

    target_retouch_ns = _retouch(target, size)
    control_retouch_ns = _retouch(control, size)
    resident_after_retouch = {
        "target": residency(target, size),
        "control": residency(control, size),
    }
    os_after_retouch = _snapshot(cg)

    digest_after = {
        "A": _digest(a, size),
        "B": _digest(b, size),
    }

    content_match = digest_before == digest_after
    events = os_after_retouch["memory_events"]
    target_fraction = resident_after_reclaim["target"]["resident_fraction"]
    control_fraction = resident_after_reclaim["control"]["resident_fraction"]

    result = {
        "experiment_id": "ENV-004",
        "target_identity": target_identity,
        "control_identity": control_identity,
        "region_mib": region_mib,
        "reclaim_request": reclaim_request,
        "cgroup_path": str(cg),
        "pageout": {
            "success": pageout_success,
            "duration_ns": pageout_ns,
            "error": pageout_error,
        },
        "reclaim": reclaim_result,
        "residency": {
            "before": resident_before,
            "after_pageout": resident_after_pageout,
            "after_reclaim": resident_after_reclaim,
            "after_retouch": resident_after_retouch,
        },
        "os": {
            "before": os_before,
            "after_pageout": os_after_pageout,
            "after_reclaim": os_after_reclaim,
            "after_retouch": os_after_retouch,
        },
        "retouch_ns": {
            "target": target_retouch_ns,
            "control": control_retouch_ns,
        },
        "content_match": content_match,
        "derived": {
            "target_resident_fraction_after_reclaim": target_fraction,
            "control_resident_fraction_after_reclaim": control_fraction,
            "selectivity_gap": control_fraction - target_fraction,
            "swap_growth_after_pageout_mib": (
                os_after_pageout["memory_swap_current"]
                - os_before["memory_swap_current"]
            ) / (1024 * 1024),
            "swap_growth_after_reclaim_mib": (
                os_after_reclaim["memory_swap_current"]
                - os_before["memory_swap_current"]
            ) / (1024 * 1024),
        },
        "checks": {
            "pageout_success": pageout_success,
            "target_fraction_le_050": target_fraction <= 0.50,
            "control_fraction_ge_090": control_fraction >= 0.90,
            "content_match": content_match,
            "no_oom": events.get("oom", 0) == 0 and events.get("oom_kill", 0) == 0,
        },
    }

    a.close()
    b.close()
    return result


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--target-identity", choices=("A", "B"), required=True)
    p.add_argument("--region-mib", type=int, required=True)
    p.add_argument("--reclaim-mib", type=int, required=True)
    p.add_argument("--post-pageout-wait-ms", type=int, required=True)
    p.add_argument("--post-reclaim-wait-ms", type=int, required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    result = run(
        args.target_identity,
        args.region_mib,
        args.reclaim_mib,
        args.post_pageout_wait_ms,
        args.post_reclaim_wait_ms,
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "target": result["target_identity"],
        "pageout_success": result["pageout"]["success"],
        "reclaim_success": result["reclaim"]["success"],
        "target_fraction": result["derived"]["target_resident_fraction_after_reclaim"],
        "control_fraction": result["derived"]["control_resident_fraction_after_reclaim"],
        "selectivity_gap": result["derived"]["selectivity_gap"],
        "content_match": result["content_match"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
