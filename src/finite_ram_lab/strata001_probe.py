from __future__ import annotations

import argparse
import ctypes
import errno
import json
import mmap
import os
import time
from pathlib import Path
from typing import Any


PAGE_SIZE = os.sysconf("SC_PAGE_SIZE")
_LIBC = ctypes.CDLL(None, use_errno=True)


def _mount_info(path: Path) -> dict[str, Any]:
    target = str(path.resolve())
    best: dict[str, Any] | None = None
    best_len = -1
    try:
        lines = Path("/proc/self/mountinfo").read_text().splitlines()
    except OSError as exc:
        return {"available": False, "error": f"{type(exc).__name__}: {exc}"}

    for line in lines:
        parts = line.split()
        if "-" not in parts or len(parts) < 10:
            continue
        sep = parts.index("-")
        if sep + 3 >= len(parts):
            continue
        mount_point = parts[4].replace("\\040", " ")
        if target == mount_point or target.startswith(mount_point.rstrip("/") + "/"):
            if len(mount_point) > best_len:
                best_len = len(mount_point)
                best = {
                    "available": True,
                    "mount_point": mount_point,
                    "mount_options": parts[5].split(","),
                    "fs_type": parts[sep + 1],
                    "source": parts[sep + 2],
                    "super_options": parts[sep + 3].split(","),
                }
    return best or {"available": False, "error": "mount point not found"}


def _file_residency(path: Path) -> dict[str, Any]:
    size = path.stat().st_size
    if size <= 0 or size % PAGE_SIZE:
        raise ValueError("file size must be a positive page multiple")
    pages = size // PAGE_SIZE

    fd = os.open(path, os.O_RDONLY)
    try:
        mm = mmap.mmap(fd, size, access=mmap.ACCESS_COPY)
    finally:
        os.close(fd)

    try:
        buf = (ctypes.c_char * size).from_buffer(mm)
        addr = ctypes.addressof(buf)
        vec = (ctypes.c_ubyte * pages)()
        rc = _LIBC.mincore(
            ctypes.c_void_p(addr),
            ctypes.c_size_t(size),
            ctypes.cast(vec, ctypes.POINTER(ctypes.c_ubyte)),
        )
        if rc != 0:
            err = ctypes.get_errno()
            raise OSError(err, os.strerror(err))
        resident = sum(1 for x in vec if x & 1)
        return {
            "pages": pages,
            "resident_pages": resident,
            "resident_fraction": resident / pages,
        }
    finally:
        del buf
        mm.close()


def _fadvise_dontneed(path: Path) -> None:
    if not hasattr(os, "posix_fadvise") or not hasattr(os, "POSIX_FADV_DONTNEED"):
        raise RuntimeError("POSIX_FADV_DONTNEED unavailable")
    fd = os.open(path, os.O_RDONLY)
    try:
        os.posix_fadvise(fd, 0, 0, os.POSIX_FADV_DONTNEED)
    finally:
        os.close(fd)


