from __future__ import annotations

import unittest

from finite_ram_lab.semantic_oom import (
    earlyoom_like_oom_score,
    rss_first,
    run_panel,
    semantic_min_loss,
)


class SemanticOomTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run_panel()

    def test_default_like_counterexample_kills_active_chrome(self):
        row = earlyoom_like_oom_score(1024)
        self.assertEqual(
            row["victims"],
            ["chrome-active"],
        )
        self.assertFalse(
            row["current_task_survives"]
        )

    def test_rss_first_has_same_small_deficit_problem(self):
        row = rss_first(1024)
        self.assertEqual(
            row["victims"],
            ["chrome-active"],
        )
        self.assertFalse(
            row["current_task_survives"]
        )

    def test_semantic_policy_preserves_current_task_at_small_pressure(self):
        row = semantic_min_loss(1024)
        self.assertTrue(row["relief_satisfied"])
        self.assertTrue(
            row["current_task_survives"]
        )
        self.assertNotIn(
            "chrome-active",
            row["victims"],
        )

    def test_semantic_policy_preserves_task_through_3072_mib(self):
        for deficit in (1024, 2048, 3072):
            self.assertTrue(
                semantic_min_loss(deficit)[
                    "current_task_survives"
                ]
            )

    def test_extreme_pressure_eventually_forces_task_loss(self):
        self.assertFalse(
            semantic_min_loss(4096)[
                "current_task_survives"
            ]
        )

    def test_semantic_loss_improves_at_every_frozen_deficit(self):
        for improvement in self.result[
            "semantic_loss_improvement_vs_oom_score"
        ].values():
            self.assertGreater(improvement, 0)

    def test_claim_ceiling_is_synthetic(self):
        self.assertTrue(self.result["synthetic_only"])
        self.assertFalse(
            self.result["empirical_earlyoom_claim"]
        )
        self.assertEqual(
            self.result["claim_ceiling"],
            "SYNTHETIC_VICTIM_SELECTION_COUNTEREXAMPLE_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
