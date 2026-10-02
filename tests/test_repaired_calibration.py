from __future__ import annotations

import unittest
from unittest.mock import patch

from finite_ram_lab.repaired_calibration_aggregate import aggregate
from finite_ram_lab.repaired_calibration_probe import run_block


def old_raw() -> dict:
    rows = []
    for block_id in range(8):
        rows.append({
            "block_id": block_id,
            "q2": {"normalized_peak_growth_bytes": 100 + block_id},
            "q4": {"normalized_peak_growth_bytes": 200 + block_id},
            "q7": {"normalized_peak_growth_bytes": 300 + block_id},
        })
    return {
        "schema": "finite-ram-lab.b487-repaired-raw-calibration/v0.1",
        "source_workflow_run_id": 36941540201,
        "rows": rows,
    }


def block(block_id: int) -> dict:
    return {
        "schema": "finite-ram-lab.repaired-calibration-block/v0.1",
        "block_id": block_id,
        "results": [
            {"q": 2, "normalized_peak_growth_bytes": 108 + block_id, "work_seconds": 1.0},
            {"q": 4, "normalized_peak_growth_bytes": 208 + block_id, "work_seconds": 1.0},
            {"q": 7, "normalized_peak_growth_bytes": 308 + block_id, "work_seconds": 1.0},
        ],
    }


class RepairedCalibrationTests(unittest.TestCase):
    def test_aggregate_reaches_n19_and_95_percent(self):
        result = aggregate(old_raw(), [block(i) for i in range(11)])
        self.assertTrue(result["all_q_target_met"])
        self.assertEqual(result["new_physical_observations"], 33)
        for row in result["summary_rows"]:
            self.assertEqual(row["pooled_sample_count"], 19)
            self.assertAlmostEqual(
                row["rank_max_one_step_predictive_coverage_floor"],
                0.95,
            )

    def test_aggregate_updates_empirical_max(self):
        result = aggregate(old_raw(), [block(i) for i in range(11)])
        q2 = next(row for row in result["summary_rows"] if row["q"] == 2)
        self.assertGreater(q2["pooled_empirical_max_peak_bytes"], q2["old_empirical_max_peak_bytes"])
        self.assertGreater(q2["new_exceedances_over_old_max"], 0)

    def test_probe_rotates_q_order_and_preserves_digest(self):
        def fake_child(**kwargs):
            q = kwargs["q"]
            return {
                "semantic_exact": True,
                "normalized_peak_growth_bytes": 1000 + q,
                "work_seconds": 1.0,
                "output_sha256": "same",
            }

        with patch(
            "finite_ram_lab.repaired_calibration_probe._run_fresh_child",
            side_effect=fake_child,
        ), patch(
            "finite_ram_lab.repaired_calibration_probe.environment_fingerprint",
            return_value={"runner_name": "test"},
        ):
            b0 = run_block(block_id=0, size=64)
            b1 = run_block(block_id=1, size=64)
            b2 = run_block(block_id=2, size=64)

        self.assertEqual(b0["execution_order"], [2, 4, 7])
        self.assertEqual(b1["execution_order"], [4, 7, 2])
        self.assertEqual(b2["execution_order"], [7, 2, 4])

    def test_wrong_block_count_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError, "new_block_count_invalid"):
            aggregate(old_raw(), [block(i) for i in range(10)])


if __name__ == "__main__":
    unittest.main()
