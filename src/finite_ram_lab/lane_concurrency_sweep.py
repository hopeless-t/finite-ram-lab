from __future__ import annotations

import argparse
import gc
import json
from pathlib import Path
import statistics
import subprocess
import sys
import time
from typing import Any

import numpy as np

from finite_ram_lab.coupled_numerical_residency import (
    DEFAULT_MODULI,
    _center_in_place,
    _conservative_bound,
    _fold_lane_in_place,
    _make_inputs,
    _modulus_product,
    _proc_status_kib,
    _produce_residue_lane,
    _validate_exact_rank1,
    _validate_moduli,
)


Q_VALUES = (1, 2, 4, 7)
BALANCED_ORDERS = (
    (1, 2, 4, 7),
    (7, 4, 2, 1),
    (2, 1, 7, 4),
    (4, 7, 1, 2),
)


def logical_live_bytes(size: int, q: int) -> int:
    if q not in Q_VALUES:
        raise ValueError("q_invalid")
    elements = size * size
    return elements * (8 + q)


def run_child(
    *,
    q: int,
    size: int,
    lane_count: int,
    seed: int,
    value_limit: int,
    tile_rows: int,
) -> dict[str, Any]:
    if q not in Q_VALUES:
        raise ValueError("q_invalid")
    if lane_count != 7:
        raise ValueError("b469_requires_seven_lanes")
    if q > lane_count:
        raise ValueError("q_exceeds_lane_count")

    moduli = _validate_moduli(DEFAULT_MODULI[:lane_count])
    left, right = _make_inputs(size, seed, value_limit)
    bound = _conservative_bound(left, right)
    product = _modulus_product(moduli)
    if product <= 2 * bound:
        raise RuntimeError("crt_uniqueness_not_proven")

    gc.collect()
    baseline = _proc_status_kib()
    peak_kib = baseline["VmHWM"]
    accumulator = np.zeros((size, size), dtype=np.int64)
    current_modulus = 1

    start_time = time.perf_counter()

    for group_start in range(0, lane_count, q):
        group_moduli = moduli[group_start : group_start + q]
        group_lanes: list[np.ndarray] = []

        for modulus in group_moduli:
            lane = _produce_residue_lane(left, right, modulus)
            group_lanes.append(lane)
            peak_kib = max(peak_kib, _proc_status_kib()["VmHWM"])

        for lane, modulus in zip(group_lanes, group_moduli, strict=True):
            current_modulus = _fold_lane_in_place(
                accumulator,
                lane,
                current_modulus=current_modulus,
                lane_modulus=modulus,
                tile_rows=tile_rows,
            )
            peak_kib = max(peak_kib, _proc_status_kib()["VmHWM"])

        group_lanes.clear()
        gc.collect()

    _center_in_place(accumulator, current_modulus)
    peak_kib = max(peak_kib, _proc_status_kib()["VmHWM"])
    work_seconds = time.perf_counter() - start_time

    exact, output_sha256 = _validate_exact_rank1(
        accumulator,
        left,
        right,
        tile_rows=tile_rows,
    )

    return {
        "schema": "finite-ram-lab.lane-concurrency-child/v0.1",
        "q": q,
        "size": size,
        "lane_count": lane_count,
        "seed": seed,
        "value_limit": value_limit,
        "tile_rows": tile_rows,
        "semantic_exact": exact,
        "output_sha256": output_sha256,
        "logical_live_bytes": logical_live_bytes(size, q),
        "baseline_vm_hwm_bytes": baseline["VmHWM"] * 1024,
        "work_peak_vm_hwm_bytes": peak_kib * 1024,
        "normalized_peak_growth_bytes": max(
            0,
            (peak_kib - baseline["VmHWM"]) * 1024,
        ),
        "work_seconds": work_seconds,
    }


def _run_fresh_child(
    *,
    q: int,
    size: int,
    lane_count: int,
    seed: int,
    value_limit: int,
    tile_rows: int,
) -> dict[str, Any]:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "finite_ram_lab.lane_concurrency_sweep",
            "--child",
            "--q",
            str(q),
            "--size",
            str(size),
            "--lanes",
            str(lane_count),
            "--seed",
            str(seed),
            "--value-limit",
            str(value_limit),
            "--tile-rows",
            str(tile_rows),
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=180,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"child_failed:q={q}:{completed.stderr[-3000:]}")
    return json.loads(completed.stdout)


