from __future__ import annotations

import argparse
import json
import mmap
import os
import struct
import subprocess
import time
from pathlib import Path
from typing import Any

from scipy.stats import fisher_exact


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


def _run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True, check=check)


def _u32(mm: mmap.mmap, off: int) -> int:
    return struct.unpack_from("<I", mm, off)[0]


def _set_u32(mm: mmap.mmap, off: int, value: int) -> None:
    struct.pack_into("<I", mm, off, int(value))


def _wait(pred, timeout: float = 10.0) -> None:
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if pred():
            return
        time.sleep(0.001)
    raise TimeoutError("shared-latch timeout")


def _proc_cpu(pid: int) -> int:
    text = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
    tail = text[text.rfind(")") + 2 :].split()
    return int(tail[36])


def _wait_cpu(pid: int, cpu: int, timeout: float = 5.0) -> None:
    _wait(lambda: _proc_cpu(pid) == cpu, timeout=timeout)


def _current(cg: Path) -> int:
    return int((cg / "memory.current").read_text(encoding="utf-8").strip())


def _start(worker: Path, root: Path, name: str, prep_cpu: int) -> dict[str, Any]:
    shared = root / f"{name}.ctl"
    fd = os.open(shared, os.O_RDWR | os.O_CREAT | os.O_TRUNC, 0o600)
    os.ftruncate(fd, CONTROL_BYTES)
    mm = mmap.mmap(fd, CONTROL_BYTES, access=mmap.ACCESS_WRITE)

    uid = os.getuid()
    _run([
        "sudo", "systemd-run", "--quiet", "--collect",
        f"--unit={name}",
        f"--uid={uid}",
        "-p", "MemoryAccounting=yes",
        "-p", f"CPUAffinity={prep_cpu}",
        str(worker),
        "--shared", str(shared),
        "--max-pages", "8",
    ])

    _wait(lambda: _u32(mm, OFF_READY) == 1)

    pid = int(_run([
        "systemctl", "show", f"{name}.service",
        "--property=MainPID", "--value",
    ]).stdout.strip())
    if pid <= 0:
        raise RuntimeError("invalid MainPID")

    cg_text = _run([
        "systemctl", "show", f"{name}.service",
        "--property=ControlGroup", "--value",
    ]).stdout.strip()
    cg = Path("/sys/fs/cgroup") / cg_text.lstrip("/")

    _wait_cpu(pid, prep_cpu)
    if _u32(mm, OFF_TOUCHED) != 0:
        raise RuntimeError("worker touched measured page before experiment")

    return {"name": name, "pid": pid, "cg": cg, "fd": fd, "mm": mm}


def _stop(u: dict[str, Any]) -> None:
    try:
        _set_u32(u["mm"], OFF_STOP, 1)
    except Exception:
        pass
    _run(["sudo", "systemctl", "stop", u["name"] + ".service"], check=False)
    try:
        u["mm"].close()
        os.close(u["fd"])
    except Exception:
        pass


def _is_q64(spec: dict[str, Any], delta_pages: float) -> bool:
    return float(spec["q64_min_pages"]) <= delta_pages <= float(spec["q64_max_pages"])


def run_probe(
    spec: dict[str, Any],
    *,
    worker: Path,
    root: Path,
    block: int,
    arm: str,
    identity: int,
    prep_cpu: int,
    stock_cpu: int,
) -> dict[str, Any]:
    runid = os.getenv("GITHUB_RUN_ID", "local")
    name = f"fr-m5e-{runid}-{block}-{arm}-{identity}"
    u = _start(worker, root, name, prep_cpu)
    page = int(spec["required_page_size"])
    target_cpu = prep_cpu if arm == "local_p" else stock_cpu
    try:
        pre = _current(u["cg"])
        pre_pages = pre / page
        stratum = "LOW" if pre_pages <= float(spec["low_threshold_pages"]) else "HIGH"

        affinity_start = time.monotonic_ns()
        os.sched_setaffinity(u["pid"], {target_cpu})
        _wait_cpu(u["pid"], target_cpu)
        mid = _current(u["cg"])

        _set_u32(u["mm"], OFF_MODE, 2)
        _set_u32(u["mm"], OFF_TARGET, target_cpu)
        _set_u32(u["mm"], OFF_DONE, 0)
        _set_u32(u["mm"], OFF_ERROR, 0)
        affinity_to_go_us = (time.monotonic_ns() - affinity_start) / 1000.0
        _set_u32(u["mm"], OFF_GO, 1)

        _wait(lambda: _u32(u["mm"], OFF_DONE) == 1)
        post = _current(u["cg"])

        migration_delta = (mid - pre) / page
        touch_delta = (post - mid) / page
        observed = _u32(u["mm"], OFF_OBS_CPU)
        worker_error = _u32(u["mm"], OFF_ERROR)
        touched = _u32(u["mm"], OFF_TOUCHED)
        cpu_match = observed == target_cpu
        valid = worker_error == 0 and touched == 1 and cpu_match

        return {
            "experiment_id": spec["experiment_id"],
            "block": block,
            "arm": arm,
            "identity": identity,
            "prep_cpu": prep_cpu,
            "stock_cpu": stock_cpu,
            "target_cpu": target_cpu,
            "pre_current_bytes": pre,
            "pre_current_pages": pre_pages,
            "stratum": stratum,
            "mid_current_bytes": mid,
            "post_current_bytes": post,
            "migration_delta_pages": migration_delta,
            "touch_delta_pages": touch_delta,
            "q64_pass": _is_q64(spec, touch_delta),
            "affinity_to_go_us": affinity_to_go_us,
            "observed_cpu": observed,
            "cpu_match": cpu_match,
            "worker_error": worker_error,
            "touched": touched,
            "valid": valid,
        }
    finally:
        _stop(u)


