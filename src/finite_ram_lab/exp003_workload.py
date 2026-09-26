from __future__ import annotations

import argparse
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


MADV_PAGEOUT = 21


def _delta_stat(before: dict[str, Any], after: dict[str, Any], key: str) -> int:
    return int(
        after["memory_stat"].get(key, 0)
        - before["memory_stat"].get(key, 0)
    )


def _retouch_range(mm: mmap.mmap, offset: int, size: int) -> int:
    start = time.perf_counter_ns()
    for i in range(offset, offset + size, PAGE_SIZE):
        value = mm[i]
        mm[i] = value
    return time.perf_counter_ns() - start


def run(
    arm: str,
    fault_order: str,
    hot_position: str,
    region_mib: int,
    pageout_mib: int,
    burst_mib: int,
    expected_high_bytes: int,
    expected_max_bytes: int,
) -> dict[str, Any]:
    if arm not in {"correct_pageout", "no_hint", "wrong_pageout"}:
        raise ValueError("invalid arm")
    if fault_order not in {"lower_upper", "upper_lower"}:
        raise ValueError("invalid fault_order")
    if hot_position not in {"lower", "upper"}:
        raise ValueError("invalid hot_position")

    region_size = region_mib * 1024 * 1024
    pageout_size = pageout_mib * 1024 * 1024
    burst_size = burst_mib * 1024 * 1024

    if pageout_size <= 0 or pageout_size > region_size:
        raise ValueError("pageout range must fit inside one logical region")
    if pageout_size % PAGE_SIZE:
        raise ValueError("pageout range must be page aligned")

    total_size = 2 * region_size
    shared = _mapping(total_size)
    offsets = {"lower": 0, "upper": region_size}
    cold_position = "upper" if hot_position == "lower" else "lower"

    addresses = {
        name: _address(shared, offset)
        for name, offset in offsets.items()
    }

    for name in fault_order.split("_"):
        _touch_range(shared, offsets[name], region_size)

    digest_before = {
        name: _digest_range(shared, offset, region_size)
        for name, offset in offsets.items()
    }

    cg = Path("/sys/fs/cgroup") / _self_cgroup_path().lstrip("/")
    os_before_advice = _snapshot(cg)

    if arm == "correct_pageout":
        target_position = cold_position
    elif arm == "wrong_pageout":
        target_position = hot_position
    else:
        target_position = None

    advice_ns = 0
    advice_success = True
    advice_error = None
    target_offset = None

    if target_position is not None:
        target_offset = offsets[target_position]
        start = time.perf_counter_ns()
        try:
            shared.madvise(
                getattr(mmap, "MADV_PAGEOUT", MADV_PAGEOUT),
                target_offset,
                pageout_size,
            )
        except Exception as exc:
            advice_success = False
            advice_error = f"{type(exc).__name__}: {exc}"
        advice_ns = time.perf_counter_ns() - start

    burst = _mapping(burst_size)
    start = time.perf_counter_ns()
    _touch(burst)
    burst_touch_ns = time.perf_counter_ns() - start

    os_pre_retouch = _snapshot(cg)
    residency_pre_retouch = {
        "lower": _range_residency(shared, offsets["lower"], region_size),
        "upper": _range_residency(shared, offsets["upper"], region_size),
        "lower_first16": _range_residency(
            shared, offsets["lower"], pageout_size
        ),
        "upper_first16": _range_residency(
            shared, offsets["upper"], pageout_size
        ),
    }

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
    target_exact = (
        pageout_size == 16 * 1024 * 1024
        and (
            target_position is None
            or target_offset == offsets[target_position]
        )
    )

    checks = {
        "advice_success_when_required": (
            advice_success if target_position is not None else True
        ),
        "no_advice_in_no_hint": (
            target_position is None if arm == "no_hint" else True
        ),
        "content_integrity": content_match,
        "no_oom": no_oom,
        "memory_high_matches": (
            os_pre_retouch["memory_high"] == expected_high_bytes
        ),
        "memory_max_matches": (
            os_pre_retouch["memory_max"] == expected_max_bytes
        ),
        "shared_halves_contiguous": shared_halves_contiguous,
        "addresses_page_aligned": addresses_page_aligned,
        "pageout_target_exactly_sixteen_mib": target_exact,
    }

    first_faulted, second_faulted = fault_order.split("_")
    aligned = hot_position == second_faulted

    result = {
        "experiment_id": "EXP-003",
        "status": "PASS" if all(checks.values()) else "INVALID",
        "arm": arm,
        "fault_order": fault_order,
        "first_faulted": first_faulted,
        "second_faulted": second_faulted,
        "hot_position": hot_position,
        "cold_position": cold_position,
        "aligned": aligned,
        "target_position": target_position,
        "parameters": {
            "region_mib": region_mib,
            "pageout_mib": pageout_mib,
            "burst_mib": burst_mib,
            "expected_high_bytes": expected_high_bytes,
            "expected_max_bytes": expected_max_bytes,
        },
        "addresses": addresses,
        "advice": {
            "success": advice_success,
            "error": advice_error,
            "duration_ns": advice_ns,
            "target_offset": target_offset,
            "target_size_bytes": (
                pageout_size if target_position is not None else 0
            ),
        },
        "burst_touch_ns": burst_touch_ns,
        "hot_retouch_ns": hot_retouch_ns,
        "work_interval_ns": (
            advice_ns + burst_touch_ns + hot_retouch_ns
        ),
        "residency_pre_retouch": {
            "hot": residency_pre_retouch[hot_position],
            "cold": residency_pre_retouch[cold_position],
            "hot_first16": residency_pre_retouch[
                f"{hot_position}_first16"
            ],
            "cold_first16": residency_pre_retouch[
                f"{cold_position}_first16"
            ],
            "lower": residency_pre_retouch["lower"],
            "upper": residency_pre_retouch["upper"],
        },
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
        "os_before_advice": os_before_advice,
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
        "--arm",
        choices=("correct_pageout", "no_hint", "wrong_pageout"),
        required=True,
    )
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
    p.add_argument("--pageout-mib", type=int, required=True)
    p.add_argument("--burst-mib", type=int, required=True)
    p.add_argument("--expected-high-bytes", type=int, required=True)
    p.add_argument("--expected-max-bytes", type=int, required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    result = run(
        args.arm,
        args.fault_order,
        args.hot_position,
        args.region_mib,
        args.pageout_mib,
        args.burst_mib,
        args.expected_high_bytes,
        args.expected_max_bytes,
    )

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    print(json.dumps({
        "status": result["status"],
        "arm": result["arm"],
        "fault_order": result["fault_order"],
        "hot_position": result["hot_position"],
        "aligned": result["aligned"],
        "target_position": result["target_position"],
        "hot_fraction": result["residency_pre_retouch"]["hot"][
            "resident_fraction"
        ],
        "hot_retouch_ms": result["hot_retouch_ns"] / 1e6,
        "work_interval_ms": result["work_interval_ns"] / 1e6,
    }, indent=2, sort_keys=True))

    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
