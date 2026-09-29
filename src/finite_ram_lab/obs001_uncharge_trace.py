from __future__ import annotations

import argparse
import json
import os
import re
import time
from collections import Counter
from pathlib import Path
from typing import Any

from .memcg005gc_controlled_spawn import (
    OFF_DONE,
    OFF_ERROR,
    OFF_GO,
    OFF_MODE,
    OFF_OBS_CPU,
    OFF_PAGE_INDEX,
    OFF_TARGET,
    OFF_TOUCHED,
    _current,
    _proc_cpu,
    _run,
    _set_u32,
    _start,
    _stop,
    _u32,
    _vmpte_kib,
    _wait,
    _wait_cpu,
    environment_receipt,
    geometry_receipt,
)

MARKER_RE = re.compile(
    r"FRL_OBS001 trial=(?P<trial>\d+:\d+) touch=(?P<touch>\d+) (?P<edge>PRE|POST)"
)


def _status_fields(pid: int) -> dict[str, int | None]:
    wanted = {
        "VmRSS": "vmrss_kib",
        "RssAnon": "rssanon_kib",
        "RssFile": "rssfile_kib",
        "RssShmem": "rssshmem_kib",
        "VmPTE": "vmpte_kib",
    }
    out: dict[str, int | None] = {v: None for v in wanted.values()}
    for line in Path(f"/proc/{pid}/status").read_text(
        encoding="utf-8"
    ).splitlines():
        key = line.split(":", 1)[0]
        if key in wanted:
            parts = line.split()
            if len(parts) >= 2:
                out[wanted[key]] = int(parts[1])
    return out


def _marker(path: Path | None, text: str) -> None:
    if path is None:
        return
    with path.open("w", encoding="utf-8") as fh:
        fh.write(text + "\n")


def _measured_touch(
    unit: dict[str, Any],
    stock_cpu: int,
    page_size: int,
    page_index: int,
    touch_number: int,
    trial_id: str,
    trace_marker: Path | None,
    worker_uid: int | None,
) -> dict[str, Any]:
    _set_u32(unit["mm"], OFF_MODE, 2)
    _set_u32(unit["mm"], OFF_TARGET, stock_cpu)
    _set_u32(unit["mm"], OFF_PAGE_INDEX, page_index)
    _set_u32(unit["mm"], OFF_DONE, 0)
    _set_u32(unit["mm"], OFF_ERROR, 0)

    _marker(
        trace_marker,
        f"FRL_OBS001 trial={trial_id} touch={touch_number} PRE",
    )
    monotonic_pre_ns = time.monotonic_ns()
    status_pre = _status_fields(unit["pid"])
    current_pre = _current(unit["cg"])

    _set_u32(unit["mm"], OFF_GO, 1)
    _wait(lambda: _u32(unit["mm"], OFF_DONE) == 1)

    current_post = _current(unit["cg"])
    status_post = _status_fields(unit["pid"])
    monotonic_post_ns = time.monotonic_ns()
    _marker(
        trace_marker,
        f"FRL_OBS001 trial={trial_id} touch={touch_number} POST",
    )

    row = {
        "touch_number": touch_number,
        "page_index": page_index,
        "monotonic_pre_ns": monotonic_pre_ns,
        "monotonic_post_ns": monotonic_post_ns,
        "duration_us": (monotonic_post_ns - monotonic_pre_ns) / 1000.0,
        "current_pre_bytes": current_pre,
        "current_post_bytes": current_post,
        "delta_pages": (current_post - current_pre) / page_size,
        "observed_cpu": _u32(unit["mm"], OFF_OBS_CPU),
        "worker_error": _u32(unit["mm"], OFF_ERROR),
        "worker_touched": _u32(unit["mm"], OFF_TOUCHED),
    }
    for key, value in status_pre.items():
        row[f"{key}_pre"] = value
    for key, value in status_post.items():
        row[f"{key}_post"] = value
    return row