def _prepare_file(path: Path, size: int, chunk: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pattern = b"\xA5" * chunk
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        remaining = size
        while remaining:
            n = min(chunk, remaining)
            view = memoryview(pattern)[:n]
            written = 0
            while written < n:
                got = os.write(fd, view[written:])
                if got <= 0:
                    raise OSError("short file preparation write")
                written += got
            remaining -= n
        os.fsync(fd)
    finally:
        os.close(fd)

    _fadvise_dontneed(path)


def _scan_mmap(path: Path, page_size: int) -> dict[str, Any]:
    size = path.stat().st_size
    fd = os.open(path, os.O_RDONLY)
    start = time.perf_counter_ns()
    checksum = 0
    try:
        mm = mmap.mmap(fd, size, access=mmap.ACCESS_READ)
        try:
            for offset in range(0, size, page_size):
                checksum = (checksum + mm[offset]) & 0xFFFFFFFF
        finally:
            mm.close()
    finally:
        os.close(fd)
    return {
        "io_path": "mmap",
        "logical_span_bytes": size,
        "elapsed_ns": time.perf_counter_ns() - start,
        "checksum": checksum,
        "direct_io": False,
        "error": None,
        "errno": None,
    }


def _scan_preadv(path: Path, chunk: int, *, direct: bool) -> dict[str, Any]:
    size = path.stat().st_size
    if chunk % PAGE_SIZE:
        raise ValueError("chunk must be page aligned")
    flags = os.O_RDONLY
    if direct:
        if not hasattr(os, "O_DIRECT"):
            return {
                "io_path": "direct_pread",
                "logical_span_bytes": 0,
                "elapsed_ns": 0,
                "checksum": None,
                "direct_io": False,
                "error": "O_DIRECT unavailable in Python/os",
                "errno": None,
            }
        flags |= os.O_DIRECT

    try:
        fd = os.open(path, flags)
    except OSError as exc:
        return {
            "io_path": "direct_pread" if direct else "buffered_pread",
            "logical_span_bytes": 0,
            "elapsed_ns": 0,
            "checksum": None,
            "direct_io": direct,
            "error": f"{type(exc).__name__}: {exc}",
            "errno": exc.errno,
        }

    buf = mmap.mmap(-1, chunk)
    view = memoryview(buf)
    checksum = 0
    total = 0
    start = time.perf_counter_ns()
    try:
        offset = 0
        while offset < size:
            want = min(chunk, size - offset)
            if want % PAGE_SIZE:
                raise ValueError("final direct-read size is not page aligned")
            try:
                got = os.preadv(fd, [view[:want]], offset)
            except OSError as exc:
                return {
                    "io_path": "direct_pread" if direct else "buffered_pread",
                    "logical_span_bytes": total,
                    "elapsed_ns": time.perf_counter_ns() - start,
                    "checksum": checksum,
                    "direct_io": direct,
                    "error": f"{type(exc).__name__}: {exc}",
                    "errno": exc.errno,
                }
            if got <= 0:
                return {
                    "io_path": "direct_pread" if direct else "buffered_pread",
                    "logical_span_bytes": total,
                    "elapsed_ns": time.perf_counter_ns() - start,
                    "checksum": checksum,
                    "direct_io": direct,
                    "error": "unexpected EOF",
                    "errno": None,
                }
            checksum = (checksum + view[0] + view[got - 1]) & 0xFFFFFFFF
            total += got
            offset += got

        return {
            "io_path": "direct_pread" if direct else "buffered_pread",
            "logical_span_bytes": total,
            "elapsed_ns": time.perf_counter_ns() - start,
            "checksum": checksum,
            "direct_io": direct,
            "error": None,
            "errno": None,
        }
    finally:
        view.release()
        buf.close()
        os.close(fd)


def classify(spec: dict[str, Any], arms: dict[str, dict[str, Any]]) -> tuple[str, dict[str, bool]]:
    prep_limit = float(spec["prepare"]["require_precache_fraction_le"])
    checks_cfg = spec["capability_checks"]

    warm_ok = all(float(a["pre"]["resident_fraction"]) <= prep_limit for a in arms.values())
    exact = all(
        int(a["scan"]["logical_span_bytes"]) == int(a["expected_bytes"])
        for a in arms.values()
    )
    direct = arms["direct_pread"]["scan"]
    direct_ok = direct.get("error") is None and bool(direct.get("direct_io"))
    buffered_cache = (
        float(arms["buffered_pread"]["post"]["resident_fraction"])
        >= float(checks_cfg["buffered_postcache_fraction_ge"])
    )
    mmap_cache = (
        float(arms["mmap"]["post"]["resident_fraction"])
        >= float(checks_cfg["mmap_postcache_fraction_ge"])
    )
    direct_cold = (
        float(arms["direct_pread"]["post"]["resident_fraction"])
        <= float(checks_cfg["direct_postcache_fraction_le"])
    )

    checks = {
        "precache_cold": warm_ok,
        "all_arms_read_exact_bytes": exact,
        "direct_io_succeeds_without_buffered_fallback": direct_ok,
        "buffered_populates_page_cache": buffered_cache,
        "mmap_populates_page_cache": mmap_cache,
        "direct_does_not_materially_populate_page_cache": direct_cold,
    }

    unsupported = {
        errno.EINVAL,
        getattr(errno, "EOPNOTSUPP", errno.EINVAL),
        getattr(errno, "ENOTSUP", errno.EINVAL),
    }
    if direct.get("error") is not None and direct.get("errno") in unsupported:
        return "CAPABILITY_HOLD", checks
    if direct.get("error") is not None and direct.get("errno") is None:
        return "CAPABILITY_HOLD", checks
    if not warm_ok:
        return "INVALID", checks
    return ("PASS" if all(checks.values()) else "FAIL"), checks


def run(spec: dict[str, Any], root: Path) -> dict[str, Any]:
    size = int(spec["file_mib_per_arm"]) * 1024 * 1024
    chunk = int(spec["chunk_kib"]) * 1024
    page_size = int(spec["page_size"])
    if page_size != PAGE_SIZE:
        raise ValueError(f"frozen page size {page_size} != host page size {PAGE_SIZE}")
    if size % page_size or chunk % page_size:
        raise ValueError("frozen sizes must be page aligned")

    root.mkdir(parents=True, exist_ok=True)
    arms: dict[str, dict[str, Any]] = {}

    for arm in spec["arms"]:
        path = root / f"{arm}.bin"
        _prepare_file(path, size, chunk)
        pre = _file_residency(path)

        if arm == "mmap":
            scan = _scan_mmap(path, page_size)
        elif arm == "buffered_pread":
            scan = _scan_preadv(path, chunk, direct=False)
        elif arm == "direct_pread":
            scan = _scan_preadv(path, chunk, direct=True)
        else:
            raise ValueError(f"unknown arm: {arm}")

        post = _file_residency(path)
        arms[arm] = {
            "path": str(path),
            "expected_bytes": size,
            "pre": pre,
            "scan": scan,
            "post": post,
        }

    status, checks = classify(spec, arms)
    return {
        "experiment_id": spec["experiment_id"],
        "status": status,
        "inspiration": spec["inspiration"],
        "host": {
            "page_size": PAGE_SIZE,
            "mount": _mount_info(root),
        },
        "arms": arms,
        "checks": checks,
        "authority": spec["authority"],
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--spec", required=True)
    p.add_argument("--dir", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    spec = json.loads(Path(args.spec).read_text())
    result = run(spec, Path(args.dir))

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    summary = {
        "status": result["status"],
        "checks": result["checks"],
        "mount": result["host"]["mount"],
        "post_cache": {
            arm: data["post"]["resident_fraction"]
            for arm, data in result["arms"].items()
        },
    }
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
