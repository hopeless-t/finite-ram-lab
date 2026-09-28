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
    role: str, index: int, cpu: int,
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
        "-p", f"CPUAffinity={cpu}",
        str(worker),
        "--control", str(fifo),
        "--status", str(status),
        "--max-pages", "256",
    ])

    _wait_for(lambda: any(
        line.startswith("READY ") for line in _status_lines(status)
    ))
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


def _event_record(
    *, m: int, target: Unit, previous_post: int,
    page_size: int, actor: str,
) -> tuple[dict[str, Any], int]:
    pre = _memory_current(target)
    stock_drop_pages = (previous_post - pre) / page_size
    _touch(target)
    post = _memory_current(target)
    probe_delta_pages = (post - pre) / page_size
    return ({
        "m": m,
        "actor": actor,
        "pre_current_bytes": pre,
        "post_probe_current_bytes": post,
        "stock_drop_pages": stock_drop_pages,
        "probe_delta_pages": probe_delta_pages,
    }, post)


def _arm(
    spec: dict[str, Any], *, block: int, arm: str,
    worker: Path, root: Path, cpu: int,
) -> dict[str, Any]:
    run_id = os.environ.get("GITHUB_RUN_ID", "local")
    prefix = f"fr-m3-{run_id}-{block}-{arm.replace('_','-')}"
    units: list[Unit] = []
    page_size = int(spec["required_page_size"])
    significant = int(spec["significant_pages"])

    try:
        for i in range(int(spec["wash_count"])):
            u = _start_unit(
                worker=worker, root=root, prefix=prefix,
                role="wash", index=i, cpu=cpu,
            )
            units.append(u)

        target = _start_unit(
            worker=worker, root=root, prefix=prefix,
            role="target", index=0, cpu=cpu,
        )
        units.append(target)
        previous_post = _memory_current(target)
        records: list[dict[str, Any]] = []

        if arm == "distinct_churn":
            for m in range(1, int(spec["challenger_count"]) + 1):
                challenger = _start_unit(
                    worker=worker, root=root, prefix=prefix,
                    role="challenger", index=m, cpu=cpu,
                )
                units.append(challenger)
                rec, previous_post = _event_record(
                    m=m, target=target, previous_post=previous_post,
                    page_size=page_size, actor=f"distinct-{m}",
                )
                records.append(rec)

        elif arm == "six_only":
            for m in range(1, 7):
                challenger = _start_unit(
                    worker=worker, root=root, prefix=prefix,
                    role="challenger", index=m, cpu=cpu,
                )
                units.append(challenger)
                rec, previous_post = _event_record(
                    m=m, target=target, previous_post=previous_post,
                    page_size=page_size, actor=f"distinct-{m}",
                )
                records.append(rec)

        elif arm == "same_memcg_activity":
            competitor = _start_unit(
                worker=worker, root=root, prefix=prefix,
                role="competitor", index=1, cpu=cpu,
            )
            units.append(competitor)
            for m in range(1, int(spec["challenger_count"]) + 1):
                _touch(competitor)
                rec, previous_post = _event_record(
                    m=m, target=target, previous_post=previous_post,
                    page_size=page_size, actor="same-memcg",
                )
                records.append(rec)

        elif arm == "no_churn":
            for m in range(1, int(spec["challenger_count"]) + 1):
                time.sleep(0.02)
                rec, previous_post = _event_record(
                    m=m, target=target, previous_post=previous_post,
                    page_size=page_size, actor="none",
                )
                records.append(rec)
        else:
            raise ValueError(f"unknown arm: {arm}")

        for rec in records:
            rec["eviction_evidence"] = bool(
                rec["stock_drop_pages"] >= significant
                or rec["probe_delta_pages"] >= significant
            )

        return {
            "experiment_id": spec["experiment_id"],
            "block": block,
            "arm": arm,
            "cpu": cpu,
            "page_size": page_size,
            "wash_count": int(spec["wash_count"]),
            "records": records,
        }
    finally:
        for unit in reversed(units):
            _stop(unit)


