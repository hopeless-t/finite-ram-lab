from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class Unit:
    name: str
    fifo: Path
    status: Path
    cgroup: Path


def load_spec(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True, check=check)


def _wait_for(predicate, timeout: float = 10.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.02)
    raise TimeoutError("timed out waiting for worker state")


def _status_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8").splitlines()


def _start_unit(
    *, worker: Path, root: Path, prefix: str,
    role: str, index: int, stock_cpu: int,
) -> Unit:
    safe_role = role.replace("_", "-")
    name = f"{prefix}-{safe_role}-{index}"
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
        "-p", f"CPUAffinity={stock_cpu}",
        str(worker),
        "--control", str(fifo),
        "--status", str(status),
        "--max-pages", "256",
    ])

    _wait_for(lambda: any(
        line.startswith("READY ") for line in _status_lines(status)
    ))
    ready = next(
        line for line in _status_lines(status)
        if line.startswith("READY ")
    )
    cpu_field = next(
        field for field in ready.split() if field.startswith("cpu=")
    )
    if int(cpu_field.split("=", 1)[1]) != stock_cpu:
        raise RuntimeError("worker READY on wrong CPU")

    show = _run([
        "systemctl", "show", f"{name}.service",
        "--property=ControlGroup", "--value",
    ])
    cg = show.stdout.strip()
    if not cg.startswith("/"):
        raise RuntimeError(f"invalid cgroup path for {name}: {cg!r}")
    return Unit(
        name=name,
        fifo=fifo,
        status=status,
        cgroup=Path("/sys/fs/cgroup") / cg.lstrip("/"),
    )


def _send(unit: Unit, command: str) -> None:
    with unit.fifo.open("w", encoding="utf-8") as fh:
        fh.write(command + "\n")
        fh.flush()


def _touch(unit: Unit) -> int:
    before = sum(line.startswith("TOUCH ") for line in _status_lines(unit.status))
    _send(unit, "TOUCH")
    _wait_for(lambda: sum(
        line.startswith("TOUCH ") for line in _status_lines(unit.status)
    ) > before)
    last = [
        line for line in _status_lines(unit.status)
        if line.startswith("TOUCH ")
    ][-1]
    for field in last.split():
        if field.startswith("count="):
            return int(field.split("=", 1)[1])
    raise RuntimeError("TOUCH receipt missing count")


def _stop(unit: Unit) -> None:
    try:
        _send(unit, "STOP")
    except (BrokenPipeError, FileNotFoundError):
        pass
    _run(["sudo", "systemctl", "stop", f"{unit.name}.service"], check=False)


def _memory_current(unit: Unit) -> int:
    return int((unit.cgroup / "memory.current").read_text(encoding="utf-8").strip())


def _passive_record(
    *, m: int, target: Unit, previous_current: int,
    page_size: int, actor: str,
) -> tuple[dict[str, Any], int]:
    current = _memory_current(target)
    drop_pages = (previous_current - current) / page_size
    return ({
        "m": m,
        "actor": actor,
        "target_current_bytes": current,
        "passive_drop_pages": drop_pages,
    }, current)


def _final_recharge(target: Unit, page_size: int) -> dict[str, Any]:
    pre = _memory_current(target)
    _touch(target)
    post = _memory_current(target)
    return {
        "pre_current_bytes": pre,
        "post_current_bytes": post,
        "delta_pages": (post - pre) / page_size,
    }


