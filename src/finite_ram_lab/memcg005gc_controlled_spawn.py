from __future__ import annotations

import argparse
import json
import mmap
import os
import platform
import struct
import subprocess
import time
from collections import Counter
from pathlib import Path
from typing import Any

from .evidence_residency import sha256_file

OFF_READY = 0
OFF_MODE = 4
OFF_TARGET = 8
OFF_GO = 12
OFF_DONE = 16
OFF_STOP = 20
OFF_OBS_CPU = 24
OFF_TOUCHED = 28
OFF_ERROR = 32
OFF_PAGE_INDEX = 36
OFF_GUARD_INDEX = 40
OFF_SAFE_START = 44
OFF_SAFE_LEN = 48
OFF_GUARD_CPU = 52
OFF_REGION_ADDR = 56
OFF_PAGE_SIZE = 64
CONTROL_BYTES = 4096


def load_spec(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        text=True,
        capture_output=True,
        check=check,
    )


def _u32(mm: mmap.mmap, offset: int) -> int:
    return struct.unpack_from("<I", mm, offset)[0]


def _u64(mm: mmap.mmap, offset: int) -> int:
    return struct.unpack_from("<Q", mm, offset)[0]


def _set_u32(mm: mmap.mmap, offset: int, value: int) -> None:
    struct.pack_into("<I", mm, offset, int(value))


def _wait(pred: Any, timeout: float = 10.0) -> None:
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if pred():
            return
        time.sleep(0.001)
    raise TimeoutError("timeout")


def _proc_cpu(pid: int) -> int:
    text = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
    return int(text[text.rfind(")") + 2 :].split()[36])


def _wait_cpu(pid: int, cpu: int) -> None:
    _wait(lambda: _proc_cpu(pid) == cpu, 5.0)


def _current(cg: Path) -> int:
    return int((cg / "memory.current").read_text(encoding="utf-8").strip())


def _vmpte_kib(pid: int) -> int:
    for line in Path(f"/proc/{pid}/status").read_text(
        encoding="utf-8"
    ).splitlines():
        if line.startswith("VmPTE:"):
            return int(line.split()[1])
    raise ValueError(f"VmPTE not found for pid {pid}")


def _q64(spec: dict[str, Any], delta_pages: float) -> bool:
    return (
        float(spec["q64_min_pages"])
        <= delta_pages
        <= float(spec["q64_max_pages"])
    )


def _zero(delta_pages: float) -> bool:
    return abs(delta_pages) < 1e-12


def arm_for(
    spec: dict[str, Any],
    block: int,
    identity: int,
) -> dict[str, Any]:
    arms = spec["arms"]
    return dict(arms[(block + identity) % len(arms)])


def expected_pattern(arm_id: str) -> list[str]:
    if arm_id == "b62":
        return ["ZERO", "ZERO", "Q64"]
    if arm_id == "b63":
        return ["ZERO", "Q64"]
    if arm_id == "b64":
        return ["Q64"]
    raise ValueError(f"unsupported arm: {arm_id}")


def _start(
    worker: Path,
    root: Path,
    name: str,
    prep_cpu: int,
    max_pages: int,
    safe_len: int,
    worker_uid: int | None = None,
) -> dict[str, Any]:
    ctl = root / f"{name}.ctl"
    fd = os.open(
        ctl,
        os.O_RDWR | os.O_CREAT | os.O_TRUNC,
        0o600,
    )
    os.ftruncate(fd, CONTROL_BYTES)
    selected_uid = os.getuid() if worker_uid is None else int(worker_uid)
    if selected_uid != os.getuid():
        os.chown(ctl, selected_uid, -1)
    mm = mmap.mmap(
        fd,
        CONTROL_BYTES,
        access=mmap.ACCESS_WRITE,
    )

    _run(
        [
            "sudo",
            "systemd-run",
            "--quiet",
            "--collect",
            f"--unit={name}",
            f"--uid={selected_uid}",
            "-p",
            "MemoryAccounting=yes",
            "-p",
            f"CPUAffinity={prep_cpu}",
            str(worker),
            "--shared",
            str(ctl),
            "--max-pages",
            str(max_pages),
            "--safe-len",
            str(safe_len),
        ]
    )
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
    _wait_cpu(pid, prep_cpu)

    return {
        "name": name,
        "pid": pid,
        "cg": cg,
        "fd": fd,
        "mm": mm,
    }


def _stop(unit: dict[str, Any]) -> None:
    try:
        _set_u32(unit["mm"], OFF_STOP, 1)
    except Exception:
        pass
    _run(
        [
            "sudo",
            "systemctl",
            "stop",
            unit["name"] + ".service",
        ],
        check=False,
    )
    try:
        unit["mm"].close()
        os.close(unit["fd"])
    except Exception:
        pass