def _pareto_q(rows: list[dict[str, Any]]) -> list[int]:
    nondominated = []
    for candidate in rows:
        dominated = False
        for other in rows:
            if other["q"] == candidate["q"]:
                continue
            no_worse = (
                other["median_peak_bytes"] <= candidate["median_peak_bytes"]
                and other["median_work_seconds"] <= candidate["median_work_seconds"]
            )
            strictly_better = (
                other["median_peak_bytes"] < candidate["median_peak_bytes"]
                or other["median_work_seconds"] < candidate["median_work_seconds"]
            )
            if no_worse and strictly_better:
                dominated = True
                break
        if not dominated:
            nondominated.append(int(candidate["q"]))
    return sorted(nondominated)


def run_sweep(
    *,
    repetitions: int = 4,
    size: int = 2048,
    lane_count: int = 7,
    seed: int = 469,
    value_limit: int = 50,
    tile_rows: int = 64,
) -> dict[str, Any]:
    if repetitions != 4:
        raise ValueError("b469_requires_four_repetitions")

    observations: dict[int, list[dict[str, Any]]] = {q: [] for q in Q_VALUES}
    execution_rows = []

    for repetition, order in enumerate(BALANCED_ORDERS):
        row = {"repetition": repetition, "order": list(order), "results": []}
        for q in order:
            result = _run_fresh_child(
                q=q,
                size=size,
                lane_count=lane_count,
                seed=seed,
                value_limit=value_limit,
                tile_rows=tile_rows,
            )
            if not result["semantic_exact"]:
                raise RuntimeError(f"semantic_gate_failed:q={q}")
            observations[q].append(result)
            row["results"].append(result)
        execution_rows.append(row)

    digests = {
        result["output_sha256"]
        for values in observations.values()
        for result in values
    }
    if len(digests) != 1:
        raise RuntimeError("cross_q_output_digest_mismatch")

    summary_rows = []
    for q in Q_VALUES:
        values = observations[q]
        peaks = [int(item["normalized_peak_growth_bytes"]) for item in values]
        times = [float(item["work_seconds"]) for item in values]
        summary_rows.append(
            {
                "q": q,
                "logical_live_bytes": logical_live_bytes(size, q),
                "median_peak_bytes": statistics.median(peaks),
                "min_peak_bytes": min(peaks),
                "max_peak_bytes": max(peaks),
                "median_work_seconds": statistics.median(times),
                "min_work_seconds": min(times),
                "max_work_seconds": max(times),
                "semantic_exact_count": sum(bool(item["semantic_exact"]) for item in values),
                "samples": len(values),
            }
        )

    q1 = next(row for row in summary_rows if row["q"] == 1)
    for row in summary_rows:
        row["peak_delta_vs_q1_bytes"] = row["median_peak_bytes"] - q1["median_peak_bytes"]
        row["latency_ratio_vs_q1"] = (
            row["median_work_seconds"] / q1["median_work_seconds"]
        )

    pareto = _pareto_q(summary_rows)

    return {
        "schema": "finite-ram-lab.lane-concurrency-sweep/v0.1",
        "claim_ceiling": "HOSTED_NUMPY_GROUPED_RESIDUE_CONCURRENCY_SWEEP",
        "q_values": list(Q_VALUES),
        "repetitions": repetitions,
        "balanced_orders": [list(order) for order in BALANCED_ORDERS],
        "size": size,
        "lane_count": lane_count,
        "seed": seed,
        "value_limit": value_limit,
        "tile_rows": tile_rows,
        "output_sha256": next(iter(digests)),
        "execution_rows": execution_rows,
        "summary_rows": summary_rows,
        "pareto_q": pareto,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--q", type=int)
    parser.add_argument("--size", type=int, default=2048)
    parser.add_argument("--lanes", type=int, default=7)
    parser.add_argument("--seed", type=int, default=469)
    parser.add_argument("--value-limit", type=int, default=50)
    parser.add_argument("--tile-rows", type=int, default=64)
    parser.add_argument("--repetitions", type=int, default=4)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    if args.child:
        if args.q is None:
            parser.error("--q required with --child")
        print(
            json.dumps(
                run_child(
                    q=args.q,
                    size=args.size,
                    lane_count=args.lanes,
                    seed=args.seed,
                    value_limit=args.value_limit,
                    tile_rows=args.tile_rows,
                ),
                sort_keys=True,
            )
        )
        return 0

    if args.out is None:
        parser.error("--out required in sweep mode")
    payload = run_sweep(
        repetitions=args.repetitions,
        size=args.size,
        lane_count=args.lanes,
        seed=args.seed,
        value_limit=args.value_limit,
        tile_rows=args.tile_rows,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "summary_rows": payload["summary_rows"],
                "pareto_q": payload["pareto_q"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
