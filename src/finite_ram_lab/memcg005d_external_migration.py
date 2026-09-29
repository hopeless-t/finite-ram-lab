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

from scipy.stats import beta, binomtest


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


def _start(
    *,
    worker: Path,
    root: Path,
    name: str,
    prep_cpu: int,
) -> dict[str, Any]:
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

    pid_text = _run([
        "systemctl", "show", f"{name}.service",
        "--property=MainPID", "--value",
    ]).stdout.strip()
    pid = int(pid_text)
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

    return {
        "name": name,
        "pid": pid,
        "cg": cg,
        "shared": shared,
        "fd": fd,
        "mm": mm,
    }


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


def _is_q64(spec: dict[str, Any], d: float) -> bool:
    return float(spec["q64_min_pages"]) <= d <= float(spec["q64_max_pages"])


def _arm_self(
    spec: dict[str, Any],
    *,
    u: dict[str, Any],
    stock_cpu: int,
) -> dict[str, Any]:
    page = int(spec["required_page_size"])
    pre = _current(u["cg"])
    _set_u32(u["mm"], OFF_MODE, 1)
    _set_u32(u["mm"], OFF_TARGET, stock_cpu)
    _set_u32(u["mm"], OFF_DONE, 0)
    _set_u32(u["mm"], OFF_ERROR, 0)
    _set_u32(u["mm"], OFF_GO, 1)
    _wait(lambda: _u32(u["mm"], OFF_DONE) == 1)
    post = _current(u["cg"])
    d = (post - pre) / page
    return {
        "pre_current_bytes": pre,
        "mid_current_bytes": None,
        "post_current_bytes": post,
        "migration_delta_pages": None,
        "touch_delta_pages": d,
        "delta_pages": d,
        "q64_pass": _is_q64(spec, d),
        "observed_cpu": _u32(u["mm"], OFF_OBS_CPU),
        "worker_error": _u32(u["mm"], OFF_ERROR),
        "touched": _u32(u["mm"], OFF_TOUCHED),
    }


def _arm_external(
    spec: dict[str, Any],
    *,
    u: dict[str, Any],
    stock_cpu: int,
) -> dict[str, Any]:
    page = int(spec["required_page_size"])
    pre = _current(u["cg"])
    os.sched_setaffinity(u["pid"], {stock_cpu})
    _wait_cpu(u["pid"], stock_cpu)
    mid = _current(u["cg"])

    _set_u32(u["mm"], OFF_MODE, 2)
    _set_u32(u["mm"], OFF_TARGET, stock_cpu)
    _set_u32(u["mm"], OFF_DONE, 0)
    _set_u32(u["mm"], OFF_ERROR, 0)
    _set_u32(u["mm"], OFF_GO, 1)
    _wait(lambda: _u32(u["mm"], OFF_DONE) == 1)
    post = _current(u["cg"])

    migration_delta = (mid - pre) / page
    touch_delta = (post - mid) / page
    return {
        "pre_current_bytes": pre,
        "mid_current_bytes": mid,
        "post_current_bytes": post,
        "migration_delta_pages": migration_delta,
        "touch_delta_pages": touch_delta,
        "delta_pages": touch_delta,
        "q64_pass": _is_q64(spec, touch_delta),
        "observed_cpu": _u32(u["mm"], OFF_OBS_CPU),
        "worker_error": _u32(u["mm"], OFF_ERROR),
        "touched": _u32(u["mm"], OFF_TOUCHED),
    }


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
    name = f"fr-m5d-{runid}-{block}-{arm}-{identity}"
    u = _start(
        worker=worker,
        root=root,
        name=name,
        prep_cpu=prep_cpu,
    )
    try:
        if arm == "self_atomic":
            measured = _arm_self(spec, u=u, stock_cpu=stock_cpu)
        elif arm == "external_atomic":
            measured = _arm_external(spec, u=u, stock_cpu=stock_cpu)
        else:
            raise ValueError(arm)

        cpu_match = measured["observed_cpu"] == stock_cpu
        valid = measured["worker_error"] == 0 and cpu_match and measured["touched"] == 1
        return {
            "experiment_id": spec["experiment_id"],
            "block": block,
            "arm": arm,
            "identity": identity,
            "prep_cpu": prep_cpu,
            "stock_cpu": stock_cpu,
            "valid": valid,
            "cpu_match": cpu_match,
            **measured,
        }
    finally:
        _stop(u)


