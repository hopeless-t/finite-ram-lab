from __future__ import annotations

import argparse
import csv
import json
import random
import statistics
from pathlib import Path
from typing import Any

from .recorder import EvidenceRecorder
from .strata004_knee_workload import run as strata_run

ARMS = ("recorder_off", "recorder_on")
BASE_SEED = 2026092806
EXPECTED_CHECKPOINTS = 24
EXPECTED_ON_RECORDS = EXPECTED_CHECKPOINTS + 2


def schedule_rows(block: int) -> list[dict[str, Any]]:
    arms = list(ARMS)
    random.Random(BASE_SEED + block).shuffle(arms)
    return [{"order": i, "mode": mode} for i, mode in enumerate(arms)]


def write_schedule(path: str | Path, block: int) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["order", "mode"])
        writer.writeheader()
        writer.writerows(schedule_rows(block))


def _count_lines(path: Path) -> int:
    with path.open("r", encoding="utf-8") as fh:
        return sum(1 for _ in fh)


def run_trial(
    *,
    mode: str,
    block: int,
    order: int,
    source_commit: str,
    file_path: Path,
    raw_evidence: Path,
    expected_high: int,
    expected_max: int,
) -> dict[str, Any]:
    if mode not in ARMS:
        raise ValueError(f"unknown mode: {mode}")

    recorder: EvidenceRecorder | None = None
    checkpoint_hook = None

    if mode == "recorder_on":
        recorder = EvidenceRecorder(
            raw_evidence,
            f"rec002-{block}-{order}-{mode}",
        )
        recorder.start(
            experiment_id="REC-002-OVERHEAD-v1",
            spec_id="docs/REC-002-OVERHEAD-v1.md",
            source_commit=source_commit,
            provenance={"block": block, "order": order},
            config={
                "mode": mode,
                "memory_high_bytes": expected_high,
                "memory_max_bytes": expected_max,
                "hot_anon_mib": 64,
                "cold_file_mib": 96,
                "read_chunk_mib": 4,
                "release_interval_mib": 80,
            },
        )

        def _record_checkpoint(checkpoint: dict[str, Any]) -> None:
            assert recorder is not None
            recorder.sample(
                "memory.current",
                int(checkpoint["post_advice"]["memory_current"]),
                "bytes",
                phase="scan",
            )

        checkpoint_hook = _record_checkpoint

    try:
        workload = strata_run(
            arm="dontneed_80m",
            file_path=file_path,
            hot_anon_mib=64,
            buffer_mib=4,
            expected_file_mib=96,
            expected_high=expected_high,
            expected_max=expected_max,
            precache_limit=0.10,
            checkpoint_hook=checkpoint_hook,
        )
        if recorder is not None:
            recorder.end(workload["status"])
    finally:
        if recorder is not None:
            recorder.close()

    if mode == "recorder_on":
        record_count = _count_lines(raw_evidence)
        jsonl_bytes = raw_evidence.stat().st_size
        recorder_ok = record_count == EXPECTED_ON_RECORDS
    else:
        record_count = 0
        jsonl_bytes = 0
        recorder_ok = not raw_evidence.exists()

    scan = workload["scan"]
    result = {
        "experiment_id": "REC-002-OVERHEAD-v1",
        "status": "PASS" if workload["status"] == "PASS" and recorder_ok else "INVALID",
        "block": block,
        "order": order,
        "mode": mode,
        "source_commit": source_commit,
        "recorder": {
            "enabled": mode == "recorder_on",
            "jsonl_bytes": jsonl_bytes,
            "record_count": record_count,
            "expected_record_count": EXPECTED_ON_RECORDS if mode == "recorder_on" else 0,
            "record_count_ok": recorder_ok,
        },
        "metrics": {
            "memory_high_events": int(workload["scan_deltas"]["memory_high_events"]),
            "max_scan_memory_bytes": int(workload["scan_deltas"]["max_memory_current"]),
            "post_scan_memory_bytes": int(workload["cgroup"]["post_scan"]["memory_current"]),
            "scan_elapsed_ns": int(scan["elapsed_ns"]),
            "file_post_fraction": float(
                workload["file"]["post_scan_residency"]["resident_fraction"]
            ),
            "advice_calls": int(scan["advice"]["calls"]),
            "pgscan": int(workload["scan_deltas"]["pgscan"]),
            "pgsteal": int(workload["scan_deltas"]["pgsteal"]),
            "hot_retouch_ns": int(workload["hot"]["retouch_ns"]),
        },
        "checks": {
            "parent_workload_pass": workload["status"] == "PASS",
            "recorder_record_count": recorder_ok,
        },
    }
    return result


def _median(trials: list[dict[str, Any]], path: tuple[str, ...]) -> float:
    values: list[float] = []
    for trial in trials:
        value: Any = trial
        for key in path:
            value = value[key]
        values.append(float(value))
    return float(statistics.median(values))


