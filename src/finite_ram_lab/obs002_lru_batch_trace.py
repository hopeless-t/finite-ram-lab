from __future__ import annotations

import argparse
import json
import os
import re
from collections import Counter
from pathlib import Path
from typing import Any

from .memcg005gc_controlled_spawn import environment_receipt
from .obs001_uncharge_trace import run_trial

MARKER_RE = re.compile(
    r"FRL_OBS001 trial=(?P<trial>\d+:\d+) touch=(?P<touch>\d+) (?P<edge>PRE|POST)"
)
NR_RE = re.compile(r"\bnr=(?P<nr>\d+)")
COUNTER_RE = re.compile(r"\bcounter=(?P<counter>0x[0-9a-fA-F]+)")
NR_PAGES_RE = re.compile(r"\bnr_pages=(?P<nr_pages>\d+)")


def _event_row(line: str) -> dict[str, Any]:
    out: dict[str, Any] = {"line": line.strip()}
    if (m := NR_RE.search(line)):
        out["nr"] = int(m.group("nr"))
    if (m := COUNTER_RE.search(line)):
        out["counter"] = m.group("counter")
    if (m := NR_PAGES_RE.search(line)):
        out["nr_pages"] = int(m.group("nr_pages"))
    return out


def parse_trace_windows(text: str) -> dict[tuple[str, int], dict[str, Any]]:
    windows: dict[tuple[str, int], dict[str, Any]] = {}
    active: tuple[str, int] | None = None

    for line in text.splitlines():
        marker = MARKER_RE.search(line)
        if marker:
            key = (marker.group("trial"), int(marker.group("touch")))
            if marker.group("edge") == "PRE":
                active = key
                windows.setdefault(
                    key,
                    {
                        "lru_add": [],
                        "lru_flush": [],
                        "folios_put": [],
                        "pc_try": [],
                        "pc_uncharge_17": [],
                    },
                )
            elif active == key:
                active = None
            continue

        if active is None:
            continue

        row = _event_row(line)
        item = windows[active]
        if "frl_lru_add:" in line:
            item["lru_add"].append(row)
        elif "frl_lru_flush:" in line:
            item["lru_flush"].append(row)
        elif "frl_folios_put:" in line:
            item["folios_put"].append(row)
        elif "frl_pc_try:" in line:
            item["pc_try"].append(row)
        elif "frl_pc_uncharge:" in line:
            item["pc_uncharge_17"].append(row)

    return windows


def _trial_files(root: Path) -> list[Path]:
    return sorted(root.rglob("trial-*.json"))


