from __future__ import annotations

import unittest

from finite_ram_lab.semantic_oom_inference_planner import (
    run_panel,
)


class SemanticOomInferencePlannerTests(
    unittest.TestCase
):
    @classmethod
    def setUpClass(cls):
        cls.result = run_panel()
        cls.iid = cls.result["arms"][
            "INDEPENDENT"
        ]
        cls.shared = cls.result["arms"][
            "SHARED_BAD"
        ]

    def test_history_inference_drives_policy(self):
        self.assertEqual(
            self.iid["history_inference"][
                "classification"
            ],
            "IID_COMPATIBLE",
        )
        self.assertEqual(
            self.shared[
                "history_inference"
            ]["classification"],
            "CROSS_ACTION_DEPENDENCE_EVIDENCE",
        )

        self.assertEqual(
            self.iid["future_policies"][
                "DEPENDENCE_AWARE"
            ]["selected_plan"],
            "COOPERATIVE_REDUNDANCY",
        )
        self.assertEqual(
            self.shared["future_policies"][
                "DEPENDENCE_AWARE"
            ]["selected_plan"],
            "BACKGROUND_SACRIFICE",
        )

    def test_iid_regime_avoids_unnecessary_escalation(self):
        naive = self.iid[
            "future_policies"
        ]["NAIVE_COOPERATIVE"]
        aware = self.iid[
            "future_policies"
        ]["DEPENDENCE_AWARE"]

        self.assertEqual(
            naive["deadline_failures"],
            1,
        )
        self.assertEqual(
            aware["deadline_failures"],
            1,
        )
        self.assertTrue(
            aware["reliability_qualified"]
        )
        self.assertEqual(
            aware["mean_semantic_loss"],
            naive["mean_semantic_loss"],
        )

    def test_shared_naive_misses_reliability_floor(self):
        row = self.shared[
            "future_policies"
        ]["NAIVE_COOPERATIVE"]

        self.assertEqual(
            row["deadline_failures"],
            82,
        )
        self.assertFalse(
            row["reliability_qualified"]
        )
        self.assertEqual(
            row["current_task_loss_count"],
            82,
        )
        self.assertEqual(
            row["p99_semantic_loss"],
            290,
        )

    def test_shared_dependence_aware_preserves_task(self):
        row = self.shared[
            "future_policies"
        ]["DEPENDENCE_AWARE"]

        self.assertEqual(
            row["deadline_failures"],
            0,
        )
        self.assertTrue(
            row["reliability_qualified"]
        )
        self.assertEqual(
            row["current_task_loss_count"],
            0,
        )
        self.assertEqual(
            row["p99_semantic_loss"],
            73,
        )

    def test_tail_safe_policy_can_have_higher_mean_cost(self):
        naive = self.shared[
            "future_policies"
        ]["NAIVE_COOPERATIVE"]
        aware = self.shared[
            "future_policies"
        ]["DEPENDENCE_AWARE"]

        self.assertLess(
            naive["mean_semantic_loss"],
            aware["mean_semantic_loss"],
        )
        self.assertGreater(
            naive["p99_semantic_loss"],
            aware["p99_semantic_loss"],
        )

    def test_dependence_aware_is_better_than_kill_first_semantically(self):
        aware = self.shared[
            "future_policies"
        ]["DEPENDENCE_AWARE"]
        kill = self.shared[
            "future_policies"
        ]["KILL_FIRST"]

        self.assertLess(
            aware["mean_semantic_loss"],
            kill["mean_semantic_loss"],
        )
        self.assertEqual(
            kill["current_task_loss_count"],
            8192,
        )

    def test_claim_ceiling_is_synthetic(self):
        self.assertTrue(
            self.result["synthetic_only"]
        )
        self.assertFalse(
            self.result["live_control_claim"]
        )
        self.assertFalse(
            self.result[
                "history_analyzer_uses_latent_labels"
            ]
        )
        self.assertEqual(
            self.result["claim_ceiling"],
            "SYNTHETIC_INFERENCE_INFORMED_PLANNING_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
