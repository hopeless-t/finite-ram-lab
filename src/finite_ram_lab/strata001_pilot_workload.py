from __future__ import annotations

import argparse
import hashlib
import json
import mmap
import os
import time
from pathlib import Path
from typing import Any

from .obs_workload import _self_cgroup_path, _snapshot
from .region_workload import PAGE_SIZE, _mapping, residency
from .strata001_probe import _fadvise_dontneed, _file_residency


def _hot_fill(mm: mmap.mmap, size: int) -> None:
    for i in range(0, size, PAGE_SIZE):
        mm[i] = ((i // PAGE_SIZE) * 17 + 23) & 0xFF


def _hot_read(mm: mmap.mmap, size: int, rounds: int = 1) -> int:
    checksum = 0
    for _ in range(rounds):
        for i in range(0, size, PAGE_SIZE):
            checksum = (checksum + mm[i]) & 0xFFFFFFFF
    return checksum


def _hot_digest(mm: mmap.mmap, size: int) -> str:
    h = hashlib.sha256()
    for i in range(0, size, PAGE_SIZE):
        h.update(bytes([mm[i]]))
    return h.hexdigest()


def _retouch(mm: mmap.mmap, size: int) -> tuple[int, int]:
    checksum = 0
    start = time.perf_counter_ns()
    for i in range(0, size, PAGE_SIZE):
        value = mm[i]
        checksum = (checksum + value) & 0xFFFFFFFF
        mm[i] = value
    return time.perf_counter_ns() - start, checksum


def _scan(
    arm: str,
    path: Path,
    scratch: mmap.mmap,
    chunk: int,
) -> dict[str, Any]:
    size = path.stat().st_size
    if size % PAGE_SIZE or chunk % PAGE_SIZE:
        raise ValueError("file and chunk sizes must be page aligned")

    if arm == "mmap":
        fd = os.open(path, os.O_RDONLY)
        checksum = 0
        start = time.perf_counter_ns()
        try:
            mm = mmap.mmap(fd, size, access=mmap.ACCESS_READ)
            try:
                for offset in range(0, size, PAGE_SIZE):
                    checksum = (checksum + mm[offset]) & 0xFFFFFFFF
            finally:
                mm.close()
        finally:
            os.close(fd)
        return {
            "arm": arm,
            "logical_span_bytes": size,
            "elapsed_ns": time.perf_counter_ns() - start,
            "checksum": checksum,
            "direct_io": False,
            "error": None,
            "errno": None,
            "full_copy_semantics": False,
        }

    if arm not in {"buffered_pread", "direct_pread"}:
        raise ValueError(f"unknown arm: {arm}")

    flags = os.O_RDONLY
    direct = arm == "direct_pread"
    if direct:
        if not hasattr(os, "O_DIRECT"):
            return {
                "arm": arm,
                "logical_span_bytes": 0,
                "elapsed_ns": 0,
                "checksum": None,
                "direct_io": False,
                "error": "O_DIRECT unavailable",
                "errno": None,
                "full_copy_semantics": True,
            }
        flags |= os.O_DIRECT

    try:
        fd = os.open(path, flags)
    except OSError as exc:
        return {
            "arm": arm,
            "logical_span_bytes": 0,
            "elapsed_ns": 0,
            "checksum": None,
            "direct_io": direct,
            "error": f"{type(exc).__name__}: {exc}",
            "errno": exc.errno,
            "full_copy_semantics": True,
        }

    view = memoryview(scratch)
    checksum = 0
    total = 0
    start = time.perf_counter_ns()
    try:
        offset = 0
        while offset < size:
            want = min(chunk, size - offset)
            if want % PAGE_SIZE:
                raise ValueError("final read is not page aligned")
            try:
                got = os.preadv(fd, [view[:want]], offset)
            except OSError as exc:
                return {
                    "arm": arm,
                    "logical_span_bytes": total,
                    "elapsed_ns": time.perf_counter_ns() - start,
                    "checksum": checksum,
                    "direct_io": direct,
                    "error": f"{type(exc).__name__}: {exc}",
                    "errno": exc.errno,
                    "full_copy_semantics": True,
                }
            if got <= 0:
                return {
                    "arm": arm,
                    "logical_span_bytes": total,
                    "elapsed_ns": time.perf_counter_ns() - start,
                    "checksum": checksum,
                    "direct_io": direct,
                    "error": "unexpected EOF",
                    "errno": None,
                    "full_copy_semantics": True,
                }
            checksum = (checksum + view[0] + view[got - 1]) & 0xFFFFFFFF
            total += got
            offset += got
    finally:
        view.release()
        os.close(fd)

    return {
        "arm": arm,
        "logical_span_bytes": total,
        "elapsed_ns": time.perf_counter_ns() - start,
        "checksum": checksum,
        "direct_io": direct,
        "error": None,
        "errno": None,
        "full_copy_semantics": True,
    }


def _delta_stat(before: dict[str, Any], after: dict[str, Any], key: str) -> int:
    return int(after["memory_stat"].get(key, 0) - before["memory_stat"].get(key, 0))


def run(
    *,
    arm: str,
    file_path: Path,
    hot_anon_mib: int,
    buffer_mib: int,
    expected_file_mib: int,
    expected_high: int,
    expected_max: int,
    precache_limit: float,
) -> dict[str, Any]:
    if arm not in {"mmap", "buffered_pread", "direct_pread"}:
        raise ValueError("invalid arm")

    hot_size = hot_anon_mib * 1024 * 1024
    buffer_size = buffer_mib * 1024 * 1024
    expected_file_bytes = expected_file_mib * 1024 * 1024

    if file_path.stat().st_size != expected_file_bytes:
        raise ValueError("cold file size does not match frozen contract")
    if hot_size % PAGE_SIZE or buffer_size % PAGE_SIZE:
        raise ValueError("hot/buffer sizes must be page aligned")

    _fadvise_dontneed(file_path)
    time.sleep(0.05)
    file_pre = _file_residency(file_path)

    rel = _self_cgroup_path()
    cg = Path("/sys/fs/cgroup") / rel.lstrip("/")
    baseline = _snapshot(cg)

    hot = _mapping(hot_size)
    scratch = _mapping(buffer_size)
    try:
        _hot_fill(hot, hot_size)
        _hot_read(hot, hot_size, rounds=3)

        # Keep the same 4 MiB resident scratch footprint in every arm.
        for i in range(0, buffer_size, PAGE_SIZE):
            scratch[i] = (i // PAGE_SIZE) & 0xFF

        digest_before = _hot_digest(hot, hot_size)
        before_scan = _snapshot(cg)

        scan = _scan(arm, file_path, scratch, buffer_size)
        file_post = _file_residency(file_path)
        hot_pre_retouch = residency(hot, hot_size)
        pre_retouch = _snapshot(cg)

        hot_retouch_ns, hot_checksum = _retouch(hot, hot_size)
        post_retouch = _snapshot(cg)
        digest_after = _hot_digest(hot, hot_size)

        events = post_retouch["memory_events"]
        content_match = digest_before == digest_after
        no_oom = events.get("oom", 0) == 0 and events.get("oom_kill", 0) == 0

        direct_ok = (
            arm != "direct_pread"
            or (
                scan["error"] is None
                and scan["direct_io"] is True
                and scan["logical_span_bytes"] == expected_file_bytes
            )
        )

        checks = {
            "memory_high_matches": post_retouch["memory_high"] == expected_high,
            "memory_max_matches": post_retouch["memory_max"] == expected_max,
            "file_cold_before_scan": file_pre["resident_fraction"] <= precache_limit,
            "full_declared_span_processed": scan["logical_span_bytes"] == expected_file_bytes,
            "scan_no_error": scan["error"] is None,
            "direct_io_no_fallback": direct_ok,
            "hot_page_count": hot_pre_retouch["total_pages"] == hot_size // PAGE_SIZE,
            "content_integrity": content_match,
            "no_oom": no_oom,
        }

        status = "PASS" if all(checks.values()) else "INVALID"

        return {
            "experiment_id": "STRATA-001-PILOT-v1",
            "status": status,
            "arm": arm,
            "parameters": {
                "hot_anon_mib": hot_anon_mib,
                "cold_file_mib": expected_file_mib,
                "buffer_mib": buffer_mib,
                "expected_high_bytes": expected_high,
                "expected_max_bytes": expected_max,
                "page_size": PAGE_SIZE,
            },
            "file": {
                "path": str(file_path),
                "pre_scan_residency": file_pre,
                "post_scan_residency": file_post,
            },
            "scan": scan,
            "hot": {
                "pre_retouch_residency": hot_pre_retouch,
                "retouch_ns": hot_retouch_ns,
                "retouch_checksum": hot_checksum,
                "digest_before": digest_before,
                "digest_after": digest_after,
            },
            "work_interval_ns": int(scan["elapsed_ns"]) + hot_retouch_ns,
            "cgroup": {
                "path": rel,
                "baseline": baseline,
                "before_scan": before_scan,
                "pre_retouch": pre_retouch,
                "post_retouch": post_retouch,
            },
            "retouch_deltas": {
                "pswpin": _delta_stat(pre_retouch, post_retouch, "pswpin"),
                "workingset_refault_anon": _delta_stat(
                    pre_retouch, post_retouch, "workingset_refault_anon"
                ),
                "pgmajfault": _delta_stat(pre_retouch, post_retouch, "pgmajfault"),
                "pgfault": _delta_stat(pre_retouch, post_retouch, "pgfault"),
                "pgscan": _delta_stat(pre_retouch, post_retouch, "pgscan"),
                "pgsteal": _delta_stat(pre_retouch, post_retouch, "pgsteal"),
            },
            "checks": checks,
        }
    finally:
        scratch.close()
        hot.close()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--arm", choices=("mmap", "buffered_pread", "direct_pread"), required=True)
    p.add_argument("--file", required=True)
    p.add_argument("--hot-anon-mib", type=int, required=True)
    p.add_argument("--buffer-mib", type=int, required=True)
    p.add_argument("--expected-file-mib", type=int, required=True)
    p.add_argument("--expected-high-bytes", type=int, required=True)
    p.add_argument("--expected-max-bytes", type=int, required=True)
    p.add_argument("--precache-limit", type=float, default=0.10)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    result = run(
        arm=args.arm,
        file_path=Path(args.file),
        hot_anon_mib=args.hot_anon_mib,
        buffer_mib=args.buffer_mib,
        expected_file_mib=args.expected_file_mib,
        expected_high=args.expected_high_bytes,
        expected_max=args.expected_max_bytes,
        precache_limit=args.precache_limit,
    )

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    print(json.dumps({
        "status": result["status"],
        "arm": result["arm"],
        "hot_resident_fraction": result["hot"]["pre_retouch_residency"]["resident_fraction"],
        "file_post_fraction": result["file"]["post_scan_residency"]["resident_fraction"],
        "hot_retouch_ms": result["hot"]["retouch_ns"] / 1e6,
        "scan_ms": result["scan"]["elapsed_ns"] / 1e6,
        "work_ms": result["work_interval_ns"] / 1e6,
        "cgroup_anon_mib": result["cgroup"]["pre_retouch"]["memory_stat"]["anon"] / (1024 * 1024),
        "cgroup_file_mib": result["cgroup"]["pre_retouch"]["memory_stat"]["file"] / (1024 * 1024),
        "swap_mib": result["cgroup"]["pre_retouch"]["memory_swap_current"] / (1024 * 1024),
    }, indent=2, sort_keys=True))

    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
