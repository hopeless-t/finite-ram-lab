from __future__ import annotations

import argparse
import json
import mmap
import os
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .obs_workload import _kv_int, _read, _self_cgroup_path, _snapshot
from .region_workload import PAGE_SIZE, _mapping, residency
from .strata001_pilot_workload import (
    _delta_stat,
    _hot_digest,
    _hot_fill,
    _hot_read,
    _retouch,
)
from .strata001_probe import _fadvise_dontneed, _file_residency


ARMS = {
    "buffered",
    "dontneed_32m",
    "dontneed_48m",
    "dontneed_64m",
    "dontneed_72m",
    "dontneed_80m",
    "dontneed_88m",
    "dontneed_96m",
}

RELEASE_MIB = {
    "buffered": None,
    "dontneed_32m": 32,
    "dontneed_48m": 48,
    "dontneed_64m": 64,
    "dontneed_72m": 72,
    "dontneed_80m": 80,
    "dontneed_88m": 88,
    "dontneed_96m": 96,
}


def _compact_snapshot(cg: Path) -> dict[str, Any]:
    stat = _kv_int(_read(cg / "memory.stat"))
    events = _kv_int(_read(cg / "memory.events"))
    return {
        "memory_current": int(_read(cg / "memory.current")),
        "memory_swap_current": int(_read(cg / "memory.swap.current")),
        "memory_events_high": int(events.get("high", 0)),
        "memory_events_oom": int(events.get("oom", 0)),
        "memory_events_oom_kill": int(events.get("oom_kill", 0)),
        "memory_stat_file": int(stat.get("file", 0)),
        "memory_stat_anon": int(stat.get("anon", 0)),
    }


def _scan(
    *,
    arm: str,
    path: Path,
    scratch: mmap.mmap,
    chunk: int,
    cg: Path,
    checkpoint_hook: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    if arm not in ARMS:
        raise ValueError(f"unknown arm: {arm}")

    size = path.stat().st_size
    if size % PAGE_SIZE or chunk % PAGE_SIZE:
        raise ValueError("file and chunk sizes must be page aligned")

    direct = arm == "direct"
    flags = os.O_RDONLY
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
                "advice": {"kind": None, "calls": 0, "ranges": [], "success": False, "error": None},
                "checkpoints": [],
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
            "advice": {"kind": None, "calls": 0, "ranges": [], "success": False, "error": None},
            "checkpoints": [],
        }

    release_mib = RELEASE_MIB[arm]
    release_bytes = None if release_mib is None else release_mib * 1024 * 1024
    advice = {
        "kind": "POSIX_FADV_DONTNEED" if release_bytes is not None else None,
        "release_interval_bytes": release_bytes,
        "calls": 0,
        "ranges": [],
        "success": True,
        "error": None,
    }

    if release_bytes is not None:
        if not hasattr(os, "POSIX_FADV_DONTNEED"):
            advice["success"] = False
            advice["error"] = "POSIX_FADV_DONTNEED unavailable"
        elif release_bytes % PAGE_SIZE:
            advice["success"] = False
            advice["error"] = "release interval is not page aligned"

    if not advice["success"]:
        os.close(fd)
        return {
            "arm": arm,
            "logical_span_bytes": 0,
            "elapsed_ns": 0,
            "checksum": None,
            "direct_io": direct,
            "error": advice["error"],
            "errno": None,
            "advice": advice,
            "checkpoints": [],
        }

    view = memoryview(scratch)
    checksum = 0
    total = 0
    released_until = 0
    checkpoints: list[dict[str, Any]] = []
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
                    "advice": advice,
                    "checkpoints": checkpoints,
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
                    "advice": advice,
                    "checkpoints": checkpoints,
                }

            checksum = (checksum + view[0] + view[got - 1]) & 0xFFFFFFFF
            total += got
            offset += got

            pre = _compact_snapshot(cg)
            checkpoint: dict[str, Any] = {
                "consumed_bytes": total,
                "pre_advice": pre,
                "advice_applied": False,
                "advice_offset": None,
                "advice_length": None,
            }

            if release_bytes is not None and (total - released_until >= release_bytes or total == size):
                length = total - released_until
                if released_until % PAGE_SIZE or length % PAGE_SIZE:
                    raise RuntimeError("release range is not page aligned")
                try:
                    os.posix_fadvise(
                        fd,
                        released_until,
                        length,
                        os.POSIX_FADV_DONTNEED,
                    )
                except OSError as exc:
                    advice["success"] = False
                    advice["error"] = f"{type(exc).__name__}: {exc}"
                    return {
                        "arm": arm,
                        "logical_span_bytes": total,
                        "elapsed_ns": time.perf_counter_ns() - start,
                        "checksum": checksum,
                        "direct_io": direct,
                        "error": advice["error"],
                        "errno": exc.errno,
                        "advice": advice,
                        "checkpoints": checkpoints,
                    }

                advice["calls"] += 1
                advice["ranges"].append({
                    "offset": released_until,
                    "length": length,
                })
                checkpoint["advice_applied"] = True
                checkpoint["advice_offset"] = released_until
                checkpoint["advice_length"] = length
                released_until = total

            checkpoint["post_advice"] = _compact_snapshot(cg)
            if checkpoint_hook is not None:
                checkpoint_hook(checkpoint)
            checkpoints.append(checkpoint)
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
        "advice": advice,
        "checkpoints": checkpoints,
    }


