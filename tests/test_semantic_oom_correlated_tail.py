from __future__ import annotations

import unittest

from finite_ram_lab.semantic_oom_correlated_tail import (
    REPLICATES,
    TAIL_COUNT_PER_ACTION,
    run_panel,
)


class SemanticOomCorrelatedTailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run_panel()
        cls.independent = cls.result["arms"][
            "INDEPENDENT"
        ]
        cls.shared = cls.result["arms"][
            "SHARED_BAD"
        ]

    def test_marginal_tail_counts_match_exactly(self):
        expected_rate = (
            TAIL_COUNT_PER_ACTION / REPLICATES
        )

        for arm in (
            self.independent,
            self.shared,
        ):
            self.assertEqual(
                set(
                    arm[
                        "per_action_tail_count"
                    ].values()
                ),
                {TAIL_COUNT_PER_ACTION},
            )
            self.assertEqual(
                set(
                    arm[
                        "per_action_tail_rate"
                    ].values()
                ),
                {expected_rate},
            )

    def test_shared_bad_hits_fewer_episodes(self):
        self.assertEqual(
            self.independent["affected_replicates"],
            484,
        )
        self.assertEqual(
            self.shared["affected_replicates"],
            164,
        )
        self.assertLess(
            self.shared["affected_rate"],
            self.independent["affected_rate"],
        )

    def test_shared_bad_is_conditionally_deeper(self):
        self.assertGreater(
            self.shared[
                "conditional_mean_tail_action_count"
            ],
            self.independent[
                "conditional_mean_tail_action_count"
            ],
        )
        self.assertEqual(
            self.shared[
                "conditional_p95_tail_action_count"
            ],
            3,
        )
        self.assertEqual(
            self.independent[
                "conditional_p95_tail_action_count"
            ],
            1,
        )

    def test_shared_bad_has_larger_relief_deficit_tail(self):
        self.assertEqual(
            self.independent[
                "conditional_p95_relief_deficit_mib"
            ],
            1500,
        )
        self.assertEqual(
            self.shared[
                "conditional_p95_relief_deficit_mib"
            ],
            3000,
        )

    def test_shared_bad_has_more_multi_action_failures(self):
        self.assertEqual(
            self.shared[
                "multi_action_tail_replicates"
            ],
            164,
        )
        self.assertEqual(
            self.independent[
                "multi_action_tail_replicates"
            ],
            8,
        )

    def test_failure_biopsy_is_retained(self):
        self.assertIsNotNone(
            self.independent["first_affected"]
        )
        self.assertIsNotNone(
            self.independent["first_multi_action"]
        )
        self.assertIsNotNone(
            self.shared["first_affected"]
        )
        self.assertIsNotNone(
            self.shared["first_multi_action"]
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
            "SYNTHETIC_CORRELATED_TAIL_RISK_SHAPE_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
