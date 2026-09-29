from __future__ import annotations

import argparse
import json
import mmap
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
    OFF_TARGET,
    _current,
    _set_u32,
    _start,
    _stop,
    _touch,
    _u32,
    _vmpte_kib,
    _wait,
    _wait_cpu,
    environment_receipt,
    geometry_receipt,
)
from .obs005_cross_cgroup_lru import (
    _command as _handoff_command,
    _event_count,
    _start_role,
    _stop_role,
    CMD_TOUCH,
)

OFF_DISCARD_START = 72
OFF_DISCARD_LEN = 76
MODE_DISCARD = 3

MARKER_RE = re.compile(
    r"FRL_OBS006 trial=(?P<trial>\d+:\d+) "
    r"phase=(?P<phase>[A-Z0-9_]+) touch=(?P<touch>\d+) "
    r"(?P<edge>PRE|POST)"
)
COUNTER_RE = re.compile(r"\bcounter=(?P<counter>0x[0-9a-fA-F]+)")
NR_RE = re.compile(r"\bnr=(?P<nr>\d+)")
NR_PAGES_RE = re.compile(r"\bnr_pages=(?P<nr_pages>\d+)")
COMM_RE = re.compile(r'\bcomm="(?P<comm>[^"]+)"')


def _marker(path: Path, text: str) -> None:
    with path.open("w", encoding="utf-8") as fh:
        fh.write(text + "\n")


def _wait_event_count(
    trace_path: Path,
    event: str,
    comm: str,
    baseline: int,
    timeout: float = 0.02,
) -> int:
    deadline = time.monotonic() + timeout
    while True:
        count = _event_count(trace_path, event, comm)
        if count > baseline:
            return count
        if time.monotonic() >= deadline:
            return count
        time.sleep(0.001)


def _discard(
    unit: dict[str, Any],
    target_cpu: int,
    page_size: int,
    start: int,
    length: int,
) -> dict[str, Any]:
    _set_u32(unit["mm"], OFF_MODE, MODE_DISCARD)
    _set_u32(unit["mm"], OFF_TARGET, target_cpu)
    _set_u32(unit["mm"], OFF_DISCARD_START, start)
    _set_u32(unit["mm"], OFF_DISCARD_LEN, length)
    _set_u32(unit["mm"], OFF_DONE, 0)
    _set_u32(unit["mm"], OFF_ERROR, 0)

    current_pre = _current(unit["cg"])
    vmpte_pre = _vmpte_kib(unit["pid"])

    _set_u32(unit["mm"], OFF_GO, 1)
    _wait(lambda: _u32(unit["mm"], OFF_DONE) == 1)

    current_post = _current(unit["cg"])
    vmpte_post = _vmpte_kib(unit["pid"])
    return {
        "phase": "DISCARD",
        "start": start,
        "length": length,
        "current_pre_bytes": current_pre,
        "current_post_bytes": current_post,
        "delta_pages": (current_post - current_pre) / page_size,
        "vmpte_pre_kib": vmpte_pre,
        "vmpte_post_kib": vmpte_post,
        "vmpte_delta_kib": vmpte_post - vmpte_pre,
        "observed_cpu": _u32(unit["mm"], OFF_OBS_CPU),
        "worker_error": _u32(unit["mm"], OFF_ERROR),
    }


def _touch_with_marker(
    *,
    unit: dict[str, Any],
    target_cpu: int,
    page_size: int,
    page_index: int,
    phase: str,
    touch_number: int,
    trial_id: str,
    trace_marker: Path,
) -> dict[str, Any]:
    _marker(
        trace_marker,
        f"FRL_OBS006 trial={trial_id} phase={phase} "
        f"touch={touch_number} PRE",
    )
    row = _touch(unit, target_cpu, page_size, page_index, phase)
    _marker(
        trace_marker,
        f"FRL_OBS006 trial={trial_id} phase={phase} "
        f"touch={touch_number} POST",
    )
    return {"touch_number": touch_number, **row}


