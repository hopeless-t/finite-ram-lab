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


def load_spec(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def schedule_rows(spec: dict[str, Any], pressure: int, block: int) -> list[dict[str, Any]]:
    highs = [int(x) for x in spec["memory_high_mib"]]
    blocks = int(spec["runner_blocks_per_pressure"])
    if pressure not in highs:
        raise ValueError("pressure outside frozen design")
    if block not in range(blocks):
        raise ValueError("block outside frozen design")
    arms = list(spec["arms"])
    random.Random(
        int(spec["base_schedule_seed"]) + pressure * 1009 + block * 9176
    ).shuffle(arms)
    return [{"order": i, "arm": arm} for i, arm in enumerate(arms)]


def write_schedule(
    spec: dict[str, Any],
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
        writer.writerows(schedule_rows(spec, pressure, block))


def _count_lines(path: Path) -> int:
    with path.open("r", encoding="utf-8") as fh:
        return sum(1 for _ in fh)


def run_trial(
    spec: dict[str, Any],
    *,
    pressure: int,
    block: int,
    order: int,
    arm: str,
    source_commit: str,
    file_path: Path,
    raw_evidence: Path,
) -> dict[str, Any]:
    if pressure not in [int(x) for x in spec["memory_high_mib"]]:
        raise ValueError("pressure outside frozen design")
    if arm not in spec["arms"]:
        raise ValueError("arm outside frozen design")

    high_bytes = pressure * 1024 * 1024
    max_bytes = int(spec["memory_max_mib"]) * 1024 * 1024
    hot_mib = int(spec["hot_anon_mib"])
    cold_mib = int(spec["cold_file_mib"])
    chunk_mib = int(spec["read_chunk_mib"])
    release_mib = spec["release_interval_mib"][arm]
    expected_records = int(spec["recorder"]["records_per_trial"])

    recorder = EvidenceRecorder(
        raw_evidence,
        f"strata005-h{pressure}-b{block}-o{order}-{arm}",
    )
    recorder.start(
        experiment_id=spec["experiment_id"],
        spec_id="specs/STRATA-005-EXTERNAL-VALIDITY-v1.json",
        source_commit=source_commit,
        provenance={
            "memory_high_mib": pressure,
            "block": block,
            "order": order,
            "arm": arm,
        },
        config={
            "memory_high_bytes": high_bytes,
            "memory_max_bytes": max_bytes,
            "hot_anon_mib": hot_mib,
            "cold_file_mib": cold_mib,
            "read_chunk_mib": chunk_mib,
            "release_interval_mib": release_mib,
        },
    )

    def checkpoint_hook(checkpoint: dict[str, Any]) -> None:
        recorder.sample(
            "memory.current",
            int(checkpoint["post_advice"]["memory_current"]),
            "bytes",
            phase="scan",
        )

    try:
        workload = strata_run(
            arm=arm,
            file_path=file_path,
            hot_anon_mib=hot_mib,
            buffer_mib=chunk_mib,
            expected_file_mib=cold_mib,
            expected_high=high_bytes,
            expected_max=max_bytes,
            precache_limit=float(
                spec["file_prepare"]["require_precache_fraction_le"]
            ),
            checkpoint_hook=checkpoint_hook,
        )
        recorder.end(workload["status"])
    finally:
        recorder.close()

    record_count = _count_lines(raw_evidence)
    recorder_ok = record_count == expected_records
    peak_bytes = int(workload["scan_deltas"]["max_memory_current"])

    return {
        "experiment_id": spec["experiment_id"],
        "status": "PASS"
        if workload["status"] == "PASS" and recorder_ok
        else "INVALID",
        "memory_high_mib": pressure,
        "block": block,
        "order": order,
        "arm": arm,
        "source_commit": source_commit,
        "parameters": {
            "expected_high_bytes": high_bytes,
            "expected_max_bytes": max_bytes,
            "hot_anon_mib": hot_mib,
            "cold_file_mib": cold_mib,
            "read_chunk_mib": chunk_mib,
            "release_interval_mib": release_mib,
        },
        "normalized": {
            "release_fraction_of_high": (
                None if release_mib is None else float(release_mib) / pressure
            ),
            "peak_fraction_of_high": peak_bytes / high_bytes,
            "headroom_over_hot_mib": pressure - hot_mib,
        },
        "recorder": {
            "record_count": record_count,
            "expected_record_count": expected_records,
            "record_count_ok": recorder_ok,
            "jsonl_bytes": raw_evidence.stat().st_size,
        },
        "metrics": {
            "memory_high_events": int(workload["scan_deltas"]["memory_high_events"]),
            "max_scan_memory_bytes": peak_bytes,
            "post_scan_memory_bytes": int(
                workload["cgroup"]["post_scan"]["memory_current"]
            ),
            "file_post_fraction": float(
                workload["file"]["post_scan_residency"]["resident_fraction"]
            ),
            "scan_elapsed_ns": int(workload["scan"]["elapsed_ns"]),
            "advice_calls": int(workload["scan"]["advice"]["calls"]),
            "pgscan": int(workload["scan_deltas"]["pgscan"]),
            "pgsteal": int(workload["scan_deltas"]["pgsteal"]),
            "hot_retouch_ns": int(workload["hot"]["retouch_ns"]),
        },
        "checks": {
            "parent_workload_pass": workload["status"] == "PASS",
            "recorder_record_count": recorder_ok,
        },
    }


def _median(rows: list[dict[str, Any]], path: tuple[str, ...]) -> float:
    values: list[float] = []
    for row in rows:
        value: Any = row
        for key in path:
            value = value[key]
        values.append(float(value))
    return float(statistics.median(values))


def _onset(cells: dict[str, Any], pressure: int) -> dict[str, Any]:
    release_panel = (48, 64, 80, 96)
    last_zero: int | None = None
    first_positive: int | None = None
    for release in release_panel:
        arm = f"dontneed_{release}m"
        if cells[str(pressure)][arm]["median_memory_high_events"] > 0:
            first_positive = release
            break
        last_zero = release

    if first_positive is None:
        raw = "> 96 MiB"
        normalized = f"> {96 / pressure:.6f}"
    elif last_zero is None:
        raw = f"<= {first_positive} MiB"
        normalized = f"<= {first_positive / pressure:.6f}"
    else:
        raw = f"{last_zero} MiB < onset <= {first_positive} MiB"
        normalized = (
            f"{last_zero / pressure:.6f} < onset <= "
            f"{first_positive / pressure:.6f}"
        )

    return {
        "memory_high_mib": pressure,
        "last_zero_median_release_mib": last_zero,
        "first_positive_median_release_mib": first_positive,
        "raw_release_interval_bracket": raw,
        "normalized_release_fraction_bracket": normalized,
    }


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
    arms = list(spec["arms"])
    blocks = int(spec["runner_blocks_per_pressure"])
    seen: set[tuple[int, int, str]] = set()
    by_cell: dict[tuple[int, str], list[dict[str, Any]]] = {}

    for row in trials:
        identity = (
            int(row["memory_high_mib"]),
            int(row["block"]),
            str(row["arm"]),
        )
        if identity in seen:
            raise ValueError(f"duplicate trial identity: {identity}")
        seen.add(identity)
        by_cell.setdefault((identity[0], identity[2]), []).append(row)

    expected_ids = {
        (high, block, arm)
        for high in highs
        for block in range(blocks)
        for arm in arms
    }
    if seen != expected_ids:
        raise ValueError("incomplete design matrix")

    metric_paths = {
        "memory_high_events": ("metrics", "memory_high_events"),
        "max_scan_memory_bytes": ("metrics", "max_scan_memory_bytes"),
        "post_scan_memory_bytes": ("metrics", "post_scan_memory_bytes"),
        "file_post_fraction": ("metrics", "file_post_fraction"),
        "scan_elapsed_ns": ("metrics", "scan_elapsed_ns"),
        "pgscan": ("metrics", "pgscan"),
        "pgsteal": ("metrics", "pgsteal"),
        "peak_fraction_of_high": ("normalized", "peak_fraction_of_high"),
        "jsonl_bytes": ("recorder", "jsonl_bytes"),
    }

    cells: dict[str, Any] = {}
    for high in highs:
        cells[str(high)] = {}
        for arm in arms:
            rows = by_cell[(high, arm)]
            if len(rows) != blocks:
                raise ValueError(f"incomplete cell {high}/{arm}")
            cell = {
                f"median_{name}": _median(rows, path)
                for name, path in metric_paths.items()
            }
            cell["positive_high_event_trials"] = sum(
                int(row["metrics"]["memory_high_events"]) > 0 for row in rows
            )
            cell["release_interval_mib"] = spec["release_interval_mib"][arm]
            cell["release_fraction_of_high"] = rows[0]["normalized"][
                "release_fraction_of_high"
            ]
            cell["headroom_over_hot_mib"] = rows[0]["normalized"][
                "headroom_over_hot_mib"
            ]
            cells[str(high)][arm] = cell

    return {
        "experiment_id": spec["experiment_id"],
        "execution_status": "PASS",
        "trial_count": len(trials),
        "cells": cells,
        "onset_screen": [_onset(cells, high) for high in highs],
        "inference_boundary": (
            "Cross-pressure directional screen only; no controller formula "
            "or OSS default authorized."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    schedule = sub.add_parser("schedule")
    schedule.add_argument("--spec", required=True)
    schedule.add_argument("--pressure", type=int, required=True)
    schedule.add_argument("--block", type=int, required=True)
    schedule.add_argument("--out", required=True)

    trial = sub.add_parser("trial")
    trial.add_argument("--spec", required=True)
    trial.add_argument("--pressure", type=int, required=True)
    trial.add_argument("--block", type=int, required=True)
    trial.add_argument("--order", type=int, required=True)
    trial.add_argument("--arm", required=True)
    trial.add_argument("--source-commit", required=True)
    trial.add_argument("--file", required=True)
    trial.add_argument("--raw-evidence", required=True)
    trial.add_argument("--out", required=True)

    aggregate = sub.add_parser("aggregate")
    aggregate.add_argument("--spec", required=True)
    aggregate.add_argument("--input-root", required=True)
    aggregate.add_argument("--out", required=True)

    args = parser.parse_args()
    spec = load_spec(args.spec)

    if args.cmd == "schedule":
        write_schedule(spec, args.pressure, args.block, args.out)
        return

    if args.cmd == "trial":
        result = run_trial(
            spec,
            pressure=args.pressure,
            block=args.block,
            order=args.order,
            arm=args.arm,
            source_commit=args.source_commit,
            file_path=Path(args.file),
            raw_evidence=Path(args.raw_evidence),
        )
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(
            json.dumps(
                {
                    "status": result["status"],
                    "memory_high_mib": result["memory_high_mib"],
                    "block": result["block"],
                    "arm": result["arm"],
                    "high_events": result["metrics"]["memory_high_events"],
                    "max_scan_memory_mib": (
                        result["metrics"]["max_scan_memory_bytes"] / (1024 * 1024)
                    ),
                    "peak_fraction_of_high": result["normalized"][
                        "peak_fraction_of_high"
                    ],
                    "scan_ms": result["metrics"]["scan_elapsed_ns"] / 1e6,
                    "recorder_records": result["recorder"]["record_count"],
                },
                indent=2,
                sort_keys=True,
            )
        )
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
