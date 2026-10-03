from __future__ import annotations

import unittest

from finite_ram_lab.semantic_oom_cross_tier import (
    run_panel,
)


class SemanticOomCrossTierTests(
    unittest.TestCase
):
    @classmethod
    def setUpClass(cls):
        cls.result = run_panel()
        cls.policies = cls.result[
            "policies"
        ]

    def test_greedy_policy_has_cross_tier_task_loss(self):
        row = self.policies[
            "TIER_LOCAL_GREEDY"
        ]

        self.assertEqual(
            row["current_task_loss_count"],
            106,
        )
        self.assertFalse(
            row["reliability_qualified"]
        )
        self.assertGreater(
            row[
                "mean_initial_gtt_spill_mib"
            ],
            1000,
        )

    def test_reactive_shrink_reduces_but_does_not_eliminate_tail(self):
        row = self.policies[
            "REACTIVE_SHRINK"
        ]

        self.assertEqual(
            row["current_task_loss_count"],
            17,
        )
        self.assertFalse(
            row["reliability_qualified"]
        )
        self.assertLess(
            row[
                "mean_final_gtt_spill_mib"
            ],
            1,
        )

    def test_cross_tier_headroom_preserves_task(self):
        row = self.policies[
            "CROSS_TIER_HEADROOM"
        ]

        self.assertEqual(
            row["current_task_loss_count"],
            0,
        )
        self.assertTrue(
            row["reliability_qualified"]
        )
        self.assertEqual(
            row[
                "mean_initial_gtt_spill_mib"
            ],
            0,
        )
        self.assertEqual(
            row["p999_semantic_loss"],
            12,
        )

    def test_expected_cost_alone_prefers_unsafe_greedy(self):
        greedy = self.policies[
            "TIER_LOCAL_GREEDY"
        ]
        headroom = self.policies[
            "CROSS_TIER_HEADROOM"
        ]

        self.assertLess(
            greedy["mean_semantic_loss"],
            headroom["mean_semantic_loss"],
        )
        self.assertGreater(
            greedy["p999_semantic_loss"],
            headroom["p999_semantic_loss"],
        )

    def test_reactive_policy_is_intermediate(self):
        greedy = self.policies[
            "TIER_LOCAL_GREEDY"
        ]
        reactive = self.policies[
            "REACTIVE_SHRINK"
        ]
        headroom = self.policies[
            "CROSS_TIER_HEADROOM"
        ]

        self.assertGreater(
            greedy["current_task_loss_count"],
            reactive["current_task_loss_count"],
        )
        self.assertGreater(
            reactive["current_task_loss_count"],
            headroom["current_task_loss_count"],
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
            "SYNTHETIC_CROSS_TIER_PRESSURE_COUPLING_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
