from __future__ import annotations

import argparse
import gc
import json
import mmap
import os
from pathlib import Path
import statistics
import subprocess
import sys
from typing import Sequence

from finite_ram_lab.obligation_residency import DEFAULT_MODULI, compare_crt_residency


def _unsigned_bytes_for_modulus(modulus: int) -> int:
    return max(1, ((modulus - 1).bit_length() + 7) // 8)


def expected_live_bytes(strategy: str, element_count: int, moduli: Sequence[int]) -> int:
    mods = tuple(int(item) for item in moduli)
    product = 1
    for modulus in mods:
        product *= modulus
    accumulator_bytes = element_count * _unsigned_bytes_for_modulus(product)
    lane_bytes = tuple(element_count * _unsigned_bytes_for_modulus(m) for m in mods)
    if strategy == "ALL_RESIDENT":
        return accumulator_bytes + sum(lane_bytes)
    if strategy == "STREAMED_FOLD":
        return accumulator_bytes + max(lane_bytes)
    raise ValueError("strategy_invalid")


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


def _touch(mapping: mmap.mmap, size: int) -> None:
    page = mmap.PAGESIZE
    for offset in range(0, size, page):
        mapping[offset : offset + 1] = b"\x01"
    if size:
        mapping[size - 1 : size] = b"\x01"


def _semantic_gate(moduli: Sequence[int]) -> None:
    result = compare_crt_residency(
        ((3, 5), (-2, 7)),
        ((11, -4), (6, 9)),
        moduli,
    )
    if not result.all_resident.exact_match or not result.streamed.exact_match:
        raise RuntimeError("semantic_gate_failed")
    if result.all_resident.output != result.streamed.output:
        raise RuntimeError("semantic_gate_strategy_mismatch")


def run_child(strategy: str, element_count: int, lane_count: int) -> dict[str, object]:
    if strategy not in {"ALL_RESIDENT", "STREAMED_FOLD"}:
        raise ValueError("strategy_invalid")
    if element_count <= 0:
        raise ValueError("element_count_invalid")
    if lane_count < 2 or lane_count > len(DEFAULT_MODULI):
        raise ValueError("lane_count_invalid")

    moduli = DEFAULT_MODULI[:lane_count]
    _semantic_gate(moduli)
    gc.collect()
    baseline = _proc_status_kib()

    product = 1
    for modulus in moduli:
        product *= modulus
    accumulator_size = element_count * _unsigned_bytes_for_modulus(product)
    lane_sizes = tuple(
        element_count * _unsigned_bytes_for_modulus(modulus)
        for modulus in moduli
    )

    accumulator = mmap.mmap(-1, accumulator_size)
    _touch(accumulator, accumulator_size)

    observed_hwm_kib = _proc_status_kib()["VmHWM"]
    lane_maps: list[mmap.mmap] = []
    try:
        if strategy == "ALL_RESIDENT":
            for lane_size in lane_sizes:
                lane = mmap.mmap(-1, lane_size)
                _touch(lane, lane_size)
                lane_maps.append(lane)
                observed_hwm_kib = max(observed_hwm_kib, _proc_status_kib()["VmHWM"])
        else:
            for lane_size in lane_sizes:
                lane = mmap.mmap(-1, lane_size)
                _touch(lane, lane_size)
                observed_hwm_kib = max(observed_hwm_kib, _proc_status_kib()["VmHWM"])
                lane.close()
        at_peak = _proc_status_kib()
    finally:
        for lane in lane_maps:
            lane.close()
        accumulator.close()

    after_cleanup = _proc_status_kib()
    normalized_peak_growth_bytes = max(
        0,
        (observed_hwm_kib - baseline["VmHWM"]) * 1024,
    )
    return {
        "strategy": strategy,
        "pid": os.getpid(),
        "page_size": mmap.PAGESIZE,
        "element_count": element_count,
        "lane_count": lane_count,
        "moduli": list(moduli),
        "accumulator_size_bytes": accumulator_size,
        "lane_sizes_bytes": list(lane_sizes),
        "expected_live_bytes": expected_live_bytes(strategy, element_count, moduli),
        "baseline_vm_hwm_bytes": baseline["VmHWM"] * 1024,
        "baseline_vm_rss_bytes": baseline["VmRSS"] * 1024,
        "observed_vm_hwm_bytes": observed_hwm_kib * 1024,
        "normalized_peak_growth_bytes": normalized_peak_growth_bytes,
        "at_peak_vm_rss_bytes": at_peak["VmRSS"] * 1024,
        "after_cleanup_vm_rss_bytes": after_cleanup["VmRSS"] * 1024,
        "semantic_exact": True,
    }


def _run_fresh_child(strategy: str, element_count: int, lane_count: int) -> dict[str, object]:
    command = [
        sys.executable,
        "-m",
        "finite_ram_lab.representation_peak_probe",
        "--child",
        "--strategy",
        strategy,
        "--elements",
        str(element_count),
        "--lanes",
        str(lane_count),
    ]
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "child_failed:" + strategy + ":" + completed.stderr[-2000:]
        )
    return json.loads(completed.stdout)


