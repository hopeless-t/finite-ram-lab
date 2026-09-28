from __future__ import annotations

import argparse
import csv
import json
import math
import random
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class TrialAnalysis:
    block: int
    mode: str
    pinned_cpu: int
    page_size: int
    steps: int
    significant_jump_positions: list[int]
    significant_jump_pages: list[float]
    spacing_pages: list[int]
    median_significant_jump_pages: float | None
    median_spacing_pages: float | None
    supports_h64: bool
    best_quantum_pages: int | None
    quantum_scores: dict[str, Any]
    autocorrelation: dict[str, float | None]


def load_spec(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def schedule_rows(spec: dict[str, Any], block: int) -> list[dict[str, Any]]:
    if block not in range(int(spec["runner_blocks"])):
        raise ValueError("block outside frozen design")
    modes = list(spec["modes"])
    random.Random(
        int(spec["base_schedule_seed"]) + block * 9176
    ).shuffle(modes)
    return [{"order": i, "mode": mode} for i, mode in enumerate(modes)]


def write_schedule(spec: dict[str, Any], block: int, out: str | Path) -> None:
    path = Path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=["order", "mode"], lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(schedule_rows(spec, block))


def read_trial_csv(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            rows.append(
                {
                    "mode": row["mode"],
                    "step": int(row["step"]),
                    "pinned_cpu": int(row["pinned_cpu"]),
                    "page_size": int(row["page_size"]),
                    "memory_current_bytes": int(row["memory_current_bytes"]),
                    "anon_bytes": int(row["anon_bytes"]),
                    "kernel_bytes": int(row["kernel_bytes"]),
                    "pagetables_bytes": int(row["pagetables_bytes"]),
                    "minor_faults": int(row["minor_faults"]),
                }
            )
    return rows


def _autocorrelation(values: list[float], lag: int) -> float | None:
    if lag <= 0 or len(values) <= lag:
        return None
    a = values[:-lag]
    b = values[lag:]
    ma = statistics.fmean(a)
    mb = statistics.fmean(b)
    da = [x - ma for x in a]
    db = [x - mb for x in b]
    denom = math.sqrt(
        sum(x * x for x in da) * sum(x * x for x in db)
    )
    if denom == 0:
        return None
    return sum(x * y for x, y in zip(da, db)) / denom


def _quantum_score(
    jumps: list[float],
    positions: list[int],
    q: int,
) -> dict[str, Any]:
    if not jumps:
        return {
            "magnitude_coverage": 0.0,
            "mean_residual_pages": None,
            "best_phase": None,
            "phase_coverage": 0.0,
        }

    residuals = []
    covered = 0
    for jump in jumps:
        multiple = max(1, round(jump / q))
        residual = abs(jump - multiple * q)
        residuals.append(residual)
        if residual <= 2:
            covered += 1

    best_phase = None
    best_hits = -1
    for phase in range(q):
        hits = 0
        for pos in positions:
            residue = (pos - phase) % q
            dist = min(residue, q - residue)
            if dist <= 2:
                hits += 1
        if hits > best_hits:
            best_hits = hits
            best_phase = phase

    return {
        "magnitude_coverage": covered / len(jumps),
        "mean_residual_pages": statistics.fmean(residuals),
        "best_phase": best_phase,
        "phase_coverage": best_hits / len(positions),
    }


def analyze_rows(
    spec: dict[str, Any],
    rows: list[dict[str, Any]],
    *,
    block: int,
) -> TrialAnalysis:
    expected_steps = int(spec["steps"])
    required_page_size = int(spec["required_page_size"])
    if len(rows) != expected_steps + 1:
        raise ValueError("wrong sample count")
    if [r["step"] for r in rows] != list(range(expected_steps + 1)):
        raise ValueError("non-contiguous steps")

    modes = {r["mode"] for r in rows}
    if len(modes) != 1:
        raise ValueError("mixed modes")
    mode = next(iter(modes))
    if mode not in spec["modes"]:
        raise ValueError("unknown mode")

    cpus = {r["pinned_cpu"] for r in rows}
    if len(cpus) != 1:
        raise ValueError("CPU pin changed")
    pinned_cpu = next(iter(cpus))

    sizes = {r["page_size"] for r in rows}
    if sizes != {required_page_size}:
        raise ValueError("page size mismatch")

    base = rows[0]["memory_current_bytes"]
    current_pages = [
        (r["memory_current_bytes"] - base) / required_page_size
        for r in rows
    ]
    diffs = [
        current_pages[i] - current_pages[i - 1]
        for i in range(1, len(current_pages))
    ]
    threshold = float(spec["significant_jump_pages"])
    positions = [
        i + 1 for i, d in enumerate(diffs) if d >= threshold
    ]
    jumps = [
        d for d in diffs if d >= threshold
    ]
    spacings = [
        b - a for a, b in zip(positions, positions[1:])
    ]

    q_scores: dict[str, Any] = {}
    candidates = [int(q) for q in spec["candidate_quanta_pages"]]
    for q in candidates:
        q_scores[str(q)] = _quantum_score(jumps, positions, q)

    best_q = None
    if jumps:
        # Prefer the largest candidate among equal best magnitude coverage,
        # then lower residual, then higher phase concentration.
        ranked = sorted(
            candidates,
            key=lambda q: (
                q_scores[str(q)]["magnitude_coverage"],
                -(
                    q_scores[str(q)]["mean_residual_pages"]
                    if q_scores[str(q)]["mean_residual_pages"] is not None
                    else 1e9
                ),
                q_scores[str(q)]["phase_coverage"],
                q,
            ),
            reverse=True,
        )
        best_q = ranked[0]

    lo_jump, hi_jump = [float(x) for x in spec["h64_jump_range_pages"]]
    lo_space, hi_space = [float(x) for x in spec["h64_spacing_range_pages"]]
    median_jump = statistics.median(jumps) if jumps else None
    median_spacing = statistics.median(spacings) if spacings else None
    supports_h64 = (
        mode == "touch"
        and len(jumps) >= 2
        and median_jump is not None
        and lo_jump <= median_jump <= hi_jump
        and median_spacing is not None
        and lo_space <= median_spacing <= hi_space
    )

    abs_diffs = [abs(x) for x in diffs]
    ac = {
        str(q): _autocorrelation(abs_diffs, q)
        for q in candidates
    }

    return TrialAnalysis(
        block=block,
        mode=mode,
        pinned_cpu=pinned_cpu,
        page_size=required_page_size,
        steps=expected_steps,
        significant_jump_positions=positions,
        significant_jump_pages=jumps,
        spacing_pages=spacings,
        median_significant_jump_pages=median_jump,
        median_spacing_pages=median_spacing,
        supports_h64=supports_h64,
        best_quantum_pages=best_q,
        quantum_scores=q_scores,
        autocorrelation=ac,
    )


def _analysis_dict(a: TrialAnalysis) -> dict[str, Any]:
    return {
        "block": a.block,
        "mode": a.mode,
        "pinned_cpu": a.pinned_cpu,
        "page_size": a.page_size,
        "steps": a.steps,
        "significant_jump_positions": a.significant_jump_positions,
        "significant_jump_pages": a.significant_jump_pages,
        "spacing_pages": a.spacing_pages,
        "median_significant_jump_pages": a.median_significant_jump_pages,
        "median_spacing_pages": a.median_spacing_pages,
        "supports_h64": a.supports_h64,
        "best_quantum_pages": a.best_quantum_pages,
        "quantum_scores": a.quantum_scores,
        "autocorrelation": a.autocorrelation,
    }


def aggregate(spec: dict[str, Any], root: Path) -> dict[str, Any]:
    trials: list[TrialAnalysis] = []
    sample_rows: list[dict[str, Any]] = []

    for path in sorted(root.rglob("trial-*.csv")):
        stem = path.stem
        # trial-<block>-<order>-<mode>
        parts = stem.split("-")
        if len(parts) != 4:
            raise ValueError(f"unexpected trial filename: {path.name}")
        block = int(parts[1])
        rows = read_trial_csv(path)
        analysis = analyze_rows(spec, rows, block=block)
        trials.append(analysis)

        base = rows[0]["memory_current_bytes"]
        for i, row in enumerate(rows):
            delta_pages = (
                row["memory_current_bytes"] - base
            ) / int(spec["required_page_size"])
            first_diff = None
            if i > 0:
                prev = (
                    rows[i - 1]["memory_current_bytes"] - base
                ) / int(spec["required_page_size"])
                first_diff = delta_pages - prev
            sample_rows.append(
                {
                    "block": block,
                    "mode": analysis.mode,
                    "step": row["step"],
                    "pinned_cpu": row["pinned_cpu"],
                    "page_size": row["page_size"],
                    "memory_current_bytes": row["memory_current_bytes"],
                    "current_delta_pages": delta_pages,
                    "first_diff_pages": first_diff,
                    "anon_bytes": row["anon_bytes"],
                    "kernel_bytes": row["kernel_bytes"],
                    "pagetables_bytes": row["pagetables_bytes"],
                    "minor_faults": row["minor_faults"],
                }
            )

    expected = int(spec["expected_trials"])
    if len(trials) != expected:
        raise ValueError(f"expected {expected} trials, got {len(trials)}")

    identities = {(t.block, t.mode) for t in trials}
    expected_ids = {
        (block, mode)
        for block in range(int(spec["runner_blocks"]))
        for mode in spec["modes"]
    }
    if identities != expected_ids:
        raise ValueError("incomplete trial matrix")

    touch = [t for t in trials if t.mode == "touch"]
    control = [t for t in trials if t.mode == "control"]
    touch_support = sum(t.supports_h64 for t in touch)
    control_support = sum(t.supports_h64 for t in control)
    required = int(spec["h64_required_touch_blocks"])

    if touch_support >= required and control_support == 0:
        decision = "SUPPORT_H64"
    elif touch_support <= 1:
        decision = "REJECT_H64"
    else:
        decision = "INCONCLUSIVE"

    touch_best = [t.best_quantum_pages for t in touch if t.best_quantum_pages]
    best_q_mode = None
    if touch_best:
        counts = {q: touch_best.count(q) for q in set(touch_best)}
        best_q_mode = max(counts, key=lambda q: (counts[q], q))

    return {
        "experiment_id": spec["experiment_id"],
        "execution_status": "PASS",
        "trial_count": len(trials),
        "decision": decision,
        "touch_h64_support_blocks": touch_support,
        "control_h64_support_blocks": control_support,
        "dominant_touch_best_quantum_pages": best_q_mode,
        "trials": [_analysis_dict(t) for t in trials],
        "sample_rows": sample_rows,
        "inference_boundary": (
            "Hosted memcg accounting-quantization probe only; "
            "does not establish hardware DRAM quantization."
        ),
    }


def write_samples_csv(result: dict[str, Any], path: Path) -> None:
    rows = result["sample_rows"]
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "block","mode","step","pinned_cpu","page_size",
        "memory_current_bytes","current_delta_pages","first_diff_pages",
        "anon_bytes","kernel_bytes","pagetables_bytes","minor_faults",
    ]
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


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
    a.add_argument("--out", required=True)
    a.add_argument("--samples-out", required=True)

    args = p.parse_args()
    spec = load_spec(args.spec)

    if args.cmd == "schedule":
        write_schedule(spec, args.block, args.out)
        return

    result = aggregate(spec, Path(args.input_root))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_samples_csv(result, Path(args.samples_out))
    print(json.dumps({
        "status": result["execution_status"],
        "decision": result["decision"],
        "touch_h64_support_blocks": result["touch_h64_support_blocks"],
        "control_h64_support_blocks": result["control_h64_support_blocks"],
        "dominant_touch_best_quantum_pages": result["dominant_touch_best_quantum_pages"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
