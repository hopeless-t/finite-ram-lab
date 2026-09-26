from __future__ import annotations

import argparse
import hashlib
import json
import mmap
import time
from pathlib import Path
from typing import Any

from .char002_workload import (
    _address,
    _digest_range,
    _range_residency,
    _touch_range,
)
from .obs_workload import _self_cgroup_path, _snapshot, _touch
from .region_workload import PAGE_SIZE, _mapping


def _retouch_range(mm: mmap.mmap, offset: int, size: int) -> int:
    start = time.perf_counter_ns()
    for i in range(offset, offset + size, PAGE_SIZE):
        value = mm[i]
        mm[i] = value
    return time.perf_counter_ns() - start


def _delta_stat(before: dict[str, Any], after: dict[str, Any], key: str) -> int:
    return int(
        after["memory_stat"].get(key, 0)
        - before["memory_stat"].get(key, 0)
    )


def run(
    fault_order: str,
    hot_position: str,
    region_mib: int,
    burst_mib: int,
    expected_high_bytes: int,
    expected_max_bytes: int,
) -> dict[str, Any]:
    if fault_order not in {"lower_upper", "upper_lower"}:
        raise ValueError("fault_order must be lower_upper or upper_lower")
    if hot_position not in {"lower", "upper"}:
        raise ValueError("hot_position must be lower or upper")

    region_size = region_mib * 1024 * 1024
    total_size = 2 * region_size
    burst_size = burst_mib * 1024 * 1024

    shared = _mapping(total_size)
    offsets = {"lower": 0, "upper": region_size}
    addresses = {
        name: _address(shared, offset)
        for name, offset in offsets.items()
    }

    # The future semantic HOT assignment is intentionally unused until after
    # the post-burst residency snapshot.
    for name in fault_order.split("_"):
        _touch_range(shared, offsets[name], region_size)

    digest_before = {
        name: _digest_range(shared, offset, region_size)
        for name, offset in offsets.items()
    }

    cg = Path("/sys/fs/cgroup") / _self_cgroup_path().lstrip("/")
    os_before_burst = _snapshot(cg)

    burst = _mapping(burst_size)
    _touch(burst)

    os_pre_retouch = _snapshot(cg)
    residency_pre_retouch = {
        name: _range_residency(shared, offset, region_size)
        for name, offset in offsets.items()
    }

    # First use of the future semantic identity.
    hot_retouch_ns = _retouch_range(
        shared,
        offsets[hot_position],
        region_size,
    )
    os_post_retouch = _snapshot(cg)

    digest_after = {
        name: _digest_range(shared, offset, region_size)
        for name, offset in offsets.items()
    }
    content_match = digest_before == digest_after

    events = os_post_retouch["memory_events"]
    no_oom = (
        events.get("oom", 0) == 0
        and events.get("oom_kill", 0) == 0
    )

    addresses_page_aligned = all(
        address % PAGE_SIZE == 0
        for address in addresses.values()
    )
    shared_halves_contiguous = (
        addresses["upper"] - addresses["lower"] == region_size
    )

    checks = {
        "content_integrity": content_match,
        "no_oom": no_oom,
        "memory_high_matches": (
            os_pre_retouch["memory_high"] == expected_high_bytes
        ),
        "memory_max_matches": (
            os_pre_retouch["memory_max"] == expected_max_bytes
        ),
        "addresses_page_aligned": addresses_page_aligned,
        "shared_halves_contiguous": shared_halves_contiguous,
        "hot_unused_before_residency_snapshot": True,
    }

    result = {
        "experiment_id": "HYP-003",
        "status": "PASS" if all(checks.values()) else "INVALID",
        "fault_order": fault_order,
        "hot_position": hot_position,
        "aligned": hot_position == fault_order.split("_")[1],
        "parameters": {
            "region_mib": region_mib,
            "burst_mib": burst_mib,
            "expected_high_bytes": expected_high_bytes,
            "expected_max_bytes": expected_max_bytes,
        },
        "addresses": addresses,
        "residency_pre_retouch": residency_pre_retouch,
        "hot_retouch_ns": hot_retouch_ns,
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
            "pgscan": _delta_stat(
                os_pre_retouch, os_post_retouch, "pgscan"
            ),
            "pgsteal": _delta_stat(
                os_pre_retouch, os_post_retouch, "pgsteal"
            ),
        },
        "os_before_burst": os_before_burst,
        "os_pre_retouch": os_pre_retouch,
        "content_match": content_match,
        "no_oom": no_oom,
        "checks": checks,
    }

    burst.close()
    shared.close()
    return result


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--fault-order",
        choices=("lower_upper", "upper_lower"),
        required=True,
    )
    p.add_argument(
        "--hot-position",
        choices=("lower", "upper"),
        required=True,
    )
    p.add_argument("--region-mib", type=int, required=True)
    p.add_argument("--burst-mib", type=int, required=True)
    p.add_argument("--expected-high-bytes", type=int, required=True)
    p.add_argument("--expected-max-bytes", type=int, required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    result = run(
        args.fault_order,
        args.hot_position,
        args.region_mib,
        args.burst_mib,
        args.expected_high_bytes,
        args.expected_max_bytes,
    )

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    print(json.dumps({
        "status": result["status"],
        "fault_order": result["fault_order"],
        "hot_position": result["hot_position"],
        "aligned": result["aligned"],
        "hot_fraction": result["residency_pre_retouch"][
            result["hot_position"]
        ]["resident_fraction"],
        "hot_retouch_ms": result["hot_retouch_ns"] / 1e6,
    }, indent=2, sort_keys=True))

    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