def _touch(
    unit: dict[str, Any],
    stock_cpu: int,
    page_size: int,
    page_index: int,
    phase: str,
) -> dict[str, Any]:
    _set_u32(unit["mm"], OFF_MODE, 2)
    _set_u32(unit["mm"], OFF_TARGET, stock_cpu)
    _set_u32(unit["mm"], OFF_PAGE_INDEX, page_index)
    _set_u32(unit["mm"], OFF_DONE, 0)
    _set_u32(unit["mm"], OFF_ERROR, 0)

    vmpte_pre = _vmpte_kib(unit["pid"])
    current_pre = _current(unit["cg"])

    _set_u32(unit["mm"], OFF_GO, 1)
    _wait(lambda: _u32(unit["mm"], OFF_DONE) == 1)

    current_post = _current(unit["cg"])
    vmpte_post = _vmpte_kib(unit["pid"])

    return {
        "phase": phase,
        "page_index": page_index,
        "current_pre_bytes": current_pre,
        "current_post_bytes": current_post,
        "delta_pages": (current_post - current_pre) / page_size,
        "vmpte_pre_kib": vmpte_pre,
        "vmpte_post_kib": vmpte_post,
        "vmpte_delta_kib": vmpte_post - vmpte_pre,
        "observed_cpu": _u32(unit["mm"], OFF_OBS_CPU),
        "worker_error": _u32(unit["mm"], OFF_ERROR),
        "worker_touched": _u32(unit["mm"], OFF_TOUCHED),
    }


def _touch_valid(
    touch: dict[str, Any],
    stock_cpu: int,
    expected_touched: int,
) -> bool:
    return (
        touch["observed_cpu"] == stock_cpu
        and touch["worker_error"] == 0
        and touch["worker_touched"] == expected_touched
    )


def _pattern_token(
    spec: dict[str, Any],
    touch: dict[str, Any],
) -> str:
    delta = float(touch["delta_pages"])
    if _zero(delta):
        return "ZERO"
    if _q64(spec, delta):
        return "Q64"
    return "OTHER"


def geometry_receipt(
    unit: dict[str, Any],
    prep_cpu: int,
) -> dict[str, Any]:
    mm = unit["mm"]
    base = _u64(mm, OFF_REGION_ADDR)
    page_size = _u64(mm, OFF_PAGE_SIZE)
    guard = _u32(mm, OFF_GUARD_INDEX)
    start = _u32(mm, OFF_SAFE_START)
    length = _u32(mm, OFF_SAFE_LEN)
    guard_cpu = _u32(mm, OFF_GUARD_CPU)

    start_pte = ((base >> 12) + start) & 511
    end_pte = ((base >> 12) + start + length - 1) & 511
    same_pte = start_pte <= end_pte and start_pte + length <= 512

    return {
        "region_addr": base,
        "page_size": page_size,
        "guard_index": guard,
        "safe_start": start,
        "safe_len": length,
        "guard_cpu": guard_cpu,
        "guard_cpu_match": guard_cpu == prep_cpu,
        "safe_start_pte_index": start_pte,
        "safe_end_pte_index": end_pte,
        "same_pte_table": same_pte,
    }


def classify_failure(
    spec: dict[str, Any],
    row: dict[str, Any],
) -> str | None:
    if not row["geometry"]["guard_cpu_match"]:
        return "PRECONDITION_CPU_MISMATCH"
    if not row["geometry"]["same_pte_table"]:
        return "GEOMETRY_INVALID"
    if row["primer_status"] == "NOT_FOUND":
        return "PRIMER_NOT_FOUND"
    if row["primer_status"] == "OTHER_DELTA":
        return "CALIBRATION_OTHER_DELTA"
    if row["primer_status"] == "PTE_CONTAMINATED":
        return "PTE_CONTAMINATED"
    if row["primer_status"] == "CPU_OR_WORKER_ERROR":
        return "CPU_OR_WORKER_ERROR"
    if row["primer_status"] == "SEQUENCE_EXHAUSTED":
        return "SEQUENCE_EXHAUSTED"

    measured = [
        *row["bait_touches"],
        *row["observed_pattern_touches"],
    ]
    if any(
        touch["worker_error"] != 0
        or touch["observed_cpu"] != row["stock_cpu"]
        for touch in measured
    ):
        return "CPU_OR_WORKER_ERROR"

    for touch in row["bait_touches"]:
        if touch["vmpte_delta_kib"] != 0:
            return "PTE_CONTAMINATED"
        if not _zero(float(touch["delta_pages"])):
            return "BAIT_NONZERO"

    if any(
        touch["vmpte_delta_kib"] != 0
        for touch in row["observed_pattern_touches"]
    ):
        return "PTE_CONTAMINATED"

    observed = [
        _pattern_token(spec, touch)
        for touch in row["observed_pattern_touches"]
    ]
    expected = expected_pattern(row["arm_id"])

    if observed == expected:
        return None
    if any(token == "OTHER" for token in observed):
        return "OTHER_NONZERO_NONQ64"
    return "NEXT_PHASE_MISMATCH"


