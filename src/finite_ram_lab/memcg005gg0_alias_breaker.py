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

from scipy.stats import fisher_exact

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


def _set(mm: mmap.mmap, offset: int, value: int) -> None:
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


def _memory_stat(cg: Path, key: str) -> int:
    for line in (cg / "memory.stat").read_text(encoding="utf-8").splitlines():
        name, value = line.split()
        if name == key:
            return int(value)
    raise ValueError(f"memory.stat key not found: {key}")


def _vmpte_kib(pid: int) -> int:
    for line in Path(f"/proc/{pid}/status").read_text(
        encoding="utf-8"
    ).splitlines():
        if line.startswith("VmPTE:"):
            parts = line.split()
            if len(parts) < 2:
                break
            return int(parts[1])
    raise ValueError(f"VmPTE not found for pid {pid}")


def _q64(spec: dict[str, Any], delta_pages: float) -> bool:
    return (
        spec["q64_min_pages"]
        <= delta_pages
        <= spec["q64_max_pages"]
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


def _start(
    worker: Path,
    root: Path,
    name: str,
    prep_cpu: int,
    token: str,
) -> dict[str, Any]:
    ctl = root / f"{name}.ctl"
    fd = os.open(
        ctl,
        os.O_RDWR | os.O_CREAT | os.O_TRUNC,
        0o600,
    )
    os.ftruncate(fd, CONTROL_BYTES)
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
            f"--uid={os.getuid()}",
            "-p",
            "MemoryAccounting=yes",
            "-p",
            f"CPUAffinity={prep_cpu}",
            str(worker),
            "--shared",
            str(ctl),
            "--max-pages",
            token,
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
        _set(unit["mm"], OFF_STOP, 1)
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


def _measured_touch(
    unit: dict[str, Any],
    stock_cpu: int,
    page_size: int,
) -> dict[str, Any]:
    _set(unit["mm"], OFF_MODE, 2)
    _set(unit["mm"], OFF_TARGET, stock_cpu)
    _set(unit["mm"], OFF_DONE, 0)
    _set(unit["mm"], OFF_ERROR, 0)

    vmpte_pre = _vmpte_kib(unit["pid"])
    pagetables_pre = _memory_stat(unit["cg"], "pagetables")
    before = _current(unit["cg"])

    _set(unit["mm"], OFF_GO, 1)
    _wait(lambda: _u32(unit["mm"], OFF_DONE) == 1)

    after = _current(unit["cg"])
    vmpte_post = _vmpte_kib(unit["pid"])
    pagetables_post = _memory_stat(unit["cg"], "pagetables")

    delta_pages = (after - before) / page_size
    return {
        "delta_pages": delta_pages,
        "q64_pass": None,
        "cpu": _u32(unit["mm"], OFF_OBS_CPU),
        "worker_error": _u32(unit["mm"], OFF_ERROR),
        "touched": _u32(unit["mm"], OFF_TOUCHED),
        "vmpte_pre_kib": vmpte_pre,
        "vmpte_post_kib": vmpte_post,
        "vmpte_delta_kib": vmpte_post - vmpte_pre,
        "pagetables_pre_bytes": pagetables_pre,
        "pagetables_post_bytes": pagetables_post,
        "pagetables_delta_bytes": pagetables_post - pagetables_pre,
    }


def classify_biopsy(row: dict[str, Any]) -> str | None:
    if not row.get("biopsy_performed"):
        return None
    if not row.get("biopsy_valid"):
        return "INVALID"
    second_vmpte = row.get("second_vmpte_delta_kib")
    if isinstance(second_vmpte, (int, float)) and second_vmpte > 0:
        return "PTE_BOUNDARY"
    if not row.get("second_q64_pass"):
        return "OTHER"
    first_vmpte = row.get("first_vmpte_delta_kib")
    if first_vmpte == 0 and second_vmpte == 0:
        return "R1_CANDIDATE"
    if (
        isinstance(first_vmpte, (int, float))
        and first_vmpte > 0
        and second_vmpte == 0
    ):
        return "R2_CANDIDATE"
    return "OTHER"


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
    token = str(arm["token"])
    name = (
        f"fr-m5gg0-{os.getenv('GITHUB_RUN_ID', 'local')}"
        f"-{block}-{identity}"
    )
    unit = _start(
        worker,
        root,
        name,
        prep_cpu,
        token,
    )
    page_size = int(spec["required_page_size"])
    try:
        pre = _current(unit["cg"])
        pre_pages = pre / page_size
        stratum = (
            "LOW"
            if pre_pages <= spec["low_threshold_pages"]
            else "HIGH"
        )

        t0 = time.monotonic_ns()
        os.sched_setaffinity(unit["pid"], {stock_cpu})
        _wait_cpu(unit["pid"], stock_cpu)
        mid = _current(unit["cg"])
        migration_delta = (mid - pre) / page_size
        affinity_to_go_us = (
            time.monotonic_ns() - t0
        ) / 1000.0

        first = _measured_touch(
            unit,
            stock_cpu,
            page_size,
        )
        first["q64_pass"] = _q64(
            spec,
            first["delta_pages"],
        )
        first_valid = (
            first["cpu"] == stock_cpu
            and first["worker_error"] == 0
            and first["touched"] == 1
        )
        zero_capture = (
            first_valid
            and stratum == "LOW"
            and _zero(first["delta_pages"])
        )

        biopsy_performed = False
        biopsy_valid: bool | None = None
        second: dict[str, Any] | None = None
        if zero_capture:
            biopsy_performed = True
            second = _measured_touch(
                unit,
                stock_cpu,
                page_size,
            )
            second["q64_pass"] = _q64(
                spec,
                second["delta_pages"],
            )
            biopsy_valid = (
                second["cpu"] == stock_cpu
                and second["worker_error"] == 0
                and second["touched"] == 2
            )

        row: dict[str, Any] = {
            "experiment_id": spec["experiment_id"],
            "block": block,
            "identity": identity,
            "arm_id": arm["id"],
            "argv_token": token,
            "capacity_pages": int(arm["capacity_pages"]),
            "prep_cpu": prep_cpu,
            "stock_cpu": stock_cpu,
            "pre_current_pages": pre_pages,
            "stratum": stratum,
            "migration_delta_pages": migration_delta,
            "affinity_to_go_us": affinity_to_go_us,
            "first_touch_delta_pages": first["delta_pages"],
            "first_q64_pass": first["q64_pass"],
            "zero_capture": zero_capture,
            "cpu_match": first["cpu"] == stock_cpu,
            "worker_error": first["worker_error"],
            "valid": first_valid,
            "first_vmpte_pre_kib": first["vmpte_pre_kib"],
            "first_vmpte_post_kib": first["vmpte_post_kib"],
            "first_vmpte_delta_kib": first["vmpte_delta_kib"],
            "first_pagetables_pre_bytes": first[
                "pagetables_pre_bytes"
            ],
            "first_pagetables_post_bytes": first[
                "pagetables_post_bytes"
            ],
            "first_pagetables_delta_bytes": first[
                "pagetables_delta_bytes"
            ],
            "biopsy_performed": biopsy_performed,
            "biopsy_valid": biopsy_valid,
            "second_touch_delta_pages": (
                None if second is None else second["delta_pages"]
            ),
            "second_q64_pass": (
                None if second is None else second["q64_pass"]
            ),
            "second_cpu_match": (
                None
                if second is None
                else second["cpu"] == stock_cpu
            ),
            "second_worker_error": (
                None
                if second is None
                else second["worker_error"]
            ),
            "second_vmpte_delta_kib": (
                None
                if second is None
                else second["vmpte_delta_kib"]
            ),
            "second_pagetables_delta_bytes": (
                None
                if second is None
                else second["pagetables_delta_bytes"]
            ),
        }
        row["biopsy_class"] = classify_biopsy(row)
        return row
    finally:
        _stop(unit)


def _sum(rows: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(rows)
    zeros = sum(bool(row["zero_capture"]) for row in rows)
    q64 = sum(bool(row["first_q64_pass"]) for row in rows)
    other = sum(
        not row["zero_capture"]
        and not row["first_q64_pass"]
        for row in rows
    )
    return {
        "n": n,
        "zero_captures": zeros,
        "zero_rate": zeros / n if n else None,
        "q64": q64,
        "other_nonzero_nonq64": other,
    }


def _pool(
    rows: list[dict[str, Any]],
    arm_ids: set[str],
) -> dict[str, Any]:
    return _sum(
        [row for row in rows if row["arm_id"] in arm_ids]
    )


def _contrast(
    a: dict[str, Any],
    b: dict[str, Any],
    *,
    a_name: str,
    b_name: str,
) -> dict[str, Any]:
    if not a["n"] or not b["n"]:
        return {
            "a": a_name,
            "b": b_name,
            "odds_ratio": None,
            "two_sided_p": None,
            "risk_difference": None,
        }
    a_nonzero = a["n"] - a["zero_captures"]
    b_nonzero = b["n"] - b["zero_captures"]
    test = fisher_exact(
        [
            [a["zero_captures"], a_nonzero],
            [b["zero_captures"], b_nonzero],
        ],
        alternative="two-sided",
    )
    return {
        "a": a_name,
        "b": b_name,
        "odds_ratio": float(test.statistic),
        "two_sided_p": float(test.pvalue),
        "risk_difference": a["zero_rate"] - b["zero_rate"],
    }


def analyze(
    spec: dict[str, Any],
    trials: list[dict[str, Any]],
) -> dict[str, Any]:
    expected = {
        (block, identity)
        for block in range(spec["runner_blocks"])
        for identity in range(spec["identities_per_block"])
    }
    got = {
        (int(row["block"]), int(row["identity"]))
        for row in trials
    }
    if got != expected:
        raise ValueError("incomplete matrix")

    arm_ids = [str(arm["id"]) for arm in spec["arms"]]
    valid_low = [
        row
        for row in trials
        if row["valid"] and row["stratum"] == "LOW"
    ]
    by_arm = {
        arm: _sum(
            [row for row in valid_low if row["arm_id"] == arm]
        )
        for arm in arm_ids
    }

    canonical = _pool(valid_low, {"C8", "C9"})
    padded = _pool(valid_low, {"P8", "P9"})
    high = _pool(valid_low, {"H10", "H32"})

    argv = _contrast(
        padded,
        canonical,
        a_name="PADDED_8_9",
        b_name="CANONICAL_8_9",
    )
    capacity = _contrast(
        high,
        padded,
        a_name="HIGH_10_32",
        b_name="PADDED_8_9",
    )

    pc = canonical["zero_rate"]
    pp = padded["zero_rate"]
    ph = high["zero_rate"]
    if pc is None or pp is None or ph is None:
        direction = "UNRESOLVED"
    elif pp > pc and abs(pp - ph) < abs(pc - ph):
        direction = "ARGV_LIKE_DIRECTION"
    elif ph > pp and abs(pp - pc) <= abs(pp - ph):
        direction = "CAPACITY_LIKE_DIRECTION"
    else:
        direction = "MIXED_DIRECTION"

    pte_zero = [
        row
        for row in valid_low
        if row["first_vmpte_delta_kib"] == 0
    ]
    pte_grow = [
        row
        for row in valid_low
        if row["first_vmpte_delta_kib"] > 0
    ]
    pte = {
        "no_growth": _sum(pte_zero),
        "growth": _sum(pte_grow),
    }
    pte["growth_vs_no_growth"] = _contrast(
        pte["growth"],
        pte["no_growth"],
        a_name="VMPTE_GROWTH",
        b_name="VMPTE_NO_GROWTH",
    )

    biopsy = Counter(
        row.get("biopsy_class")
        for row in valid_low
        if row.get("biopsy_performed")
    )
    cpu_mismatches = sum(
        not row["cpu_match"]
        for row in trials
    )

    return {
        "experiment_id": spec["experiment_id"],
        "stage": spec["stage"],
        "interpretation": direction,
        "by_arm": by_arm,
        "pooled": {
            "canonical_8_9": canonical,
            "padded_8_9": padded,
            "high_10_32": high,
        },
        "argv_width_contrast": argv,
        "capacity_survival_contrast": capacity,
        "pte_receipt": pte,
        "biopsy_classes": dict(
            sorted(
                (str(key), int(value))
                for key, value in biopsy.items()
            )
        ),
        "cpu_mismatches": cpu_mismatches,
        "trials": trials,
    }


def environment_receipt(
    worker: Path,
    cpus: list[int],
) -> dict[str, Any]:
    thp_root = Path(
        "/sys/kernel/mm/transparent_hugepage"
    )
    thp: dict[str, str] = {}
    if thp_root.exists():
        enabled = thp_root / "enabled"
        if enabled.exists():
            thp["enabled"] = enabled.read_text(
                encoding="utf-8"
            ).strip()
        for path in sorted(
            thp_root.glob("hugepages-*/enabled")
        ):
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
        "runner_image": os.getenv("ImageOS"),
        "runner_name": os.getenv("RUNNER_NAME"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(
        dest="cmd",
        required=True,
    )

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
            raise RuntimeError("G0 requires at least 3 CPUs")
        controller, prep_cpu, stock_cpu = (
            cpus[0],
            cpus[1],
            cpus[-1],
        )
        os.sched_setaffinity(0, {controller})
        root = Path(args.out_root)
        root.mkdir(parents=True, exist_ok=True)
        worker = Path(args.worker).resolve()

        receipt = environment_receipt(worker, cpus)
        (root / "environment.json").write_text(
            json.dumps(receipt, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )

        for identity in range(
            spec["identities_per_block"]
        ):
            trial_root = root / f"id-{identity}"
            trial_root.mkdir(
                parents=True,
                exist_ok=True,
            )
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
                json.dumps(
                    row,
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
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
        json.dumps(result, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "interpretation": result[
                    "interpretation"
                ],
                "by_arm": result["by_arm"],
                "argv_width_contrast": result[
                    "argv_width_contrast"
                ],
                "capacity_survival_contrast": result[
                    "capacity_survival_contrast"
                ],
                "pte_receipt": result["pte_receipt"],
                "biopsy_classes": result[
                    "biopsy_classes"
                ],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
