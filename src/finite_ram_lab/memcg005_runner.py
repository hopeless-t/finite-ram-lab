from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any

from .memcg005_calibrated_k7 import analyze_trials, load_spec


def _run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True, check=check)


def _lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines() if path.exists() else []


def _wait(predicate, timeout: float = 10.0) -> None:
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if predicate():
            return
        time.sleep(0.02)
    raise TimeoutError("worker receipt timeout")


def _start(worker: Path, root: Path, name: str, cpu: int) -> dict[str, Any]:
    fifo = root / f"{name}.fifo"
    status = root / f"{name}.status"
    if fifo.exists():
        fifo.unlink()
    os.mkfifo(fifo)
    status.write_text("", encoding="utf-8")

    _run([
        "sudo", "systemd-run", "--quiet", "--collect",
        f"--unit={name}",
        "-p", "MemoryAccounting=yes",
        "-p", f"CPUAffinity={cpu}",
        str(worker),
        "--control", str(fifo),
        "--status", str(status),
        "--max-pages", "512",
    ])

    _wait(lambda: any(x.startswith("READY ") for x in _lines(status)))
    ready = next(x for x in _lines(status) if x.startswith("READY "))
    if "touched=0" not in ready:
        raise RuntimeError("worker not zero-touch at READY")
    cpu_field = next(x for x in ready.split() if x.startswith("cpu="))
    if int(cpu_field.split("=", 1)[1]) != cpu:
        raise RuntimeError("worker READY on wrong CPU")

    show = _run([
        "systemctl", "show", f"{name}.service",
        "--property=ControlGroup", "--value",
    ]).stdout.strip()

    return {
        "name": name,
        "fifo": fifo,
        "status": status,
        "cg": Path("/sys/fs/cgroup") / show.lstrip("/"),
        "ready": ready,
    }


def _send(u: dict[str, Any], cmd: str, receipt_prefix: str | None = None) -> None:
    before = 0
    if receipt_prefix:
        before = sum(x.startswith(receipt_prefix) for x in _lines(u["status"]))
    with u["fifo"].open("w", encoding="utf-8") as fh:
        fh.write(cmd + "\n")
        fh.flush()
    if receipt_prefix:
        _wait(lambda: sum(x.startswith(receipt_prefix) for x in _lines(u["status"])) > before)


def _cur(u: dict[str, Any]) -> int:
    return int((u["cg"] / "memory.current").read_text(encoding="utf-8").strip())


def _touch_delta(u: dict[str, Any], page_size: int) -> tuple[float, int, int]:
    pre = _cur(u)
    _send(u, "TOUCH_ONE", "TOUCH ")
    post = _cur(u)
    return (post - pre) / page_size, pre, post


def _touch_n(u: dict[str, Any], n: int) -> dict[str, Any]:
    before_lines = [x for x in _lines(u["status"]) if x.startswith("BATCH ")]
    _send(u, f"TOUCH_N {n}", "BATCH ")
    after_lines = [x for x in _lines(u["status"]) if x.startswith("BATCH ")]
    if len(after_lines) <= len(before_lines):
        raise RuntimeError("missing BATCH receipt")
    return {"receipt": after_lines[-1]}


def _stop(u: dict[str, Any]) -> None:
    try:
        _send(u, "STOP")
    except Exception:
        pass
    _run(["sudo", "systemctl", "stop", u["name"] + ".service"], check=False)


def _is_q64(spec: dict[str, Any], delta: float) -> bool:
    return float(spec["q64_min_pages"]) <= delta <= float(spec["q64_max_pages"])


def _normalize_empty(
    spec: dict[str, Any],
    u: dict[str, Any],
    page_size: int,
) -> dict[str, Any]:
    calibration_touch = None
    calibration_delta = None
    for i in range(1, int(spec["max_prime_touches"]) + 1):
        d, pre, post = _touch_delta(u, page_size)
        if _is_q64(spec, d):
            calibration_touch = i
            calibration_delta = d
            calibration_pre = pre
            calibration_post = post
            break
    if calibration_touch is None:
        return {
            "ok": False,
            "reason": "NO_CALIBRATION_Q64",
        }

    before = _cur(u)
    batch = _touch_n(u, int(spec["normalize_consume_touches"]))
    after = _cur(u)

    return {
        "ok": True,
        "calibration_touch": calibration_touch,
        "calibration_delta_pages": calibration_delta,
        "calibration_pre_current_bytes": calibration_pre,
        "calibration_post_current_bytes": calibration_post,
        "consume63_delta_pages": (after - before) / page_size,
        "batch_receipt": batch["receipt"],
    }


def _measured_insert(
    spec: dict[str, Any],
    u: dict[str, Any],
    page_size: int,
) -> dict[str, Any]:
    d, pre, post = _touch_delta(u, page_size)
    return {
        "delta_pages": d,
        "pre_current_bytes": pre,
        "post_current_bytes": post,
        "q64_verified": _is_q64(spec, d),
    }


def _target_state(spec: dict[str, Any], delta: float) -> str:
    if _is_q64(spec, delta):
        return "ABSENT"
    if abs(delta) < float(spec["present_abs_lt_pages"]):
        return "PRESENT"
    return "AMBIGUOUS"


