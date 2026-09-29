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

TRIAL_RE = re.compile(
    r"FRL_TRIAL trial=(?P<trial>\d+:\d+) "
    r"(?P<edge>START|READY|END)(?: pid=(?P<pid>\d+))?"
)
TOUCH_RE = re.compile(
    r"FRL_OBS001 trial=(?P<trial>\d+:\d+) "
    r"touch=(?P<touch>\d+) (?P<edge>PRE|POST)"
)
COUNTER_RE = re.compile(r"\bcounter=(?P<counter>0x[0-9a-fA-F]+)")
NR_RE = re.compile(r"\bnr=(?P<nr>\d+)")
NR_PAGES_RE = re.compile(r"\bnr_pages=(?P<nr_pages>\d+)")
COMM_RE = re.compile(r'\bcomm="(?P<comm>[^"]+)"')


def _event_row(line: str) -> dict[str, Any]:
    out: dict[str, Any] = {"line": line.strip()}
    if (m := COUNTER_RE.search(line)):
        out["counter"] = m.group("counter").lower()
    if (m := NR_RE.search(line)):
        out["nr"] = int(m.group("nr"))
    if (m := NR_PAGES_RE.search(line)):
        out["nr_pages"] = int(m.group("nr_pages"))
    if (m := COMM_RE.search(line)):
        out["comm"] = m.group("comm")
    return out


def parse_trace(text: str) -> dict[str, Any]:
    trials: dict[str, dict[str, Any]] = {}
    current_trial: str | None = None
    active_touch: tuple[str, int] | None = None
    active_stack: list[str] | None = None

    for line in text.splitlines():
        trial_marker = TRIAL_RE.search(line)
        if trial_marker:
            trial_id = trial_marker.group("trial")
            edge = trial_marker.group("edge")
            item = trials.setdefault(
                trial_id,
                {
                    "worker_pid": None,
                    "worker_counters": [],
                    "touches": {},
                },
            )
            if edge == "START":
                current_trial = trial_id
                active_touch = None
                active_stack = None
            elif edge == "READY":
                current_trial = trial_id
                if trial_marker.group("pid"):
                    item["worker_pid"] = int(trial_marker.group("pid"))
            elif edge == "END":
                if current_trial == trial_id:
                    current_trial = None
                active_touch = None
                active_stack = None
            continue

        touch_marker = TOUCH_RE.search(line)
        if touch_marker:
            trial_id = touch_marker.group("trial")
            touch = int(touch_marker.group("touch"))
            edge = touch_marker.group("edge")
            item = trials.setdefault(
                trial_id,
                {
                    "worker_pid": None,
                    "worker_counters": [],
                    "touches": {},
                },
            )
            if edge == "PRE":
                current_trial = trial_id
                active_touch = (trial_id, touch)
                item["touches"].setdefault(
                    touch,
                    {
                        "lru_flush": [],
                        "folios_put": [],
                        "drain_stock": [],
                        "pc_uncharge_17": [],
                        "pc_uncharge_17_stacks": [],
                    },
                )
            elif active_touch == (trial_id, touch):
                active_touch = None
                active_stack = None
            continue

        if current_trial is not None and "frl_pc_try:" in line:
            row = _event_row(line)
            counter = row.get("counter")
            if counter and row.get("comm") == "memcg005gc_spaw":
                counters = trials[current_trial]["worker_counters"]
                if counter not in counters:
                    counters.append(counter)
            active_stack = None
            continue

        if active_touch is None:
            continue

        trial_id, touch = active_touch
        item = trials[trial_id]["touches"][touch]
        row = _event_row(line)

        if "frl_lru_flush:" in line:
            item["lru_flush"].append(row)
            active_stack = None
        elif "frl_folios_put:" in line:
            item["folios_put"].append(row)
            active_stack = None
        elif "frl_drain_stock:" in line:
            item["drain_stock"].append(row)
            active_stack = None
        elif "frl_pc_uncharge:" in line:
            item["pc_uncharge_17"].append(row)
            stack: list[str] = []
            item["pc_uncharge_17_stacks"].append(stack)
            active_stack = stack
        elif active_stack is not None:
            stripped = line.strip()
            if stripped:
                active_stack.append(stripped)

    return trials


def _has_symbol(stack: list[str], symbol: str) -> bool:
    return any(symbol in line for line in stack)