def _success_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    valid = [r for r in rows if r["valid"]]
    successes = sum(bool(r["q64_pass"]) for r in valid)
    n = len(valid)
    return {
        "valid_n": n,
        "q64_successes": successes,
        "failures": n - successes,
        "success_rate": successes / n if n else None,
        "zero_delta": sum(float(r["touch_delta_pages"]) == 0.0 for r in valid),
        "other_delta": sum(
            (not bool(r["q64_pass"])) and float(r["touch_delta_pages"]) != 0.0
            for r in valid
        ),
    }


def _dwell_quartiles(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    valid = sorted(
        [r for r in rows if r["valid"]],
        key=lambda r: float(r["affinity_to_go_us"]),
    )
    out = []
    n = len(valid)
    if not n:
        return out
    for q in range(4):
        lo = q * n // 4
        hi = (q + 1) * n // 4
        chunk = valid[lo:hi]
        if not chunk:
            continue
        out.append({
            "quartile": q + 1,
            "n": len(chunk),
            "latency_us_min": float(chunk[0]["affinity_to_go_us"]),
            "latency_us_max": float(chunk[-1]["affinity_to_go_us"]),
            "q64_successes": sum(bool(r["q64_pass"]) for r in chunk),
            "success_rate": sum(bool(r["q64_pass"]) for r in chunk) / len(chunk),
        })
    return out


def analyze_trials(spec: dict[str, Any], trials: list[dict[str, Any]]) -> dict[str, Any]:
    blocks = int(spec["runner_blocks"])
    nident = int(spec["identities_per_arm"])
    expected = {
        (b, arm, i)
        for b in range(blocks)
        for arm in spec["arms"]
        for i in range(nident)
    }
    got = {(int(t["block"]), t["arm"], int(t["identity"])) for t in trials}
    if got != expected:
        raise ValueError("incomplete trial matrix")

    threshold = float(spec["low_threshold_pages"])
    threshold_mismatches = [
        t for t in trials
        if t["stratum"] != ("LOW" if float(t["pre_current_pages"]) <= threshold else "HIGH")
    ]
    if threshold_mismatches:
        raise ValueError("stratum label mismatch")

    cpu_mismatches = sum(not bool(t["cpu_match"]) for t in trials)
    valid = [t for t in trials if t["valid"]]
    low = [t for t in valid if t["stratum"] == "LOW"]
    high = [t for t in valid if t["stratum"] == "HIGH"]

    low_s = _success_summary(low)
    high_s = _success_summary(high)

    table = [
        [low_s["q64_successes"], low_s["failures"]],
        [high_s["q64_successes"], high_s["failures"]],
    ]
    fisher = fisher_exact(table, alternative="greater")

    by_arm = {}
    for arm in spec["arms"]:
        rows = [t for t in valid if t["arm"] == arm]
        by_arm[arm] = {
            "overall": _success_summary(rows),
            "LOW": _success_summary([t for t in rows if t["stratum"] == "LOW"]),
            "HIGH": _success_summary([t for t in rows if t["stratum"] == "HIGH"]),
            "dwell_quartiles": _dwell_quartiles(rows),
            "migration_delta_sequence": [float(t["migration_delta_pages"]) for t in rows],
        }

    locality = {}
    for stratum in ["LOW", "HIGH"]:
        local = [t for t in valid if t["arm"] == "local_p" and t["stratum"] == stratum]
        remote = [t for t in valid if t["arm"] == "remote_s" and t["stratum"] == stratum]
        ls = _success_summary(local)
        rs = _success_summary(remote)
        if ls["valid_n"] and rs["valid_n"]:
            f = fisher_exact(
                [
                    [ls["q64_successes"], ls["failures"]],
                    [rs["q64_successes"], rs["failures"]],
                ],
                alternative="two-sided",
            )
            p = float(f.pvalue)
            rd = float(ls["success_rate"] - rs["success_rate"])
        else:
            p = None
            rd = None
        locality[stratum] = {
            "local_p": ls,
            "remote_s": rs,
            "risk_difference_local_minus_remote": rd,
            "fisher_two_sided_p": p,
        }

    low_arm_ok = all(
        by_arm[arm]["LOW"]["valid_n"] > 0
        and by_arm[arm]["LOW"]["success_rate"] >= float(spec["support_low_per_arm_success_rate"])
        for arm in spec["arms"]
    )

    support = (
        low_s["valid_n"] >= int(spec["support_min_low_n"])
        and low_s["success_rate"] >= float(spec["support_low_success_rate"])
        and low_arm_ok
        and high_s["valid_n"] > 0
        and high_s["success_rate"] <= float(spec["support_high_max_success_rate"])
        and float(fisher.pvalue) < float(spec["support_fisher_p_max"])
        and cpu_mismatches == 0
    )

    rate_diff = (
        low_s["success_rate"] - high_s["success_rate"]
        if low_s["success_rate"] is not None and high_s["success_rate"] is not None
        else None
    )
    reject = (
        (low_s["valid_n"] > 0 and low_s["success_rate"] < float(spec["reject_low_success_rate"]))
        or (
            low_s["valid_n"] >= int(spec["reject_min_each_stratum_n"])
            and high_s["valid_n"] >= int(spec["reject_min_each_stratum_n"])
            and rate_diff is not None
            and abs(rate_diff) < float(spec["reject_max_rate_difference"])
        )
    )

    decision = (
        "SUPPORT_BASELINE_GATE" if support
        else "REJECT_BASELINE_GATE" if reject
        else "INCONCLUSIVE"
    )

    block_rows = []
    for b in range(blocks):
        br = {"block": b}
        for arm in spec["arms"]:
            rows = [t for t in valid if int(t["block"]) == b and t["arm"] == arm]
            br[arm] = {
                "LOW": _success_summary([t for t in rows if t["stratum"] == "LOW"]),
                "HIGH": _success_summary([t for t in rows if t["stratum"] == "HIGH"]),
            }
        block_rows.append(br)

    return {
        "experiment_id": spec["experiment_id"],
        "decision": decision,
        "threshold_pages": threshold,
        "cpu_mismatches": cpu_mismatches,
        "LOW": low_s,
        "HIGH": high_s,
        "low_minus_high_success_rate": rate_diff,
        "primary_fisher": {
            "odds_ratio": float(fisher.statistic),
            "one_sided_p": float(fisher.pvalue),
        },
        "by_arm": by_arm,
        "cpu_locality": locality,
        "blocks": block_rows,
        "trials": trials,
        "inference_boundary": (
            "Hosted prospective baseline-predictor validation only; "
            "does not estimate memcg slot capacity."
        ),
    }


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

    a = p.parse_args()
    spec = load_spec(a.spec)

    if a.cmd == "run-block":
        cpus = sorted(os.sched_getaffinity(0))
        if len(cpus) < 3:
            raise RuntimeError("requires >=3 CPUs")
        control, prep, stock = cpus[0], cpus[1], cpus[-1]
        if len({control, prep, stock}) < 3:
            raise RuntimeError("CPU roles must be distinct")
        os.sched_setaffinity(0, {control})

        root = Path(a.out_root)
        root.mkdir(parents=True, exist_ok=True)
        (root / "cpu-receipt.json").write_text(
            json.dumps({
                "control_cpu": control,
                "prep_cpu": prep,
                "stock_cpu": stock,
            }, indent=2) + "\n",
            encoding="utf-8",
        )

        arms = ["local_p", "remote_s"] if a.block % 2 == 0 else ["remote_s", "local_p"]
        for i in range(int(spec["identities_per_arm"])):
            for arm in arms:
                ar = root / arm / f"id-{i}"
                ar.mkdir(parents=True, exist_ok=True)
                trial = run_probe(
                    spec,
                    worker=Path(a.worker).resolve(),
                    root=ar,
                    block=a.block,
                    arm=arm,
                    identity=i,
                    prep_cpu=prep,
                    stock_cpu=stock,
                )
                (root / f"trial-{a.block}-{arm}-{i}.json").write_text(
                    json.dumps(trial, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
        return

    trials = [
        json.loads(x.read_text(encoding="utf-8"))
        for x in sorted(Path(a.input_root).rglob("trial-*.json"))
    ]
    result = analyze_trials(spec, trials)
    out = Path(a.json_out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "decision": result["decision"],
        "LOW": result["LOW"],
        "HIGH": result["HIGH"],
        "p": result["primary_fisher"]["one_sided_p"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
