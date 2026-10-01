from __future__ import annotations

import random
import unittest

from finite_ram_lab.intervention_staircase import (
    advice_calls,
    brute_frontier,
    cadence_roles,
    frozen_staircase_frontier,
    staircase_thresholds,
)


class InterventionStaircaseTests(unittest.TestCase):
    def test_advice_call_staircase(self):
        self.assertEqual(
            {
                cadence: advice_calls(
                    file_span_mib=96,
                    cadence_mib=cadence,
                )
                for cadence in (32, 48, 64, 80, 96)
            },
            {32: 3, 48: 2, 64: 2, 80: 2, 96: 1},
        )

    def test_closed_form_thresholds(self):
        thresholds = staircase_thresholds()
        self.assertAlmostEqual(
            thresholds["activate_32_tradeoff_mib"],
            110.609,
            places=6,
        )
        self.assertAlmostEqual(
            thresholds["activate_48_tradeoff_mib"],
            126.609,
            places=6,
        )

    def test_three_capacity_regimes(self):
        self.assertEqual(
            frozen_staircase_frontier(memory_high_mib=100),
            (96,),
        )
        self.assertEqual(
            frozen_staircase_frontier(memory_high_mib=120),
            (32, 96),
        )
        self.assertEqual(
            frozen_staircase_frontier(memory_high_mib=144),
            (32, 48, 96),
        )
        self.assertEqual(
            frozen_staircase_frontier(memory_high_mib=160),
            (32, 48, 96),
        )
        self.assertEqual(
            frozen_staircase_frontier(memory_high_mib=176),
            (32, 48, 96),
        )

    def test_mechanism_arms_are_not_frontier_arms_in_closed_form(self):
        roles = cadence_roles()
        self.assertIn("mechanism", roles[64])
        self.assertIn("threshold", roles[80])
        for high in (80, 100, 110.609, 120, 126.609, 144, 176, 220):
            frontier = frozen_staircase_frontier(memory_high_mib=high)
            self.assertNotIn(64, frontier)
            self.assertNotIn(80, frontier)

    def test_10000_random_capacities_match_brute_pareto(self):
        rng = random.Random(452)
        for _ in range(10_000):
            high = rng.uniform(76.700001, 240.0)
            self.assertEqual(
                frozen_staircase_frontier(memory_high_mib=high),
                brute_frontier(memory_high_mib=high),
            )


if __name__ == "__main__":
    unittest.main()