def _clopper(successes: int, n: int, confidence: float) -> list[float]:
    alpha = 1.0 - confidence
    lo = 0.0 if successes == 0 else float(beta.ppf(alpha / 2, successes, n - successes + 1))
    hi = 1.0 if successes == n else float(beta.ppf(1 - alpha / 2, successes + 1, n - successes))
    return [lo, hi]


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

    totals: dict[str, Any] = {}
    block_rows = []
    perfect_external = 0
    cpu_mismatches = 0

    for arm in spec["arms"]:
        rows = [t for t in trials if t["arm"] == arm]
        valid_rows = [t for t in rows if t["valid"]]
        successes = sum(bool(t["q64_pass"]) for t in valid_rows)
        zeros = sum(float(t["delta_pages"]) == 0.0 for t in valid_rows)
        other = len(valid_rows) - successes - zeros
        cpu_mismatches += sum(not bool(t["cpu_match"]) for t in rows)
        totals[arm] = {
            "n": len(rows),
            "valid_n": len(valid_rows),
            "q64_successes": successes,
            "failures": len(valid_rows) - successes,
            "zero_delta": zeros,
            "other_delta": other,
            "success_rate": successes / len(valid_rows) if valid_rows else None,
        }

    diffs = []
    paired_table = {
        "both_pass": 0,
        "self_only_pass": 0,
        "external_only_pass": 0,
        "both_fail": 0,
    }

    for b in range(blocks):
        row: dict[str, Any] = {"block": b}
        for arm in spec["arms"]:
            rs = sorted(
                [t for t in trials if int(t["block"]) == b and t["arm"] == arm],
                key=lambda t: int(t["identity"]),
            )
            valid = [t for t in rs if t["valid"]]
            ok = sum(bool(t["q64_pass"]) for t in valid)
            fails = len(valid) - ok
            row[arm] = {
                "valid_n": len(valid),
                "q64_successes": ok,
                "failures": fails,
                "failure_rate": fails / len(valid) if valid else None,
                "delta_sequence": [float(t["delta_pages"]) for t in rs],
                "migration_delta_sequence": [
                    t.get("migration_delta_pages") for t in rs
                ],
            }

        if row["external_atomic"]["failures"] == 0 and row["external_atomic"]["valid_n"] == nident:
            perfect_external += 1

        if row["self_atomic"]["valid_n"] == nident and row["external_atomic"]["valid_n"] == nident:
            diff = row["self_atomic"]["failure_rate"] - row["external_atomic"]["failure_rate"]
            diffs.append(diff)
            row["paired_failure_rate_improvement"] = diff
        else:
            row["paired_failure_rate_improvement"] = None

        for i in range(nident):
            s = next(t for t in trials if int(t["block"]) == b and t["arm"] == "self_atomic" and int(t["identity"]) == i)
            e = next(t for t in trials if int(t["block"]) == b and t["arm"] == "external_atomic" and int(t["identity"]) == i)
            if not s["valid"] or not e["valid"]:
                continue
            sp, ep = bool(s["q64_pass"]), bool(e["q64_pass"])
            if sp and ep:
                paired_table["both_pass"] += 1
            elif sp and not ep:
                paired_table["self_only_pass"] += 1
            elif not sp and ep:
                paired_table["external_only_pass"] += 1
            else:
                paired_table["both_fail"] += 1

        block_rows.append(row)

    ext = totals["external_atomic"]
    ext_ci = _clopper(
        ext["q64_successes"], ext["valid_n"], float(spec["confidence_level"])
    ) if ext["valid_n"] else [0.0, 1.0]

    nonzero = [d for d in diffs if d != 0]
    positive = sum(d > 0 for d in nonzero)
    sign_p = float(
        binomtest(positive, len(nonzero), 0.5, alternative="greater").pvalue
    ) if nonzero else 1.0

    support = (
        ext["valid_n"] == 92
        and ext["q64_successes"] >= int(spec["external_support_min_successes"])
        and perfect_external >= int(spec["external_support_required_perfect_blocks"])
        and ext["failures"] < totals["self_atomic"]["failures"]
        and cpu_mismatches == 0
    )
    reject = ext["failures"] >= int(spec["external_reject_min_failures"])
    decision = (
        "SUPPORT_EXTERNAL_PATH" if support
        else "REJECT_EXTERNAL_PATH" if reject
        else "INCONCLUSIVE"
    )

    return {
        "experiment_id": spec["experiment_id"],
        "decision": decision,
        "totals": totals,
        "perfect_external_blocks": perfect_external,
        "cpu_mismatches": cpu_mismatches,
        "external_success_clopper_pearson": ext_ci,
        "paired_block_failure_rate_improvements": diffs,
        "paired_sign_test": {
            "nonzero_blocks": len(nonzero),
            "positive_improvements": positive,
            "one_sided_p": sign_p,
        },
        "paired_outcome_table": paired_table,
        "blocks": block_rows,
        "trials": trials,
        "inference_boundary": (
            "Hosted first-touch path decomposition only; "
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

        arms = ["self_atomic", "external_atomic"] if a.block % 2 == 0 else ["external_atomic", "self_atomic"]
        for i in range(int(spec["identities_per_arm"])):
            for arm in arms:
                ar = root / arm / f"id-{i}"
                ar.mkdir(parents=True, exist_ok=True)
                t = run_probe(
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
                    json.dumps(t, indent=2, sort_keys=True) + "\n",
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
        "self": result["totals"]["self_atomic"],
        "external": result["totals"]["external_atomic"],
        "perfect_external_blocks": result["perfect_external_blocks"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
