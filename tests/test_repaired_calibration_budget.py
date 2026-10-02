from __future__ import annotations

import unittest

from finite_ram_lab.repaired_calibration_budget import (
    build_budget,
    minimum_samples_for_rank_max_coverage,
)


def b487() -> dict:
    return {
        "schema": "finite-ram-lab.b487-result/v0.1",
        "workflow_run_id": 36941540201,
        "aggregate_sha256": "6fe3498850d88de869b2dce5c6b8bd1b444b380dfecf4e88637766aef3b7f5af",
        "runner_block_count": 8,
        "repaired_pareto_q": [2, 4, 7],
    }


class RepairedCalibrationBudgetTests(unittest.TestCase):
    def test_common_rank_targets(self):
        self.assertEqual(minimum_samples_for_rank_max_coverage(0.95), 19)
        self.assertEqual(minimum_samples_for_rank_max_coverage(0.99), 99)

    def test_95_percent_budget_is_33_runner_observations(self):
        result = build_budget(b487())
        self.assertEqual(result["required_sample_count_per_q"], 19)
        self.assertEqual(result["dominated_q_excluded"], [1])
        self.assertEqual(result["total_additional_runner_observations"], 33)
        for row in result["rows"]:
            self.assertEqual(row["current_independent_runner_samples"], 8)
            self.assertEqual(row["additional_runner_samples_required"], 11)
            self.assertAlmostEqual(row["current_rank_max_coverage_floor"], 8 / 9)

    def test_pareto_change_fails_closed(self):
        payload = b487()
        payload["repaired_pareto_q"] = [1, 2, 4, 7]
        with self.assertRaisesRegex(RuntimeError, "repaired_pareto_changed"):
            build_budget(payload)

    def test_invalid_target_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "target_invalid"):
            minimum_samples_for_rank_max_coverage(1.0)


if __name__ == "__main__":
    unittest.main()
