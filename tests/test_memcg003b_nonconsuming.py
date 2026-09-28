from __future__ import annotations

import json
import unittest
from pathlib import Path

from finite_ram_lab.memcg003b_nonconsuming import analyze_trials


ROOT = Path(__file__).resolve().parents[1]
SPEC = json.loads(
    (ROOT / "specs/MEMCG-003B-NONCONSUMING-SEVEN-SLOT-v1.json")
    .read_text(encoding="utf-8")
)


def trial(
    block: int,
    arm: str,
    drop_at: int | None,
    *,
    final_delta: float,
) -> dict:
    max_m = 6 if arm == "six_only" else 8
    records = []
    for m in range(1, max_m + 1):
        records.append({
            "m": m,
            "actor": arm,
            "target_current_bytes": 0,
            "passive_drop_pages": 63.0 if drop_at == m else 0.0,
        })
    return {
        "experiment_id": SPEC["experiment_id"],
        "block": block,
        "arm": arm,
        "control_cpu": 0,
        "stock_cpu": 1,
        "page_size": 4096,
        "wash_count": 7,
        "records": records,
        "final_recharge": {
            "pre_current_bytes": 0,
            "post_current_bytes": 0,
            "delta_pages": final_delta,
        },
    }


def matrix(k: int) -> list[dict]:
    rows = []
    for b in range(4):
        rows.extend([
            trial(b, "distinct_churn", k, final_delta=64.0),
            trial(b, "same_memcg_activity", None, final_delta=0.0),
            trial(b, "six_only", None, final_delta=0.0),
            trial(b, "no_churn", None, final_delta=0.0),
        ])
    return rows


class Memcg003BTests(unittest.TestCase):
    def test_exact_k7_support(self) -> None:
        result = analyze_trials(SPEC, matrix(7))
        self.assertEqual(result["decision"], "SUPPORT_K7_SLOT_MODEL_B")
        self.assertEqual(result["thresholds"], [7,7,7,7])
        self.assertEqual(result["best_k_by_absolute_error"], 7)
        self.assertEqual(result["best_k_by_mdl"], 7)
        self.assertEqual(result["posterior_mode_k"], 7)
        self.assertTrue(all(
            f["trained_k"] == 7 for f in result["leave_one_block_out"]
        ))

    def test_stable_alternative_k_rejects(self) -> None:
        result = analyze_trials(SPEC, matrix(3))
        self.assertEqual(result["decision"], "REJECT_K7_SLOT_MODEL_B")
        self.assertEqual(result["best_k_by_absolute_error"], 3)
        self.assertEqual(result["posterior_mode_k"], 3)

    def test_control_drop_rejects_block_support(self) -> None:
        rows = matrix(7)
        rows = [
            trial(
                t["block"],
                t["arm"],
                4 if t["block"] == 0 and t["arm"] == "no_churn"
                else (
                    7 if t["arm"] == "distinct_churn"
                    else None
                ),
                final_delta=64.0 if t["arm"] == "distinct_churn" else 0.0,
            )
            if t["block"] == 0 else t
            for t in rows
        ]
        result = analyze_trials(SPEC, rows)
        self.assertFalse(result["blocks"][0]["supports_k7_model_b"])
        self.assertEqual(result["support_blocks"], 3)


if __name__ == "__main__":
    unittest.main()