def run_block(
    spec: dict[str, Any], *, block: int,
    worker: Path, out_root: Path,
) -> None:
    allowed = sorted(os.sched_getaffinity(0))
    if not allowed:
        raise RuntimeError("no allowed CPU")
    cpu = allowed[0]
    if os.sysconf("SC_PAGE_SIZE") != int(spec["required_page_size"]):
        raise RuntimeError("page-size mismatch")
    out_root.mkdir(parents=True, exist_ok=True)

    for arm in spec["arms"]:
        arm_root = out_root / arm
        arm_root.mkdir(parents=True, exist_ok=True)
        result = _arm(
            spec, block=block, arm=arm, worker=worker,
            root=arm_root, cpu=cpu,
        )
        (out_root / f"trial-{block}-{arm}.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def _first_event(trial: dict[str, Any]) -> int | None:
    for row in trial["records"]:
        if row["eviction_evidence"]:
            return int(row["m"])
    return None


def _fresh_q64_at_first(spec: dict[str, Any], trial: dict[str, Any]) -> bool:
    e = _first_event(trial)
    if e is None:
        return False
    row = next(r for r in trial["records"] if int(r["m"]) == e)
    delta = float(row["probe_delta_pages"])
    return int(spec["q64_min_pages"]) <= delta <= int(spec["q64_max_pages"])


def _candidate_error(observed: int | None, k: int, max_m: int) -> int:
    if observed is None:
        return max(0, (max_m + 1) - k)
    return abs(observed - k)


def _posterior(
    spec: dict[str, Any], thresholds: list[int | None],
) -> dict[str, float]:
    candidates = [int(k) for k in spec["candidate_k"]]
    max_m = int(spec["challenger_count"])
    logs: dict[int, float] = {}
    for k in candidates:
        lp = -math.log(len(candidates))
        for obs in thresholds:
            if obs is None:
                likelihood = 0.75 if k > max_m else 0.025
            else:
                d = abs(obs - k)
                likelihood = (
                    0.60 if d == 0 else
                    0.18 if d == 1 else
                    0.04 if d == 2 else
                    0.005
                )
            lp += math.log(likelihood)
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
        e = _first_event(distinct)
        thresholds.append(e)
        same_events = sum(
            r["eviction_evidence"]
            for r in by_arm["same_memcg_activity"]["records"]
        )
        six_events = sum(
            r["eviction_evidence"] for r in by_arm["six_only"]["records"]
        )
        no_events = sum(
            r["eviction_evidence"] for r in by_arm["no_churn"]["records"]
        )
        block_support = (
            e in window
            and _fresh_q64_at_first(spec, distinct)
            and same_events == 0
            and six_events == 0
            and no_events == 0
        )
        support += int(block_support)
        blocks.append({
            "block": block,
            "eviction_threshold": e,
            "fresh_q64_at_threshold": _fresh_q64_at_first(spec, distinct),
            "same_memcg_event_count": same_events,
            "six_only_event_count": six_events,
            "no_churn_event_count": no_events,
            "supports_k7_model": block_support,
        })

    required = int(spec["required_support_blocks"])
    if support >= required:
        decision = "SUPPORT_K7_SLOT_MODEL"
    elif support <= 1:
        decision = "REJECT_K7_SLOT_MODEL"
    else:
        decision = "INCONCLUSIVE"

    candidates = [int(k) for k in spec["candidate_k"]]
    max_m = int(spec["challenger_count"])
    total_error = {
        str(k): sum(_candidate_error(e, k, max_m) for e in thresholds)
        for k in candidates
    }
    best_k = min(candidates, key=lambda k: (total_error[str(k)], k))

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

    observed_only = [e for e in thresholds if e is not None]
    modal = None
    if observed_only:
        counts = {e: observed_only.count(e) for e in set(observed_only)}
        modal = max(counts, key=lambda x: (counts[x], -x))
    median = statistics.median(observed_only) if observed_only else None
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
        "candidate_total_absolute_error": total_error,
        "posterior_k": posterior,
        "posterior_mode_k": int(max(posterior, key=posterior.get)),
        "leave_one_block_out": folds,
        "blocks": blocks,
        "trials": trials,
        "inference_boundary": (
            "Hosted Linux memcg seven-slot cache probe; "
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
        "# MEMCG-003 Seven-Slot Eviction Result",
        "",
        f"- decision: **{result['decision']}**",
        f"- support blocks: **{result['support_blocks']}/{len(result['blocks'])}**",
        f"- thresholds: **{result['thresholds']}**",
        f"- modal threshold: **{result['modal_threshold']}**",
        f"- median threshold: **{result['median_threshold']}**",
        f"- best K by absolute error: **{result['best_k_by_absolute_error']}**",
        f"- Bayesian posterior mode K: **{result['posterior_mode_k']}**",
        "",
        "## Blocks",
        "",
    ]
    for b in result["blocks"]:
        lines.append(
            f"- block {b['block']}: E={b['eviction_threshold']}, "
            f"Q64={b['fresh_q64_at_threshold']}, "
            f"same={b['same_memcg_event_count']}, "
            f"six={b['six_only_event_count']}, "
            f"no_churn={b['no_churn_event_count']}, "
            f"support={b['supports_k7_model']}"
        )
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
        "posterior_mode_k": result["posterior_mode_k"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
