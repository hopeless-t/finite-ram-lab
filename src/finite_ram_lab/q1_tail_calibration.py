from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics
from typing import Any, Mapping

from finite_ram_lab.lane_concurrency_sweep import _run_fresh_child


TARGET_Q = 1
ADDITIONAL_SAMPLES = 12


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _q1_from_b469(result: Mapping[str, Any]) -> dict[str, Any]:
    if result.get("schema") != "finite-ram-lab.b469-result/v0.1":
        raise RuntimeError("b469_schema_invalid")
    row = next(
        (item for item in result["summary_rows"] if int(item["q"]) == TARGET_Q),
        None,
    )
    if row is None:
        raise RuntimeError("b469_q1_missing")
    return dict(row)


def _q1_from_b471(result: Mapping[str, Any]) -> dict[str, Any]:
    if result.get("schema") != "finite-ram-lab.b471-result/v0.1":
        raise RuntimeError("b471_schema_invalid")
    row = next(
        (
            item
            for item in result["summary_rows"]
            if int(item["selected_q"]) == TARGET_Q
        ),
        None,
    )
    if row is None:
        raise RuntimeError("b471_q1_missing")
    return dict(row)


def rank_max_predictive_coverage_floor(sample_count: int) -> float:
    if sample_count <= 0:
        raise ValueError("sample_count_invalid")
    return sample_count / (sample_count + 1)


def run_q1_tail_panel(
    b469: Mapping[str, Any],
    b471: Mapping[str, Any],
    *,
    additional_samples: int = ADDITIONAL_SAMPLES,
    size: int = 2048,
    seed: int = 472,
    value_limit: int = 50,
    tile_rows: int = 64,
) -> dict[str, Any]:
    if additional_samples <= 0:
        raise ValueError("additional_samples_invalid")

    old = _q1_from_b469(b469)
    fresh = _q1_from_b471(b471)

    old_samples = int(old.get("samples", 4))
    fresh_samples = int(fresh.get("samples", 4))
    prior_sample_count = old_samples + fresh_samples

    prior_max = max(
        int(old["max_peak_bytes"]),
        int(fresh["max_observed_peak_bytes"]),
    )

    observations = []
    for repetition in range(additional_samples):
        result = _run_fresh_child(
            q=TARGET_Q,
            size=size,
            lane_count=7,
            seed=seed,
            value_limit=value_limit,
            tile_rows=tile_rows,
        )
        if not result["semantic_exact"]:
            raise RuntimeError(f"semantic_gate_failed:rep={repetition}")
        observations.append(
            {
                "repetition": repetition,
                "observed_peak_bytes": int(
                    result["normalized_peak_growth_bytes"]
                ),
                "work_seconds": float(result["work_seconds"]),
                "output_sha256": result["output_sha256"],
            }
        )

    digests = {item["output_sha256"] for item in observations}
    if len(digests) != 1:
        raise RuntimeError("output_digest_mismatch")

    peaks = [item["observed_peak_bytes"] for item in observations]
    new_max = max(peaks)
    union_max = max(prior_max, new_max)
    total_sample_count = prior_sample_count + additional_samples
    coverage_floor = rank_max_predictive_coverage_floor(total_sample_count)
    prior_exceed_count = sum(peak > prior_max for peak in peaks)

    return {
        "schema": "finite-ram-lab.q1-tail-calibration/v0.1",
        "claim_ceiling": "EXCHANGEABILITY_CONDITIONAL_EMPIRICAL_MAX_CALIBRATION",
        "q": TARGET_Q,
        "size": size,
        "seed": seed,
        "value_limit": value_limit,
        "tile_rows": tile_rows,
        "prior": {
            "b469_samples": old_samples,
            "b471_samples": fresh_samples,
            "combined_sample_count": prior_sample_count,
            "b469_max_peak_bytes": int(old["max_peak_bytes"]),
            "b471_max_peak_bytes": int(fresh["max_observed_peak_bytes"]),
            "union_max_peak_bytes": prior_max,
        },
        "new_panel": {
            "sample_count": additional_samples,
            "observed_peak_bytes": peaks,
            "median_peak_bytes": statistics.median(peaks),
            "max_peak_bytes": new_max,
            "prior_boundary_exceed_count": prior_exceed_count,
            "median_work_seconds": statistics.median(
                item["work_seconds"] for item in observations
            ),
            "semantic_exact_count": additional_samples,
            "output_sha256": next(iter(digests)),
        },
        "union": {
            "sample_count": total_sample_count,
            "empirical_max_peak_bytes": union_max,
            "max_moved_bytes": union_max - prior_max,
            "rank_max_one_step_predictive_coverage_floor": coverage_floor,
            "rank_max_one_step_exceedance_ceiling": 1.0 - coverage_floor,
            "assumption": (
                "future observation exchangeable with the pooled comparable "
                "fresh-process observations; this is not a worst-case guarantee"
            ),
        },
        "classification": (
            "Q1_EMPIRICAL_MAX_STABLE_IN_TARGETED_PANEL"
            if prior_exceed_count == 0
            else "Q1_EMPIRICAL_MAX_MOVED"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--b469", type=Path, required=True)
    parser.add_argument("--b471", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--additional-samples", type=int, default=ADDITIONAL_SAMPLES)
    parser.add_argument("--size", type=int, default=2048)
    parser.add_argument("--seed", type=int, default=472)
    args = parser.parse_args()

    payload = run_q1_tail_panel(
        _load(args.b469),
        _load(args.b471),
        additional_samples=args.additional_samples,
        size=args.size,
        seed=args.seed,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
