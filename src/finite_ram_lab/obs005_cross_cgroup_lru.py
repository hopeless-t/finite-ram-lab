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

from .memcg005gc_controlled_spawn import _current, _run, _wait, _wait_cpu, environment_receipt

CONTROL_BYTES = 4096
OFF_READY = 0
OFF_COMMAND = 4
OFF_DONE = 8
OFF_STOP = 12
OFF_TARGET_CPU = 16
OFF_OBSERVED_CPU = 20
OFF_TOUCHED = 24
OFF_ERROR = 28
OFF_UNMAPPED = 32
OFF_PAGE_SIZE = 36
OFF_REGION_ADDR = 40
OFF_MAX_PAGES = 48

CMD_TOUCH = 1
CMD_UNMAP = 2

TRIAL_RE = re.compile(r"FRL_OBS005 trial=(?P<trial>\d+:\d+) (?P<edge>START|END)")
PHASE_RE = re.compile(
    r"FRL_OBS005 trial=(?P<trial>\d+:\d+) "
    r"phase=(?P<phase>SCRUB|PRODUCER|UNMAP|TRIGGER) "
    r"touch=(?P<touch>\d+) (?P<edge>PRE|POST)"
)
COUNTER_RE = re.compile(r"\bcounter=(?P<counter>0x[0-9a-fA-F]+)")
NR_RE = re.compile(r"\bnr=(?P<nr>\d+)")
NR_PAGES_RE = re.compile(r"\bnr_pages=(?P<nr_pages>\d+)")
COMM_RE = re.compile(r'\bcomm="(?P<comm>[^"]+)"')
PID_RE = re.compile(r"-(?P<pid>\d+)\s+\[\d+\]")


def _u32(mm: mmap.mmap, off: int) -> int:
    return int.from_bytes(mm[off : off + 4], "little")


def _set_u32(mm: mmap.mmap, off: int, value: int) -> None:
    mm[off : off + 4] = int(value).to_bytes(4, "little")


def _marker(path: Path, text: str) -> None:
    with path.open("w", encoding="utf-8") as fh:
        fh.write(text + "\n")


def _start_role(
    *,
    worker: Path,
    root: Path,
    name: str,
    role: str,
    cpu: int,
    max_pages: int,
    worker_uid: int,
    restrict_cpuset: bool = False,
) -> dict[str, Any]:
    ctl = root / f"{name}.ctl"
    fd = os.open(ctl, os.O_RDWR | os.O_CREAT | os.O_TRUNC, 0o600)
    os.ftruncate(fd, CONTROL_BYTES)
    os.chown(ctl, worker_uid, -1)
    mm = mmap.mmap(fd, CONTROL_BYTES, access=mmap.ACCESS_WRITE)

    command = [
        "sudo",
        "systemd-run",
        "--quiet",
        "--collect",
        f"--unit={name}",
        f"--uid={worker_uid}",
        "-p",
        "MemoryAccounting=yes",
        "-p",
        f"CPUAffinity={cpu}",
    ]
    if restrict_cpuset:
        command.extend(
            [
                "-p",
                f"AllowedCPUs={cpu}",
            ]
        )
    command.extend(
        [
            str(worker),
            "--shared",
            str(ctl),
            "--role",
            role,
            "--max-pages",
            str(max_pages),
        ]
    )
    _run(command)
    _wait(lambda: _u32(mm, OFF_READY) == 1)

    pid = int(
        _run(
            [
                "systemctl",
                "show",
                f"{name}.service",
                "--property=MainPID",
                "--value",
            ]
        ).stdout.strip()
    )
    cgroup_text = _run(
        [
            "systemctl",
            "show",
            f"{name}.service",
            "--property=ControlGroup",
            "--value",
        ]
    ).stdout.strip()
    cg = Path("/sys/fs/cgroup") / cgroup_text.lstrip("/")
    _wait_cpu(pid, cpu)

    _set_u32(mm, OFF_TARGET_CPU, cpu)
    return {"name": name, "role": role, "pid": pid, "cg": cg, "fd": fd, "mm": mm}


def _stop_role(unit: dict[str, Any]) -> None:
    try:
        _set_u32(unit["mm"], OFF_STOP, 1)
    except Exception:
        pass
    _run(
        ["sudo", "systemctl", "stop", unit["name"] + ".service"],
        check=False,
    )
    try:
        unit["mm"].close()
        os.close(unit["fd"])
    except Exception:
        pass