def run_probe(
    spec: dict[str, Any],
    worker: Path,
    root: Path,
    block: int,
    identity: int,
    prep_cpu: int,
    stock_cpu: int,
) -> dict[str, Any]:
    arm = arm_for(spec, block, identity)
    name = (
        f"fr-m5gc-{os.getenv('GITHUB_RUN_ID', 'local')}"
        f"-{block}-{identity}"
    )
    unit = _start(
        worker,
        root,
        name,
        prep_cpu,
        int(spec["max_pages"]),
        int(spec["safe_len"]),
    )
    try:
        page_size = int(spec["required_page_size"])
        geometry = geometry_receipt(unit, prep_cpu)
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
        cursor = 0
        touches: list[dict[str, Any]] = []
        primer: dict[str, Any] | None = None
        primer_status = "NOT_FOUND"

        for calibration_index in range(
            int(spec["calibration_max_touches"])
        ):
            if cursor >= len(sequence):
                break
            touch = _touch(
                unit,
                stock_cpu,
                page_size,
                sequence[cursor],
                f"calibration-{calibration_index + 1}",
            )
            cursor += 1
            touches.append(touch)

            if not _touch_valid(touch, stock_cpu, len(touches)):
                primer_status = "CPU_OR_WORKER_ERROR"
                break
            if touch["vmpte_delta_kib"] != 0:
                primer_status = "PTE_CONTAMINATED"
                break
            token = _pattern_token(spec, touch)
            if token == "Q64":
                primer = touch
                primer_status = "FOUND"
                break
            if token != "ZERO":
                primer_status = "OTHER_DELTA"
                break

        bait_touches: list[dict[str, Any]] = []
        pattern_touches: list[dict[str, Any]] = []

        if primer_status == "FOUND":
            bait_count = int(arm["batch_consumed_before_target"]) - 1
            for bait_index in range(bait_count):
                if cursor >= len(sequence):
                    primer_status = "SEQUENCE_EXHAUSTED"
                    break
                touch = _touch(
                    unit,
                    stock_cpu,
                    page_size,
                    sequence[cursor],
                    f"bait-{bait_index + 1}",
                )
                cursor += 1
                touches.append(touch)
                bait_touches.append(touch)
                if not _touch_valid(touch, stock_cpu, len(touches)):
                    break

            if (
                primer_status == "FOUND"
                and len(bait_touches) == bait_count
                and all(
                    _touch_valid(t, stock_cpu, i + len(touches) - len(bait_touches) + 1)
                    for i, t in enumerate(bait_touches)
                )
            ):
                for phase in ["target", "next1", "next2"][
                    : len(expected_pattern(str(arm["id"])))
                ]:
                    if cursor >= len(sequence):
                        primer_status = "SEQUENCE_EXHAUSTED"
                        break
                    touch = _touch(
                        unit,
                        stock_cpu,
                        page_size,
                        sequence[cursor],
                        phase,
                    )
                    cursor += 1
                    touches.append(touch)
                    pattern_touches.append(touch)

        row: dict[str, Any] = {
            "experiment_id": spec["experiment_id"],
            "block": block,
            "identity": identity,
            "arm_id": arm["id"],
            "batch_consumed_before_target": int(
                arm["batch_consumed_before_target"]
            ),
            "prep_cpu": prep_cpu,
            "stock_cpu": stock_cpu,
            "geometry": geometry,
            "vmpte_after_guard_kib": vmpte_after_guard,
            "pre_migration_current_pages": (
                pre_migration_current / page_size
            ),
            "post_migration_current_pages": (
                post_migration_current / page_size
            ),
            "migration_delta_pages": (
                post_migration_current - pre_migration_current
            )
            / page_size,
            "primer_status": primer_status,
            "primer_touch_number": (
                None if primer is None else touches.index(primer) + 1
            ),
            "primer_delta_pages": (
                None if primer is None else primer["delta_pages"]
            ),
            "calibration_touches": [
                t for t in touches if str(t["phase"]).startswith("calibration-")
            ],
            "bait_touches": bait_touches,
            "observed_pattern_touches": pattern_touches,
            "expected_pattern": expected_pattern(str(arm["id"])),
            "total_measured_touches": len(touches),
        }
        failure = classify_failure(spec, row)
        row["failure_class"] = failure
        row["exact_recovery"] = failure is None
        return row
    finally:
        _stop(unit)


