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

from finite_ram_lab.center_temporary_probe import (
    COUNT_HIGH,
    COUNT_SEED474,
    COUNT_SEED476,
    ELEMENT_COUNT,
)
from finite_ram_lab.coupled_numerical_residency import (
    DEFAULT_MODULI,
    _center_in_place,
    _modulus_product,
    _proc_status_kib,
)
from finite_ram_lab.runner_block_probe import environment_fingerprint


STRATEGIES = ("BOOLEAN_INDEX", "TILED_WHERE")
COUNTS = (COUNT_SEED476, COUNT_SEED474, COUNT_HIGH)
TILE_ELEMENTS = 262_144


def center_tiled_where(
    accumulator: np.ndarray,
    modulus_product: int,
    *,
    tile_elements: int = TILE_ELEMENTS,
) -> None:
    if accumulator.dtype != np.int64:
        raise ValueError("accumulator_dtype_invalid")
    if tile_elements <= 0:
        raise ValueError("tile_elements_invalid")

    flat = accumulator.reshape(-1)
    half = modulus_product // 2
    mask = np.empty(min(tile_elements, flat.size), dtype=np.bool_)

    for start in range(0, flat.size, tile_elements):
        stop = min(flat.size, start + tile_elements)
        view = flat[start:stop]
        live_mask = mask[: stop - start]
        np.greater(view, half, out=live_mask)
        np.subtract(
            view,
            modulus_product,
            out=view,
            where=live_mask,
        )


def run_child(
    *,
    strategy: str,
    selected_count: int,
    element_count: int = ELEMENT_COUNT,
    tile_elements: int = TILE_ELEMENTS,
) -> dict[str, Any]:
    if strategy not in STRATEGIES:
        raise ValueError("strategy_invalid")
    if not (0 <= selected_count <= element_count):
        raise ValueError("selected_count_invalid")

    product = _modulus_product(DEFAULT_MODULI)
    accumulator = np.ones(element_count, dtype=np.int64)
    if selected_count:
        accumulator[:selected_count] = product - 1

    gc.collect()
    baseline = _proc_status_kib()
    base_hwm = baseline["VmHWM"] * 1024
    base_rss = baseline["VmRSS"] * 1024

    start = time.perf_counter()
    if strategy == "BOOLEAN_INDEX":
        _center_in_place(accumulator, product)
    else:
        center_tiled_where(
            accumulator,
            product,
            tile_elements=tile_elements,
        )
    elapsed = time.perf_counter() - start

    after = _proc_status_kib()
    after_hwm = after["VmHWM"] * 1024
    after_rss = after["VmRSS"] * 1024

    negative_count = int(np.count_nonzero(accumulator < 0))
    if negative_count != selected_count:
        raise RuntimeError("center_semantic_count_mismatch")
    if selected_count:
        if not np.all(accumulator[:selected_count] == -1):
            raise RuntimeError("selected_value_mismatch")
    if selected_count < element_count:
        if not np.all(accumulator[selected_count:] == 1):
            raise RuntimeError("unselected_value_mismatch")

    return {
        "schema": "finite-ram-lab.center-repair-child/v0.1",
        "strategy": strategy,
        "selected_count": selected_count,
        "element_count": element_count,
        "tile_elements": tile_elements,
        "semantic_exact": True,
        "hwm_growth_bytes": max(0, after_hwm - base_hwm),
        "rss_delta_bytes": after_rss - base_rss,
        "elapsed_seconds": elapsed,
    }


def _run_fresh_child(
    *,
    strategy: str,
    selected_count: int,
) -> dict[str, Any]:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "finite_ram_lab.center_repair",
            "--child",
            "--strategy",
            strategy,
            "--selected-count",
            str(selected_count),
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"child_failed:{strategy}:{selected_count}:{completed.stderr[-2500:]}"
        )
    return json.loads(completed.stdout)


CONDITIONS = tuple(
    (strategy, count)
    for strategy in STRATEGIES
    for count in COUNTS
)


def run_block(*, block_id: int) -> dict[str, Any]:
    if not (0 <= block_id < 8):
        raise ValueError("block_id_invalid")

    # Six-condition cyclic schedule; the extra two blocks repeat two rotations.
    shift = block_id % len(CONDITIONS)
    order = CONDITIONS[shift:] + CONDITIONS[:shift]
    results = []

    for strategy, count in order:
        observed = _run_fresh_child(
            strategy=strategy,
            selected_count=count,
        )
        if not observed["semantic_exact"]:
            raise RuntimeError("semantic_gate_failed")
        results.append(observed)

    return {
        "schema": "finite-ram-lab.center-repair-block/v0.1",
        "claim_ceiling": "ISOLATED_EXACT_CENTER_REPAIR",
        "block_id": block_id,
        "environment": environment_fingerprint(),
        "conditions": [
            {"strategy": strategy, "selected_count": count}
            for strategy, count in CONDITIONS
        ],
        "execution_order": [
            {"strategy": strategy, "selected_count": count}
            for strategy, count in order
        ],
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--strategy", choices=STRATEGIES)
    parser.add_argument("--selected-count", type=int)
    parser.add_argument("--block-id", type=int)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    if args.child:
        if args.strategy is None or args.selected_count is None:
            parser.error("--strategy and --selected-count required with --child")
        print(json.dumps(run_child(
            strategy=args.strategy,
            selected_count=args.selected_count,
        ), sort_keys=True))
        return 0

    if args.block_id is None or args.out is None:
        parser.error("--block-id and --out required in block mode")
    payload = run_block(block_id=args.block_id)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