def run_matched_panel(
    *,
    pairs: int = 6,
    element_count: int = 4_194_304,
    lane_count: int = 7,
) -> dict[str, object]:
    if pairs <= 0:
        raise ValueError("pairs_invalid")

    pair_rows = []
    for repetition in range(pairs):
        if repetition % 2 == 0:
            order = ("ALL_RESIDENT", "STREAMED_FOLD")
        else:
            order = ("STREAMED_FOLD", "ALL_RESIDENT")

        results = {}
        for strategy in order:
            results[strategy] = _run_fresh_child(strategy, element_count, lane_count)

        reference = results["ALL_RESIDENT"]
        treatment = results["STREAMED_FOLD"]
        delta = (
            int(treatment["normalized_peak_growth_bytes"])
            - int(reference["normalized_peak_growth_bytes"])
        )
        pair_rows.append(
            {
                "repetition": repetition,
                "order": list(order),
                "reference": reference,
                "treatment": treatment,
                "treatment_minus_reference_peak_bytes": delta,
            }
        )

    deltas = [row["treatment_minus_reference_peak_bytes"] for row in pair_rows]
    negative = sum(delta < 0 for delta in deltas)
    positive = sum(delta > 0 for delta in deltas)
    zeros = sum(delta == 0 for delta in deltas)
    classification = (
        "PHYSICAL_PEAK_SCHEDULE_EFFECT_REPLICATED"
        if negative == pairs
        else "PHYSICAL_PEAK_SCHEDULE_EFFECT_PARTIAL"
    )

    return {
        "schema": "finite-ram-lab.representation-peak-panel/v0.1",
        "claim_ceiling": "HOSTED_LINUX_MMAP_REPRESENTATION_SCHEDULE_PROXY",
        "pairs": pairs,
        "element_count": element_count,
        "lane_count": lane_count,
        "pair_rows": pair_rows,
        "summary": {
            "classification": classification,
            "negative_count": negative,
            "positive_count": positive,
            "zero_count": zeros,
            "median_treatment_minus_reference_peak_bytes": statistics.median(deltas),
            "deltas_bytes": deltas,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--strategy", choices=("ALL_RESIDENT", "STREAMED_FOLD"))
    parser.add_argument("--elements", type=int, default=4_194_304)
    parser.add_argument("--lanes", type=int, default=7)
    parser.add_argument("--pairs", type=int, default=6)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    if args.child:
        if args.strategy is None:
            parser.error("--strategy is required with --child")
        print(json.dumps(run_child(args.strategy, args.elements, args.lanes), sort_keys=True))
        return 0

    if args.out is None:
        parser.error("--out is required for panel mode")
    payload = run_matched_panel(
        pairs=args.pairs,
        element_count=args.elements,
        lane_count=args.lanes,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