def run_trial(
    *,
    worker: Path,
    root: Path,
    block: int,
    identity: int,
    prep_cpu: int,
    stock_cpu: int,
    max_pages: int,
    safe_len: int,
    touches_per_trial: int,
    trace_marker: Path | None,
) -> dict[str, Any]:
    name = (
        f"fr-obs001-{os.getenv('GITHUB_RUN_ID', 'local')}"
        f"-{block}-{identity}"
    )
    unit = _start(
        worker,
        root,
        name,
        prep_cpu,
        max_pages,
        safe_len,
        worker_uid=worker_uid,
    )
    trial_id = f"{block}:{identity}"
    try:
        geometry = geometry_receipt(unit, prep_cpu)
        page_size = int(geometry["page_size"])
        vmpte_after_guard = _vmpte_kib(unit["pid"])
        pre_migration_current = _current(unit["cg"])

        os.sched_setaffinity(unit["pid"], {stock_cpu})
        _wait_cpu(unit["pid"], stock_cpu)
        post_migration_current = _current(unit["cg"])

        sequence = list(
            range(
                int(geometry["safe_start"]) + 1,
                int(geometry["safe_start"]) + int(geometry["safe_len"]),
            )
        )
        if touches_per_trial > len(sequence):
            raise ValueError("touches_per_trial exceeds safe span")

        touches: list[dict[str, Any]] = []
        for touch_number, page_index in enumerate(
            sequence[:touches_per_trial],
            start=1,
        ):
            touches.append(
                _measured_touch(
                    unit,
                    stock_cpu,
                    page_size,
                    page_index,
                    touch_number,
                    trial_id,
                    trace_marker,
                )
            )

        return {
            "experiment_id": "OBS-001-17-PAGE-UNCHARGETRACE-v1",
            "block": block,
            "identity": identity,
            "prep_cpu": prep_cpu,
            "stock_cpu": stock_cpu,
            "geometry": geometry,
            "vmpte_after_guard_kib": vmpte_after_guard,
            "pre_migration_current_pages": pre_migration_current / page_size,
            "post_migration_current_pages": post_migration_current / page_size,
            "migration_delta_pages": (
                post_migration_current - pre_migration_current
            )
            / page_size,
            "touches": touches,
        }
    finally:
        _stop(unit)


def parse_trace_windows(text: str) -> dict[tuple[str, int], dict[str, Any]]:
    windows: dict[tuple[str, int], dict[str, Any]] = {}
    active: tuple[str, int] | None = None

    for line in text.splitlines():
        marker = MARKER_RE.search(line)
        if marker:
            key = (
                marker.group("trial"),
                int(marker.group("touch")),
            )
            edge = marker.group("edge")
            if edge == "PRE":
                active = key
                windows.setdefault(
                    key,
                    {
                        "drain_stock_events": 0,
                        "page_counter_uncharge_17_events": 0,
                        "refill_stock_events": 0,
                        "raw_event_lines": [],
                    },
                )
            elif edge == "POST":
                active = None
            continue

        if active is None:
            continue

        item = windows[active]
        if "frl_drain_stock:" in line:
            item["drain_stock_events"] += 1
            item["raw_event_lines"].append(line.strip())
        elif "frl_page_counter_uncharge:" in line:
            if "nr_pages=17" in line:
                item["page_counter_uncharge_17_events"] += 1
            item["raw_event_lines"].append(line.strip())
        elif "frl_refill_stock:" in line:
            item["refill_stock_events"] += 1
            item["raw_event_lines"].append(line.strip())

    return windows


def classify_touch(
    touch: dict[str, Any],
    trace: dict[str, Any] | None,
) -> str | None:
    if float(touch["delta_pages"]) != -17.0:
        return None
    if trace is None:
        return "TRACE_MISSING"
    pc17 = int(trace["page_counter_uncharge_17_events"])
    drain = int(trace["drain_stock_events"])
    if pc17 >= 1 and drain >= 1:
        return "STOCK_DRAIN"
    if pc17 >= 1:
        return "OTHER_UNCHARGE"
    return "UNCORRELATED"


