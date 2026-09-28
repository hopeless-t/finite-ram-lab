from __future__ import annotations

import argparse
import csv
import json
import mmap
import random
import statistics
from pathlib import Path
from typing import Any

from .obs_workload import _self_cgroup_path, _snapshot
from .region_workload import PAGE_SIZE, _mapping
from .strata001_pilot_workload import (
    _hot_digest,
    _hot_fill,
    _hot_read,
    _retouch,
)
from .strata001_probe import _file_residency
from .strata004_knee_workload import _max_checkpoint, _scan


def load_spec(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def schedule_rows(spec: dict[str, Any], block: int) -> list[dict[str, Any]]:
    if block not in range(int(spec["runner_blocks"])):
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

    expected_file_bytes = size_mib * 1024 * 1024
    if file_path.stat().st_size != expected_file_bytes:
        raise ValueError("file size mismatch")

    hot_mib = int(spec["hot_anon_mib"])
    chunk_mib = int(spec["read_chunk_mib"])
    hot_size = hot_mib * 1024 * 1024
    buffer_size = chunk_mib * 1024 * 1024
    arm = str(spec["release_arm"])

    if hot_size % PAGE_SIZE or buffer_size % PAGE_SIZE:
        raise ValueError("hot/buffer sizes must be page aligned")

    rel = _self_cgroup_path()
    cg = Path("/sys/fs/cgroup") / rel.lstrip("/")

    baseline = _snapshot(cg)
    hot = _mapping(hot_size)
    scratch: mmap.mmap = _mapping(buffer_size)

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
            checkpoint_hook=None,
        )

        # Clean workload-floor snapshot: no post-scan mincore has run yet.
        post_scan_pre_observer = _snapshot(cg)

        # Preserve the historical observer implementation deliberately.
        file_post = _file_residency(file_path)
        post_scan_post_observer = _snapshot(cg)

        hot_retouch_ns, hot_checksum = _retouch(hot, hot_size)
        post_retouch = _snapshot(cg)
        digest_after = _hot_digest(hot, hot_size)

        before_events = before_scan["memory_events"]
        pre_events = post_scan_pre_observer["memory_events"]
        final_events = post_retouch["memory_events"]

        high_events = int(
            pre_events.get("high", 0) - before_events.get("high", 0)
        )
        no_oom = (
            int(final_events.get("oom", 0)) == 0
            and int(final_events.get("oom_kill", 0)) == 0
        )

        pre_current = int(post_scan_pre_observer["memory_current"])
        post_current = int(post_scan_post_observer["memory_current"])
        observer_delta = post_current - pre_current

        checks = {
            "full_span_processed": int(scan["logical_span_bytes"])
            == expected_file_bytes,
            "scan_no_error": scan["error"] is None,
            "advice_success": bool(scan["advice"]["success"]),
            "file_cold_after_observer": float(file_post["resident_fraction"])
            <= float(spec["external_cold_fraction_max"]),
            "content_integrity": digest_before == digest_after,
            "no_oom": no_oom,
            "checkpoint_count": len(scan["checkpoints"])
            == expected_file_bytes // buffer_size,
        }
        status = "PASS" if all(checks.values()) else "INVALID"

        return {
            "experiment_id": spec["experiment_id"],
            "status": status,
            "source_commit": source_commit,
            "block": block,
            "order": order,
            "size_mib": size_mib,
            "arm": arm,
            "cgroup_path": rel,
            "snapshots": {
                "baseline": baseline,
                "before_scan": before_scan,
                "post_scan_pre_observer": post_scan_pre_observer,
                "post_scan_post_observer": post_scan_post_observer,
                "post_retouch": post_retouch,
            },
            "file_post_residency": file_post,
            "scan": {
                "logical_span_bytes": int(scan["logical_span_bytes"]),
                "elapsed_ns": int(scan["elapsed_ns"]),
                "advice_calls": int(scan["advice"]["calls"]),
            },
            "metrics": {
                "memory_high_events": high_events,
                "max_scan_memory_bytes": int(
                    _max_checkpoint(scan["checkpoints"], "memory_current")
                ),
                "pre_observer_current_bytes": pre_current,
                "post_observer_current_bytes": post_current,
                "observer_current_delta_bytes": observer_delta,
                "pre_observer_minus_hot_mib": (
                    pre_current - hot_size
                ) / (1024 * 1024),
                "post_observer_minus_hot_mib": (
                    post_current - hot_size
                ) / (1024 * 1024),
                "observer_anon_delta_bytes": int(
                    post_scan_post_observer["memory_stat"].get("anon", 0)
                    - post_scan_pre_observer["memory_stat"].get("anon", 0)
                ),
                "observer_file_delta_bytes": int(
                    post_scan_post_observer["memory_stat"].get("file", 0)
                    - post_scan_pre_observer["memory_stat"].get("file", 0)
                ),
                "observer_kernel_delta_bytes": int(
                    post_scan_post_observer["memory_stat"].get("kernel", 0)
                    - post_scan_pre_observer["memory_stat"].get("kernel", 0)
                ),
                "hot_retouch_ns": hot_retouch_ns,
                "hot_retouch_checksum": hot_checksum,
            },
            "checks": checks,
        }
    finally:
        scratch.close()
        hot.close()


def _median(rows: list[dict[str, Any]], key: str) -> float:
    return float(statistics.median(float(r["metrics"][key]) for r in rows))


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
    keys = (
        "memory_high_events",
        "max_scan_memory_bytes",
        "pre_observer_current_bytes",
        "post_observer_current_bytes",
        "observer_current_delta_bytes",
        "pre_observer_minus_hot_mib",
        "post_observer_minus_hot_mib",
        "observer_anon_delta_bytes",
        "observer_file_delta_bytes",
        "observer_kernel_delta_bytes",
    )
    for size in sizes:
        rows = by_size[size]
        cell = {f"median_{key}": _median(rows, key) for key in keys}
        cell["trial_count"] = len(rows)
        cell["positive_observer_delta_trials"] = sum(
            int(r["metrics"]["observer_current_delta_bytes"]) > 0
            for r in rows
        )
        cell["positive_high_event_trials"] = sum(
            int(r["metrics"]["memory_high_events"]) > 0
            for r in rows
        )
        cell["median_file_post_fraction"] = float(
            statistics.median(
                float(r["file_post_residency"]["resident_fraction"])
                for r in rows
            )
        )
        cells[str(size)] = cell

    pre_medians = [
        float(cells[str(size)]["median_pre_observer_minus_hot_mib"])
        for size in sizes
    ]
    post_medians = [
        float(cells[str(size)]["median_post_observer_minus_hot_mib"])
        for size in sizes
    ]

    return {
        "experiment_id": spec["experiment_id"],
        "execution_status": "PASS",
        "trial_count": len(trials),
        "cells": cells,
        "derived": {
            "pre_observer_floor_span_mib": max(pre_medians) - min(pre_medians),
            "post_observer_floor_span_mib": max(post_medians) - min(post_medians),
        },
        "inference_boundary": (
            "Measurement-hygiene validation only; does not choose a "
            "production memory policy."
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
            "high_events": result["metrics"]["memory_high_events"],
            "pre_floor_mib": result["metrics"]["pre_observer_minus_hot_mib"],
            "post_floor_mib": result["metrics"]["post_observer_minus_hot_mib"],
            "observer_delta_kib": (
                result["metrics"]["observer_current_delta_bytes"] / 1024
            ),
        }, indent=2, sort_keys=True))
        if result["status"] != "PASS":
            raise SystemExit(1)
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
