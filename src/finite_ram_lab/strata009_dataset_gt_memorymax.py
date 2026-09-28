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


SPEC_ID = "specs/STRATA-009-DATASET-GT-MEMORYMAX-v1.json"


def load_spec(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def schedule_rows(spec: dict[str, Any], block: int) -> list[dict[str, Any]]:
    if block not in range(int(spec["runner_blocks"])):
        raise ValueError("block outside frozen design")
    arms = list(spec["arms"])
    random.Random(
        int(spec["base_schedule_seed"]) + block * 9176
    ).shuffle(arms)
    return [{"order": i, "arm": arm} for i, arm in enumerate(arms)]


def write_schedule(spec: dict[str, Any], block: int, out: str | Path) -> None:
    path = Path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["order", "arm"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(schedule_rows(spec, block))


def _count_lines(path: Path) -> int:
    with path.open("r", encoding="utf-8") as fh:
        return sum(1 for _ in fh)


def run_trial(
    spec: dict[str, Any],
    *,
    block: int,
    order: int,
    arm: str,
    source_commit: str,
    file_path: Path,
    raw_evidence: Path,
) -> dict[str, Any]:
    if block not in range(int(spec["runner_blocks"])):
        raise ValueError("block outside frozen design")
    if arm not in spec["arms"]:
        raise ValueError("arm outside frozen design")

    high_mib = int(spec["memory_high_mib"])
    max_mib = int(spec["memory_max_mib"])
    hot_mib = int(spec["hot_anon_mib"])
    cold_mib = int(spec["cold_file_mib"])
    chunk_mib = int(spec["read_chunk_mib"])
    release_mib = int(spec["release_interval_mib"][arm])
    high_bytes = high_mib * 1024 * 1024
    max_bytes = max_mib * 1024 * 1024
    expected_records = int(spec["recorder"]["records_per_trial"])

    recorder = EvidenceRecorder(
        raw_evidence,
        f"strata009-b{block}-o{order}-{arm}",
    )
    recorder.start(
        experiment_id=spec["experiment_id"],
        spec_id=SPEC_ID,
        source_commit=source_commit,
        provenance={
            "runner": spec["runner"],
            "block": block,
            "order": order,
            "arm": arm,
        },
        config={
            "memory_high_mib": high_mib,
            "memory_max_mib": max_mib,
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
    post_bytes = int(workload["cgroup"]["post_scan"]["memory_current"])
    no_oom = bool(workload["checks"]["no_oom"])

    return {
        "experiment_id": spec["experiment_id"],
        "status": (
            "PASS"
            if workload["status"] == "PASS" and recorder_ok and no_oom
            else "INVALID"
        ),
        "runner": spec["runner"],
        "block": block,
        "order": order,
        "arm": arm,
        "source_commit": source_commit,
        "memory_high_mib": high_mib,
        "memory_max_mib": max_mib,
        "hot_anon_mib": hot_mib,
        "cold_file_mib": cold_mib,
        "metrics": {
            "memory_high_events": int(
                workload["scan_deltas"]["memory_high_events"]
            ),
            "max_scan_memory_bytes": peak_bytes,
            "post_scan_memory_bytes": post_bytes,
            "post_scan_non_hot_floor_mib": (
                post_bytes / (1024 * 1024) - hot_mib
            ),
            "file_post_fraction": float(
                workload["file"]["post_scan_residency"]["resident_fraction"]
            ),
            "logical_span_bytes": int(workload["scan"]["logical_span_bytes"]),
            "advice_calls": int(workload["scan"]["advice"]["calls"]),
            "scan_elapsed_ns": int(workload["scan"]["elapsed_ns"]),
            "pgscan": int(workload["scan_deltas"]["pgscan"]),
            "pgsteal": int(workload["scan_deltas"]["pgsteal"]),
            "oom": int(
                workload["cgroup"]["post_retouch"]["memory_events"].get(
                    "oom", 0
                )
            ),
            "oom_kill": int(
                workload["cgroup"]["post_retouch"]["memory_events"].get(
                    "oom_kill", 0
                )
            ),
        },
        "recorder": {
            "record_count": record_count,
            "expected_record_count": expected_records,
            "record_count_ok": recorder_ok,
        },
        "checks": {
            "parent_workload_pass": workload["status"] == "PASS",
            "no_oom": no_oom,
            "recorder_count_ok": recorder_ok,
        },
    }


def _median(rows: list[dict[str, Any]], key: str) -> float:
    return float(statistics.median(float(r["metrics"][key]) for r in rows))


def _onset(cells: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    releases = sorted(int(v) for v in spec["release_interval_mib"].values())
    last_zero = None
    first_positive = None
    for release in releases:
        arm = f"dontneed_{release}m"
        if cells[arm]["median_memory_high_events"] > 0:
            first_positive = release
            break
        last_zero = release

    high = int(spec["memory_high_mib"])
    hot = int(spec["hot_anon_mib"])
    if first_positive is None:
        assert last_zero is not None
        return {
            "raw_release_interval_bracket": f"> {last_zero} MiB",
            "knee_plus_hot_bracket": f"> {last_zero + hot} MiB",
            "non_hot_floor_interval": f"< {high - last_zero - hot} MiB",
        }
    if last_zero is None:
        return {
            "raw_release_interval_bracket": f"<= {first_positive} MiB",
            "knee_plus_hot_bracket": f"<= {first_positive + hot} MiB",
            "non_hot_floor_interval": (
                f">= {high - first_positive - hot} MiB"
            ),
        }
    return {
        "raw_release_interval_bracket": (
            f"{last_zero} MiB < onset <= {first_positive} MiB"
        ),
        "knee_plus_hot_bracket": (
            f"{last_zero + hot} MiB < K+hot <= "
            f"{first_positive + hot} MiB"
        ),
        "non_hot_floor_interval": (
            f"[{high - first_positive - hot}, "
            f"{high - last_zero - hot}) MiB"
        ),
    }


def summarize(spec: dict[str, Any], root: Path) -> dict[str, Any]:
    trials = [
        json.loads(p.read_text(encoding="utf-8"))
        for p in sorted(root.rglob("trial-*.json"))
    ]
    expected = int(spec["expected_trials"])
    if len(trials) != expected:
        raise ValueError(f"expected {expected} trials, got {len(trials)}")
    if any(r.get("status") != "PASS" for r in trials):
        raise ValueError("all trials must PASS")

    arms = list(spec["arms"])
    blocks = int(spec["runner_blocks"])
    seen: set[tuple[int, str]] = set()
    by_arm: dict[str, list[dict[str, Any]]] = {}

    for r in trials:
        ident = (int(r["block"]), str(r["arm"]))
        if ident in seen:
            raise ValueError(f"duplicate trial identity: {ident}")
        seen.add(ident)
        by_arm.setdefault(ident[1], []).append(r)

    expected_ids = {
        (block, arm)
        for block in range(blocks)
        for arm in arms
    }
    if seen != expected_ids:
        raise ValueError("incomplete design matrix")

    cells: dict[str, Any] = {}
    metric_names = [
        "memory_high_events",
        "max_scan_memory_bytes",
        "post_scan_memory_bytes",
        "post_scan_non_hot_floor_mib",
        "file_post_fraction",
        "logical_span_bytes",
        "advice_calls",
        "scan_elapsed_ns",
        "pgscan",
        "pgsteal",
        "oom",
        "oom_kill",
    ]
    for arm in arms:
        rows = by_arm[arm]
        cell = {
            f"median_{name}": _median(rows, name)
            for name in metric_names
        }
        cell["positive_high_event_trials"] = sum(
            int(r["metrics"]["memory_high_events"]) > 0 for r in rows
        )
        cell["valid_trials"] = len(rows)
        cell["release_interval_mib"] = int(
            spec["release_interval_mib"][arm]
        )
        cells[arm] = cell

    return {
        "experiment_id": spec["experiment_id"],
        "execution_status": "PASS",
        "trial_count": len(trials),
        "cold_file_mib": int(spec["cold_file_mib"]),
        "memory_max_mib": int(spec["memory_max_mib"]),
        "dataset_exceeds_memory_max": (
            int(spec["cold_file_mib"]) > int(spec["memory_max_mib"])
        ),
        "cells": cells,
        "onset_screen": _onset(cells, spec),
        "anchor": spec["anchor"],
        "inference_boundary": (
            "Bounded-policy dataset-over-MemoryMax screen only; "
            "buffered/unbounded arm intentionally not tested."
        ),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("schedule")
    s.add_argument("--spec", required=True)
    s.add_argument("--block", type=int, required=True)
    s.add_argument("--out", required=True)

    t = sub.add_parser("trial")
    t.add_argument("--spec", required=True)
    t.add_argument("--block", type=int, required=True)
    t.add_argument("--order", type=int, required=True)
    t.add_argument("--arm", required=True)
    t.add_argument("--source-commit", required=True)
    t.add_argument("--file", required=True)
    t.add_argument("--raw-evidence", required=True)
    t.add_argument("--out", required=True)

    a = sub.add_parser("aggregate")
    a.add_argument("--spec", required=True)
    a.add_argument("--input-root", required=True)
    a.add_argument("--out", required=True)

    args = p.parse_args()
    spec = load_spec(args.spec)

    if args.cmd == "schedule":
        write_schedule(spec, args.block, args.out)
        return

    if args.cmd == "trial":
        result = run_trial(
            spec,
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
        print(json.dumps(result, indent=2, sort_keys=True))
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