def _max_checkpoint(checkpoints: list[dict[str, Any]], key: str) -> int:
    values: list[int] = []
    for cp in checkpoints:
        values.append(int(cp["pre_advice"][key]))
        values.append(int(cp["post_advice"][key]))
    return max(values) if values else 0


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
    checkpoint_hook: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    if arm not in ARMS:
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
        for i in range(0, buffer_size, PAGE_SIZE):
            scratch[i] = (i // PAGE_SIZE) & 0xFF

        digest_before = _hot_digest(hot, hot_size)
        before_scan = _snapshot(cg)

        scan = _scan(
            arm=arm,
            path=file_path,
            scratch=scratch,
            chunk=buffer_size,
            cg=cg,
            checkpoint_hook=checkpoint_hook,
        )

        file_post = _file_residency(file_path)
        hot_pre_retouch = residency(hot, hot_size)
        post_scan = _snapshot(cg)

        hot_retouch_ns, hot_checksum = _retouch(hot, hot_size)
        post_retouch = _snapshot(cg)
        digest_after = _hot_digest(hot, hot_size)

        content_match = digest_before == digest_after
        final_events = post_retouch["memory_events"]
        no_oom = final_events.get("oom", 0) == 0 and final_events.get("oom_kill", 0) == 0

        direct_ok = (
            arm != "direct"
            or (
                scan["error"] is None
                and scan["direct_io"] is True
                and scan["logical_span_bytes"] == expected_file_bytes
            )
        )
        advice_required = RELEASE_MIB[arm] is not None
        advice_ok = (not advice_required) or bool(scan["advice"]["success"])
        aligned_ok = True
        if advice_required:
            aligned_ok = all(
                int(r["offset"]) % PAGE_SIZE == 0
                and int(r["length"]) % PAGE_SIZE == 0
                for r in scan["advice"]["ranges"]
            )

        checks = {
            "memory_high_matches": post_retouch["memory_high"] == expected_high,
            "memory_max_matches": post_retouch["memory_max"] == expected_max,
            "file_cold_before_scan": file_pre["resident_fraction"] <= precache_limit,
            "full_declared_span_processed": scan["logical_span_bytes"] == expected_file_bytes,
            "scan_no_error": scan["error"] is None,
            "advice_success": advice_ok,
            "release_ranges_page_aligned": aligned_ok,
            "direct_io_no_fallback": direct_ok,
            "checkpoint_count": len(scan["checkpoints"]) == expected_file_bytes // buffer_size,
            "hot_page_count": hot_pre_retouch["total_pages"] == hot_size // PAGE_SIZE,
            "content_integrity": content_match,
            "no_oom": no_oom,
        }

        scan_deltas = {
            "memory_high_events": int(
                post_scan["memory_events"].get("high", 0)
                - before_scan["memory_events"].get("high", 0)
            ),
            "pgscan": _delta_stat(before_scan, post_scan, "pgscan"),
            "pgsteal": _delta_stat(before_scan, post_scan, "pgsteal"),
            "pgmajfault": _delta_stat(before_scan, post_scan, "pgmajfault"),
            "max_memory_current": _max_checkpoint(
                scan["checkpoints"], "memory_current"
            ),
            "max_memory_swap_current": _max_checkpoint(
                scan["checkpoints"], "memory_swap_current"
            ),
            "max_cgroup_file": _max_checkpoint(
                scan["checkpoints"], "memory_stat_file"
            ),
        }

        status = "PASS" if all(checks.values()) else "INVALID"

        return {
            "experiment_id": "STRATA-004-KNEE-v1",
            "status": status,
            "arm": arm,
            "parameters": {
                "hot_anon_mib": hot_anon_mib,
                "cold_file_mib": expected_file_mib,
                "read_chunk_mib": buffer_mib,
                "release_interval_mib": RELEASE_MIB[arm],
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
            "scan_deltas": scan_deltas,
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
                "post_scan": post_scan,
                "post_retouch": post_retouch,
            },
            "checks": checks,
        }
    finally:
        scratch.close()
        hot.close()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--arm", choices=tuple(sorted(ARMS)), required=True)
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
        "advice_calls": result["scan"]["advice"]["calls"],
        "high_events": result["scan_deltas"]["memory_high_events"],
        "max_scan_memory_mib": result["scan_deltas"]["max_memory_current"] / (1024 * 1024),
        "post_scan_memory_mib": result["cgroup"]["post_scan"]["memory_current"] / (1024 * 1024),
        "file_post_fraction": result["file"]["post_scan_residency"]["resident_fraction"],
        "scan_ms": result["scan"]["elapsed_ns"] / 1e6,
    }, indent=2, sort_keys=True))

    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