def aggregate(input_root: Path, trace_text: str) -> dict[str, Any]:
    windows = parse_trace_windows(trace_text)
    trials = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in _trial_files(input_root)
    ]

    negative_17: list[dict[str, Any]] = []
    other_negative: list[dict[str, Any]] = []
    first_flush_rows: list[dict[str, Any]] = []
    all_add_counts: list[int] = []

    for trial in trials:
        trial_id = f"{trial['block']}:{trial['identity']}"
        first_flush_touch: int | None = None

        for touch in trial["touches"]:
            touch_number = int(touch["touch_number"])
            trace = windows.get(
                (trial_id, touch_number),
                {
                    "lru_add": [],
                    "lru_flush": [],
                    "folios_put": [],
                    "pc_try": [],
                    "pc_uncharge_17": [],
                },
            )
            add_count = len(trace["lru_add"])
            all_add_counts.append(add_count)
            flush_nrs = [
                int(event["nr"])
                for event in trace["lru_flush"]
                if "nr" in event
            ]
            put_nrs = [
                int(event["nr"])
                for event in trace["folios_put"]
                if "nr" in event
            ]

            if first_flush_touch is None and 31 in flush_nrs:
                first_flush_touch = touch_number

            delta_pages = float(touch["delta_pages"])
            if delta_pages < 0:
                row = {
                    "trial": trial_id,
                    "block": trial["block"],
                    "identity": trial["identity"],
                    "start_pages": trial["post_migration_current_pages"],
                    "touch_number": touch_number,
                    "delta_pages": delta_pages,
                    "lru_add_count": add_count,
                    "lru_flush_nrs": flush_nrs,
                    "folios_put_nrs": put_nrs,
                    "page_counter_uncharge_17_count": len(
                        trace["pc_uncharge_17"]
                    ),
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
                }
                if delta_pages == -17.0:
                    negative_17.append(row)
                else:
                    other_negative.append(row)

        if first_flush_touch is not None:
            first_flush_delta = next(
                float(t["delta_pages"])
                for t in trial["touches"]
                if int(t["touch_number"]) == first_flush_touch
            )
            first_flush_rows.append(
                {
                    "trial": trial_id,
                    "start_pages": trial["post_migration_current_pages"],
                    "first_flush_touch": first_flush_touch,
                    "inferred_initial_lru_add_occupancy": 31
                    - first_flush_touch,
                    "exact_minus17_at_first_flush": (
                        first_flush_delta == -17.0
                    ),
                }
            )

    occupancy_hist = Counter(
        row["inferred_initial_lru_add_occupancy"]
        for row in first_flush_rows
    )
    target = [
        row
        for row in first_flush_rows
        if row["inferred_initial_lru_add_occupancy"] in (17, 18)
    ]
    other = [
        row
        for row in first_flush_rows
        if row["inferred_initial_lru_add_occupancy"] not in (17, 18)
    ]

    full_chain_count = sum(
        31 in row["lru_flush_nrs"]
        and 31 in row["folios_put_nrs"]
        and row["page_counter_uncharge_17_count"] >= 1
        for row in negative_17
    )

    return {
        "experiment_id": "OBS-002-LRU-BATCH-OCCUPANCY-v1",
        "trial_count": len(trials),
        "measured_touch_count": sum(
            len(trial["touches"]) for trial in trials
        ),
        "instrumentation_correction": {
            "invalid_field": (
                "__folio_batch_add_and_move arg1 dereference as folio_batch.nr"
            ),
            "reason": (
                "arg1 is a __percpu pointer base; the function applies "
                "this_cpu_ptr() before dereferencing"
            ),
            "valid_substitute": (
                "one lru_add event per measured touch plus first "
                "folio_batch_move_lru(nr=31) timing"
            ),
            "all_measured_touches_lru_add_count_exactly_one": all(
                count == 1 for count in all_add_counts
            ),
        },
        "negative_events": {
            "exact_minus17_count": len(negative_17),
            "other_negative_count": len(other_negative),
            "exact_minus17_with_full_lru_chain": full_chain_count,
            "exact_minus17_without_lru_flush": sum(
                31 not in row["lru_flush_nrs"] for row in negative_17
            ),
            "touch_histogram": dict(
                Counter(
                    str(row["touch_number"])
                    for row in negative_17
                )
            ),
            "start_histogram": dict(
                Counter(
                    str(row["start_pages"])
                    for row in negative_17
                )
            ),
            "exact_minus17_specimens": negative_17,
            "other_negative_specimens": other_negative,
        },
        "first_flush_analysis": {
            "trials_with_first_lru_flush_within_window": len(
                first_flush_rows
            ),
            "inferred_initial_occupancy_histogram": dict(
                sorted(occupancy_hist.items())
            ),
            "occupancy_17_or_18": {
                "n": len(target),
                "minus17_at_first_flush": sum(
                    row["exact_minus17_at_first_flush"]
                    for row in target
                ),
            },
            "other_occupancies": {
                "n": len(other),
                "minus17_at_first_flush": sum(
                    row["exact_minus17_at_first_flush"]
                    for row in other
                ),
            },
            "rows": first_flush_rows,
        },
    }


def run_block(args: argparse.Namespace) -> None:
    cpus = sorted(os.sched_getaffinity(0))
    if len(cpus) < 3:
        raise RuntimeError("OBS-002 requires at least 3 CPUs")

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
        row["experiment_id"] = "OBS-002-LRU-BATCH-OCCUPANCY-v1"
        (root / f"trial-{args.block}-{identity}.json").write_text(
            json.dumps(row, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


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
        run_block(args)
        return

    result = aggregate(
        Path(args.input_root),
        Path(args.trace_log).read_text(
            encoding="utf-8",
            errors="replace",
        ),
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
                "measured_touch_count": result["measured_touch_count"],
                "negative_events": {
                    "exact_minus17_count": result[
                        "negative_events"
                    ]["exact_minus17_count"],
                    "exact_minus17_with_full_lru_chain": result[
                        "negative_events"
                    ]["exact_minus17_with_full_lru_chain"],
                    "exact_minus17_without_lru_flush": result[
                        "negative_events"
                    ]["exact_minus17_without_lru_flush"],
                },
                "first_flush_analysis": result[
                    "first_flush_analysis"
                ],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
