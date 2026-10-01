from __future__ import annotations

import argparse
import gc
import hashlib
import json
from math import gcd
from pathlib import Path
import statistics
import subprocess
import sys
import time
from typing import Sequence

import numpy as np


DEFAULT_MODULI = (127, 125, 121, 119, 113, 109, 107)


def _proc_status_kib() -> dict[str, int]:
    result: dict[str, int] = {}
    for line in Path("/proc/self/status").read_text().splitlines():
        if line.startswith(("VmRSS:", "VmHWM:")):
            key, rest = line.split(":", 1)
            fields = rest.strip().split()
            if len(fields) < 2 or fields[1] != "kB":
                raise RuntimeError("proc_status_unit_unexpected")
            result[key] = int(fields[0])
    if "VmRSS" not in result or "VmHWM" not in result:
        raise RuntimeError("proc_status_missing_memory_fields")
    return result


def _validate_moduli(moduli: Sequence[int]) -> tuple[int, ...]:
    values = tuple(int(item) for item in moduli)
    if not values:
        raise ValueError("moduli_empty")
    if any(item <= 1 or item > 255 for item in values):
        raise ValueError("modulus_invalid")
    for index, left in enumerate(values):
        for right in values[index + 1 :]:
            if gcd(left, right) != 1:
                raise ValueError("moduli_not_pairwise_coprime")
    product = 1
    for modulus in values:
        product *= modulus
    if product >= 2**63:
        raise ValueError("crt_product_exceeds_int64")
    return values


def _modulus_product(moduli: Sequence[int]) -> int:
    product = 1
    for modulus in moduli:
        product *= int(modulus)
    return product


def _make_inputs(size: int, seed: int, value_limit: int) -> tuple[np.ndarray, np.ndarray]:
    if size <= 0:
        raise ValueError("size_invalid")
    if value_limit <= 0 or value_limit > 1000:
        raise ValueError("value_limit_invalid")
    rng = np.random.default_rng(seed)
    left = rng.integers(
        -value_limit,
        value_limit + 1,
        size=size,
        dtype=np.int64,
    )
    right = rng.integers(
        -value_limit,
        value_limit + 1,
        size=size,
        dtype=np.int64,
    )
    return left, right


def _conservative_bound(left: np.ndarray, right: np.ndarray) -> int:
    return int(np.max(np.abs(left))) * int(np.max(np.abs(right)))


def _produce_residue_lane(
    left: np.ndarray,
    right: np.ndarray,
    modulus: int,
) -> np.ndarray:
    left_mod = np.mod(left, modulus).astype(np.uint16, copy=False)
    right_mod = np.mod(right, modulus).astype(np.uint16, copy=False)
    lane = np.multiply.outer(left_mod, right_mod)
    np.remainder(lane, modulus, out=lane)
    return lane.astype(np.uint8, copy=False)


def _fold_lane_in_place(
    accumulator: np.ndarray,
    lane: np.ndarray,
    *,
    current_modulus: int,
    lane_modulus: int,
    tile_rows: int,
) -> int:
    inverse = pow(current_modulus % lane_modulus, -1, lane_modulus)
    rows = accumulator.shape[0]

    for start in range(0, rows, tile_rows):
        stop = min(rows, start + tile_rows)
        acc_view = accumulator[start:stop]
        lane_view = lane[start:stop]

        delta = lane_view.astype(np.int64)
        delta -= np.remainder(acc_view, lane_modulus)
        np.remainder(delta, lane_modulus, out=delta)
        delta *= inverse
        np.remainder(delta, lane_modulus, out=delta)
        acc_view += current_modulus * delta

    return current_modulus * lane_modulus


def _center_in_place(accumulator: np.ndarray, modulus_product: int) -> None:
    half = modulus_product // 2
    mask = accumulator > half
    accumulator[mask] -= modulus_product


def _validate_exact_rank1(
    accumulator: np.ndarray,
    left: np.ndarray,
    right: np.ndarray,
    *,
    tile_rows: int,
) -> tuple[bool, str]:
    digest = hashlib.sha256()
    rows = accumulator.shape[0]
    exact = True

    for start in range(0, rows, tile_rows):
        stop = min(rows, start + tile_rows)
        expected = np.multiply.outer(left[start:stop], right)
        actual = accumulator[start:stop]
        if not np.array_equal(actual, expected):
            exact = False
        digest.update(actual.astype("<i8", copy=False).tobytes(order="C"))

    return exact, digest.hexdigest()