def _command(unit: dict[str, Any], command: int) -> dict[str, int]:
    _set_u32(unit["mm"], OFF_DONE, 0)
    _set_u32(unit["mm"], OFF_ERROR, 0)
    _set_u32(unit["mm"], OFF_COMMAND, command)
    _wait(lambda: _u32(unit["mm"], OFF_DONE) == 1)
    return {
        "error": _u32(unit["mm"], OFF_ERROR),
        "observed_cpu": _u32(unit["mm"], OFF_OBSERVED_CPU),
        "touched": _u32(unit["mm"], OFF_TOUCHED),
        "unmapped": _u32(unit["mm"], OFF_UNMAPPED),
    }


def _event_count(trace_path: Path, event: str, comm: str) -> int:
    text = trace_path.read_text(encoding="utf-8", errors="replace")
    return sum(
        1
        for line in text.splitlines()
        if event in line and f'comm="{comm}"' in line
    )


def run_trial(
    *,
    worker: Path,
    root: Path,
    trace_marker: Path,
    trace_path: Path,
    block: int,
    identity: int,
    controller_cpu: int,
    target_cpu: int,
    worker_uid: int,
    producer_pages: int,
    trigger_pages: int,
    scrub_max_touches: int,
) -> dict[str, Any]:
    trial_id = f"{block}:{identity}"
    prefix = f"fr-obs005-{os.getenv('GITHUB_RUN_ID', 'local')}-{block}-{identity}"
    producer = trigger = scrubber = None

    _marker(trace_marker, f"FRL_OBS005 trial={trial_id} START")
    try:
        for d in [root / "producer", root / "trigger", root / "scrubber"]:
            d.mkdir(parents=True, exist_ok=True)

        producer = _start_role(
            worker=worker,
            root=root / "producer",
            name=prefix + "-p",
            role="producer",
            cpu=target_cpu,
            max_pages=max(64, producer_pages),
            worker_uid=worker_uid,
        )
        trigger = _start_role(
            worker=worker,
            root=root / "trigger",
            name=prefix + "-t",
            role="trigger",
            cpu=target_cpu,
            max_pages=max(64, trigger_pages),
            worker_uid=worker_uid,
        )
        scrubber = _start_role(
            worker=worker,
            root=root / "scrubber",
            name=prefix + "-s",
            role="scrubber",
            cpu=target_cpu,
            max_pages=max(96, scrub_max_touches),
            worker_uid=worker_uid,
        )

        scrub_base = _event_count(trace_path, "frl_lru_flush:", "frlscrub")
        scrub_flush_touch = None
        scrub_rows = []
        for touch in range(1, scrub_max_touches + 1):
            _marker(
                trace_marker,
                f"FRL_OBS005 trial={trial_id} phase=SCRUB touch={touch} PRE",
            )
            row = _command(scrubber, CMD_TOUCH)
            _marker(
                trace_marker,
                f"FRL_OBS005 trial={trial_id} phase=SCRUB touch={touch} POST",
            )
            scrub_rows.append({"touch": touch, **row})
            if _event_count(trace_path, "frl_lru_flush:", "frlscrub") > scrub_base:
                scrub_flush_touch = touch
                break

        producer_rows = []
        for touch in range(1, producer_pages + 1):
            _marker(
                trace_marker,
                f"FRL_OBS005 trial={trial_id} phase=PRODUCER touch={touch} PRE",
            )
            row = _command(producer, CMD_TOUCH)
            _marker(
                trace_marker,
                f"FRL_OBS005 trial={trial_id} phase=PRODUCER touch={touch} POST",
            )
            producer_rows.append({"touch": touch, **row})

        _marker(
            trace_marker,
            f"FRL_OBS005 trial={trial_id} phase=UNMAP touch=0 PRE",
        )
        unmap_row = _command(producer, CMD_UNMAP)
        _marker(
            trace_marker,
            f"FRL_OBS005 trial={trial_id} phase=UNMAP touch=0 POST",
        )

        page_size = _u32(producer["mm"], OFF_PAGE_SIZE)
        producer_current_after_unmap = _current(producer["cg"])

        trigger_rows = []
        for touch in range(1, trigger_pages + 1):
            before = _current(producer["cg"])
            _marker(
                trace_marker,
                f"FRL_OBS005 trial={trial_id} phase=TRIGGER touch={touch} PRE",
            )
            row = _command(trigger, CMD_TOUCH)
            _marker(
                trace_marker,
                f"FRL_OBS005 trial={trial_id} phase=TRIGGER touch={touch} POST",
            )
            after = _current(producer["cg"])
            trigger_rows.append(
                {
                    "touch": touch,
                    **row,
                    "producer_current_pre_pages": before / page_size,
                    "producer_current_post_pages": after / page_size,
                    "producer_current_delta_pages": (after - before) / page_size,
                }
            )

        return {
            "experiment_id": "OBS-005-CROSS-CGROUP-LRU-HANDOFF-v1",
            "block": block,
            "identity": identity,
            "controller_cpu": controller_cpu,
            "target_cpu": target_cpu,
            "producer_pid": producer["pid"],
            "trigger_pid": trigger["pid"],
            "scrubber_pid": scrubber["pid"],
            "producer_cgroup": str(producer["cg"]),
            "trigger_cgroup": str(trigger["cg"]),
            "scrubber_cgroup": str(scrubber["cg"]),
            "page_size": page_size,
            "scrub_flush_touch": scrub_flush_touch,
            "producer_pages": producer_pages,
            "trigger_pages": trigger_pages,
            "producer_current_after_unmap_pages": producer_current_after_unmap / page_size,
            "scrub_rows": scrub_rows,
            "producer_rows": producer_rows,
            "producer_unmap": unmap_row,
            "trigger_rows": trigger_rows,
        }
    finally:
        _marker(trace_marker, f"FRL_OBS005 trial={trial_id} END")
        for unit in [scrubber, trigger, producer]:
            if unit is not None:
                _stop_role(unit)


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
    if (m := PID_RE.search(line)):
        row["pid"] = int(m.group("pid"))
    return row