def run_trial(
    *,
    worker: Path,
    scrubber_worker: Path,
    root: Path,
    trace_marker: Path,
    trace_path: Path,
    block: int,
    identity: int,
    controller_cpu: int,
    prep_cpu: int,
    target_cpu: int,
    worker_uid: int,
    calibration_max: int,
    consume_after_primer: int,
    producer_pages: int,
    collision_pages: int,
    scrub_max_touches: int,
) -> dict[str, Any]:
    trial_id = f"{block}:{identity}"
    prefix = f"fr-obs006-{os.getenv('GITHUB_RUN_ID', 'local')}-{block}-{identity}"
    unit = scrubber = None

    qroot = root / "q6"
    sroot = root / "scrubber"
    qroot.mkdir(parents=True, exist_ok=True)
    sroot.mkdir(parents=True, exist_ok=True)

    unit = _start(
        worker,
        qroot,
        prefix + "-q",
        prep_cpu,
        1024,
        192,
        worker_uid=worker_uid,
    )
    try:
        geometry = geometry_receipt(unit, prep_cpu)
        page_size = int(geometry["page_size"])
        os.sched_setaffinity(unit["pid"], {target_cpu})
        _wait_cpu(unit["pid"], target_cpu)

        sequence = list(
            range(
                int(geometry["safe_start"]) + 1,
                int(geometry["safe_start"]) + int(geometry["safe_len"]),
            )
        )
        cursor = 0

        refill_baseline = _event_count(
            trace_path,
            "frl_refill_stock:",
            "frlq6",
        )

        calibration: list[dict[str, Any]] = []
        primer_touch: int | None = None
        for touch_no in range(1, calibration_max + 1):
            row = _touch_with_marker(
                unit=unit,
                target_cpu=target_cpu,
                page_size=page_size,
                page_index=sequence[cursor],
                phase="CALIBRATE",
                touch_number=touch_no,
                trial_id=trial_id,
                trace_marker=trace_marker,
            )
            cursor += 1
            calibration.append(row)

            count = _wait_event_count(
                trace_path,
                "frl_refill_stock:",
                "frlq6",
                refill_baseline,
            )
            if count > refill_baseline:
                primer_touch = touch_no
                refill_baseline = count
                break

        consume: list[dict[str, Any]] = []
        if primer_touch is not None:
            for touch_no in range(1, consume_after_primer + 1):
                row = _touch_with_marker(
                    unit=unit,
                    target_cpu=target_cpu,
                    page_size=page_size,
                    page_index=sequence[cursor],
                    phase="CONSUME",
                    touch_number=touch_no,
                    trial_id=trial_id,
                    trace_marker=trace_marker,
                )
                cursor += 1
                consume.append(row)

        scrub_flush_touch: int | None = None
        scrub_rows: list[dict[str, Any]] = []
        if primer_touch is not None:
            scrubber = _start_role(
                worker=scrubber_worker,
                root=sroot,
                name=prefix + "-s",
                role="scrubber",
                cpu=target_cpu,
                max_pages=max(96, scrub_max_touches),
                worker_uid=worker_uid,
            )
            scrub_base = _event_count(
                trace_path,
                "frl_lru_scrub:",
                "frlscrub",
            )
            for touch_no in range(1, scrub_max_touches + 1):
                _marker(
                    trace_marker,
                    f"FRL_OBS006 trial={trial_id} phase=SCRUB "
                    f"touch={touch_no} PRE",
                )
                row = _handoff_command(scrubber, CMD_TOUCH)
                _marker(
                    trace_marker,
                    f"FRL_OBS006 trial={trial_id} phase=SCRUB "
                    f"touch={touch_no} POST",
                )
                scrub_rows.append({"touch_number": touch_no, **row})
                count = _wait_event_count(
                    trace_path,
                    "frl_lru_scrub:",
                    "frlscrub",
                    scrub_base,
                )
                if count > scrub_base:
                    scrub_flush_touch = touch_no
                    break

        producer_start = sequence[cursor] if cursor < len(sequence) else -1
        producer: list[dict[str, Any]] = []
        if primer_touch is not None and scrub_flush_touch is not None:
            for touch_no in range(1, producer_pages + 1):
                row = _touch_with_marker(
                    unit=unit,
                    target_cpu=target_cpu,
                    page_size=page_size,
                    page_index=sequence[cursor],
                    phase="PRODUCER",
                    touch_number=touch_no,
                    trial_id=trial_id,
                    trace_marker=trace_marker,
                )
                cursor += 1
                producer.append(row)

        discard: dict[str, Any] | None = None
        if producer:
            _marker(
                trace_marker,
                f"FRL_OBS006 trial={trial_id} phase=DISCARD touch=0 PRE",
            )
            discard = _discard(
                unit,
                target_cpu,
                page_size,
                producer_start,
                producer_pages,
            )
            _marker(
                trace_marker,
                f"FRL_OBS006 trial={trial_id} phase=DISCARD touch=0 POST",
            )

        collision: list[dict[str, Any]] = []
        if discard is not None and int(discard["worker_error"]) == 0:
            for touch_no in range(1, collision_pages + 1):
                row = _touch_with_marker(
                    unit=unit,
                    target_cpu=target_cpu,
                    page_size=page_size,
                    page_index=sequence[cursor],
                    phase="COLLISION",
                    touch_number=touch_no,
                    trial_id=trial_id,
                    trace_marker=trace_marker,
                )
                cursor += 1
                collision.append(row)

        return {
            "experiment_id": "OBS-006-MASKED-Q64-OBSERVER-v1",
            "block": block,
            "identity": identity,
            "worker_pid": unit["pid"],
            "controller_cpu": controller_cpu,
            "prep_cpu": prep_cpu,
            "target_cpu": target_cpu,
            "geometry": geometry,
            "page_size": page_size,
            "primer_touch": primer_touch,
            "consume_after_primer": consume_after_primer,
            "scrub_flush_touch": scrub_flush_touch,
            "producer_start": producer_start,
            "producer_pages": producer_pages,
            "collision_pages": collision_pages,
            "calibration": calibration,
            "consume": consume,
            "scrub": scrub_rows,
            "producer": producer,
            "discard": discard,
            "collision": collision,
        }
    finally:
        if scrubber is not None:
            _stop_role(scrubber)
        if unit is not None:
            _stop(unit)