def _logical_bytes(strategy: str, size: int, lane_count: int) -> int:
    elements = size * size
    accumulator = elements * 8
    if strategy == "ALL_RESIDENT":
        return accumulator + elements * lane_count
    if strategy == "STREAMED_FOLD":
        return accumulator + elements
    raise ValueError("strategy_invalid")


def run_child(
    *,
    strategy: str,
    size: int,
    lane_count: int,
    seed: int,
    value_limit: int,
    tile_rows: int,
) -> dict[str, object]:
    if strategy not in {"ALL_RESIDENT", "STREAMED_FOLD"}:
        raise ValueError("strategy_invalid")
    if lane_count < 2 or lane_count > len(DEFAULT_MODULI):
        raise ValueError("lane_count_invalid")
    if tile_rows <= 0:
        raise ValueError("tile_rows_invalid")

    moduli = _validate_moduli(DEFAULT_MODULI[:lane_count])
    left, right = _make_inputs(size, seed, value_limit)
    bound = _conservative_bound(left, right)
    modulus_product = _modulus_product(moduli)
    if modulus_product <= 2 * bound:
        raise RuntimeError("crt_uniqueness_not_proven")

    gc.collect()
    baseline = _proc_status_kib()
    peak_kib = baseline["VmHWM"]

    start = time.perf_counter()
    accumulator = np.zeros((size, size), dtype=np.int64)
    peak_kib = max(peak_kib, _proc_status_kib()["VmHWM"])
    current_modulus = 1
    lane_checksums: list[str] = []

    if strategy == "ALL_RESIDENT":
        lanes: list[np.ndarray] = []
        for modulus in moduli:
            lane = _produce_residue_lane(left, right, modulus)
            lanes.append(lane)
            lane_checksums.append(hashlib.sha256(lane.tobytes(order="C")).hexdigest())
            peak_kib = max(peak_kib, _proc_status_kib()["VmHWM"])

        for lane, modulus in zip(lanes, moduli, strict=True):
            current_modulus = _fold_lane_in_place(
                accumulator,
                lane,
                current_modulus=current_modulus,
                lane_modulus=modulus,
                tile_rows=tile_rows,
            )
            peak_kib = max(peak_kib, _proc_status_kib()["VmHWM"])
    else:
        for modulus in moduli:
            lane = _produce_residue_lane(left, right, modulus)
            lane_checksums.append(hashlib.sha256(lane.tobytes(order="C")).hexdigest())
            peak_kib = max(peak_kib, _proc_status_kib()["VmHWM"])
            current_modulus = _fold_lane_in_place(
                accumulator,
                lane,
                current_modulus=current_modulus,
                lane_modulus=modulus,
                tile_rows=tile_rows,
            )
            peak_kib = max(peak_kib, _proc_status_kib()["VmHWM"])
            del lane
            gc.collect()

    _center_in_place(accumulator, current_modulus)
    peak_kib = max(peak_kib, _proc_status_kib()["VmHWM"])
    work_seconds = time.perf_counter() - start

    exact, output_sha256 = _validate_exact_rank1(
        accumulator,
        left,
        right,
        tile_rows=tile_rows,
    )
    after_validation = _proc_status_kib()

    return {
        "schema": "finite-ram-lab.coupled-numerical-child/v0.1",
        "strategy": strategy,
        "size": size,
        "element_count": size * size,
        "lane_count": lane_count,
        "moduli": list(moduli),
        "modulus_product": modulus_product,
        "conservative_abs_bound": bound,
        "seed": seed,
        "value_limit": value_limit,
        "tile_rows": tile_rows,
        "semantic_exact": exact,
        "output_sha256": output_sha256,
        "lane_sha256": lane_checksums,
        "logical_live_bytes": _logical_bytes(strategy, size, lane_count),
        "baseline_vm_hwm_bytes": baseline["VmHWM"] * 1024,
        "baseline_vm_rss_bytes": baseline["VmRSS"] * 1024,
        "work_peak_vm_hwm_bytes": peak_kib * 1024,
        "normalized_peak_growth_bytes": max(
            0,
            (peak_kib - baseline["VmHWM"]) * 1024,
        ),
        "work_seconds": work_seconds,
        "post_validation_vm_hwm_bytes": after_validation["VmHWM"] * 1024,
        "post_validation_vm_rss_bytes": after_validation["VmRSS"] * 1024,
    }


