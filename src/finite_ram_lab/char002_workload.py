from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import mmap
from pathlib import Path
from typing import Any

from .obs_workload import _self_cgroup_path, _snapshot, _touch
from .region_workload import LIBC, PAGE_SIZE, _mapping, residency


def _address(mm: mmap.mmap, offset: int = 0) -> int:
    return ctypes.addressof(ctypes.c_char.from_buffer(mm, offset))


def _range_residency(mm: mmap.mmap, offset: int, size: int) -> dict[str, Any]:
    if offset % PAGE_SIZE or size % PAGE_SIZE:
        raise ValueError("range must be page aligned")

    pages = size // PAGE_SIZE
    vec = (ctypes.c_ubyte * pages)()
    address = _address(mm, offset)

    rc = LIBC.mincore(
        ctypes.c_void_p(address),
        ctypes.c_size_t(size),
        vec,
    )
    if rc != 0:
        err = ctypes.get_errno()
        raise OSError(err, "mincore failed")

    resident = sum(1 for value in vec if value & 1)
    return {
        "page_size": PAGE_SIZE,
        "total_pages": pages,
        "resident_pages": resident,
        "missing_pages": pages - resident,
        "resident_fraction": resident / pages if pages else 0.0,
        "base_address": address,
    }


def _touch_range(mm: mmap.mmap, offset: int, size: int) -> None:
    for i in range(offset, offset + size, PAGE_SIZE):
        mm[i] = (mm[i] + 1) & 0xFF


def _digest_range(mm: mmap.mmap, offset: int, size: int) -> str:
    h = hashlib.sha256()
    for i in range(offset, offset + size, PAGE_SIZE):
        h.update(bytes([mm[i]]))
    return h.hexdigest()


def _event_oom(snapshot: dict[str, Any]) -> bool:
    events = snapshot["memory_events"]
    return events.get("oom", 0) != 0 or events.get("oom_kill", 0) != 0


def run_separate(
    creation_order: str,
    fault_order: str,
    region_mib: int,
    burst_mib: int,
    expected_high_bytes: int,
    expected_max_bytes: int,
) -> dict[str, Any]:
    if creation_order not in {"AB", "BA"}:
        raise ValueError("creation_order must be AB or BA")
    if fault_order not in {"AB", "BA"}:
        raise ValueError("fault_order must be AB or BA")

    region_size = region_mib * 1024 * 1024
    burst_size = burst_mib * 1024 * 1024
    regions: dict[str, mmap.mmap] = {}

    for identity in creation_order:
        regions[identity] = _mapping(region_size)

    addresses = {identity: _address(mm) for identity, mm in regions.items()}

    for identity in fault_order:
        _touch(regions[identity])

    digest_before = {
        identity: _digest_range(mm, 0, region_size)
        for identity, mm in regions.items()
    }

    cg = Path("/sys/fs/cgroup") / _self_cgroup_path().lstrip("/")
    os_before_burst = _snapshot(cg)

    burst = _mapping(burst_size)
    _touch(burst)

    os_after_burst = _snapshot(cg)
    residencies = {
        identity: residency(mm, region_size)
        for identity, mm in regions.items()
    }

    digest_after = {
        identity: _digest_range(mm, 0, region_size)
        for identity, mm in regions.items()
    }

    content_match = digest_before == digest_after
    lower_identity = min(addresses, key=addresses.get)
    higher_identity = max(addresses, key=addresses.get)
    aligned = all(address % PAGE_SIZE == 0 for address in addresses.values())

    checks = {
        "content_integrity": content_match,
        "no_oom": not _event_oom(os_after_burst),
        "memory_high_matches": os_after_burst["memory_high"] == expected_high_bytes,
        "memory_max_matches": os_after_burst["memory_max"] == expected_max_bytes,
        "addresses_page_aligned": aligned,
        "mappings_distinct": addresses["A"] != addresses["B"],
    }

    result = {
        "experiment_id": "CHAR-002",
        "family": "separate",
        "status": "PASS" if all(checks.values()) else "INVALID",
        "parameters": {
            "creation_order": creation_order,
            "fault_order": fault_order,
            "region_mib": region_mib,
            "burst_mib": burst_mib,
            "expected_high_bytes": expected_high_bytes,
            "expected_max_bytes": expected_max_bytes,
        },
        "addresses": {
            "A": addresses["A"],
            "B": addresses["B"],
            "lower_identity": lower_identity,
            "higher_identity": higher_identity,
        },
        "residency_after_burst": residencies,
        "os_before_burst": os_before_burst,
        "os_after_burst": os_after_burst,
        "content_match": content_match,
        "no_oom": not _event_oom(os_after_burst),
        "checks": checks,
    }

    burst.close()
    regions["A"].close()
    regions["B"].close()
    return result


