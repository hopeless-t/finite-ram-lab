from __future__ import annotations

import argparse
import gc
import json
from pathlib import Path
import statistics
import subprocess
import sys
from typing import Any

import numpy as np

from finite_ram_lab.coupled_numerical_residency import (
    DEFAULT_MODULI,
    _center_in_place,
    _modulus_product,
    _proc_status_kib,
)
from finite_ram_lab.runner_block_probe import environment_fingerprint


ELEMENT_COUNT = 2048 * 2048
COUNT_LOW = 1_000_000
COUNT_SEED476 = 2_051_952
COUNT_SEED474 = 2_068_892
COUNT_HIGH = 3_000_000
COUNT_LEVELS = (COUNT_LOW, COUNT_SEED476, COUNT_SEED474, COUNT_HIGH)
EXPECTED_ACTUAL_PAIR_PAYLOAD_DELTA_BYTES = (COUNT_SEED476 - COUNT_SEED474) * 8

BASE_ORDERS = (
    (COUNT_LOW, COUNT_SEED476, COUNT_SEED474, COUNT_HIGH),
    (COUNT_HIGH, COUNT_SEED474, COUNT_SEED476, COUNT_LOW),
    (COUNT_SEED476, COUNT_LOW, COUNT_HIGH, COUNT_SEED474),
    (COUNT_SEED474, COUNT_HIGH, COUNT_LOW, COUNT_SEED476),
)


def run_child(
    *,
    selected_count: int,
    element_count: int = ELEMENT_COUNT,
) -> dict[str, Any]:
    if not (0 <= selected_count <= element_count):
        raise ValueError("selected_count_invalid")

    product = _modulus_product(DEFAULT_MODULI)
    half = product // 2

    accumulator = np.ones(element_count, dtype=np.int64)
    if selected_count:
        accumulator[:selected_count] = product - 1

    gc.collect()
    baseline = _proc_status_kib()
    base_hwm = baseline["VmHWM"] * 1024
    base_rss = baseline["VmRSS"] * 1024

    _center_in_place(accumulator, product)

    after = _proc_status_kib()
    after_hwm = after["VmHWM"] * 1024
    after_rss = after["VmRSS"] * 1024

    selected_after = int(np.count_nonzero(accumulator < 0))
    if selected_after != selected_count:
        raise RuntimeError("center_semantic_count_mismatch")

    return {
        "schema": "finite-ram-lab.center-temporary-child/v0.1",
        "selected_count": selected_count,
        "element_count": element_count,
        "selected_payload_bytes": selected_count * 8,
        "mask_bytes": element_count,
        "baseline_vm_hwm_bytes": base_hwm,
        "baseline_vm_rss_bytes": base_rss,
        "post_center_vm_hwm_bytes": after_hwm,
        "post_center_vm_rss_bytes": after_rss,
        "hwm_growth_bytes": max(0, after_hwm - base_hwm),
        "rss_delta_bytes": after_rss - base_rss,
        "semantic_count_exact": True,
        "centered_negative_count": selected_after,
        "half": half,
        "modulus_product": product,
    }


def _run_fresh_child(
    *,
    selected_count: int,
    element_count: int,
) -> dict[str, Any]:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "finite_ram_lab.center_temporary_probe",
            "--child",
            "--selected-count",
            str(selected_count),
            "--element-count",
            str(element_count),
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"child_failed:selected={selected_count}:{completed.stderr[-2500:]}"
        )
    return json.loads(completed.stdout)


def run_block(
    *,
    block_id: int,
    element_count: int = ELEMENT_COUNT,
) -> dict[str, Any]:
    if not (0 <= block_id < 8):
        raise ValueError("block_id_invalid")

    first = BASE_ORDERS[block_id % len(BASE_ORDERS)]
    orders = (first, tuple(reversed(first)))
    observations = {count: [] for count in COUNT_LEVELS}
    execution_rows = []

    for replicate, order in enumerate(orders):
        row = {"replicate": replicate, "order": list(order), "results": []}
        for selected_count in order:
            result = _run_fresh_child(
                selected_count=selected_count,
                element_count=element_count,
            )
            if not result["semantic_count_exact"]:
                raise RuntimeError("semantic_gate_failed")
            observations[selected_count].append(result)
            row["results"].append(result)
        execution_rows.append(row)

    summaries = []
    for selected_count in COUNT_LEVELS:
        values = observations[selected_count]
        summaries.append(
            {
                "selected_count": selected_count,
                "sample_count": len(values),
                "selected_payload_bytes": selected_count * 8,
                "median_hwm_growth_bytes": statistics.median(
                    int(item["hwm_growth_bytes"]) for item in values
                ),
                "median_rss_delta_bytes": statistics.median(
                    int(item["rss_delta_bytes"]) for item in values
                ),
            }
        )

    return {
        "schema": "finite-ram-lab.center-temporary-block/v0.1",
        "claim_ceiling": "ISOLATED_NUMPY_BOOLEAN_INDEX_CENTERING",
        "block_id": block_id,
        "environment": environment_fingerprint(),
        "element_count": element_count,
        "count_levels": list(COUNT_LEVELS),
        "expected_actual_pair_payload_delta_bytes": EXPECTED_ACTUAL_PAIR_PAYLOAD_DELTA_BYTES,
        "execution_rows": execution_rows,
        "condition_summaries": summaries,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--selected-count", type=int)
    parser.add_argument("--element-count", type=int, default=ELEMENT_COUNT)
    parser.add_argument("--block-id", type=int)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    if args.child:
        if args.selected_count is None:
            parser.error("--selected-count required with --child")
        print(json.dumps(run_child(
            selected_count=args.selected_count,
            element_count=args.element_count,
        ), sort_keys=True))
        return 0

    if args.block_id is None or args.out is None:
        parser.error("--block-id and --out required in block mode")
    payload = run_block(block_id=args.block_id, element_count=args.element_count)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "block_id": payload["block_id"],
        "environment": payload["environment"],
        "condition_summaries": payload["condition_summaries"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