def aggregate(
    input_root: Path,
    trace_text: str,
) -> dict[str, Any]:
    windows = parse_trace_windows(trace_text)
    trials = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(input_root.rglob("trial-*.json"))
    ]

    classifications: list[dict[str, Any]] = []
    start_hist: Counter[str] = Counter()

    for trial in trials:
        trial_id = f"{trial['block']}:{trial['identity']}"
        start_hist[str(trial["post_migration_current_pages"])] += 1
        for touch in trial["touches"]:
            key = (trial_id, int(touch["touch_number"]))
            trace = windows.get(key)
            classification = classify_touch(touch, trace)
            if classification is not None:
                classifications.append(
                    {
                        "trial": trial_id,
                        "block": trial["block"],
                        "identity": trial["identity"],
                        "start_pages": trial["post_migration_current_pages"],
                        "touch_number": touch["touch_number"],
                        "delta_pages": touch["delta_pages"],
                        "rss_delta_kib": (
                            None
                            if touch["vmrss_kib_pre"] is None
                            or touch["vmrss_kib_post"] is None
                            else touch["vmrss_kib_post"]
                            - touch["vmrss_kib_pre"]
                        ),
                        "vmpte_delta_kib": (
                            None
                            if touch["vmpte_kib_pre"] is None
                            or touch["vmpte_kib_post"] is None
                            else touch["vmpte_kib_post"]
                            - touch["vmpte_kib_pre"]
                        ),
                        "trace": trace,
                        "classification": classification,
                    }
                )

    return {
        "experiment_id": "OBS-001-17-PAGE-UNCHARGETRACE-v1",
        "trial_count": len(trials),
        "start_state_histogram": dict(sorted(start_hist.items())),
        "negative_17_count": len(classifications),
        "classification_counts": dict(
            Counter(row["classification"] for row in classifications)
        ),
        "negative_17_specimens": classifications,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run-block")
    run.add_argument("--block", type=int, required=True)
    run.add_argument("--worker", required=True)
    run.add_argument("--out-root", required=True)
    run.add_argument("--identities", type=int, default=12)
    run.add_argument("--touches", type=int, default=24)
    run.add_argument("--max-pages", type=int, default=1024)
    run.add_argument("--safe-len", type=int, default=192)
    run.add_argument("--trace-marker")
    run.add_argument("--worker-uid", type=int)

    agg = sub.add_parser("aggregate")
    agg.add_argument("--input-root", required=True)
    agg.add_argument("--trace-log", required=True)
    agg.add_argument("--json-out", required=True)

    args = parser.parse_args()

    if args.cmd == "run-block":
        cpus = sorted(os.sched_getaffinity(0))
        if len(cpus) < 3:
            raise RuntimeError("OBS-001 requires at least 3 CPUs")
        controller_cpu, prep_cpu, stock_cpu = cpus[0], cpus[1], cpus[-1]
        os.sched_setaffinity(0, {controller_cpu})

        root = Path(args.out_root)
        root.mkdir(parents=True, exist_ok=True)
        worker = Path(args.worker).resolve()
        marker = Path(args.trace_marker) if args.trace_marker else None

        (root / "environment.json").write_text(
            json.dumps(
                environment_receipt(worker, cpus),
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

        for identity in range(args.identities):
            trial_root = root / f"id-{identity}"
            trial_root.mkdir(parents=True, exist_ok=True)
            row = run_trial(
                worker=worker,
                root=trial_root,
                block=args.block,
                identity=identity,
                prep_cpu=prep_cpu,
                stock_cpu=stock_cpu,
                max_pages=args.max_pages,
                safe_len=args.safe_len,
                touches_per_trial=args.touches,
                trace_marker=marker,
                worker_uid=args.worker_uid,
            )
            (
                root / f"trial-{args.block}-{identity}.json"
            ).write_text(
                json.dumps(row, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        return

    result = aggregate(
        Path(args.input_root),
        Path(args.trace_log).read_text(encoding="utf-8", errors="replace"),
    )
    out = Path(args.json_out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "trial_count": result["trial_count"],
                "negative_17_count": result["negative_17_count"],
                "classification_counts": result["classification_counts"],
                "start_state_histogram": result["start_state_histogram"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
