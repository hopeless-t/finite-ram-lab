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
from .reclaim_probe import _reclaim


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
    reclaim_mib: int,
    post_pageout_wait_ms: int,
    post_reclaim_wait_ms: int,
    target_fraction_max: float,
    nontarget_fraction_min: float,
) -> dict[str, Any]:
    if arm not in {"hot_evict", "cold_evict"}:
        raise ValueError("invalid arm")
    if hot_identity not in {"A", "B"}:
        raise ValueError("hot_identity must be A or B")

    cold_identity = "B" if hot_identity == "A" else "A"
    target_identity = hot_identity if arm == "hot_evict" else cold_identity
    nontarget_identity = cold_identity if arm == "hot_evict" else hot_identity

    size = region_mib * 1024 * 1024
    a = _mapping(size)
    b = _mapping(size)
    regions = {"A": a, "B": b}
    _touch(a)
    _touch(b)

    hot = regions[hot_identity]
    target = regions[target_identity]
    nontarget = regions[nontarget_identity]
    cg = Path("/sys/fs/cgroup") / _self_cgroup_path().lstrip("/")

    digest_before = {"A": _digest(a, size), "B": _digest(b, size)}
    os_before = _snapshot(cg)

    advice = getattr(mmap, "MADV_PAGEOUT", 21)
    pageout_success = False
    pageout_error = None
    start = time.perf_counter_ns()
    try:
        target.madvise(advice, 0, size)
        pageout_success = True
    except Exception as exc:
        pageout_error = f"{type(exc).__name__}: {exc}"
    pageout_ns = time.perf_counter_ns() - start
    time.sleep(post_pageout_wait_ms / 1000.0)

    reclaim = _reclaim(cg / "memory.reclaim", f"{reclaim_mib}M swappiness=max")
    time.sleep(post_reclaim_wait_ms / 1000.0)
    os_pre_retouch = _snapshot(cg)
    target_res = residency(target, size)
    nontarget_res = residency(nontarget, size)
    hot_res = residency(hot, size)

    hot_retouch_ns = _retouch(hot, size)
    os_post_retouch = _snapshot(cg)

    digest_after = {"A": _digest(a, size), "B": _digest(b, size)}
    content_match = digest_before == digest_after
    events = os_post_retouch["memory_events"]
    no_oom = events.get("oom", 0) == 0 and events.get("oom_kill", 0) == 0

    fidelity = {
        "pageout_success": pageout_success,
        "target_nonresident": target_res["resident_fraction"] <= target_fraction_max,
        "nontarget_resident": nontarget_res["resident_fraction"] >= nontarget_fraction_min,
        "content_match": content_match,
        "no_oom": no_oom,
    }

    result = {
        "experiment_id": "EXP-001",
        "status": "PASS" if all(fidelity.values()) else "INVALID",
        "arm": arm,
        "hot_identity": hot_identity,
        "cold_identity": cold_identity,
        "target_identity": target_identity,
        "nontarget_identity": nontarget_identity,
        "region_mib": region_mib,
        "pageout": {
            "success": pageout_success,
            "error": pageout_error,
            "duration_ns": pageout_ns,
        },
        "reclaim": reclaim,
        "residency_pre_retouch": {
            "target": target_res,
            "nontarget": nontarget_res,
            "hot": hot_res,
        },
        "hot_retouch_ns": hot_retouch_ns,
        "retouch_deltas": {
            "pswpin": _delta_stat(os_pre_retouch, os_post_retouch, "pswpin"),
            "workingset_refault_anon": _delta_stat(os_pre_retouch, os_post_retouch, "workingset_refault_anon"),
            "pgmajfault": _delta_stat(os_pre_retouch, os_post_retouch, "pgmajfault"),
            "pgfault": _delta_stat(os_pre_retouch, os_post_retouch, "pgfault"),
            "pgscan": _delta_stat(os_pre_retouch, os_post_retouch, "pgscan"),
            "pgsteal": _delta_stat(os_pre_retouch, os_post_retouch, "pgsteal"),
        },
        "swap_mib_pre_retouch": os_pre_retouch["memory_swap_current"] / (1024 * 1024),
        "content_match": content_match,
        "fidelity": fidelity,
        "os_before": os_before,
    }

    a.close()
    b.close()
    return result


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--arm", choices=("hot_evict", "cold_evict"), required=True)
    p.add_argument("--hot-identity", choices=("A", "B"), required=True)
    p.add_argument("--region-mib", type=int, required=True)
    p.add_argument("--reclaim-mib", type=int, required=True)
    p.add_argument("--post-pageout-wait-ms", type=int, required=True)
    p.add_argument("--post-reclaim-wait-ms", type=int, required=True)
    p.add_argument("--target-fraction-max", type=float, required=True)
    p.add_argument("--nontarget-fraction-min", type=float, required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()
    result = run(
        args.arm, args.hot_identity, args.region_mib, args.reclaim_mib,
        args.post_pageout_wait_ms, args.post_reclaim_wait_ms,
        args.target_fraction_max, args.nontarget_fraction_min,
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": result["status"],
        "arm": result["arm"],
        "hot_identity": result["hot_identity"],
        "target_fraction": result["residency_pre_retouch"]["target"]["resident_fraction"],
        "nontarget_fraction": result["residency_pre_retouch"]["nontarget"]["resident_fraction"],
        "hot_retouch_ms": result["hot_retouch_ns"] / 1e6,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