def _event_row(line: str) -> dict[str, Any]:
    row: dict[str, Any] = {"line": line.strip()}
    if (m := COUNTER_RE.search(line)):
        row["counter"] = m.group("counter").lower()
    if (m := NR_RE.search(line)):
        row["nr"] = int(m.group("nr"))
    if (m := NR_PAGES_RE.search(line)):
        row["nr_pages"] = int(m.group("nr_pages"))
    if (m := COMM_RE.search(line)):
        row["comm"] = m.group("comm")
    return row


def parse_trace(text: str) -> dict[tuple[str, str, int], dict[str, Any]]:
    windows: dict[tuple[str, str, int], dict[str, Any]] = {}
    active: tuple[str, str, int] | None = None
    active_stack: list[str] | None = None

    for line in text.splitlines():
        marker = MARKER_RE.search(line)
        if marker:
            key = (
                marker.group("trial"),
                marker.group("phase"),
                int(marker.group("touch")),
            )
            if marker.group("edge") == "PRE":
                active = key
                windows.setdefault(
                    key,
                    {
                        "refill63": [],
                        "pc_try64": [],
                        "pc_uncharge17": [],
                        "pc_uncharge17_stacks": [],
                        "lru_flush": [],
                        "folios_put": [],
                        "drain_stock": [],
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

        if "frl_refill_stock:" in line:
            item["refill63"].append(row)
            active_stack = None
        elif "frl_pc_try64:" in line:
            item["pc_try64"].append(row)
            active_stack = None
        elif "frl_pc_uncharge17:" in line:
            item["pc_uncharge17"].append(row)
            stack: list[str] = []
            item["pc_uncharge17_stacks"].append(stack)
            active_stack = stack
        elif "frl_lru_flush:" in line:
            item["lru_flush"].append(row)
            active_stack = None
        elif "frl_folios_put:" in line:
            item["folios_put"].append(row)
            active_stack = None
        elif "frl_drain_stock:" in line:
            item["drain_stock"].append(row)
            active_stack = None
        elif active_stack is not None:
            stripped = line.strip()
            if stripped:
                active_stack.append(stripped)

    return windows


def _window(
    windows: dict[tuple[str, str, int], dict[str, Any]],
    trial_id: str,
    phase: str,
    touch: int,
) -> dict[str, Any]:
    return windows.get(
        (trial_id, phase, touch),
        {
            "refill63": [],
            "pc_try64": [],
            "pc_uncharge17": [],
            "pc_uncharge17_stacks": [],
            "lru_flush": [],
            "folios_put": [],
            "drain_stock": [],
        },
    )


def classify_trial(
    trial: dict[str, Any],
    windows: dict[tuple[str, str, int], dict[str, Any]],
) -> dict[str, Any]:
    trial_id = f"{trial['block']}:{trial['identity']}"

    if trial.get("primer_touch") is None:
        return {"classification": "PRIMER_NOT_FOUND"}
    if trial.get("scrub_flush_touch") is None:
        return {"classification": "SCRUB_NO_FLUSH"}
    if trial.get("discard") is None or int(trial["discard"]["worker_error"]) != 0:
        return {"classification": "DISCARD_FAILED"}

    all_measured = (
        trial["calibration"]
        + trial["consume"]
        + trial["producer"]
        + trial["collision"]
    )
    if any(float(row["vmpte_delta_kib"]) != 0.0 for row in all_measured):
        return {"classification": "PTE_CONTAMINATED"}

    unexpected_refill = []
    for phase, rows in [
        ("CONSUME", trial["consume"]),
        ("PRODUCER", trial["producer"]),
    ]:
        for row in rows:
            w = _window(
                windows,
                trial_id,
                phase,
                int(row["touch_number"]),
            )
            if w["refill63"]:
                unexpected_refill.append(
                    {"phase": phase, "touch": row["touch_number"]}
                )

    collision_events = []
    early_release = []
    for row in trial["collision"]:
        touch = int(row["touch_number"])
        w = _window(windows, trial_id, "COLLISION", touch)
        counters = [
            e["counter"]
            for e in w["pc_try64"]
            if "counter" in e
        ]
        same_counter_uncharge = [
            e
            for e in w["pc_uncharge17"]
            if e.get("counter") in counters
        ]
        flush_nrs = [e["nr"] for e in w["lru_flush"] if "nr" in e]
        put_nrs = [e["nr"] for e in w["folios_put"] if "nr" in e]
        event = {
            "touch": touch,
            "net_delta_pages": row["delta_pages"],
            "refill63_count": len(w["refill63"]),
            "pc_try64_counters": counters,
            "same_counter_uncharge17_count": len(same_counter_uncharge),
            "all_uncharge17": w["pc_uncharge17"],
            "flush_nrs": flush_nrs,
            "put_nrs": put_nrs,
            "drain_stock_count": len(w["drain_stock"]),
        }
        collision_events.append(event)
        if touch < int(trial["collision_pages"]) and w["pc_uncharge17"]:
            early_release.append(event)

    if unexpected_refill:
        return {
            "classification": "STOCK_STATE_LOST",
            "unexpected_refill": unexpected_refill,
            "collision_events": collision_events,
        }
    if early_release:
        return {
            "classification": "EARLY_RELEASE",
            "early_release": early_release,
            "collision_events": collision_events,
        }

    final = collision_events[-1]
    charge = final["refill63_count"] >= 1 and bool(final["pc_try64_counters"])
    release = final["same_counter_uncharge17_count"] >= 1
    lru = 31 in final["flush_nrs"] and 31 in final["put_nrs"]

    if charge and release and lru:
        cls = "MASKED_Q64_PASS"
    elif charge and not release:
        cls = "Q64_DIRECT_RELEASE_MISSING"
    elif release and not charge:
        cls = "LRU_RELEASE_Q64_MISSING"
    else:
        cls = "COLLISION_CHAIN_MISSING"

    return {
        "classification": cls,
        "collision_events": collision_events,
        "final_net_delta_pages": final["net_delta_pages"],
        "final_direct_q64": charge,
        "final_direct_release17": release,
        "final_lru_flush31": lru,
        "final_net47": float(final["net_delta_pages"]) == 47.0,
    }


def aggregate(input_root: Path, trace_text: str) -> dict[str, Any]:
    windows = parse_trace(trace_text)
    rows = []
    for path in sorted(input_root.rglob("trial-*.json")):
        trial = json.loads(path.read_text(encoding="utf-8"))
        derived = classify_trial(trial, windows)
        rows.append({**trial, **derived})

    return {
        "experiment_id": "OBS-006-MASKED-Q64-OBSERVER-v1",
        "trial_count": len(rows),
        "classification_counts": dict(
            Counter(row["classification"] for row in rows)
        ),
        "masked_q64_pass_count": sum(
            row["classification"] == "MASKED_Q64_PASS" for row in rows
        ),
        "masked_q64_net47_count": sum(
            bool(row.get("final_net47")) for row in rows
        ),
        "trials": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run-block")
    run.add_argument("--block", type=int, required=True)
    run.add_argument("--worker", required=True)
    run.add_argument("--scrubber-worker", required=True)
    run.add_argument("--out-root", required=True)
    run.add_argument("--trace-marker", required=True)
    run.add_argument("--trace-path", required=True)
    run.add_argument("--identities", type=int, default=4)
    run.add_argument("--calibration-max", type=int, default=64)
    run.add_argument("--consume-after-primer", type=int, default=33)
    run.add_argument("--producer-pages", type=int, default=17)
    run.add_argument("--collision-pages", type=int, default=14)
    run.add_argument("--scrub-max-touches", type=int, default=64)
    run.add_argument("--worker-uid", type=int, required=True)

    agg = sub.add_parser("aggregate")
    agg.add_argument("--input-root", required=True)
    agg.add_argument("--trace-log", required=True)
    agg.add_argument("--json-out", required=True)

    args = parser.parse_args()
    if args.cmd == "run-block":
        cpus = sorted(os.sched_getaffinity(0))
        if len(cpus) < 3:
            raise RuntimeError("OBS-006 requires at least 3 CPUs")
        controller_cpu, prep_cpu, target_cpu = cpus[0], cpus[1], cpus[-1]
        os.sched_setaffinity(0, {controller_cpu})

        root = Path(args.out_root)
        root.mkdir(parents=True, exist_ok=True)
        worker = Path(args.worker).resolve()
        scrubber_worker = Path(args.scrubber_worker).resolve()

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
                scrubber_worker=scrubber_worker,
                root=trial_root,
                trace_marker=Path(args.trace_marker),
                trace_path=Path(args.trace_path),
                block=args.block,
                identity=identity,
                controller_cpu=controller_cpu,
                prep_cpu=prep_cpu,
                target_cpu=target_cpu,
                worker_uid=args.worker_uid,
                calibration_max=args.calibration_max,
                consume_after_primer=args.consume_after_primer,
                producer_pages=args.producer_pages,
                collision_pages=args.collision_pages,
                scrub_max_touches=args.scrub_max_touches,
            )
            (root / f"trial-{args.block}-{identity}.json").write_text(
                json.dumps(row, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
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
                "classification_counts": result["classification_counts"],
                "masked_q64_pass_count": result["masked_q64_pass_count"],
                "masked_q64_net47_count": result["masked_q64_net47_count"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