def parse_trace(text: str) -> dict[str, Any]:
    trials: dict[str, dict[str, Any]] = {}
    current_trial: str | None = None
    active: tuple[str, str, int] | None = None
    active_stack: list[str] | None = None

    for line in text.splitlines():
        if (m := TRIAL_RE.search(line)):
            trial_id = m.group("trial")
            trials.setdefault(
                trial_id,
                {"pc_try": [], "windows": {}},
            )
            if m.group("edge") == "START":
                current_trial = trial_id
            else:
                current_trial = None
                active = None
                active_stack = None
            continue

        if (m := PHASE_RE.search(line)):
            trial_id = m.group("trial")
            key = (m.group("phase"), int(m.group("touch")))
            item = trials.setdefault(
                trial_id,
                {"pc_try": [], "windows": {}},
            )
            if m.group("edge") == "PRE":
                current_trial = trial_id
                active = (trial_id, key[0], key[1])
                item["windows"].setdefault(
                    key,
                    {
                        "lru_flush": [],
                        "folios_put": [],
                        "pc_uncharge_17": [],
                        "pc_uncharge_17_stacks": [],
                        "drain_stock": [],
                    },
                )
            else:
                active = None
                active_stack = None
            continue

        if current_trial is not None and "frl_pc_try:" in line:
            trials[current_trial]["pc_try"].append(_event_row(line))
            active_stack = None
            continue

        if active is None:
            continue

        trial_id, phase, touch = active
        window = trials[trial_id]["windows"][(phase, touch)]
        row = _event_row(line)
        if "frl_lru_flush:" in line:
            window["lru_flush"].append(row)
            active_stack = None
        elif "frl_folios_put:" in line:
            window["folios_put"].append(row)
            active_stack = None
        elif "frl_drain_stock:" in line:
            window["drain_stock"].append(row)
            active_stack = None
        elif "frl_pc_uncharge:" in line:
            window["pc_uncharge_17"].append(row)
            stack: list[str] = []
            window["pc_uncharge_17_stacks"].append(stack)
            active_stack = stack
        elif active_stack is not None:
            stripped = line.strip()
            if stripped:
                active_stack.append(stripped)

    return trials


