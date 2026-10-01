from __future__ import annotations

import argparse
import json
import mmap
import os
from pathlib import Path
import platform
import statistics
from typing import Any

import numpy as np

from finite_ram_lab.lane_concurrency_sweep import _run_fresh_child


BASE_ORDERS = (
    ((2,474),(2,476),(4,474),(4,476)),
    ((4,476),(4,474),(2,476),(2,474)),
    ((2,476),(2,474),(4,476),(4,474)),
    ((4,474),(4,476),(2,474),(2,476)),
)


def _read_first(prefix: str, path: str) -> str | None:
    try:
        for line in Path(path).read_text().splitlines():
            if line.startswith(prefix):
                return line.split(":",1)[1].strip()
    except OSError:
        return None
    return None


def environment_fingerprint() -> dict[str, Any]:
    return {
        "runner_name": os.environ.get("RUNNER_NAME"),
        "image_os": os.environ.get("ImageOS"),
        "image_version": os.environ.get("ImageVersion"),
        "kernel_release": platform.release(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "page_size": mmap.PAGESIZE,
        "cpu_model": _read_first("model name", "/proc/cpuinfo"),
        "mem_total": _read_first("MemTotal", "/proc/meminfo"),
    }


def run_block(
    *,
    block_id: int,
    size: int = 2048,
    value_limit: int = 50,
    tile_rows: int = 64,
) -> dict[str, Any]:
    if not (0 <= block_id < 8):
        raise ValueError("block_id_invalid")

    first = BASE_ORDERS[block_id % len(BASE_ORDERS)]
    orders = (first, tuple(reversed(first)))
    observations: dict[tuple[int,int], list[dict[str, Any]]] = {
        (2,474): [], (2,476): [], (4,474): [], (4,476): []
    }
    execution_rows = []

    for replicate, order in enumerate(orders):
        row = {
            "replicate": replicate,
            "order": [{"q": q, "seed": seed} for q,seed in order],
            "results": [],
        }
        for q,seed in order:
            result = _run_fresh_child(
                q=q,
                size=size,
                lane_count=7,
                seed=seed,
                value_limit=value_limit,
                tile_rows=tile_rows,
            )
            if not result["semantic_exact"]:
                raise RuntimeError(
                    f"semantic_gate_failed:block={block_id}:q={q}:seed={seed}"
                )
            item = {
                "q": q,
                "seed": seed,
                "replicate": replicate,
                "observed_peak_bytes": int(result["normalized_peak_growth_bytes"]),
                "work_seconds": float(result["work_seconds"]),
                "output_sha256": result["output_sha256"],
            }
            observations[(q,seed)].append(item)
            row["results"].append(item)
        execution_rows.append(row)

    summaries = []
    for condition, values in sorted(observations.items()):
        q,seed = condition
        digests = {item["output_sha256"] for item in values}
        if len(digests) != 1:
            raise RuntimeError(f"condition_digest_mismatch:q={q}:seed={seed}")
        peaks = [item["observed_peak_bytes"] for item in values]
        summaries.append(
            {
                "q": q,
                "seed": seed,
                "sample_count": len(values),
                "peak_bytes": peaks,
                "median_peak_bytes": statistics.median(peaks),
                "median_work_seconds": statistics.median(
                    item["work_seconds"] for item in values
                ),
                "output_sha256": next(iter(digests)),
            }
        )

    return {
        "schema": "finite-ram-lab.runner-block/v0.1",
        "claim_ceiling": "GITHUB_HOSTED_JOB_BLOCK_OBSERVATION",
        "block_id": block_id,
        "environment": environment_fingerprint(),
        "size": size,
        "value_limit": value_limit,
        "tile_rows": tile_rows,
        "execution_rows": execution_rows,
        "condition_summaries": summaries,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--block-id", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--size", type=int, default=2048)
    args = parser.parse_args()

    payload = run_block(block_id=args.block_id, size=args.size)
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