def _run_fresh_child(
    *,
    strategy: str,
    size: int,
    lane_count: int,
    seed: int,
    value_limit: int,
    tile_rows: int,
) -> dict[str, object]:
    command = [
        sys.executable,
        "-m",
        "finite_ram_lab.coupled_numerical_residency",
        "--child",
        "--strategy",
        strategy,
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
    ]
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        timeout=180,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"child_failed:{strategy}:{completed.stderr[-3000:]}"
        )
    return json.loads(completed.stdout)


def run_matched_panel(
    *,
    pairs: int = 6,
    size: int = 2048,
    lane_count: int = 7,
    seed: int = 463,
    value_limit: int = 50,
    tile_rows: int = 64,
) -> dict[str, object]:
    if pairs <= 0:
        raise ValueError("pairs_invalid")

    rows = []
    for repetition in range(pairs):
        order = (
            ("ALL_RESIDENT", "STREAMED_FOLD")
            if repetition % 2 == 0
            else ("STREAMED_FOLD", "ALL_RESIDENT")
        )
        results: dict[str, dict[str, object]] = {}

        for strategy in order:
            results[strategy] = _run_fresh_child(
                strategy=strategy,
                size=size,
                lane_count=lane_count,
                seed=seed,
                value_limit=value_limit,
                tile_rows=tile_rows,
            )

        reference = results["ALL_RESIDENT"]
        treatment = results["STREAMED_FOLD"]
        semantic_match = bool(reference["semantic_exact"]) and bool(
            treatment["semantic_exact"]
        ) and reference["output_sha256"] == treatment["output_sha256"]
        if not semantic_match:
            raise RuntimeError("matched_pair_semantic_gate_failed")

        peak_delta = (
            int(treatment["normalized_peak_growth_bytes"])
            - int(reference["normalized_peak_growth_bytes"])
        )
        latency_delta = (
            float(treatment["work_seconds"])
            - float(reference["work_seconds"])
        )
        rows.append(
            {
                "repetition": repetition,
                "order": list(order),
                "semantic_match": semantic_match,
                "reference": reference,
                "treatment": treatment,
                "treatment_minus_reference_peak_bytes": peak_delta,
                "treatment_minus_reference_seconds": latency_delta,
                "latency_ratio_treatment_over_reference": (
                    float(treatment["work_seconds"])
                    / float(reference["work_seconds"])
                ),
            }
        )

    peak_deltas = [row["treatment_minus_reference_peak_bytes"] for row in rows]
    latency_ratios = [row["latency_ratio_treatment_over_reference"] for row in rows]
    negative = sum(delta < 0 for delta in peak_deltas)
    positive = sum(delta > 0 for delta in peak_deltas)
    zeros = sum(delta == 0 for delta in peak_deltas)
    classification = (
        "COUPLED_EXACT_PEAK_EFFECT_REPLICATED"
        if negative == pairs
        else "COUPLED_EXACT_PEAK_EFFECT_PARTIAL"
    )

    return {
        "schema": "finite-ram-lab.coupled-numerical-panel/v0.1",
        "claim_ceiling": "HOSTED_NUMPY_RANK1_RESIDUE_CRT_IMPLEMENTATION",
        "pairs": pairs,
        "size": size,
        "lane_count": lane_count,
        "seed": seed,
        "value_limit": value_limit,
        "tile_rows": tile_rows,
        "pair_rows": rows,
        "summary": {
            "classification": classification,
            "semantic_match_count": sum(bool(row["semantic_match"]) for row in rows),
            "negative_peak_count": negative,
            "positive_peak_count": positive,
            "zero_peak_count": zeros,
            "median_treatment_minus_reference_peak_bytes": statistics.median(peak_deltas),
            "median_latency_ratio_treatment_over_reference": statistics.median(latency_ratios),
            "peak_deltas_bytes": peak_deltas,
            "latency_ratios": latency_ratios,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--strategy", choices=("ALL_RESIDENT", "STREAMED_FOLD"))
    parser.add_argument("--size", type=int, default=2048)
    parser.add_argument("--lanes", type=int, default=7)
    parser.add_argument("--seed", type=int, default=463)
    parser.add_argument("--value-limit", type=int, default=50)
    parser.add_argument("--tile-rows", type=int, default=64)
    parser.add_argument("--pairs", type=int, default=6)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    if args.child:
        if args.strategy is None:
            parser.error("--strategy is required with --child")
        print(
            json.dumps(
                run_child(
                    strategy=args.strategy,
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
        parser.error("--out is required for panel mode")

    payload = run_matched_panel(
        pairs=args.pairs,
        size=args.size,
        lane_count=args.lanes,
        seed=args.seed,
        value_limit=args.value_limit,
        tile_rows=args.tile_rows,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
