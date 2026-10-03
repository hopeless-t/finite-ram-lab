from __future__ import annotations

import unittest

from finite_ram_lab.fr_loop_speed_governor import (
    exact_fanout,
    governor_decision,
    monte_carlo_rework_sensitivity,
)


class LoopSpeedGovernorTests(unittest.TestCase):
    def test_exact_fanout(self) -> None:
        row = exact_fanout()
        self.assertEqual(row["baseline_mean_commits"], 6.0)
        self.assertEqual(row["baseline_mean_total_runs"], 10.0)
        self.assertAlmostEqual(row["commit_reduction_fraction"], 2 / 3)
        self.assertAlmostEqual(row["workflow_run_reduction_fraction"], 0.6)
        self.assertAlmostEqual(row["push_run_reduction_fraction"], 0.625)

    def test_governor_promotes_atomic_bundle(self) -> None:
        result = governor_decision()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(
            result["decision"],
            "ASSEMBLE_DETACHED_ATOMIC_COMMIT_THEN_PUBLISH_BRANCH",
        )
        self.assertTrue(all(result["checks"].values()))

    def test_rework_sensitivity(self) -> None:
        result = monte_carlo_rework_sensitivity(trials=2000)
        self.assertTrue(result["all_mean_savings_positive"])
        self.assertEqual(len(result["scenarios"]), 9)


if __name__ == "__main__":
    unittest.main()