def summarize_arm(rows: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(rows)
    exact = sum(bool(row["exact_recovery"]) for row in rows)
    primer = sum(row["primer_status"] == "FOUND" for row in rows)
    return {
        "n": n,
        "primer_found": primer,
        "exact_recovery": exact,
        "exact_recovery_rate": exact / n if n else None,
        "failure_classes": dict(
            Counter(
                str(row["failure_class"])
                for row in rows
                if row["failure_class"] is not None
            )
        ),
        "primer_touch_histogram": dict(
            Counter(
                str(row["primer_touch_number"])
                for row in rows
                if row["primer_touch_number"] is not None
            )
        ),
    }


def analyze(
    spec: dict[str, Any],
    trials: list[dict[str, Any]],
) -> dict[str, Any]:
    expected = {
        (block, identity)
        for block in range(int(spec["runner_blocks"]))
        for identity in range(int(spec["identities_per_block"]))
    }
    got = {
        (int(row["block"]), int(row["identity"]))
        for row in trials
    }
    if got != expected:
        raise ValueError("incomplete matrix")

    by_arm = {
        str(arm["id"]): summarize_arm(
            [
                row
                for row in trials
                if row["arm_id"] == arm["id"]
            ]
        )
        for arm in spec["arms"]
    }
    return {
        "experiment_id": spec["experiment_id"],
        "stage": spec["stage"],
        "by_arm": by_arm,
        "overall": {
            "n": len(trials),
            "primer_found": sum(
                row["primer_status"] == "FOUND"
                for row in trials
            ),
            "exact_recovery": sum(
                bool(row["exact_recovery"])
                for row in trials
            ),
            "failure_classes": dict(
                Counter(
                    str(row["failure_class"])
                    for row in trials
                    if row["failure_class"] is not None
                )
            ),
        },
        "trials": trials,
    }


def environment_receipt(
    worker: Path,
    cpus: list[int],
) -> dict[str, Any]:
    thp_root = Path("/sys/kernel/mm/transparent_hugepage")
    thp: dict[str, str] = {}
    if thp_root.exists():
        enabled = thp_root / "enabled"
        if enabled.exists():
            thp["enabled"] = enabled.read_text(
                encoding="utf-8"
            ).strip()
        for path in sorted(thp_root.glob("hugepages-*/enabled")):
            thp[path.parent.name] = path.read_text(
                encoding="utf-8"
            ).strip()

    return {
        "uname": list(os.uname()),
        "platform": platform.platform(),
        "libc": list(platform.libc_ver()),
        "page_size": os.sysconf("SC_PAGESIZE"),
        "available_cpus": cpus,
        "worker_sha256": sha256_file(worker),
        "transparent_hugepage": thp,
        "github_run_id": os.getenv("GITHUB_RUN_ID"),
        "github_sha": os.getenv("GITHUB_SHA"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run-block")
    run.add_argument("--spec", required=True)
    run.add_argument("--block", type=int, required=True)
    run.add_argument("--worker", required=True)
    run.add_argument("--out-root", required=True)

    agg = sub.add_parser("aggregate")
    agg.add_argument("--spec", required=True)
    agg.add_argument("--input-root", required=True)
    agg.add_argument("--json-out", required=True)

    args = parser.parse_args()
    spec = load_spec(args.spec)

    if args.cmd == "run-block":
        cpus = sorted(os.sched_getaffinity(0))
        if len(cpus) < 3:
            raise RuntimeError("controlled spawn requires at least 3 CPUs")
        controller_cpu, prep_cpu, stock_cpu = cpus[0], cpus[1], cpus[-1]
        os.sched_setaffinity(0, {controller_cpu})

        root = Path(args.out_root)
        root.mkdir(parents=True, exist_ok=True)
        worker = Path(args.worker).resolve()

        (root / "environment.json").write_text(
            json.dumps(
                environment_receipt(worker, cpus),
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

        for identity in range(int(spec["identities_per_block"])):
            trial_root = root / f"id-{identity}"
            trial_root.mkdir(parents=True, exist_ok=True)
            row = run_probe(
                spec,
                worker,
                trial_root,
                args.block,
                identity,
                prep_cpu,
                stock_cpu,
            )
            (
                root
                / f"trial-{args.block}-{identity}.json"
            ).write_text(
                json.dumps(row, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        return

    trials = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(
            Path(args.input_root).rglob("trial-*.json")
        )
    ]
    result = analyze(spec, trials)
    out = Path(args.json_out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "by_arm": result["by_arm"],
                "overall": result["overall"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
