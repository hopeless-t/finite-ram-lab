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
MOVE_RE = re.compile(r"\bmove=(?P<move>\S+)")
COUNTER_RE = re.compile(r"\bcounter=(?P<counter>0x[0-9a-fA-F]+)")
NR_PAGES_RE = re.compile(r"\bnr_pages=(?P<nr_pages>\d+)")


def _event_row(line: str) -> dict[str, Any]:
    out: dict[str, Any] = {"line": line.strip()}
    if (m := NR_RE.search(line)):
        out["nr"] = int(m.group("nr"))
    if (m := MOVE_RE.search(line)):
        out["move"] = m.group("move")
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
    trials = [json.loads(p.read_text(encoding="utf-8")) for p in _trial_files(input_root)]

    specimens: list[dict[str, Any]] = []
    first_touch_nr: list[int] = []
    neg_touch_nr: list[int] = []
    flush_nr: list[int] = []

    for trial in trials:
        trial_id = f"{trial['block']}:{trial['identity']}"
        per_touch: list[dict[str, Any]] = []

        for touch in trial["touches"]:
            key = (trial_id, int(touch["touch_number"]))
            trace = windows.get(
                key,
                {
                    "lru_add": [],
                    "lru_flush": [],
                    "folios_put": [],
                    "pc_try": [],
                    "pc_uncharge_17": [],
                },
            )

            add_nrs = [
                int(e["nr"])
                for e in trace["lru_add"]
                if "nr" in e and str(e.get("move", "")).startswith("lru_add")
            ]
            flush_nrs = [
                int(e["nr"])
                for e in trace["lru_flush"]
                if "nr" in e and str(e.get("move", "")).startswith("lru_add")
            ]
            put_nrs = [int(e["nr"]) for e in trace["folios_put"] if "nr" in e]

            if int(touch["touch_number"]) == 1 and add_nrs:
                first_touch_nr.extend(add_nrs)

            if float(touch["delta_pages"]) == -17.0:
                neg_touch_nr.extend(add_nrs)
                flush_nr.extend(flush_nrs)
                specimens.append(
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
                            else touch["vmrss_kib_post"] - touch["vmrss_kib_pre"]
                        ),
                        "lru_add_nrs": add_nrs,
                        "lru_flush_nrs": flush_nrs,
                        "folios_put_nrs": put_nrs,
                        "pc_uncharge_17": trace["pc_uncharge_17"],
                        "pc_try": trace["pc_try"],
                    }
                )

            per_touch.append(
                {
                    "touch_number": touch["touch_number"],
                    "delta_pages": touch["delta_pages"],
                    "lru_add_nrs": add_nrs,
                    "lru_flush_nrs": flush_nrs,
                    "folios_put_nrs": put_nrs,
                }
            )

    exact_chain = 0
    for row in specimens:
        if (
            30 in row["lru_add_nrs"]
            and 31 in row["lru_flush_nrs"]
            and 31 in row["folios_put_nrs"]
            and len(row["pc_uncharge_17"]) >= 1
        ):
            exact_chain += 1

    return {
        "experiment_id": "OBS-002-LRU-BATCH-OCCUPANCY-v1",
        "trial_count": len(trials),
        "negative_17_count": len(specimens),
        "negative_17_exact_30_to_31_chain": exact_chain,
        "first_touch_lru_add_nr_histogram": dict(Counter(first_touch_nr)),
        "negative_touch_lru_add_nr_histogram": dict(Counter(neg_touch_nr)),
        "negative_touch_lru_flush_nr_histogram": dict(Counter(flush_nr)),
        "negative_17_specimens": specimens,
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
        json.dumps(environment_receipt(worker, cpus), indent=2, sort_keys=True) + "\n",
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
        Path(args.trace_log).read_text(encoding="utf-8", errors="replace"),
    )
    out = Path(args.json_out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "trial_count": result["trial_count"],
                "negative_17_count": result["negative_17_count"],
                "negative_17_exact_30_to_31_chain": result[
                    "negative_17_exact_30_to_31_chain"
                ],
                "first_touch_lru_add_nr_histogram": result[
                    "first_touch_lru_add_nr_histogram"
                ],
                "negative_touch_lru_add_nr_histogram": result[
                    "negative_touch_lru_add_nr_histogram"
                ],
                "negative_touch_lru_flush_nr_histogram": result[
                    "negative_touch_lru_flush_nr_histogram"
                ],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