def classify_trial(trial: dict[str, Any], trace: dict[str, Any]) -> dict[str, Any]:
    producer_pid = int(trial.get("producer_pid", -1))
    counters: list[str] = []
    for event in trace.get("pc_try", []):
        if event.get("pid") != producer_pid:
            continue
        counter = event.get("counter")
        if counter and counter not in counters:
            counters.append(counter)
    windows = trace.get("windows", {})

    producer_flushes = []
    for (phase, touch), w in windows.items():
        if phase in {"PRODUCER", "UNMAP"}:
            producer_flushes.extend(
                e for e in w["lru_flush"] if e.get("comm") == "frlprod"
            )

    matches: list[dict[str, Any]] = []
    for (phase, touch), w in windows.items():
        if phase != "TRIGGER":
            continue
        selected = [
            e
            for e in w["pc_uncharge_17"]
            if e.get("counter") in counters and e.get("comm") == "frltrig"
        ]
        if selected:
            matches.append(
                {
                    "touch": touch,
                    "selected_uncharge": selected,
                    "flush_nrs": [
                        e["nr"]
                        for e in w["lru_flush"]
                        if e.get("comm") == "frltrig" and "nr" in e
                    ],
                    "put_nrs": [
                        e["nr"]
                        for e in w["folios_put"]
                        if e.get("comm") == "frltrig" and "nr" in e
                    ],
                }
            )

    if trial.get("scrub_flush_touch") is None:
        classification = "SCRUB_NO_FLUSH"
    elif producer_flushes:
        classification = "PRODUCER_FLUSH_CONTAMINATED"
    elif not counters:
        classification = "COUNTER_UNKNOWN"
    elif not matches:
        classification = "NO_HANDOFF_UNCHARGE"
    else:
        primary = matches[0]
        if (
            primary["touch"] == int(trial["trigger_pages"])
            and 31 in primary["flush_nrs"]
            and 31 in primary["put_nrs"]
        ):
            classification = "CONTROLLED_HANDOFF_PASS"
        else:
            classification = "HANDOFF_NONCANONICAL_TIMING"

    return {
        "classification": classification,
        "producer_counters": counters,
        "producer_flush_count": len(producer_flushes),
        "handoff_matches": matches,
    }


def aggregate(input_root: Path, trace_text: str) -> dict[str, Any]:
    traces = parse_trace(trace_text)
    rows = []
    for path in sorted(input_root.rglob("trial-*.json")):
        trial = json.loads(path.read_text(encoding="utf-8"))
        trial_id = f"{trial['block']}:{trial['identity']}"
        derived = classify_trial(
            trial,
            traces.get(trial_id, {"pc_try": [], "windows": {}}),
        )
        rows.append({**trial, **derived})

    return {
        "experiment_id": "OBS-005-CROSS-CGROUP-LRU-HANDOFF-v1",
        "trial_count": len(rows),
        "classification_counts": dict(
            Counter(r["classification"] for r in rows)
        ),
        "trials": rows,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run-block")
    run.add_argument("--block", type=int, required=True)
    run.add_argument("--worker", required=True)
    run.add_argument("--out-root", required=True)
    run.add_argument("--trace-marker", required=True)
    run.add_argument("--trace-path", required=True)
    run.add_argument("--identities", type=int, default=4)
    run.add_argument("--producer-pages", type=int, default=17)
    run.add_argument("--trigger-pages", type=int, default=14)
    run.add_argument("--scrub-max-touches", type=int, default=64)
    run.add_argument("--worker-uid", type=int, required=True)

    agg = sub.add_parser("aggregate")
    agg.add_argument("--input-root", required=True)
    agg.add_argument("--trace-log", required=True)
    agg.add_argument("--json-out", required=True)

    args = p.parse_args()

    if args.cmd == "run-block":
        cpus = sorted(os.sched_getaffinity(0))
        if len(cpus) < 2:
            raise RuntimeError("OBS-005 requires at least 2 CPUs")
        controller_cpu, target_cpu = cpus[0], cpus[-1]
        os.sched_setaffinity(0, {controller_cpu})

        root = Path(args.out_root)
        root.mkdir(parents=True, exist_ok=True)
        worker = Path(args.worker).resolve()
        (root / "environment.json").write_text(
            json.dumps(environment_receipt(worker, cpus), indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )

        for identity in range(args.identities):
            trial_root = root / f"id-{identity}"
            for d in [
                trial_root / "producer",
                trial_root / "trigger",
                trial_root / "scrubber",
            ]:
                d.mkdir(parents=True, exist_ok=True)
            row = run_trial(
                worker=worker,
                root=trial_root,
                trace_marker=Path(args.trace_marker),
                trace_path=Path(args.trace_path),
                block=args.block,
                identity=identity,
                controller_cpu=controller_cpu,
                target_cpu=target_cpu,
                worker_uid=args.worker_uid,
                producer_pages=args.producer_pages,
                trigger_pages=args.trigger_pages,
                scrub_max_touches=args.scrub_max_touches,
            )
            (root / f"trial-{args.block}-{identity}.json").write_text(
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
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "trial_count": result["trial_count"],
                "classification_counts": result["classification_counts"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