def run_shared(
    fault_order: str,
    region_mib: int,
    burst_mib: int,
    expected_high_bytes: int,
    expected_max_bytes: int,
) -> dict[str, Any]:
    if fault_order not in {"lower_upper", "upper_lower"}:
        raise ValueError("fault_order must be lower_upper or upper_lower")

    region_size = region_mib * 1024 * 1024
    total_size = 2 * region_size
    burst_size = burst_mib * 1024 * 1024

    shared = _mapping(total_size)
    offsets = {"lower": 0, "upper": region_size}
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
    os_before_burst = _snapshot(cg)

    burst = _mapping(burst_size)
    _touch(burst)

    os_after_burst = _snapshot(cg)
    residencies = {
        name: _range_residency(shared, offset, region_size)
        for name, offset in offsets.items()
    }

    digest_after = {
        name: _digest_range(shared, offset, region_size)
        for name, offset in offsets.items()
    }

    content_match = digest_before == digest_after
    aligned = all(address % PAGE_SIZE == 0 for address in addresses.values())
    contiguous = addresses["upper"] - addresses["lower"] == region_size

    checks = {
        "content_integrity": content_match,
        "no_oom": not _event_oom(os_after_burst),
        "memory_high_matches": os_after_burst["memory_high"] == expected_high_bytes,
        "memory_max_matches": os_after_burst["memory_max"] == expected_max_bytes,
        "addresses_page_aligned": aligned,
        "shared_halves_contiguous": contiguous,
    }

    result = {
        "experiment_id": "CHAR-002",
        "family": "shared",
        "status": "PASS" if all(checks.values()) else "INVALID",
        "parameters": {
            "creation_order": "NA",
            "fault_order": fault_order,
            "region_mib": region_mib,
            "burst_mib": burst_mib,
            "expected_high_bytes": expected_high_bytes,
            "expected_max_bytes": expected_max_bytes,
        },
        "addresses": addresses,
        "residency_after_burst": residencies,
        "os_before_burst": os_before_burst,
        "os_after_burst": os_after_burst,
        "content_match": content_match,
        "no_oom": not _event_oom(os_after_burst),
        "checks": checks,
    }

    burst.close()
    shared.close()
    return result


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--family", choices=("separate", "shared"), required=True)
    p.add_argument("--creation-order", default="NA")
    p.add_argument("--fault-order", required=True)
    p.add_argument("--region-mib", type=int, required=True)
    p.add_argument("--burst-mib", type=int, required=True)
    p.add_argument("--expected-high-bytes", type=int, required=True)
    p.add_argument("--expected-max-bytes", type=int, required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    if args.family == "separate":
        result = run_separate(
            args.creation_order,
            args.fault_order,
            args.region_mib,
            args.burst_mib,
            args.expected_high_bytes,
            args.expected_max_bytes,
        )
    else:
        result = run_shared(
            args.fault_order,
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
        "family": result["family"],
        "parameters": result["parameters"],
        "addresses": result["addresses"],
        "residency_after_burst": result["residency_after_burst"],
    }, indent=2, sort_keys=True))

    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
