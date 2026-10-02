from __future__ import annotations

import unittest

from finite_ram_lab.semantic_trajectory_survival import (
    BUDGETS,
    LENGTHS,
    run_panel,
    simulate_trajectory,
)


class SemanticTrajectorySurvivalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run_panel()

    def _cell(self, budget: int, length: int) -> dict:
        block = next(
            row
            for row in self.result["by_budget"]
            if row["budget"] == budget
        )
        return next(
            row
            for row in block["cells"]
            if row["length"] == length
        )

    def test_trajectory_is_deterministic_for_same_identity(self):
        first = simulate_trajectory(
            budget=4,
            replicate=123,
        )
        second = simulate_trajectory(
            budget=4,
            replicate=123,
        )
        self.assertEqual(first, second)

    def test_survival_is_monotone_with_length(self):
        for budget in BUDGETS:
            rates = [
                self._cell(budget, length)[
                    "trajectory_survival_rate"
                ]
                for length in LENGTHS
            ]
            self.assertEqual(
                rates,
                sorted(rates, reverse=True),
            )

    def test_one_step_can_be_perfect_while_long_survival_is_not(self):
        self.assertEqual(
            self._cell(4, 1)[
                "trajectory_survival_rate"
            ],
            1.0,
        )
        self.assertLess(
            self._cell(4, 32)[
                "trajectory_survival_rate"
            ],
            0.70,
        )
        self.assertEqual(
            self._cell(6, 1)[
                "trajectory_survival_rate"
            ],
            1.0,
        )
        self.assertLess(
            self._cell(6, 32)[
                "trajectory_survival_rate"
            ],
            0.75,
        )

    def test_refresh_endpoint_can_hide_prior_failures(self):
        for budget, minimum_gap in (
            (2, 0.60),
            (4, 0.35),
            (6, 0.30),
        ):
            row = self._cell(budget, 32)
            self.assertGreater(
                row["endpoint_masking_gap"],
                minimum_gap,
            )
            self.assertGreater(
                row["recovered_trajectory_count"],
                0,
            )

    def test_larger_budget_improves_long_trajectory_survival(self):
        rates = [
            self._cell(budget, 32)[
                "trajectory_survival_rate"
            ]
            for budget in BUDGETS
        ]
        self.assertEqual(rates, sorted(rates))

    def test_claim_ceiling_remains_synthetic(self):
        self.assertTrue(self.result["synthetic_only"])
        self.assertFalse(self.result["empirical_model_claim"])
        self.assertEqual(
            self.result["claim_ceiling"],
            "SYNTHETIC_TRAJECTORY_SURVIVAL_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