def _arm(
    spec: dict[str, Any], *, block: int, arm: str,
    worker: Path, root: Path, control_cpu: int, stock_cpu: int,
) -> dict[str, Any]:
    run_id = os.environ.get("GITHUB_RUN_ID", "local")
    prefix = f"fr-m3b-{run_id}-{block}-{arm.replace('_','-')}"
    units: list[Unit] = []
    page_size = int(spec["required_page_size"])

    try:
        for i in range(int(spec["wash_count"])):
            u = _start_unit(
                worker=worker, root=root, prefix=prefix,
                role="wash", index=i, stock_cpu=stock_cpu,
            )
            units.append(u)

        target = _start_unit(
            worker=worker, root=root, prefix=prefix,
            role="target", index=0, stock_cpu=stock_cpu,
        )
        units.append(target)
        previous_current = _memory_current(target)
        records: list[dict[str, Any]] = []

        if arm == "distinct_churn":
            for m in range(1, int(spec["challenger_count"]) + 1):
                challenger = _start_unit(
                    worker=worker, root=root, prefix=prefix,
                    role="challenger", index=m, stock_cpu=stock_cpu,
                )
                units.append(challenger)
                rec, previous_current = _passive_record(
                    m=m, target=target, previous_current=previous_current,
                    page_size=page_size, actor=f"distinct-{m}",
                )
                records.append(rec)

        elif arm == "six_only":
            for m in range(1, 7):
                challenger = _start_unit(
                    worker=worker, root=root, prefix=prefix,
                    role="challenger", index=m, stock_cpu=stock_cpu,
                )
                units.append(challenger)
                rec, previous_current = _passive_record(
                    m=m, target=target, previous_current=previous_current,
                    page_size=page_size, actor=f"distinct-{m}",
                )
                records.append(rec)

        elif arm == "same_memcg_activity":
            competitor = _start_unit(
                worker=worker, root=root, prefix=prefix,
                role="competitor", index=1, stock_cpu=stock_cpu,
            )
            units.append(competitor)
            for m in range(1, int(spec["challenger_count"]) + 1):
                _touch(competitor)
                rec, previous_current = _passive_record(
                    m=m, target=target, previous_current=previous_current,
                    page_size=page_size, actor="same-memcg",
                )
                records.append(rec)

        elif arm == "no_churn":
            for m in range(1, int(spec["challenger_count"]) + 1):
                time.sleep(0.02)
                rec, previous_current = _passive_record(
                    m=m, target=target, previous_current=previous_current,
                    page_size=page_size, actor="none",
                )
                records.append(rec)
        else:
            raise ValueError(f"unknown arm: {arm}")

        final = _final_recharge(target, page_size)

        return {
            "experiment_id": spec["experiment_id"],
            "block": block,
            "arm": arm,
            "control_cpu": control_cpu,
            "stock_cpu": stock_cpu,
            "page_size": page_size,
            "wash_count": int(spec["wash_count"]),
            "records": records,
            "final_recharge": final,
        }
    finally:
        for unit in reversed(units):
            _stop(unit)


