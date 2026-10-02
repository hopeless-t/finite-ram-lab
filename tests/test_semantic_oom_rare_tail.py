from __future__ import annotations

import unittest

from finite_ram_lab.semantic_oom_rare_tail import (
    DEADLINE_MS,
    run_panel,
)


class SemanticOomRareTailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run_panel()
        cls.plans = cls.result["plans"]

    def test_mean_fast_plan_is_not_tail_safe(self):
        row = self.plans["MEAN_COOPERATIVE"]
        self.assertLess(
            row["mean_completion_latency_ms"],
            DEADLINE_MS,
        )
        self.assertFalse(
            row["reliability_qualified"]
        )
        self.assertGreater(
            row["p95_completion_latency_ms"],
            DEADLINE_MS,
        )

    def test_tail_aware_plan_qualifies_99_percent_floor(self):
        row = self.plans["TAIL_AWARE_MIXED"]
        self.assertTrue(
            row["reliability_qualified"]
        )
        self.assertGreaterEqual(
            row["deadline_success_wilson95"][0],
            0.99,
        )
        self.assertLessEqual(
            row["p99_completion_latency_ms"],
            DEADLINE_MS,
        )

    def test_tail_aware_plan_preserves_current_task(self):
        row = self.plans["TAIL_AWARE_MIXED"]
        self.assertTrue(
            row["current_task_survives"]
        )
        self.assertEqual(
            row["hard_kill_count"],
            1,
        )
        self.assertEqual(
            row["semantic_loss"],
            14,
        )

    def test_kill_first_is_fast_but_semantically_expensive(self):
        row = self.plans["KILL_FIRST"]
        self.assertTrue(
            row["reliability_qualified"]
        )
        self.assertFalse(
            row["current_task_survives"]
        )
        self.assertEqual(
            row["semantic_loss"],
            280,
        )

    def test_failure_biopsy_is_retained(self):
        mean_row = self.plans["MEAN_COOPERATIVE"]
        self.assertIsNotNone(
            mean_row["first_deadline_miss"]
        )
        self.assertIsNotNone(
            mean_row["first_relief_miss"]
        )

    def test_frozen_rates_match_reference_vector(self):
        mean_row = self.plans["MEAN_COOPERATIVE"]
        tail_row = self.plans["TAIL_AWARE_MIXED"]
        kill_row = self.plans["KILL_FIRST"]

        self.assertEqual(
            mean_row["deadline_successes"],
            7525,
        )
        self.assertEqual(
            tail_row["deadline_successes"],
            8168,
        )
        self.assertEqual(
            kill_row["deadline_successes"],
            8192,
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
            "SYNTHETIC_RARE_TAIL_POLICY_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
