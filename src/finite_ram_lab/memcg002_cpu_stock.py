from __future__ import annotations

import argparse
import csv
import json
import random
import statistics
from pathlib import Path
from typing import Any


def load_spec(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def schedule_rows(spec: dict[str, Any], block: int) -> list[dict[str, Any]]:
    if block not in range(int(spec["runner_blocks"])):
        raise ValueError("block outside frozen design")
    arms = list(spec["arms"])
    random.Random(
        int(spec["base_schedule_seed"]) + block * 9176
    ).shuffle(arms)
    return [{"order": i, "arm": arm} for i, arm in enumerate(arms)]


def write_schedule(spec: dict[str, Any], block: int, out: str | Path) -> None:
    path = Path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=["order", "arm"], lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(schedule_rows(spec, block))


def read_trial_csv(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            rows.append({
                "arm": row["arm"],
                "step": int(row["step"]),
                "cpu_a": int(row["cpu_a"]),
                "cpu_b": int(row["cpu_b"]),
                "current_cpu": int(row["current_cpu"]),
                "page_size": int(row["page_size"]),
                "migration_marker": int(row["migration_marker"]),
                "touched": int(row["touched"]),
                "memory_current_bytes": int(row["memory_current_bytes"]),
                "anon_bytes": int(row["anon_bytes"]),
                "kernel_bytes": int(row["kernel_bytes"]),
                "pagetables_bytes": int(row["pagetables_bytes"]),
                "minor_faults": int(row["minor_faults"]),
            })
    return rows


def circular_distance(a: int, b: int, q: int) -> int:
    d = abs((a - b) % q)
    return min(d, q - d)


def _events(rows: list[dict[str, Any]], threshold_pages: int) -> list[dict[str, Any]]:
    page_size = rows[0]["page_size"]
    out = []
    for i in range(1, len(rows)):
        d = (
            rows[i]["memory_current_bytes"]
            - rows[i - 1]["memory_current_bytes"]
        ) / page_size
        if abs(d) >= threshold_pages:
            out.append({
                "step": rows[i]["step"],
                "delta_pages": d,
                "cpu": rows[i]["current_cpu"],
                "migration_marker": rows[i]["migration_marker"],
            })
    return out


def _positive(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [e for e in events if e["delta_pages"] > 0]


def _phase(events: list[dict[str, Any]], q: int) -> int | None:
    if not events:
        return None
    residues = [int(e["step"]) % q for e in events]
    # Exact Q64 data should agree. Median keeps this deterministic if jitter occurs.
    return int(statistics.median(residues)) % q


def _next_phase_step(after: int, phase: int, q: int) -> int:
    n = after + 1
    while n % q != phase:
        n += 1
    return n


def analyze_trial(
    spec: dict[str, Any],
    rows: list[dict[str, Any]],
    *,
    block: int,
) -> dict[str, Any]:
    steps = int(spec["steps"])
    migrate_after = int(spec["migrate_after_step"])
    return_after = int(spec["return_after_step"])
    q = int(spec["quantum_pages"])
    threshold = int(spec["significant_jump_pages"])

    if len(rows) != steps + 1:
        raise ValueError("wrong sample count")
    if [r["step"] for r in rows] != list(range(steps + 1)):
        raise ValueError("non-contiguous steps")
    if {r["page_size"] for r in rows} != {int(spec["required_page_size"])}:
        raise ValueError("page-size mismatch")
    if len({r["arm"] for r in rows}) != 1:
        raise ValueError("mixed arm")
    arm = rows[0]["arm"]
    if arm not in spec["arms"]:
        raise ValueError("unknown arm")
    cpu_a = rows[0]["cpu_a"]
    cpu_b = rows[0]["cpu_b"]
    if cpu_a == cpu_b:
        raise ValueError("CPU pair invalid")

    for r in rows:
        step = r["step"]
        expected_cpu = cpu_a
        if arm in {"migrate_touch", "roundtrip_touch", "roundtrip_control"}:
            if step > migrate_after:
                expected_cpu = cpu_b
            if arm in {"roundtrip_touch", "roundtrip_control"} and step > return_after:
                expected_cpu = cpu_a
        if r["current_cpu"] != expected_cpu:
            raise ValueError(
                f"CPU receipt mismatch arm={arm} step={step}: "
                f"{r['current_cpu']} != {expected_cpu}"
            )

    events = _events(rows, threshold)
    pos = _positive(events)

    pre = [e for e in pos if e["step"] <= migrate_after]
    after_migrate = [e for e in pos if e["step"] > migrate_after]
    if arm == "migrate_touch":
        b_side = [
            e for e in pos
            if e["step"] > migrate_after
        ]
    else:
        b_side = [
            e for e in pos
            if migrate_after < e["step"] <= return_after
        ]
    a_return = [e for e in pos if e["step"] > return_after]

    pre_phase = _phase(pre, q)
    post_phase = _phase(after_migrate, q)
    fixed_phase_error = None
    if pre_phase is not None and post_phase is not None:
        fixed_phase_error = circular_distance(pre_phase, post_phase, q)

    first_delay = None
    if after_migrate:
        first_delay = int(after_migrate[0]["step"]) - migrate_after

    b_spacings = [
        b["step"] - a["step"] for a, b in zip(b_side, b_side[1:])
    ]
    b_spacing_errors = [abs(x - q) for x in b_spacings]

    return_phase_error = None
    predicted_return_step = None
    observed_return_step = None
    if pre_phase is not None and a_return:
        predicted_return_step = _next_phase_step(return_after, pre_phase, q)
        observed_return_step = int(a_return[0]["step"])
        return_phase_error = circular_distance(
            observed_return_step % q, pre_phase, q
        )

    positive_magnitudes = [e["delta_pages"] for e in pos]
    q64_magnitudes = all(abs(x - q) <= 1 for x in positive_magnitudes)

    tol = int(spec["phase_tolerance_pages"])
    allowed_delay = set(int(x) for x in spec["migration_first_delay_allowed"])

    criteria: dict[str, bool] = {}
    if arm == "fixed_touch":
        criteria = {
            "enough_pre_events": len(pre) >= 2,
            "enough_post_events": len(after_migrate) >= 2,
            "q64_magnitudes": q64_magnitudes,
            "fixed_phase_stable": (
                fixed_phase_error is not None and fixed_phase_error <= tol
            ),
        }
    elif arm == "migrate_touch":
        criteria = {
            "enough_pre_events": len(pre) >= 2,
            "q64_magnitudes": q64_magnitudes,
            "first_b_charge_prompt": first_delay in allowed_delay,
            "b_spacing_q64": (
                not b_spacing_errors or max(b_spacing_errors) <= tol
            ),
            "post_event_cpu_b": all(e["cpu"] == cpu_b for e in after_migrate),
        }
    elif arm == "roundtrip_touch":
        first_b_delay = None
        if b_side:
            first_b_delay = int(b_side[0]["step"]) - migrate_after
        criteria = {
            "enough_pre_events": len(pre) >= 2,
            "q64_magnitudes": q64_magnitudes,
            "first_b_charge_prompt": first_b_delay in allowed_delay,
            "return_phase_restored": (
                return_phase_error is not None and return_phase_error <= tol
            ),
            "return_step_matches_old_phase": (
                predicted_return_step is not None
                and observed_return_step is not None
                and abs(observed_return_step - predicted_return_step) <= tol
            ),
            "b_event_cpu_b": all(e["cpu"] == cpu_b for e in b_side),
            "return_event_cpu_a": all(e["cpu"] == cpu_a for e in a_return),
        }
    else:
        criteria = {
            "no_positive_events": len(pos) == 0,
        }

    return {
        "block": block,
        "arm": arm,
        "cpu_a": cpu_a,
        "cpu_b": cpu_b,
        "events": events,
        "positive_events": pos,
        "pre_phase": pre_phase,
        "post_phase": post_phase,
        "fixed_phase_error": fixed_phase_error,
        "migration_first_charge_delay": first_delay,
        "b_side_spacings": b_spacings,
        "b_side_spacing_errors": b_spacing_errors,
        "predicted_return_step": predicted_return_step,
        "observed_return_step": observed_return_step,
        "return_phase_error": return_phase_error,
        "criteria": criteria,
        "arm_pass": all(criteria.values()),
    }


def _exception_count(predicted: set[int], observed: set[int]) -> int:
    return len(predicted - observed) + len(observed - predicted)


def causal_models(
    spec: dict[str, Any],
    trial_results: list[dict[str, Any]],
) -> dict[str, Any]:
    q = int(spec["quantum_pages"])
    migrate_after = int(spec["migrate_after_step"])
    return_after = int(spec["return_after_step"])
    steps = int(spec["steps"])

    global_exceptions = 0
    percpu_exceptions = 0

    for r in trial_results:
        if r["arm"] not in {"migrate_touch", "roundtrip_touch"}:
            continue
        observed = {int(e["step"]) for e in r["positive_events"]}
        pre_phase = r["pre_phase"]
        if pre_phase is None:
            continue

        global_pred = {
            n for n in range(1, steps + 1) if n % q == pre_phase
        }
        global_exceptions += _exception_count(global_pred, observed)

        percpu_pred = {
            n for n in range(1, migrate_after + 1) if n % q == pre_phase
        }
        if r["arm"] == "migrate_touch":
            percpu_pred.update(
                range(migrate_after + 1, steps + 1, q)
            )
        else:
            percpu_pred.update(
                range(migrate_after + 1, return_after + 1, q)
            )
            percpu_pred.update(
                n for n in range(return_after + 1, steps + 1)
                if n % q == pre_phase
            )
        percpu_exceptions += _exception_count(percpu_pred, observed)

    return {
        "global_phase_exception_count": global_exceptions,
        "percpu_phase_exception_count": percpu_exceptions,
        "preferred_by_exceptions": (
            "PERCPU_PHASE"
            if percpu_exceptions < global_exceptions
            else "GLOBAL_PHASE"
            if global_exceptions < percpu_exceptions
            else "TIE"
        ),
    }


def aggregate(spec: dict[str, Any], root: Path) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for path in sorted(root.rglob("trial-*.csv")):
        parts = path.stem.split("-")
        if len(parts) < 4:
            raise ValueError(f"unexpected trial filename: {path.name}")
        block = int(parts[1])
        rows = read_trial_csv(path)
        results.append(analyze_trial(spec, rows, block=block))

    if len(results) != int(spec["expected_trials"]):
        raise ValueError("incomplete trial count")

    ids = {(r["block"], r["arm"]) for r in results}
    expected = {
        (b, arm)
        for b in range(int(spec["runner_blocks"]))
        for arm in spec["arms"]
    }
    if ids != expected:
        raise ValueError("incomplete trial matrix")

    block_rows = []
    support_blocks = 0
    for block in range(int(spec["runner_blocks"])):
        arms = {
            r["arm"]: r for r in results if r["block"] == block
        }
        passes = {arm: row["arm_pass"] for arm, row in arms.items()}
        block_pass = all(passes.values())
        support_blocks += int(block_pass)
        block_rows.append({
            "block": block,
            "arm_passes": passes,
            "block_supports_percpu_stock": block_pass,
        })

    required = int(spec["required_support_blocks"])
    if support_blocks >= required:
        decision = "SUPPORT_PERCPU_STOCK"
    elif support_blocks <= 1:
        decision = "REJECT_PERCPU_STOCK"
    else:
        decision = "INCONCLUSIVE"

    return {
        "experiment_id": spec["experiment_id"],
        "execution_status": "PASS",
        "trial_count": len(results),
        "decision": decision,
        "support_blocks": support_blocks,
        "required_support_blocks": required,
        "blocks": block_rows,
        "trials": results,
        "causal_models": causal_models(spec, results),
        "inference_boundary": (
            "Hosted Linux memcg per-CPU stock causal probe; "
            "not a DRAM hardware law and not yet local-substrate replicated."
        ),
    }


def render_md(result: dict[str, Any]) -> str:
    lines = [
        "# MEMCG-002 CPU-Stock Causal Result",
        "",
        f"- decision: **{result['decision']}**",
        f"- support blocks: **{result['support_blocks']}/{len(result['blocks'])}**",
        f"- preferred causal model by event exceptions: "
        f"**{result['causal_models']['preferred_by_exceptions']}**",
        "",
        "## Block results",
        "",
    ]
    for b in result["blocks"]:
        lines.append(
            f"- block {b['block']}: "
            f"{'PASS' if b['block_supports_percpu_stock'] else 'FAIL'} "
            f"{b['arm_passes']}"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("schedule")
    s.add_argument("--spec", required=True)
    s.add_argument("--block", type=int, required=True)
    s.add_argument("--out", required=True)

    a = sub.add_parser("aggregate")
    a.add_argument("--spec", required=True)
    a.add_argument("--input-root", required=True)
    a.add_argument("--json-out", required=True)
    a.add_argument("--md-out", required=True)

    args = p.parse_args()
    spec = load_spec(args.spec)

    if args.cmd == "schedule":
        write_schedule(spec, args.block, args.out)
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
        "support_blocks": result["support_blocks"],
        "causal_models": result["causal_models"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