def run_block(
    spec: dict[str, Any], *, block: int,
    worker: Path, out_root: Path,
) -> None:
    allowed = sorted(os.sched_getaffinity(0))
    if len(allowed) < 2:
        raise RuntimeError("MEMCG-003B requires at least two allowed CPUs")
    control_cpu, stock_cpu = allowed[0], allowed[1]

    os.sched_setaffinity(0, {control_cpu})
    if os.sched_getaffinity(0) != {control_cpu}:
        raise RuntimeError("failed to isolate orchestrator on control CPU")

    if os.sysconf("SC_PAGE_SIZE") != int(spec["required_page_size"]):
        raise RuntimeError("page-size mismatch")

    out_root.mkdir(parents=True, exist_ok=True)
    receipt = {
        "control_cpu": control_cpu,
        "stock_cpu": stock_cpu,
        "orchestrator_affinity": sorted(os.sched_getaffinity(0)),
    }
    (out_root / "cpu-isolation.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    for arm in spec["arms"]:
        arm_root = out_root / arm
        arm_root.mkdir(parents=True, exist_ok=True)
        result = _arm(
            spec, block=block, arm=arm, worker=worker,
            root=arm_root, control_cpu=control_cpu, stock_cpu=stock_cpu,
        )
        (out_root / f"trial-{block}-{arm}.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def _first_drop(spec: dict[str, Any], trial: dict[str, Any]) -> int | None:
    threshold = float(spec["significant_drop_pages"])
    for row in trial["records"]:
        if float(row["passive_drop_pages"]) >= threshold:
            return int(row["m"])
    return None


def _has_drop(spec: dict[str, Any], trial: dict[str, Any]) -> bool:
    return _first_drop(spec, trial) is not None


def _final_q64(spec: dict[str, Any], trial: dict[str, Any]) -> bool:
    d = float(trial["final_recharge"]["delta_pages"])
    return float(spec["q64_min_pages"]) <= d <= float(spec["q64_max_pages"])


def _candidate_error(observed: int | None, k: int, max_m: int) -> int:
    if observed is None:
        return max(0, (max_m + 1) - k)
    return abs(observed - k)


def _likelihood(observed: int | None, k: int, max_m: int) -> float:
    if observed is None:
        return 0.75 if k > max_m else 0.025
    d = abs(observed - k)
    return (
        0.60 if d == 0 else
        0.18 if d == 1 else
        0.04 if d == 2 else
        0.005
    )


def _posterior(
    spec: dict[str, Any], thresholds: list[int | None],
) -> dict[str, float]:
    candidates = [int(k) for k in spec["candidate_k"]]
    max_m = int(spec["challenger_count"])
    logs = {}
    for k in candidates:
        lp = -math.log(len(candidates))
        for obs in thresholds:
            lp += math.log(_likelihood(obs, k, max_m))
        logs[k] = lp
    mx = max(logs.values())
    weights = {k: math.exp(v - mx) for k, v in logs.items()}
    total = sum(weights.values())
    return {str(k): weights[k] / total for k in candidates}


def analyze_trials(
    spec: dict[str, Any], trials: list[dict[str, Any]],
) -> dict[str, Any]:
    expected = {
        (b, arm)
        for b in range(int(spec["runner_blocks"]))
        for arm in spec["arms"]
    }
    got = {(int(t["block"]), t["arm"]) for t in trials}
    if got != expected:
        raise ValueError("incomplete trial matrix")

    blocks = []
    thresholds: list[int | None] = []
    support = 0
    window = {int(x) for x in spec["support_window"]}

    for block in range(int(spec["runner_blocks"])):
        by_arm = {
            t["arm"]: t for t in trials if int(t["block"]) == block
        }
        distinct = by_arm["distinct_churn"]
        e = _first_drop(spec, distinct)
        thresholds.append(e)

        six_drop = _has_drop(spec, by_arm["six_only"])
        same_drop = _has_drop(spec, by_arm["same_memcg_activity"])
        no_drop = _has_drop(spec, by_arm["no_churn"])
        final_q64 = _final_q64(spec, distinct)

        block_support = (
            e in window
            and not six_drop
            and not same_drop
            and not no_drop
            and final_q64
        )
        support += int(block_support)
        blocks.append({
            "block": block,
            "eviction_threshold": e,
            "distinct_final_q64_recharge": final_q64,
            "six_only_has_drop": six_drop,
            "same_memcg_has_drop": same_drop,
            "no_churn_has_drop": no_drop,
            "supports_k7_model_b": block_support,
        })

    required = int(spec["required_support_blocks"])
    if support >= required:
        decision = "SUPPORT_K7_SLOT_MODEL_B"
    elif support <= 1:
        decision = "REJECT_K7_SLOT_MODEL_B"
    else:
        decision = "INCONCLUSIVE"

    candidates = [int(k) for k in spec["candidate_k"]]
    max_m = int(spec["challenger_count"])

    total_error = {
        str(k): sum(_candidate_error(e, k, max_m) for e in thresholds)
        for k in candidates
    }
    best_k = min(candidates, key=lambda k: (total_error[str(k)], k))

    mdl_bits = {
        str(k): math.log2(len(candidates)) + sum(
            -math.log2(_likelihood(e, k, max_m))
            for e in thresholds
        )
        for k in candidates
    }
    best_mdl_k = min(candidates, key=lambda k: (mdl_bits[str(k)], k))

    folds = []
    for held in range(int(spec["runner_blocks"])):
        train = [e for i, e in enumerate(thresholds) if i != held]
        train_err = {
            k: sum(_candidate_error(e, k, max_m) for e in train)
            for k in candidates
        }
        trained_k = min(candidates, key=lambda k: (train_err[k], k))
        obs = thresholds[held]
        folds.append({
            "heldout_block": held,
            "trained_k": trained_k,
            "observed_threshold": obs,
            "absolute_error": _candidate_error(obs, trained_k, max_m),
        })

    observed = [e for e in thresholds if e is not None]
    modal = None
    if observed:
        counts = {e: observed.count(e) for e in set(observed)}
        modal = max(counts, key=lambda x: (counts[x], -x))
    median = statistics.median(observed) if observed else None

    posterior = _posterior(spec, thresholds)

    return {
        "experiment_id": spec["experiment_id"],
        "execution_status": "PASS",
        "trial_count": len(trials),
        "decision": decision,
        "support_blocks": support,
        "thresholds": thresholds,
        "modal_threshold": modal,
        "median_threshold": median,
        "best_k_by_absolute_error": best_k,
        "best_k_by_mdl": best_mdl_k,
        "candidate_total_absolute_error": total_error,
        "candidate_mdl_bits": mdl_bits,
        "posterior_k": posterior,
        "posterior_mode_k": int(max(posterior, key=posterior.get)),
        "leave_one_block_out": folds,
        "blocks": blocks,
        "trials": trials,
        "inference_boundary": (
            "Hosted non-consuming Linux memcg seven-slot probe; "
            "not a hardware-memory law and not local-substrate replicated."
        ),
    }


def aggregate(spec: dict[str, Any], root: Path) -> dict[str, Any]:
    trials = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(root.rglob("trial-*.json"))
    ]
    if len(trials) != int(spec["expected_trials"]):
        raise ValueError(
            f"expected {spec['expected_trials']} trials, got {len(trials)}"
        )
    return analyze_trials(spec, trials)


def render_md(result: dict[str, Any]) -> str:
    lines = [
        "# MEMCG-003B Non-Consuming Seven-Slot Result",
        "",
        f"- decision: **{result['decision']}**",
        f"- support blocks: **{result['support_blocks']}/{len(result['blocks'])}**",
        f"- thresholds: **{result['thresholds']}**",
        f"- modal threshold: **{result['modal_threshold']}**",
        f"- median threshold: **{result['median_threshold']}**",
        f"- best K absolute error: **{result['best_k_by_absolute_error']}**",
        f"- best K MDL: **{result['best_k_by_mdl']}**",
        f"- posterior mode K: **{result['posterior_mode_k']}**",
        "",
    ]
    for b in result["blocks"]:
        lines.append(f"- block {b['block']}: {b}")
    return "\n".join(lines) + "\n"


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
    ag.add_argument("--md-out", required=True)

    args = p.parse_args()
    spec = load_spec(args.spec)

    if args.cmd == "run-block":
        run_block(
            spec,
            block=args.block,
            worker=Path(args.worker).resolve(),
            out_root=Path(args.out_root).resolve(),
        )
        return

    result = aggregate(spec, Path(args.input_root))
    jout = Path(args.json_out)
    mout = Path(args.md_out)
    jout.parent.mkdir(parents=True, exist_ok=True)
    mout.parent.mkdir(parents=True, exist_ok=True)
    jout.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    mout.write_text(render_md(result), encoding="utf-8")
    print(json.dumps({
        "decision": result["decision"],
        "thresholds": result["thresholds"],
        "best_k": result["best_k_by_absolute_error"],
        "best_k_mdl": result["best_k_by_mdl"],
        "posterior_mode_k": result["posterior_mode_k"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
