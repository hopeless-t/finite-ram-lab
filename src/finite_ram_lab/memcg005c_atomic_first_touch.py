from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import time
from pathlib import Path
from typing import Any

from scipy.stats import beta, binomtest


def load_spec(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True, check=check)


def _lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines() if path.exists() else []


def _wait(pred, timeout: float = 10.0) -> None:
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if pred():
            return
        time.sleep(0.02)
    raise TimeoutError("worker receipt timeout")


def _start(worker: Path, root: Path, name: str, prep_cpu: int) -> dict[str, Any]:
    fifo = root / f"{name}.fifo"
    status = root / f"{name}.status"
    if fifo.exists():
        fifo.unlink()
    os.mkfifo(fifo)
    status.write_text("", encoding="utf-8")
    _run([
        "sudo","systemd-run","--quiet","--collect",
        f"--unit={name}",
        "-p","MemoryAccounting=yes",
        "-p",f"CPUAffinity={prep_cpu}",
        str(worker),
        "--control",str(fifo),
        "--status",str(status),
        "--max-pages","16",
    ])
    _wait(lambda: any(x.startswith("READY ") for x in _lines(status)))
    ready = next(x for x in _lines(status) if x.startswith("READY "))
    cpu = int(next(x for x in ready.split() if x.startswith("cpu=")).split("=",1)[1])
    if cpu != prep_cpu or "touched=0" not in ready:
        raise RuntimeError("invalid READY")
    cg = _run([
        "systemctl","show",f"{name}.service",
        "--property=ControlGroup","--value",
    ]).stdout.strip()
    return {
        "name":name,
        "fifo":fifo,
        "status":status,
        "cg":Path("/sys/fs/cgroup") / cg.lstrip("/"),
        "ready":ready,
    }


def _send(u: dict[str, Any], cmd: str, prefix: str | None = None) -> str | None:
    before = sum(x.startswith(prefix) for x in _lines(u["status"])) if prefix else 0
    with u["fifo"].open("w", encoding="utf-8") as fh:
        fh.write(cmd + "\n")
        fh.flush()
    if not prefix:
        return None
    _wait(lambda: sum(x.startswith(prefix) for x in _lines(u["status"])) > before)
    return [x for x in _lines(u["status"]) if x.startswith(prefix)][-1]


def _current(u: dict[str, Any]) -> int:
    return int((u["cg"] / "memory.current").read_text(encoding="utf-8").strip())


def _stop(u: dict[str, Any]) -> None:
    try:
        _send(u, "STOP")
    except Exception:
        pass
    _run(["sudo","systemctl","stop",u["name"] + ".service"], check=False)


def _is_q64(spec: dict[str, Any], d: float) -> bool:
    return float(spec["q64_min_pages"]) <= d <= float(spec["q64_max_pages"])


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
    name = f"fr-m5c-{runid}-{block}-{arm}-{identity}"
    u = _start(worker, root, name, prep_cpu)
    page = int(spec["required_page_size"])
    try:
        if arm == "two_step":
            migrate = _send(u, f"MIGRATE {stock_cpu}", "MIGRATE ")
            pre = _current(u)
            touch = _send(u, "TOUCH_ONE", "TOUCH ")
            post = _current(u)
            receipt = {"migrate": migrate, "touch": touch}
        elif arm == "atomic":
            pre = _current(u)
            atomic = _send(u, f"MIGRATE_TOUCH {stock_cpu}", "MIGRATE_TOUCH ")
            post = _current(u)
            receipt = {"atomic": atomic}
        else:
            raise ValueError(arm)

        d = (post - pre) / page
        return {
            "experiment_id": spec["experiment_id"],
            "block": block,
            "arm": arm,
            "identity": identity,
            "prep_cpu": prep_cpu,
            "stock_cpu": stock_cpu,
            "pre_current_bytes": pre,
            "post_current_bytes": post,
            "delta_pages": d,
            "q64_pass": _is_q64(spec, d),
            "receipt": receipt,
        }
    finally:
        _stop(u)