def classify_negative(
    *,
    worker_counters: list[str],
    touch_trace: dict[str, Any],
) -> tuple[str, list[int]]:
    if not worker_counters:
        return "COUNTER_UNKNOWN", []

    matching_indexes = [
        i
        for i, event in enumerate(touch_trace["pc_uncharge_17"])
        if event.get("counter") in worker_counters
    ]
    external_indexes = [
        i
        for i, event in enumerate(touch_trace["pc_uncharge_17"])
        if event.get("counter") not in worker_counters
    ]

    if matching_indexes:
        flush_nrs = [
            int(event["nr"])
            for event in touch_trace["lru_flush"]
            if "nr" in event
        ]
        put_nrs = [
            int(event["nr"])
            for event in touch_trace["folios_put"]
            if "nr" in event
        ]
        if 31 in flush_nrs and 31 in put_nrs:
            return "WORKER_LRU_BATCH", matching_indexes

        for i in matching_indexes:
            stack = touch_trace["pc_uncharge_17_stacks"][i]
            if _has_symbol(stack, "drain_stock") or _has_symbol(
                stack, "refill_stock"
            ):
                return "STOCK_DRAIN_SAME_COUNTER", matching_indexes

        return "SAME_COUNTER_ASYNC", matching_indexes

    if external_indexes:
        return "EXTERNAL_COINCIDENCE", external_indexes

    return "TRACE_MISS", []


def aggregate(input_root: Path, trace_text: str) -> dict[str, Any]:
    traces = parse_trace(trace_text)
    trials = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(input_root.rglob("trial-*.json"))
    ]

    specimens: list[dict[str, Any]] = []
    counter_cardinality: Counter[int] = Counter()

    for trial in trials:
        trial_id = f"{trial['block']}:{trial['identity']}"
        trial_trace = traces.get(
            trial_id,
            {"worker_pid": None, "worker_counters": [], "touches": {}},
        )
        worker_counters = list(trial_trace["worker_counters"])
        counter_cardinality[len(worker_counters)] += 1

        for touch in trial["touches"]:
            if float(touch["delta_pages"]) != -17.0:
                continue

            touch_no = int(touch["touch_number"])
            touch_trace = trial_trace["touches"].get(
                touch_no,
                {
                    "lru_flush": [],
                    "folios_put": [],
                    "drain_stock": [],
                    "pc_uncharge_17": [],
                    "pc_uncharge_17_stacks": [],
                },
            )
            classification, indexes = classify_negative(
                worker_counters=worker_counters,
                touch_trace=touch_trace,
            )

            matching = [
                touch_trace["pc_uncharge_17"][i]
                for i in indexes
                if i < len(touch_trace["pc_uncharge_17"])
            ]
            matching_stacks = [
                touch_trace["pc_uncharge_17_stacks"][i]
                for i in indexes
                if i < len(touch_trace["pc_uncharge_17_stacks"])
            ]

            specimens.append(
                {
                    "trial": trial_id,
                    "block": trial["block"],
                    "identity": trial["identity"],
                    "worker_pid_receipt": trial.get("worker_pid"),
                    "trace_worker_pid": trial_trace.get("worker_pid"),
                    "worker_counters": worker_counters,
                    "start_pages": trial["post_migration_current_pages"],
                    "touch_number": touch_no,
                    "delta_pages": touch["delta_pages"],
                    "classification": classification,
                    "lru_flush_nrs": [
                        event["nr"]
                        for event in touch_trace["lru_flush"]
                        if "nr" in event
                    ],
                    "folios_put_nrs": [
                        event["nr"]
                        for event in touch_trace["folios_put"]
                        if "nr" in event
                    ],
                    "drain_stock_count": len(touch_trace["drain_stock"]),
                    "all_pc_uncharge_17": touch_trace["pc_uncharge_17"],
                    "selected_pc_uncharge_17": matching,
                    "selected_pc_uncharge_17_stacks": matching_stacks,
                }
            )

    return {
        "experiment_id": "OBS-004-PAGE-COUNTER-IDENTITY-v1",
        "trial_count": len(trials),
        "measured_touch_count": sum(len(t["touches"]) for t in trials),
        "worker_counter_cardinality_histogram": {
            str(k): v for k, v in sorted(counter_cardinality.items())
        },
        "exact_minus17_count": len(specimens),
        "classification_counts": dict(
            Counter(row["classification"] for row in specimens)
        ),
        "exact_minus17_specimens": specimens,
    }


def run_block(args: argparse.Namespace) -> None:
    cpus = sorted(os.sched_getaffinity(0))
    if len(cpus) < 3:
        raise RuntimeError("OBS-004 requires at least 3 CPUs")

    controller_cpu, prep_cpu, stock_cpu = cpus[0], cpus[1], cpus[-1]
    os.sched_setaffinity(0, {controller_cpu})

    root = Path(args.out_root)
    root.mkdir(parents=True, exist_ok=True)
    worker = Path(args.worker).resolve()
    marker = Path(args.trace_marker) if args.trace_marker else None

    (root / "environment.json").write_text(
        json.dumps(environment_receipt(worker, cpus), indent=2, sort_keys=True)
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
        row["experiment_id"] = "OBS-004-PAGE-COUNTER-IDENTITY-v1"
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
                "measured_touch_count": result["measured_touch_count"],
                "worker_counter_cardinality_histogram": result[
                    "worker_counter_cardinality_histogram"
                ],
                "exact_minus17_count": result["exact_minus17_count"],
                "classification_counts": result["classification_counts"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