def summarize_trials(trials: list[dict[str, Any]]) -> dict[str, Any]:
    expected = 8 * len(ARMS)
    if len(trials) != expected:
        raise ValueError(f"expected {expected} trials, got {len(trials)}")
    if any(t.get("status") != "PASS" for t in trials):
        raise ValueError("all REC-002 trials must PASS before aggregation")

    by_block: dict[int, dict[str, dict[str, Any]]] = {}
    for trial in trials:
        block = int(trial["block"])
        mode = str(trial["mode"])
        if mode not in ARMS:
            raise ValueError(f"unexpected mode: {mode}")
        if mode in by_block.setdefault(block, {}):
            raise ValueError(f"duplicate block/mode: {block}/{mode}")
        by_block[block][mode] = trial

    if set(by_block) != set(range(8)):
        raise ValueError("expected blocks 0..7")
    if any(set(modes) != set(ARMS) for modes in by_block.values()):
        raise ValueError("each block must contain both recorder arms")

    metric_paths = {
        "memory_high_events": ("metrics", "memory_high_events"),
        "max_scan_memory_bytes": ("metrics", "max_scan_memory_bytes"),
        "post_scan_memory_bytes": ("metrics", "post_scan_memory_bytes"),
        "scan_elapsed_ns": ("metrics", "scan_elapsed_ns"),
        "file_post_fraction": ("metrics", "file_post_fraction"),
        "hot_retouch_ns": ("metrics", "hot_retouch_ns"),
        "jsonl_bytes": ("recorder", "jsonl_bytes"),
    }

    cells: dict[str, Any] = {}
    for mode in ARMS:
        subset = [by_block[b][mode] for b in sorted(by_block)]
        cells[mode] = {
            f"median_{name}": _median(subset, path)
            for name, path in metric_paths.items()
        }

    paired: list[dict[str, Any]] = []
    for block in sorted(by_block):
        off = by_block[block]["recorder_off"]
        on = by_block[block]["recorder_on"]
        paired.append({
            "block": block,
            "delta_memory_high_events": (
                int(on["metrics"]["memory_high_events"])
                - int(off["metrics"]["memory_high_events"])
            ),
            "delta_max_scan_memory_bytes": (
                int(on["metrics"]["max_scan_memory_bytes"])
                - int(off["metrics"]["max_scan_memory_bytes"])
            ),
            "delta_scan_elapsed_ns": (
                int(on["metrics"]["scan_elapsed_ns"])
                - int(off["metrics"]["scan_elapsed_ns"])
            ),
            "scan_elapsed_ratio_on_over_off": (
                float(on["metrics"]["scan_elapsed_ns"])
                / float(off["metrics"]["scan_elapsed_ns"])
            ),
        })

    return {
        "experiment_id": "REC-002-OVERHEAD-v1",
        "status": "PASS",
        "trial_count": len(trials),
        "block_count": len(by_block),
        "cells": cells,
        "paired": paired,
        "paired_medians": {
            key: float(statistics.median(float(row[key]) for row in paired))
            for key in (
                "delta_memory_high_events",
                "delta_max_scan_memory_bytes",
                "delta_scan_elapsed_ns",
                "scan_elapsed_ratio_on_over_off",
            )
        },
        "interpretation_boundary": (
            "Observer-effect screen for this hosted workload only; "
            "no universal recorder-transparency claim."
        ),
    }


def aggregate(input_root: Path, out: Path) -> dict[str, Any]:
    trials = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(input_root.rglob("trial-*.json"))
    ]
    summary = summarize_trials(trials)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("schedule")
    s.add_argument("--block", type=int, required=True)
    s.add_argument("--out", required=True)

    t = sub.add_parser("trial")
    t.add_argument("--mode", choices=ARMS, required=True)
    t.add_argument("--block", type=int, required=True)
    t.add_argument("--order", type=int, required=True)
    t.add_argument("--source-commit", required=True)
    t.add_argument("--file", required=True)
    t.add_argument("--raw-evidence", required=True)
    t.add_argument("--expected-high-bytes", type=int, required=True)
    t.add_argument("--expected-max-bytes", type=int, required=True)
    t.add_argument("--out", required=True)

    a = sub.add_parser("aggregate")
    a.add_argument("--input-root", required=True)
    a.add_argument("--out", required=True)

    args = p.parse_args()
    if args.command == "schedule":
        write_schedule(args.out, args.block)
        return
    if args.command == "trial":
        result = run_trial(
            mode=args.mode,
            block=args.block,
            order=args.order,
            source_commit=args.source_commit,
            file_path=Path(args.file),
            raw_evidence=Path(args.raw_evidence),
            expected_high=args.expected_high_bytes,
            expected_max=args.expected_max_bytes,
        )
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({
            "status": result["status"],
            "block": result["block"],
            "mode": result["mode"],
            "high_events": result["metrics"]["memory_high_events"],
            "max_scan_memory_mib": result["metrics"]["max_scan_memory_bytes"] / (1024 * 1024),
            "scan_ms": result["metrics"]["scan_elapsed_ns"] / 1e6,
            "jsonl_bytes": result["recorder"]["jsonl_bytes"],
        }, indent=2, sort_keys=True))
        if result["status"] != "PASS":
            raise SystemExit(1)
        return

    summary = aggregate(Path(args.input_root), Path(args.out))
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
