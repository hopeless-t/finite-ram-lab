from __future__ import annotations

import unittest

from finite_ram_lab.semantic_temporal_error_shape import (
    MARKOV_BAD_PERSISTENCE,
    MARKOV_GOOD_TO_BAD,
    MARGINAL_FLIP_RATE,
    run_panel,
    simulate_trajectory,
)


class SemanticTemporalErrorShapeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run_panel()
        cls.by_arm = {
            row["arm"]: row
            for row in cls.result["arms"]
        }

    def test_markov_transition_has_target_stationary_rate(self):
        implied = (
            MARKOV_GOOD_TO_BAD
            / (
                MARKOV_GOOD_TO_BAD
                + 1.0
                - MARKOV_BAD_PERSISTENCE
            )
        )
        self.assertAlmostEqual(
            implied,
            MARGINAL_FLIP_RATE,
            places=12,
        )

    def test_trajectory_is_deterministic(self):
        first = simulate_trajectory(
            arm="MARKOV_BURST",
            replicate=123,
        )
        second = simulate_trajectory(
            arm="MARKOV_BURST",
            replicate=123,
        )
        self.assertEqual(first, second)

    def test_marginal_label_flip_rates_are_matched(self):
        for row in self.result["arms"]:
            self.assertGreaterEqual(
                row["observed_label_flip_rate"],
                0.009,
            )
            self.assertLessEqual(
                row["observed_label_flip_rate"],
                0.011,
            )

    def test_temporal_dependence_changes_survival(self):
        self.assertLess(
            self.by_arm["IID_EVENT"][
                "trajectory_survival_rate"
            ],
            self.by_arm["STEP_SHARED"][
                "trajectory_survival_rate"
            ],
        )
        self.assertLess(
            self.by_arm["STEP_SHARED"][
                "trajectory_survival_rate"
            ],
            self.by_arm["MARKOV_BURST"][
                "trajectory_survival_rate"
            ],
        )

    def test_burst_arm_concentrates_but_deepens_failure(self):
        self.assertLess(
            self.by_arm["MARKOV_BURST"][
                "affected_trajectory_rate"
            ],
            0.25,
        )
        self.assertGreaterEqual(
            self.by_arm["MARKOV_BURST"][
                "conditional_p95_max_failure_run"
            ],
            12,
        )
        self.assertGreater(
            self.by_arm["MARKOV_BURST"][
                "conditional_mean_max_failure_run"
            ],
            self.by_arm["IID_EVENT"][
                "conditional_mean_max_failure_run"
            ],
        )

    def test_claim_ceiling_remains_synthetic(self):
        self.assertTrue(self.result["synthetic_only"])
        self.assertFalse(self.result["empirical_model_claim"])
        self.assertEqual(
            self.result["claim_ceiling"],
            "SYNTHETIC_TEMPORAL_ERROR_SHAPE_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
