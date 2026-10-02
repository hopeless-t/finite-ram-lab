from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from finite_ram_lab.repaired_q_frontier import _run_fresh_child
from finite_ram_lab.runner_block_probe import environment_fingerprint


Q_VALUES = (2, 4, 7)
RUNNER_BLOCKS = 11
ORDERS = (
    (2, 4, 7),
    (4, 7, 2),
    (7, 2, 4),
)


def run_block(*, block_id: int, size: int = 2048) -> dict[str, Any]:
    if not (0 <= block_id < RUNNER_BLOCKS):
        raise ValueError("block_id_invalid")

    order = ORDERS[block_id % len(ORDERS)]
    results = []
    for q in order:
        observed = _run_fresh_child(
            strategy="TILED_WHERE",
            q=q,
            size=size,
        )
        if not observed["semantic_exact"]:
            raise RuntimeError(f"semantic_gate_failed:q={q}:block={block_id}")
        results.append(
            {
                "q": q,
                "normalized_peak_growth_bytes": int(
                    observed["normalized_peak_growth_bytes"]
                ),
                "work_seconds": float(observed["work_seconds"]),
                "output_sha256": observed["output_sha256"],
            }
        )

    digests = {row["output_sha256"] for row in results}
    if len(digests) != 1:
        raise RuntimeError("cross_q_output_digest_mismatch")

    return {
        "schema": "finite-ram-lab.repaired-calibration-block/v0.1",
        "claim_ceiling": "INDEPENDENT_HOSTED_RUNNER_REPAIRED_CALIBRATION",
        "implementation": "TILED_WHERE",
        "block_id": block_id,
        "environment": environment_fingerprint(),
        "size": size,
        "seed": 469,
        "execution_order": list(order),
        "results": results,
        "output_sha256": next(iter(digests)),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--block-id", type=int, required=True)
    parser.add_argument("--size", type=int, default=2048)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    payload = run_block(block_id=args.block_id, size=args.size)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
