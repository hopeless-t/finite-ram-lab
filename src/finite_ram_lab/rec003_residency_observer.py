from __future__ import annotations

import argparse
import csv
import ctypes
import gc
import json
import mmap
import os
import random
import statistics
import time
from pathlib import Path
from typing import Any

from .obs_workload import _kv_int, _read, _self_cgroup_path
from .strata001_probe import PAGE_SIZE


_LIBC = ctypes.CDLL(None, use_errno=True)
PHASES = (
    "baseline",
    "after_mmap",
    "after_ctypes_view",
    "after_mincore_vec",
    "after_mincore",
    "after_count",
    "after_cleanup",
    "after_gc_settle",
)


def load_spec(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def schedule_rows(spec: dict[str, Any], block: int) -> list[dict[str, Any]]:
    blocks = int(spec["runner_blocks"])
    if block not in range(blocks):
        raise ValueError("block outside frozen design")
    sizes = [int(x) for x in spec["file_sizes_mib"]]
    random.Random(
        int(spec["base_schedule_seed"]) + block * 9176
    ).shuffle(sizes)
    return [{"order": i, "size_mib": size} for i, size in enumerate(sizes)]


def write_schedule(spec: dict[str, Any], block: int, out: str | Path) -> None:
    path = Path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["order", "size_mib"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(schedule_rows(spec, block))


def _snapshot(cg: Path, fields: list[str]) -> dict[str, Any]:
    stat = _kv_int(_read(cg / "memory.stat"))
    peak_path = cg / "memory.peak"
    try:
        peak = int(_read(peak_path))
    except OSError:
        peak = None
    return {
        "memory_current": int(_read(cg / "memory.current")),
        "memory_peak": peak,
        "memory_stat": {field: int(stat.get(field, 0)) for field in fields},
    }


def _delta_snapshot(
    baseline: dict[str, Any],
    snap: dict[str, Any],
) -> dict[str, Any]:
    base_current = int(baseline["memory_current"])
    base_stat = baseline["memory_stat"]
    return {
        "memory_current_delta": int(snap["memory_current"]) - base_current,
        "memory_stat_delta": {
            key: int(snap["memory_stat"][key]) - int(base_stat[key])
            for key in base_stat
        },
    }


def run_trial(
    spec: dict[str, Any],
    *,
    block: int,
    order: int,
    size_mib: int,
    file_path: Path,
    source_commit: str,
) -> dict[str, Any]:
    sizes = [int(x) for x in spec["file_sizes_mib"]]
    if size_mib not in sizes:
        raise ValueError("size outside frozen design")
    if block not in range(int(spec["runner_blocks"])):
        raise ValueError("block outside frozen design")

    size = size_mib * 1024 * 1024
    if file_path.stat().st_size != size:
        raise ValueError("prepared file size mismatch")
    if size % PAGE_SIZE:
        raise ValueError("file size must be page aligned")
    pages = size // PAGE_SIZE

    rel = _self_cgroup_path()
    cg = Path("/sys/fs/cgroup") / rel.lstrip("/")
    fields = list(spec["memory_stat_fields"])
    snaps: dict[str, dict[str, Any]] = {}

    snaps["baseline"] = _snapshot(cg, fields)

    fd = os.open(file_path, os.O_RDONLY)
    try:
        mm = mmap.mmap(fd, size, access=mmap.ACCESS_COPY)
    finally:
        os.close(fd)
    snaps["after_mmap"] = _snapshot(cg, fields)

    buf = (ctypes.c_char * size).from_buffer(mm)
    snaps["after_ctypes_view"] = _snapshot(cg, fields)

    vec = (ctypes.c_ubyte * pages)()
    snaps["after_mincore_vec"] = _snapshot(cg, fields)

    addr = ctypes.addressof(buf)
    rc = _LIBC.mincore(
        ctypes.c_void_p(addr),
        ctypes.c_size_t(size),
        ctypes.cast(vec, ctypes.POINTER(ctypes.c_ubyte)),
    )
    if rc != 0:
        err = ctypes.get_errno()
        del buf
        mm.close()
        raise OSError(err, os.strerror(err))
    snaps["after_mincore"] = _snapshot(cg, fields)

    resident = sum(1 for x in vec if x & 1)
    snaps["after_count"] = _snapshot(cg, fields)

    del buf
    del vec
    mm.close()
    snaps["after_cleanup"] = _snapshot(cg, fields)

    gc.collect()
    time.sleep(float(spec["settle_seconds"]))
    snaps["after_gc_settle"] = _snapshot(cg, fields)

    baseline = snaps["baseline"]
    deltas = {
        phase: _delta_snapshot(baseline, snaps[phase])
        for phase in PHASES
    }

    phase_current_deltas = [
        int(deltas[phase]["memory_current_delta"])
        for phase in PHASES
    ]
    final_peak = snaps["after_gc_settle"]["memory_peak"]
    peak_minus_baseline = (
        None
        if final_peak is None
        else int(final_peak) - int(baseline["memory_current"])
    )

    return {
        "experiment_id": spec["experiment_id"],
        "status": "PASS",
        "source_commit": source_commit,
        "block": block,
        "order": order,
        "size_mib": size_mib,
        "file_bytes": size,
        "page_size": PAGE_SIZE,
        "pages": pages,
        "mincore_vector_bytes": pages,
        "resident_pages": resident,
        "resident_fraction": resident / pages,
        "cgroup_path": rel,
        "snapshots": snaps,
        "deltas": deltas,
        "derived": {
            "max_observed_phase_current_delta_bytes": max(phase_current_deltas),
            "post_cleanup_current_delta_bytes": int(
                deltas["after_cleanup"]["memory_current_delta"]
            ),
            "post_gc_settle_current_delta_bytes": int(
                deltas["after_gc_settle"]["memory_current_delta"]
            ),
            "final_memory_peak_minus_baseline_current_bytes": peak_minus_baseline,
        },
    }


def _median(rows: list[dict[str, Any]], path: tuple[str, ...]) -> float:
    values: list[float] = []
    for row in rows:
        value: Any = row
        for key in path:
            value = value[key]
        if value is not None:
            values.append(float(value))
    if not values:
        return float("nan")
    return float(statistics.median(values))


def summarize(spec: dict[str, Any], root: Path) -> dict[str, Any]:
    trials = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(root.rglob("trial-*.json"))
    ]
    expected = int(spec["expected_trials"])
    if len(trials) != expected:
        raise ValueError(f"expected {expected} trials, got {len(trials)}")
    if any(row.get("status") != "PASS" for row in trials):
        raise ValueError("all trials must PASS")

    sizes = [int(x) for x in spec["file_sizes_mib"]]
    blocks = int(spec["runner_blocks"])
    seen: set[tuple[int, int]] = set()
    by_size: dict[int, list[dict[str, Any]]] = {}

    for row in trials:
        ident = (int(row["block"]), int(row["size_mib"]))
        if ident in seen:
            raise ValueError(f"duplicate trial identity: {ident}")
        seen.add(ident)
        by_size.setdefault(ident[1], []).append(row)

    expected_ids = {
        (block, size)
        for block in range(blocks)
        for size in sizes
    }
    if seen != expected_ids:
        raise ValueError("incomplete design matrix")

    cells: dict[str, Any] = {}
    for size in sizes:
        rows = by_size[size]
        cell: dict[str, Any] = {
            "trial_count": len(rows),
            "median_mincore_vector_bytes": _median(
                rows, ("mincore_vector_bytes",)
            ),
            "median_resident_fraction": _median(
                rows, ("resident_fraction",)
            ),
            "median_max_phase_delta_bytes": _median(
                rows,
                ("derived", "max_observed_phase_current_delta_bytes"),
            ),
            "median_post_cleanup_delta_bytes": _median(
                rows,
                ("derived", "post_cleanup_current_delta_bytes"),
            ),
            "median_post_gc_settle_delta_bytes": _median(
                rows,
                ("derived", "post_gc_settle_current_delta_bytes"),
            ),
            "median_peak_minus_baseline_bytes": _median(
                rows,
                (
                    "derived",
                    "final_memory_peak_minus_baseline_current_bytes",
                ),
            ),
            "phase_median_current_delta_bytes": {},
            "phase_median_pagetables_delta_bytes": {},
            "phase_median_kernel_delta_bytes": {},
            "phase_median_anon_delta_bytes": {},
            "phase_median_file_delta_bytes": {},
        }
        for phase in PHASES:
            cell["phase_median_current_delta_bytes"][phase] = _median(
                rows, ("deltas", phase, "memory_current_delta")
            )
            for field, key in (
                ("pagetables", "phase_median_pagetables_delta_bytes"),
                ("kernel", "phase_median_kernel_delta_bytes"),
                ("anon", "phase_median_anon_delta_bytes"),
                ("file", "phase_median_file_delta_bytes"),
            ):
                cell[key][phase] = _median(
                    rows,
                    (
                        "deltas",
                        phase,
                        "memory_stat_delta",
                        field,
                    ),
                )
        cells[str(size)] = cell

    return {
        "experiment_id": spec["experiment_id"],
        "execution_status": "PASS",
        "trial_count": len(trials),
        "cells": cells,
        "inference_boundary": (
            "Observer-only memory footprint audit; no streaming-workload "
            "performance or policy inference."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("schedule")
    s.add_argument("--spec", required=True)
    s.add_argument("--block", type=int, required=True)
    s.add_argument("--out", required=True)

    t = sub.add_parser("trial")
    t.add_argument("--spec", required=True)
    t.add_argument("--block", type=int, required=True)
    t.add_argument("--order", type=int, required=True)
    t.add_argument("--size-mib", type=int, required=True)
    t.add_argument("--file", required=True)
    t.add_argument("--source-commit", required=True)
    t.add_argument("--out", required=True)

    a = sub.add_parser("aggregate")
    a.add_argument("--spec", required=True)
    a.add_argument("--input-root", required=True)
    a.add_argument("--out", required=True)

    args = parser.parse_args()
    spec = load_spec(args.spec)

    if args.cmd == "schedule":
        write_schedule(spec, args.block, args.out)
        return

    if args.cmd == "trial":
        result = run_trial(
            spec,
            block=args.block,
            order=args.order,
            size_mib=args.size_mib,
            file_path=Path(args.file),
            source_commit=args.source_commit,
        )
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(json.dumps({
            "status": result["status"],
            "size_mib": result["size_mib"],
            "resident_fraction": result["resident_fraction"],
            "max_phase_delta_mib": (
                result["derived"]["max_observed_phase_current_delta_bytes"]
                / (1024 * 1024)
            ),
            "post_gc_delta_mib": (
                result["derived"]["post_gc_settle_current_delta_bytes"]
                / (1024 * 1024)
            ),
        }, indent=2, sort_keys=True))
        return

    result = summarize(spec, Path(args.input_root))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
