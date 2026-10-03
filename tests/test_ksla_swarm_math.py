from __future__ import annotations

import unittest

from finite_ram_lab.ksla_swarm_math import (
    expected_best_of_batch,
    marginal_batch_gain,
    run_panel,
)


class KslaSwarmMathTests(
    unittest.TestCase
):
    def test_expected_best_increases_with_batch(self):
        pmf = (
            (0.0, 0.8),
            (1.0, 0.15),
            (5.0, 0.05),
        )

        previous = 0.0

        for batch in range(
            1,
            33,
        ):
            current = (
                expected_best_of_batch(
                    pmf,
                    batch,
                )
            )

            self.assertGreaterEqual(
                current,
                previous,
            )

            previous = current

    def test_marginal_gain_has_diminishing_returns(self):
        pmf = (
            (0.0, 0.8),
            (1.0, 0.15),
            (5.0, 0.05),
        )

        marginal = [
            marginal_batch_gain(
                pmf,
                batch,
            )
            for batch in range(
                1,
                33,
            )
        ]

        self.assertTrue(
            all(
                right
                <= left + 1e-12
                for left, right
                in zip(
                    marginal,
                    marginal[1:],
                )
            )
        )

    def test_toy_cost_model_has_finite_knee(self):
        result = run_panel()

        self.assertEqual(
            result[
                "toy_order_statistics"
            ][
                "best_efficiency_batch"
            ],
            12,
        )

    def test_ksla002_cost_frontier(self):
        result = run_panel()

        intervals = result[
            "ksla002_empirical_cost_envelope"
        ][
            "optimal_intervals"
        ]

        self.assertEqual(
            [
                row[
                    "optimal_batch"
                ]
                for row in intervals
            ],
            [
                8,
                16,
                32,
                64,
                128,
            ],
        )

    def test_common_random_number_fix_is_frozen(self):
        result = run_panel()

        correction = result[
            "experiment_design_correction"
        ]

        self.assertIn(
            "common-random-number",
            correction["fix"],
        )

    def test_claim_ceiling_is_analytic(self):
        result = run_panel()

        self.assertEqual(
            result[
                "claim_ceiling"
            ],
            "ANALYTIC_AND_SYNTHETIC_SWARM_WIDTH_MODEL_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
