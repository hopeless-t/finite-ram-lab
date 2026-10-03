from __future__ import annotations

import unittest

from finite_ram_lab.ksla_bounded_idiocy import (
    Composition,
    analytic_panel,
    expected_progress,
    run_panel,
)


class KslaBoundedIdiocyTests(
    unittest.TestCase
):
    @classmethod
    def setUpClass(cls):
        cls.panel = run_panel()

    def test_hard_budget_prefers_mixed_portfolio(self):
        result = analytic_panel()
        best = result[
            "best_expected_progress"
        ]

        self.assertEqual(
            (
                best["experts"],
                best["idiots"],
            ),
            (1, 8),
        )

    def test_resource_price_creates_bounded_idiocy(self):
        result = analytic_panel()
        best = result[
            "best_utility"
        ]

        self.assertEqual(
            (
                best["experts"],
                best["idiots"],
            ),
            (1, 3),
        )
        self.assertLess(
            best["cost"],
            16,
        )

    def test_mixed_progress_beats_pure_extremes(self):
        mixed = expected_progress(
            Composition(1, 8)
        )
        expert = expected_progress(
            Composition(1, 0)
        )
        idiot = expected_progress(
            Composition(0, 16)
        )

        self.assertGreater(
            mixed,
            expert,
        )
        self.assertGreater(
            mixed,
            idiot,
        )

    def test_dominated_idiot_has_zero_progress_value(self):
        result = analytic_panel()
        control = result[
            "dominated_idiot_control"
        ]

        self.assertEqual(
            control[
                "marginal_progress_of_first_idiot"
            ],
            0.0,
        )
        self.assertTrue(
            control[
                "positive_cost_means_reject"
            ]
        )

    def test_monte_carlo_matches_analytic(self):
        self.assertLess(
            self.panel[
                "monte_carlo"
            ][
                "max_absolute_analytic_error"
            ],
            0.08,
        )

    def test_bounded_mix_beats_controls_in_matched_mc(self):
        selected = self.panel[
            "monte_carlo"
        ][
            "selected"
        ]

        mixed = selected[
            "bounded_idiocy"
        ]["utility"]

        self.assertGreater(
            mixed,
            selected[
                "expert_only"
            ]["utility"],
        )
        self.assertGreater(
            mixed,
            selected[
                "pure_idiot_16"
            ]["utility"],
        )

    def test_claim_ceiling_is_toy(self):
        self.assertEqual(
            self.panel[
                "claim_ceiling"
            ],
            "TOY_ANALYTIC_AND_MATCHED_MONTE_CARLO_BOUNDED_IDIOCY_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