def run_replica(
    spec: dict[str, Any],
    *,
    block: int,
    m: int,
    worker: Path,
    root: Path,
    stock_cpu: int,
) -> dict[str, Any]:
    run_id = os.getenv("GITHUB_RUN_ID", "local")
    prefix = f"fr-m5-{run_id}-{block}-m{m}"
    units: list[dict[str, Any]] = []

    try:
        roles: list[tuple[str, int]] = (
            [("w", i) for i in range(int(spec["wash_count"]))]
            + [("t", 0)]
            + [("c", i) for i in range(1, int(spec["max_challengers"]) + 1)]
        )

        by_key: dict[str, dict[str, Any]] = {}
        for role, idx in roles:
            name = f"{prefix}-{role}{idx}"
            u = _start(worker, root, name, stock_cpu)
            units.append(u)
            by_key[f"{role}{idx}"] = u

        page_size = int(spec["required_page_size"])
        normalization: dict[str, Any] = {}
        for role, idx in roles:
            key = f"{role}{idx}"
            normalization[key] = _normalize_empty(spec, by_key[key], page_size)
            if not normalization[key]["ok"]:
                return {
                    "experiment_id": spec["experiment_id"],
                    "block": block,
                    "m": m,
                    "valid_state": False,
                    "invalid_reason": f"{key}:{normalization[key]['reason']}",
                    "normalization": normalization,
                    "insertions": [],
                    "target_probe": None,
                    "target_state": "INVALID",
                }

        insertions = []

        for i in range(int(spec["wash_count"])):
            key = f"w{i}"
            ins = _measured_insert(spec, by_key[key], page_size)
            insertions.append({"identity": key, **ins})
            if not ins["q64_verified"]:
                return {
                    "experiment_id": spec["experiment_id"],
                    "block": block,
                    "m": m,
                    "valid_state": False,
                    "invalid_reason": f"{key}:INSERT_NOT_Q64",
                    "normalization": normalization,
                    "insertions": insertions,
                    "target_probe": None,
                    "target_state": "INVALID",
                }

        target_insert = _measured_insert(spec, by_key["t0"], page_size)
        insertions.append({"identity": "t0", **target_insert})
        if not target_insert["q64_verified"]:
            return {
                "experiment_id": spec["experiment_id"],
                "block": block,
                "m": m,
                "valid_state": False,
                "invalid_reason": "t0:INSERT_NOT_Q64",
                "normalization": normalization,
                "insertions": insertions,
                "target_probe": None,
                "target_state": "INVALID",
            }

        for i in range(1, m + 1):
            key = f"c{i}"
            ins = _measured_insert(spec, by_key[key], page_size)
            insertions.append({"identity": key, **ins})
            if not ins["q64_verified"]:
                return {
                    "experiment_id": spec["experiment_id"],
                    "block": block,
                    "m": m,
                    "valid_state": False,
                    "invalid_reason": f"{key}:INSERT_NOT_Q64",
                    "normalization": normalization,
                    "insertions": insertions,
                    "target_probe": None,
                    "target_state": "INVALID",
                }

        d, pre, post = _touch_delta(by_key["t0"], page_size)
        state = _target_state(spec, d)
        valid = state in {"PRESENT", "ABSENT"}

        return {
            "experiment_id": spec["experiment_id"],
            "block": block,
            "m": m,
            "valid_state": valid,
            "invalid_reason": None if valid else "TARGET_PROBE_AMBIGUOUS",
            "normalization": normalization,
            "insertions": insertions,
            "target_probe": {
                "delta_pages": d,
                "pre_current_bytes": pre,
                "post_current_bytes": post,
            },
            "target_state": state,
        }
    finally:
        for u in reversed(units):
            _stop(u)


def main() -> None:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    rb = sub.add_parser("run-block")
    rb.add_argument("--spec", required=True)
    rb.add_argument("--block", type=int, required=True)
    rb.add_argument("--worker", required=True)
    rb.add_argument("--out-root", required=True)

    ag = sub.add_parser("aggregate")
    ag.add_argument("--spec", required=True)
    ag.add_argument("--input-root", required=True)
    ag.add_argument("--json-out", required=True)

    args = p.parse_args()
    spec = load_spec(args.spec)

    if args.cmd == "run-block":
        cpus = sorted(os.sched_getaffinity(0))
        if len(cpus) < 2:
            raise RuntimeError("requires >=2 CPUs")
        control_cpu, stock_cpu = cpus[0], cpus[1]
        os.sched_setaffinity(0, {control_cpu})

        root = Path(args.out_root)
        root.mkdir(parents=True, exist_ok=True)
        (root / "cpu-receipt.json").write_text(
            json.dumps({
                "control_cpu": control_cpu,
                "stock_cpu": stock_cpu,
                "orchestrator_affinity": sorted(os.sched_getaffinity(0)),
            }, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        for m in [int(x) for x in spec["tested_m"]]:
            replica_root = root / f"m-{m}"
            replica_root.mkdir(parents=True, exist_ok=True)
            trial = run_replica(
                spec,
                block=args.block,
                m=m,
                worker=Path(args.worker).resolve(),
                root=replica_root,
                stock_cpu=stock_cpu,
            )
            (root / f"trial-{args.block}-m{m}.json").write_text(
                json.dumps(trial, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        return

    trials = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(Path(args.input_root).rglob("trial-*-m*.json"))
    ]
    result = analyze_trials(spec, trials)
    out = Path(args.json_out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "decision": result["decision"],
        "support_blocks": result["support_blocks"],
        "complete_valid_blocks": result["complete_valid_blocks"],
        "best_k_by_errors": result["best_k_by_errors"],
        "best_k_by_mdl": result["best_k_by_mdl"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
