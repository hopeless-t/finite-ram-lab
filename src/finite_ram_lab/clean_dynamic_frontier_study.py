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
from .region_workload import PAGE_SIZE, _mapping, residency
from .strata001_pilot_workload import (
    _delta_stat,
    _hot_digest,
    _hot_fill,
    _hot_read,
    _retouch,
)
from .strata001_probe import _file_residency
from .strata004_knee_workload import _max_checkpoint, _scan


def load_spec(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def schedule_rows(
    spec: dict[str, Any],
    *,
    pressure: int,
    block: int,
) -> list[dict[str, Any]]:
    highs = [int(x) for x in spec["memory_high_mib"]]
    if pressure not in highs:
        raise ValueError("pressure outside frozen design")
    if block not in range(int(spec["runner_blocks_per_pressure"])):
        raise ValueError("block outside frozen design")

    arms = [str(x) for x in spec["arms"]]
    random.Random(
        int(spec["base_schedule_seed"]) + pressure * 1009 + block * 9176
    ).shuffle(arms)
    return [{"order": i, "arm": arm} for i, arm in enumerate(arms)]


def write_schedule(
    spec: dict[str, Any],
    *,
    pressure: int,
    block: int,
    out: str | Path,
) -> None:
    path = Path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["order", "arm"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(schedule_rows(spec, pressure=pressure, block=block))


def run_trial(
    spec: dict[str, Any],
    *,
    pressure: int,
    block: int,
    order: int,
    arm: str,
    file_path: Path,
    source_commit: str,
) -> dict[str, Any]:
    highs = [int(x) for x in spec["memory_high_mib"]]
    arms = [str(x) for x in spec["arms"]]
    if pressure not in highs:
        raise ValueError("pressure outside frozen design")
    if arm not in arms:
        raise ValueError("arm outside frozen design")
    if block not in range(int(spec["runner_blocks_per_pressure"])):
        raise ValueError("block outside frozen design")

    hot_mib = int(spec["hot_anon_mib"])
    cold_mib = int(spec["cold_file_mib"])
    chunk_mib = int(spec["read_chunk_mib"])
    hot_size = hot_mib * 1024 * 1024
    cold_size = cold_mib * 1024 * 1024
    buffer_size = chunk_mib * 1024 * 1024

    if file_path.stat().st_size != cold_size:
        raise ValueError("cold file size mismatch")
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

        # Important B444/B447 identity rule:
        # no external Recorder hook is executed inside the scan.
        scan = _scan(
            arm=arm,
            path=file_path,
            scratch=scratch,
            chunk=buffer_size,
            cg=cg,
            checkpoint_hook=None,
        )

        # Clean floor before mincore/residency diagnostics.
        post_scan_pre_observer = _snapshot(cg)

        file_post = _file_residency(file_path)
        hot_post = residency(hot, hot_size)
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
        peak_bytes = max(
            int(before_scan["memory_current"]),
            int(post_scan_pre_observer["memory_current"]),
            int(_max_checkpoint(scan["checkpoints"], "memory_current")),
        )
        clean_floor = int(post_scan_pre_observer["memory_current"])
        post_observer = int(post_scan_post_observer["memory_current"])
        ephemeral_excess = peak_bytes - clean_floor
        observer_delta = post_observer - clean_floor

        no_oom = (
            int(final_events.get("oom", 0)) == 0
            and int(final_events.get("oom_kill", 0)) == 0
        )

        release_required = arm.startswith("dontneed_")
        checks = {
            "memory_high_matches": int(post_retouch["memory_high"])
            == pressure * 1024 * 1024,
            "memory_max_matches": int(post_retouch["memory_max"])
            == int(spec["memory_max_mib"]) * 1024 * 1024,
            "full_span_processed": int(scan["logical_span_bytes"]) == cold_size,
            "scan_no_error": scan["error"] is None,
            "advice_success": (not release_required)
            or bool(scan["advice"]["success"]),
            "checkpoint_count": len(scan["checkpoints"])
            == cold_size // buffer_size,
            "content_integrity": digest_before == digest_after,
            "no_oom": no_oom,
            "peak_not_below_clean_floor": ephemeral_excess >= 0,
            "file_post_residency_bounded": float(file_post["resident_fraction"])
            <= float(spec["post_observer_file_fraction_max"]),
            "hot_page_count": int(hot_post["total_pages"])
            == hot_size // PAGE_SIZE,
        }

        return {
            "experiment_id": spec["experiment_id"],
            "observer_contract_version": spec["observer_contract_version"],
            "status": "PASS" if all(checks.values()) else "INVALID",
            "source_commit": source_commit,
            "pressure_mib": pressure,
            "block": block,
            "order": order,
            "arm": arm,
            "parameters": {
                "memory_high_mib": pressure,
                "memory_max_mib": int(spec["memory_max_mib"]),
                "hot_anon_mib": hot_mib,
                "cold_file_mib": cold_mib,
                "read_chunk_mib": chunk_mib,
            },
            "snapshots": {
                "baseline": baseline,
                "before_scan": before_scan,
                "post_scan_pre_observer": post_scan_pre_observer,
                "post_scan_post_observer": post_scan_post_observer,
                "post_retouch": post_retouch,
            },
            "diagnostics": {
                "file_post_residency": file_post,
                "hot_post_residency": hot_post,
            },
            "metrics": {
                "peak_ram_bytes": peak_bytes,
                "clean_floor_bytes": clean_floor,
                "ephemeral_excess_bytes": ephemeral_excess,
                "observer_current_delta_bytes": observer_delta,
                "memory_high_events": high_events,
                "pgscan": int(
                    _delta_stat(before_scan, post_scan_pre_observer, "pgscan")
                ),
                "pgsteal": int(
                    _delta_stat(before_scan, post_scan_pre_observer, "pgsteal")
                ),
                "advice_calls": int(scan["advice"]["calls"]),
                "scan_elapsed_ns": int(scan["elapsed_ns"]),
                "hot_retouch_ns": int(hot_retouch_ns),
                "hot_retouch_checksum": int(hot_checksum),
            },
            "checks": checks,
        }
    finally:
        scratch.close()
        hot.close()


def _median(rows: list[dict[str, Any]], metric: str) -> float:
    return float(
        statistics.median(float(row["metrics"][metric]) for row in rows)
    )


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

    highs = [int(x) for x in spec["memory_high_mib"]]
    arms = [str(x) for x in spec["arms"]]
    blocks = int(spec["runner_blocks_per_pressure"])

    seen: set[tuple[int, int, str]] = set()
    by_cell: dict[tuple[int, str], list[dict[str, Any]]] = {}
    for row in trials:
        ident = (
            int(row["pressure_mib"]),
            int(row["block"]),
            str(row["arm"]),
        )
        if ident in seen:
            raise ValueError(f"duplicate trial identity: {ident}")
        seen.add(ident)
        by_cell.setdefault((ident[0], ident[2]), []).append(row)

    expected_ids = {
        (high, block, arm)
        for high in highs
        for block in range(blocks)
        for arm in arms
    }
    if seen != expected_ids:
        raise ValueError("incomplete design matrix")

    metric_names = (
        "peak_ram_bytes",
        "clean_floor_bytes",
        "ephemeral_excess_bytes",
        "observer_current_delta_bytes",
        "memory_high_events",
        "pgscan",
        "pgsteal",
        "advice_calls",
        "scan_elapsed_ns",
        "hot_retouch_ns",
    )
    cells: dict[str, Any] = {}
    for high in highs:
        cells[str(high)] = {}
        for arm in arms:
            rows = by_cell[(high, arm)]
            cell = {
                f"median_{name}": _median(rows, name)
                for name in metric_names
            }
            cell["positive_high_event_trials"] = sum(
                int(row["metrics"]["memory_high_events"]) > 0
                for row in rows
            )
            cell["positive_observer_delta_trials"] = sum(
                int(row["metrics"]["observer_current_delta_bytes"]) > 0
                for row in rows
            )
            cell["negative_observer_delta_trials"] = sum(
                int(row["metrics"]["observer_current_delta_bytes"]) < 0
                for row in rows
            )
            cell["block_rows"] = [
                {
                    "block": int(row["block"]),
                    **{
                        name: row["metrics"][name]
                        for name in metric_names
                    },
                }
                for row in sorted(rows, key=lambda x: int(x["block"]))
            ]
            cells[str(high)][arm] = cell

    return {
        "experiment_id": spec["experiment_id"],
        "observer_contract_version": spec["observer_contract_version"],
        "execution_status": "PASS",
        "trial_count": len(trials),
        "cells": cells,
        "claim_ceiling": spec["qualification"]["claim_ceiling"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("schedule")
    s.add_argument("--spec", required=True)
    s.add_argument("--pressure", type=int, required=True)
    s.add_argument("--block", type=int, required=True)
    s.add_argument("--out", required=True)

    t = sub.add_parser("trial")
    t.add_argument("--spec", required=True)
    t.add_argument("--pressure", type=int, required=True)
    t.add_argument("--block", type=int, required=True)
    t.add_argument("--order", type=int, required=True)
    t.add_argument("--arm", required=True)
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
        write_schedule(
            spec,
            pressure=args.pressure,
            block=args.block,
            out=args.out,
        )
        return

    if args.cmd == "trial":
        result = run_trial(
            spec,
            pressure=args.pressure,
            block=args.block,
            order=args.order,
            arm=args.arm,
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
            "pressure_mib": result["pressure_mib"],
            "arm": result["arm"],
            "high_events": result["metrics"]["memory_high_events"],
            "peak_mib": result["metrics"]["peak_ram_bytes"] / (1024 * 1024),
            "clean_floor_mib": (
                result["metrics"]["clean_floor_bytes"] / (1024 * 1024)
            ),
            "ephemeral_excess_mib": (
                result["metrics"]["ephemeral_excess_bytes"] / (1024 * 1024)
            ),
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
