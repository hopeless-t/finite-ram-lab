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


MADV_PAGEOUT = 21


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


def _delta_stat(before: dict[str, Any], after: dict[str, Any], key: str) -> int:
    return int(after["memory_stat"].get(key, 0) - before["memory_stat"].get(key, 0))


def run(
    arm: str,
    hot_identity: str,
    region_mib: int,
    pageout_mib: int,
    burst_mib: int,
) -> dict[str, Any]:
    if arm not in {"correct_pageout", "wrong_pageout", "no_hint"}:
        raise ValueError("invalid arm")
    if hot_identity not in {"A", "B"}:
        raise ValueError("hot_identity must be A or B")

    cold_identity = "B" if hot_identity == "A" else "A"
    region_size = region_mib * 1024 * 1024
    pageout_size = pageout_mib * 1024 * 1024
    burst_size = burst_mib * 1024 * 1024

    a = _mapping(region_size)
    b = _mapping(region_size)
    regions = {"A": a, "B": b}
    _touch(a)
    _touch(b)
    hot = regions[hot_identity]
    cold = regions[cold_identity]

    digest_before = {"A": _digest(a, region_size), "B": _digest(b, region_size)}
    cg = Path("/sys/fs/cgroup") / _self_cgroup_path().lstrip("/")
    os_before = _snapshot(cg)

    if arm == "correct_pageout":
        target_identity = cold_identity
    elif arm == "wrong_pageout":
        target_identity = hot_identity
    else:
        target_identity = None

    advice_ns = 0
    advice_success = True
    advice_error = None
    if target_identity is not None:
        target = regions[target_identity]
        start = time.perf_counter_ns()
        try:
            target.madvise(getattr(mmap, "MADV_PAGEOUT", MADV_PAGEOUT), 0, pageout_size)
        except Exception as exc:
            advice_success = False
            advice_error = f"{type(exc).__name__}: {exc}"
        advice_ns = time.perf_counter_ns() - start

    burst = _mapping(burst_size)
    start = time.perf_counter_ns()
    _touch(burst)
    burst_touch_ns = time.perf_counter_ns() - start

    os_pre_retouch = _snapshot(cg)
    hot_residency = residency(hot, region_size)
    cold_residency = residency(cold, region_size)
    hot_first16 = residency(hot, pageout_size)
    cold_first16 = residency(cold, pageout_size)

    hot_retouch_ns = _retouch(hot, region_size)
    os_post_retouch = _snapshot(cg)

    digest_after = {"A": _digest(a, region_size), "B": _digest(b, region_size)}
    content_match = digest_before == digest_after
    events = os_post_retouch["memory_events"]
    no_oom = events.get("oom", 0) == 0 and events.get("oom_kill", 0) == 0

    result = {
        "experiment_id": "EXP-002",
        "status": "PASS" if advice_success and content_match and no_oom else "INVALID",
        "arm": arm,
        "hot_identity": hot_identity,
        "cold_identity": cold_identity,
        "target_identity": target_identity,
        "advice": {
            "success": advice_success,
            "error": advice_error,
            "duration_ns": advice_ns,
        },
        "burst_touch_ns": burst_touch_ns,
        "hot_retouch_ns": hot_retouch_ns,
        "work_interval_ns": advice_ns + burst_touch_ns + hot_retouch_ns,
        "residency_pre_retouch": {
            "hot": hot_residency,
            "cold": cold_residency,
            "hot_first16": hot_first16,
            "cold_first16": cold_first16,
        },
        "swap_mib_pre_retouch": os_pre_retouch["memory_swap_current"] / (1024 * 1024),
        "retouch_deltas": {
            "pswpin": _delta_stat(os_pre_retouch, os_post_retouch, "pswpin"),
            "workingset_refault_anon": _delta_stat(os_pre_retouch, os_post_retouch, "workingset_refault_anon"),
            "pgmajfault": _delta_stat(os_pre_retouch, os_post_retouch, "pgmajfault"),
            "pgfault": _delta_stat(os_pre_retouch, os_post_retouch, "pgfault"),
            "pgscan": _delta_stat(os_pre_retouch, os_post_retouch, "pgscan"),
            "pgsteal": _delta_stat(os_pre_retouch, os_post_retouch, "pgsteal"),
        },
        "content_match": content_match,
        "no_oom": no_oom,
        "os_before": os_before,
    }

    burst.close()
    a.close()
    b.close()
    return result


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--arm", choices=("correct_pageout", "wrong_pageout", "no_hint"), required=True)
    p.add_argument("--hot-identity", choices=("A", "B"), required=True)
    p.add_argument("--region-mib", type=int, required=True)
    p.add_argument("--pageout-mib", type=int, required=True)
    p.add_argument("--burst-mib", type=int, required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()
    result = run(args.arm, args.hot_identity, args.region_mib, args.pageout_mib, args.burst_mib)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": result["status"],
        "arm": result["arm"],
        "hot_identity": result["hot_identity"],
        "hot_fraction": result["residency_pre_retouch"]["hot"]["resident_fraction"],
        "cold_fraction": result["residency_pre_retouch"]["cold"]["resident_fraction"],
        "hot_retouch_ms": result["hot_retouch_ns"] / 1e6,
        "work_interval_ms": result["work_interval_ns"] / 1e6,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
