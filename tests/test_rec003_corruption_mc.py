from __future__ import annotations

import unittest

from finite_ram_lab.rec003_corruption_mc import MUTATION_NAMES, run_campaign


class Rec003MonteCarloTests(unittest.TestCase):
    def test_campaign_is_deterministic_and_fail_closed(self) -> None:
        a = run_campaign(5000, seed=2026092807, max_mutations=4)
        b = run_campaign(5000, seed=2026092807, max_mutations=4)
        self.assertEqual(a, b)
        self.assertEqual(a["strict_false_accept"], 0)
        self.assertEqual(a["strict_false_reject"], 0)
        self.assertGreater(a["legacy_negative_control_false_accept"], 0)

    def test_every_mutation_family_is_exercised(self) -> None:
        result = run_campaign(5000, seed=2026092808, max_mutations=4)
        self.assertEqual(set(result["mutation_counts"]), set(MUTATION_NAMES))
        self.assertTrue(all(value > 0 for value in result["mutation_counts"].values()))


if __name__ == "__main__":
    unittest.main()
