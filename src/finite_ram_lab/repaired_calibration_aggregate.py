from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics
from typing import Any, Mapping


Q_VALUES = (2, 4, 7)
EXPECTED_NEW_BLOCKS = 11
TARGET_COVERAGE = 0.95


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _old_values(raw: Mapping[str, Any], q: int) -> list[int]:
    if raw.get("schema") != "finite-ram-lab.b487-repaired-raw-calibration/v0.1":
        raise RuntimeError("raw_schema_invalid")
    return [
        int(row[f"q{q}"]["normalized_peak_growth_bytes"])
        for row in raw["rows"]
    ]


def aggregate(
    old_raw: Mapping[str, Any],
    new_blocks: list[Mapping[str, Any]],
) -> dict[str, Any]:
    if len(new_blocks) != EXPECTED_NEW_BLOCKS:
        raise RuntimeError("new_block_count_invalid")

    ids = sorted(int(block["block_id"]) for block in new_blocks)
    if ids != list(range(EXPECTED_NEW_BLOCKS)):
        raise RuntimeError("new_block_ids_invalid")

    summary_rows = []
    for q in Q_VALUES:
        old = _old_values(old_raw, q)
        new = []
        latencies = []
        for block in new_blocks:
            row = next(item for item in block["results"] if int(item["q"]) == q)
            new.append(int(row["normalized_peak_growth_bytes"]))
            latencies.append(float(row["work_seconds"]))

        pooled = old + new
        n = len(pooled)
        if n != 19:
            raise RuntimeError(f"pooled_sample_count_invalid:q={q}:n={n}")

        old_max = max(old)
        new_max = max(new)
        pooled_max = max(pooled)
        coverage = n / (n + 1)

        summary_rows.append(
            {
                "q": q,
                "old_sample_count": len(old),
                "new_sample_count": len(new),
                "pooled_sample_count": n,
                "old_peak_samples_bytes": old,
                "new_peak_samples_bytes": new,
                "old_empirical_max_peak_bytes": old_max,
                "new_panel_max_peak_bytes": new_max,
                "pooled_empirical_max_peak_bytes": pooled_max,
                "empirical_max_moved_bytes": pooled_max - old_max,
                "new_exceedances_over_old_max": sum(value > old_max for value in new),
                "rank_max_one_step_predictive_coverage_floor": coverage,
                "median_new_work_seconds": statistics.median(latencies),
                "target_coverage_met": coverage >= TARGET_COVERAGE,
            }
        )

    return {
        "schema": "finite-ram-lab.repaired-calibration-result/v0.1",
        "status": "CALIBRATED",
        "claim_ceiling": "EXCHANGEABILITY_CONDITIONAL_REPAIRED_95P_CALIBRATION",
        "implementation": "TILED_WHERE",
        "pareto_q": list(Q_VALUES),
        "new_runner_block_count": EXPECTED_NEW_BLOCKS,
        "new_physical_observations": EXPECTED_NEW_BLOCKS * len(Q_VALUES),
        "target_coverage": TARGET_COVERAGE,
        "summary_rows": summary_rows,
        "all_q_target_met": all(row["target_coverage_met"] for row in summary_rows),
        "source_b487_workflow_run_id": old_raw["source_workflow_run_id"],
        "assumption": (
            "future repaired-runtime observations are exchangeable with the pooled "
            "independent hosted-runner calibration observations"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--old-raw", type=Path, required=True)
    parser.add_argument("--blocks-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    blocks = [
        json.loads(path.read_text())
        for path in sorted(args.blocks_dir.glob("block-*.json"))
    ]
    result = aggregate(_load(args.old_raw), blocks)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
