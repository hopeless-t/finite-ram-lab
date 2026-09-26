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


def _delta_stat(before: dict[str, Any], after: dict[str, Any], key: str) -> int:
    return int(
        after["memory_stat"].get(key, 0)
        - before["memory_stat"].get(key, 0)
    )


def run(
    recent_identity: str,
    hot_identity: str,
    region_mib: int,
    burst_mib: int,
    touch_rounds: int,
) -> dict[str, Any]:
    if recent_identity not in {"A", "B"}:
        raise ValueError("recent_identity must be A or B")
    if hot_identity not in {"A", "B"}:
        raise ValueError("hot_identity must be A or B")

    older_identity = "B" if recent_identity == "A" else "A"
    region_size = region_mib * 1024 * 1024
    burst_size = burst_mib * 1024 * 1024

    a = _mapping(region_size)
    b = _mapping(region_size)
    regions = {"A": a, "B": b}

    # Fault both mappings in. Mapping identity is counterbalanced by the
    # randomized recent_identity factor in the factorial design.
    _touch(a)
    _touch(b)

    # Equal touch counts, controlled final order.
    _touch(regions[older_identity], rounds=touch_rounds)
    _touch(regions[recent_identity], rounds=touch_rounds)

    # Content-integrity baseline belongs after the intentional recency writes.
    # Capturing it before those writes would classify the designed workload
    # mutation itself as corruption.
    digest_before = {
        "A": _digest(a, region_size),
        "B": _digest(b, region_size),
    }

    cg = Path("/sys/fs/cgroup") / _self_cgroup_path().lstrip("/")
    os_before_burst = _snapshot(cg)

    burst = _mapping(burst_size)
    burst_start = time.perf_counter_ns()
    _touch(burst)
    burst_touch_ns = time.perf_counter_ns() - burst_start

    os_pre_retouch = _snapshot(cg)
    residency_pre_retouch = {
        "A": residency(a, region_size),
        "B": residency(b, region_size),
    }

    hot_retouch_ns = _retouch(regions[hot_identity], region_size)
    os_post_retouch = _snapshot(cg)

    digest_after = {
        "A": _digest(a, region_size),
        "B": _digest(b, region_size),
    }
    content_match = digest_before == digest_after

    events = os_post_retouch["memory_events"]
    no_oom = (
        events.get("oom", 0) == 0
        and events.get("oom_kill", 0) == 0
    )

    result = {
        "experiment_id": "HYP-002",
        "status": "PASS" if content_match and no_oom else "INVALID",
        "recent_identity": recent_identity,
        "older_identity": older_identity,
        "hot_identity": hot_identity,
        "aligned": hot_identity == recent_identity,
        "parameters": {
            "region_mib": region_mib,
            "burst_mib": burst_mib,
            "recency_touch_rounds": touch_rounds,
        },
        "burst_touch_ns": burst_touch_ns,
        "hot_retouch_ns": hot_retouch_ns,
        "residency_pre_retouch": residency_pre_retouch,
        "swap_mib_pre_retouch": (
            os_pre_retouch["memory_swap_current"] / (1024 * 1024)
        ),
        "retouch_deltas": {
            "pswpin": _delta_stat(
                os_pre_retouch, os_post_retouch, "pswpin"
            ),
            "workingset_refault_anon": _delta_stat(
                os_pre_retouch,
                os_post_retouch,
                "workingset_refault_anon",
            ),
            "pgmajfault": _delta_stat(
                os_pre_retouch, os_post_retouch, "pgmajfault"
            ),
            "pgfault": _delta_stat(
                os_pre_retouch, os_post_retouch, "pgfault"
            ),
        },
        "content_match": content_match,
        "no_oom": no_oom,
        "os_before_burst": os_before_burst,
    }

    burst.close()
    a.close()
    b.close()
    return result


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--recent-identity", choices=("A", "B"), required=True)
    p.add_argument("--hot-identity", choices=("A", "B"), required=True)
    p.add_argument("--region-mib", type=int, required=True)
    p.add_argument("--burst-mib", type=int, required=True)
    p.add_argument("--touch-rounds", type=int, required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    result = run(
        args.recent_identity,
        args.hot_identity,
        args.region_mib,
        args.burst_mib,
        args.touch_rounds,
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    recent = result["residency_pre_retouch"][result["recent_identity"]][
        "resident_fraction"
    ]
    older = result["residency_pre_retouch"][result["older_identity"]][
        "resident_fraction"
    ]

    print(json.dumps({
        "status": result["status"],
        "recent_identity": result["recent_identity"],
        "hot_identity": result["hot_identity"],
        "aligned": result["aligned"],
        "recent_fraction": recent,
        "older_fraction": older,
        "hot_retouch_ms": result["hot_retouch_ns"] / 1e6,
    }, indent=2, sort_keys=True))

    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
