from __future__ import annotations

import unittest

from finite_ram_lab.fr_rematerialization import (
    evaluate,
    run_panel,
)


class FrRematerializationTests(
    unittest.TestCase
):
    @classmethod
    def setUpClass(cls):
        cls.result = run_panel()

    def test_keep_all_is_infeasible(self):
        self.assertFalse(
            self.result[
                "baselines"
            ][
                "KEEP_ALL"
            ]["feasible"]
        )

    def test_mixed_policy_beats_recompute_heuristic(self):
        optimal = self.result[
            "optimal_mixed"
        ][
            "objective"
        ]

        cheap = self.result[
            "baselines"
        ][
            "CHEAP_RECOMPUTE_FIRST"
        ][
            "objective"
        ]

        self.assertLess(
            optimal,
            cheap,
        )

    def test_nonrebuildable_recompute_is_invalid(self):
        choices = (
            "KEEP",
            "KEEP",
            "KEEP",
            "KEEP",
            "KEEP",
            "KEEP",
            "RECOMPUTE",
        )

        self.assertIsNone(
            evaluate(
                choices
            )
        )

    def test_optimal_uses_all_three_actions(self):
        choices = set(
            self.result[
                "optimal_mixed"
            ]["choices"]
        )

        self.assertEqual(
            choices,
            {
                "KEEP",
                "RECOMPUTE",
                "OFFLOAD",
            },
        )

    def test_claim_ceiling(self):
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "SOURCE_GROUNDED_SYNTHETIC_REMATERIALIZATION_PLANNER_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
