from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

from finite_ram_lab.center_temporary_probe import (
    ELEMENT_COUNT,
    run_child,
)
from finite_ram_lab.runner_block_probe import environment_fingerprint


BASE_DIFF = 16_940
MIDPOINT = 2_060_422
MULTIPLIERS = (1, 2, 4, 8)


def count_pair(multiplier: int) -> tuple[int, int]:
    if multiplier not in MULTIPLIERS:
        raise ValueError("multiplier_invalid")
    half = (BASE_DIFF * multiplier) // 2
    return MIDPOINT - half, MIDPOINT + half


CONDITIONS = tuple(
    (multiplier, side, count)
    for multiplier in MULTIPLIERS
    for side, count in zip(("low", "high"), count_pair(multiplier), strict=True)
)


def _run_fresh_child(*, selected_count: int) -> dict[str, Any]:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "finite_ram_lab.center_temporary_probe",
            "--child",
            "--selected-count",
            str(selected_count),
            "--element-count",
            str(ELEMENT_COUNT),
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


def run_block(*, block_id: int) -> dict[str, Any]:
    if not (0 <= block_id < 8):
        raise ValueError("block_id_invalid")

    # Eight cyclic rotations: every condition occupies every execution position once.
    order = CONDITIONS[block_id:] + CONDITIONS[:block_id]
    results = []
    for multiplier, side, count in order:
        observed = _run_fresh_child(selected_count=count)
        if not observed["semantic_count_exact"]:
            raise RuntimeError("semantic_gate_failed")
        results.append({
            "multiplier": multiplier,
            "side": side,
            "selected_count": count,
            "hwm_growth_bytes": int(observed["hwm_growth_bytes"]),
            "rss_delta_bytes": int(observed["rss_delta_bytes"]),
        })

    return {
        "schema": "finite-ram-lab.center-amplification-block/v0.1",
        "claim_ceiling": "ISOLATED_CENTER_SELECTED_COUNT_AMPLIFICATION",
        "block_id": block_id,
        "environment": environment_fingerprint(),
        "conditions": [
            {"multiplier": m, "low": count_pair(m)[0], "high": count_pair(m)[1]}
            for m in MULTIPLIERS
        ],
        "execution_order": [
            {"multiplier": m, "side": side, "selected_count": count}
            for m, side, count in order
        ],
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--block-id", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    payload = run_block(block_id=args.block_id)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