def _clopper_pearson(successes: int, n: int, confidence: float) -> list[float]:
    alpha = 1.0 - confidence
    lower = 0.0 if successes == 0 else float(beta.ppf(alpha / 2, successes, n - successes + 1))
    upper = 1.0 if successes == n else float(beta.ppf(1 - alpha / 2, successes + 1, n - successes))
    return [lower, upper]


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

    block_rows = []
    totals = {}
    for arm in spec["arms"]:
        rows = [t for t in trials if t["arm"] == arm]
        successes = sum(bool(t["q64_pass"]) for t in rows)
        zeros = sum(float(t["delta_pages"]) == 0.0 for t in rows)
        other = len(rows) - successes - zeros
        totals[arm] = {
            "n": len(rows),
            "q64_successes": successes,
            "failures": len(rows) - successes,
            "zero_delta": zeros,
            "other_delta": other,
            "success_rate": successes / len(rows),
        }

    diffs = []
    perfect_atomic = 0
    for b in range(blocks):
        row = {"block": b}
        for arm in spec["arms"]:
            rows = sorted(
                [t for t in trials if int(t["block"]) == b and t["arm"] == arm],
                key=lambda t: int(t["identity"]),
            )
            ok = sum(bool(t["q64_pass"]) for t in rows)
            fails = len(rows) - ok
            row[arm] = {
                "q64_successes": ok,
                "failures": fails,
                "failure_rate": fails / len(rows),
                "delta_sequence": [float(t["delta_pages"]) for t in rows],
            }
        if row["atomic"]["failures"] == 0:
            perfect_atomic += 1
        diff = row["two_step"]["failure_rate"] - row["atomic"]["failure_rate"]
        row["paired_failure_rate_improvement"] = diff
        diffs.append(diff)
        block_rows.append(row)

    atomic_s = totals["atomic"]["q64_successes"]
    atomic_n = totals["atomic"]["n"]
    ci = _clopper_pearson(
        atomic_s, atomic_n, float(spec["confidence_level"])
    )
    nonzero = [d for d in diffs if d != 0]
    if nonzero:
        positive = sum(d > 0 for d in nonzero)
        sign_p = float(binomtest(positive, len(nonzero), 0.5, alternative="greater").pvalue)
    else:
        positive = 0
        sign_p = 1.0

    support = (
        atomic_s >= int(spec["atomic_support_min_successes"])
        and perfect_atomic >= int(spec["atomic_support_required_perfect_blocks"])
        and totals["atomic"]["failures"] < totals["two_step"]["failures"]
    )
    reject = totals["atomic"]["failures"] >= int(spec["atomic_reject_min_failures"])
    decision = (
        "SUPPORT_ATOMIC_PATH" if support else
        "REJECT_ATOMIC_PATH" if reject else
        "INCONCLUSIVE"
    )

    return {
        "experiment_id": spec["experiment_id"],
        "decision": decision,
        "totals": totals,
        "perfect_atomic_blocks": perfect_atomic,
        "atomic_success_clopper_pearson": ci,
        "paired_block_failure_rate_improvements": diffs,
        "paired_sign_test": {
            "nonzero_blocks": len(nonzero),
            "positive_improvements": positive,
            "one_sided_p": sign_p,
        },
        "blocks": block_rows,
        "trials": trials,
        "inference_boundary": (
            "Hosted control-path integrity experiment; "
            "does not itself estimate memcg slot capacity."
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

        # Alternate arm order by block parity to reduce temporal-order confounding.
        arms = ["two_step", "atomic"] if a.block % 2 == 0 else ["atomic", "two_step"]
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
        "atomic": result["totals"]["atomic"],
        "two_step": result["totals"]["two_step"],
        "perfect_atomic_blocks": result["perfect_atomic_blocks"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
