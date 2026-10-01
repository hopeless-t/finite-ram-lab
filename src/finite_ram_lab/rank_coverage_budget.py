from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Mapping


Q_VALUES = (1, 2, 4, 7)


def minimum_samples_for_rank_max_coverage(target_coverage: float) -> int:
    if not (0.0 < target_coverage < 1.0):
        raise ValueError("target_coverage_invalid")
    return math.ceil(target_coverage / (1.0 - target_coverage))


def rank_max_coverage_floor(sample_count: int) -> float:
    if sample_count <= 0:
        raise ValueError("sample_count_invalid")
    return sample_count / (sample_count + 1)


def _q_counts(
    b469: Mapping[str, Any],
    b471: Mapping[str, Any],
    b472: Mapping[str, Any],
) -> dict[int, int]:
    if b469.get("schema") != "finite-ram-lab.b469-result/v0.1":
        raise RuntimeError("b469_schema_invalid")
    if b471.get("schema") != "finite-ram-lab.b471-result/v0.1":
        raise RuntimeError("b471_schema_invalid")
    if b472.get("schema") != "finite-ram-lab.b472-result/v0.1":
        raise RuntimeError("b472_schema_invalid")

    counts = {}
    for q in Q_VALUES:
        b469_row = next(
            row for row in b469["summary_rows"] if int(row["q"]) == q
        )
        b471_row = next(
            row for row in b471["summary_rows"] if int(row["selected_q"]) == q
        )
        counts[q] = int(b469_row.get("samples", 4)) + int(
            b471_row.get("samples", 4)
        )

    if int(b472["q"]) != 1:
        raise RuntimeError("b472_not_q1")
    counts[1] = int(b472["total_sample_count"])
    return counts


def build_sample_budget(
    b469: Mapping[str, Any],
    b471: Mapping[str, Any],
    b472: Mapping[str, Any],
    *,
    target_coverage: float = 0.95,
) -> dict[str, Any]:
    required_n = minimum_samples_for_rank_max_coverage(target_coverage)
    counts = _q_counts(b469, b471, b472)

    rows = []
    for q in Q_VALUES:
        current = counts[q]
        additional = max(0, required_n - current)
        rows.append(
            {
                "q": q,
                "current_sample_count": current,
                "current_rank_max_coverage_floor": rank_max_coverage_floor(current),
                "target_coverage": target_coverage,
                "required_sample_count": required_n,
                "additional_samples_required": additional,
                "target_met": current >= required_n,
            }
        )

    return {
        "schema": "finite-ram-lab.rank-coverage-budget/v0.1",
        "status": "PROPOSAL_ONLY",
        "claim_ceiling": "EXCHANGEABILITY_CONDITIONAL_SAMPLE_BUDGET",
        "target_coverage": target_coverage,
        "required_sample_count_per_q": required_n,
        "rows": rows,
        "total_additional_samples_required": sum(
            row["additional_samples_required"] for row in rows
        ),
        "reference_targets": {
            "coverage_0_95_required_n": minimum_samples_for_rank_max_coverage(0.95),
            "coverage_0_99_required_n": minimum_samples_for_rank_max_coverage(0.99),
        },
        "assumption": (
            "future observations are exchangeable with the comparable pooled "
            "fresh-process observations; sample-max coverage is not a worst-case guarantee"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--b469", type=Path, required=True)
    parser.add_argument("--b471", type=Path, required=True)
    parser.add_argument("--b472", type=Path, required=True)
    parser.add_argument("--target-coverage", type=float, default=0.95)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    payload = build_sample_budget(
        json.loads(args.b469.read_text()),
        json.loads(args.b471.read_text()),
        json.loads(args.b472.read_text()),
        target_coverage=args.target_coverage,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
