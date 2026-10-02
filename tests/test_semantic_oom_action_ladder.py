from __future__ import annotations

import unittest

from finite_ram_lab.semantic_oom_action_ladder import (
    earlyoom_like_kill_first,
    run_panel,
)


class SemanticOomActionLadderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run_panel()
        cls.by_deadline = {
            row["deadline_ms"]: row
            for row in cls.result["semantic_plans"]
        }

    def test_kill_first_baseline_destroys_current_task(self):
        row = earlyoom_like_kill_first()
        self.assertEqual(
            row["actions"],
            ["CHROME_KILL"],
        )
        self.assertFalse(
            row["current_task_survives"]
        )
        self.assertEqual(
            row["semantic_loss"],
            280,
        )

    def test_25ms_semantic_plan_preserves_task_but_uses_kills(self):
        row = self.by_deadline[25]
        self.assertTrue(
            row["current_task_survives"]
        )
        self.assertEqual(
            row["hard_kill_count"],
            3,
        )
        self.assertEqual(
            row["semantic_loss"],
            73,
        )

    def test_100ms_unlocks_cooperative_relief(self):
        row = self.by_deadline[100]
        self.assertEqual(
            row["hard_kill_count"],
            1,
        )
        self.assertEqual(
            row["semantic_loss"],
            14,
        )
        self.assertIn(
            "CHROME_TRIM_CACHE",
            row["actions"],
        )

    def test_200ms_removes_hard_kills(self):
        row = self.by_deadline[200]
        self.assertEqual(
            row["hard_kill_count"],
            0,
        )
        self.assertEqual(
            row["semantic_loss"],
            9,
        )

    def test_600ms_reduces_semantic_loss_to_three(self):
        row = self.by_deadline[600]
        self.assertEqual(
            row["hard_kill_count"],
            0,
        )
        self.assertEqual(
            row["semantic_loss"],
            3,
        )
        self.assertEqual(
            row["relief_mib"],
            3000,
        )

    def test_more_time_never_worsens_frozen_semantic_loss(self):
        losses = [
            self.by_deadline[deadline][
                "semantic_loss"
            ]
            for deadline in (25, 100, 200, 600)
        ]
        self.assertEqual(
            losses,
            sorted(losses, reverse=True),
        )

    def test_claim_ceiling_is_synthetic(self):
        self.assertTrue(
            self.result["synthetic_only"]
        )
        self.assertFalse(
            self.result["live_control_claim"]
        )
        self.assertEqual(
            self.result["claim_ceiling"],
            "SYNTHETIC_DEADLINE_ACTION_LADDER_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
