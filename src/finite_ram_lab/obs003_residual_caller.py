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
NR_PAGES_RE = re.compile(r"\bnr_pages=(?P<nr_pages>\d+)")


def _event_row(line: str) -> dict[str, Any]:
    out: dict[str, Any] = {"line": line.strip()}
    if (m := NR_RE.search(line)):
        out["nr"] = int(m.group("nr"))
    if (m := NR_PAGES_RE.search(line)):
        out["nr_pages"] = int(m.group("nr_pages"))
    return out


def parse_trace_windows(text: str) -> dict[tuple[str, int], dict[str, Any]]:
    windows: dict[tuple[str, int], dict[str, Any]] = {}
    active: tuple[str, int] | None = None
    active_stack: list[str] | None = None

    for line in text.splitlines():
        marker = MARKER_RE.search(line)
        if marker:
            key = (marker.group("trial"), int(marker.group("touch")))
            if marker.group("edge") == "PRE":
                active = key
                active_stack = None
                windows.setdefault(
                    key,
                    {
                        "drain_stock": [],
                        "lru_flush": [],
                        "folios_put": [],
                        "pc_uncharge_17": [],
                        "pc_uncharge_17_stacks": [],
                    },
                )
            elif active == key:
                active = None
                active_stack = None
            continue

        if active is None:
            continue

        item = windows[active]
        row = _event_row(line)

        if "frl_drain_stock:" in line:
            item["drain_stock"].append(row)
            active_stack = None
        elif "frl_lru_flush:" in line:
            item["lru_flush"].append(row)
            active_stack = None
        elif "frl_folios_put:" in line:
            item["folios_put"].append(row)
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


def classify_negative(
    trace: dict[str, Any],
) -> str:
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
    pc17 = len(trace["pc_uncharge_17"])
    drains = len(trace["drain_stock"])

    if 31 in flush_nrs and 31 in put_nrs and pc17 >= 1:
        return "LRU_BATCH"
    if drains >= 1 and pc17 >= 1:
        return "STOCK_DRAIN"
    if pc17 >= 1:
        return "OTHER_STACK"
    return "TRACE_MISS"


def _stack_symbols(stacks: list[list[str]]) -> list[str]:
    seen: list[str] = []
    for stack in stacks:
        for line in stack:
            if line not in seen:
                seen.append(line)
    return seen


def aggregate(input_root: Path, trace_text: str) -> dict[str, Any]:
    windows = parse_trace_windows(trace_text)
    trials = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(input_root.rglob("trial-*.json"))
    ]

    specimens: list[dict[str, Any]] = []
    other_negative: list[dict[str, Any]] = []

    for trial in trials:
        trial_id = f"{trial['block']}:{trial['identity']}"
        for touch in trial["touches"]:
            delta = float(touch["delta_pages"])
            if delta >= 0:
                continue

            key = (trial_id, int(touch["touch_number"]))
            trace = windows.get(
                key,
                {
                    "drain_stock": [],
                    "lru_flush": [],
                    "folios_put": [],
                    "pc_uncharge_17": [],
                    "pc_uncharge_17_stacks": [],
                },
            )
            row = {
                "trial": trial_id,
                "block": trial["block"],
                "identity": trial["identity"],
                "start_pages": trial["post_migration_current_pages"],
                "touch_number": int(touch["touch_number"]),
                "delta_pages": delta,
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
                "drain_stock_count": len(trace["drain_stock"]),
                "lru_flush_nrs": [
                    int(event["nr"])
                    for event in trace["lru_flush"]
                    if "nr" in event
                ],
                "folios_put_nrs": [
                    int(event["nr"])
                    for event in trace["folios_put"]
                    if "nr" in event
                ],
                "page_counter_uncharge_17_count": len(
                    trace["pc_uncharge_17"]
                ),
                "page_counter_uncharge_17_stack_lines": _stack_symbols(
                    trace["pc_uncharge_17_stacks"]
                ),
            }

            if delta == -17.0:
                row["classification"] = classify_negative(trace)
                specimens.append(row)
            else:
                other_negative.append(row)

    return {
        "experiment_id": "OBS-003-RESIDUAL-17-CALLER-v1",
        "trial_count": len(trials),
        "measured_touch_count": sum(
            len(trial["touches"]) for trial in trials
        ),
        "exact_minus17_count": len(specimens),
        "classification_counts": dict(
            Counter(row["classification"] for row in specimens)
        ),
        "exact_minus17_specimens": specimens,
        "other_negative_specimens": other_negative,
    }


def run_block(args: argparse.Namespace) -> None:
    cpus = sorted(os.sched_getaffinity(0))
    if len(cpus) < 3:
        raise RuntimeError("OBS-003 requires at least 3 CPUs")

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
        row["experiment_id"] = "OBS-003-RESIDUAL-17-CALLER-v1"
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
                "exact_minus17_count": result["exact_minus17_count"],
                "classification_counts": result["classification_counts"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
