from __future__ import annotations

import unittest

from finite_ram_lab.semantic_reliability_surface import (
    run_surface,
    noisy_relevance_indices,
    wilson_interval,
)
from finite_ram_lab.semantic_working_set import corpus


class SemanticReliabilitySurfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run_surface()

    def test_noisy_selector_is_deterministic(self):
        case = corpus()[0]
        first = noisy_relevance_indices(
            case,
            2,
            replicate=123,
            error_probability=0.01,
        )
        second = noisy_relevance_indices(
            case,
            2,
            replicate=123,
            error_probability=0.01,
        )
        self.assertEqual(first, second)

    def test_wilson_interval_bounds_rate(self):
        lower, upper = wilson_interval(95, 100)
        self.assertLess(lower, 0.95)
        self.assertGreater(upper, 0.95)

    def test_frontier_moves_with_selector_error(self):
        frontier = self.result[
            "minimum_qualified_budget_by_error"
        ]
        self.assertEqual(frontier["0.0"], 2)
        self.assertEqual(frontier["0.01"], 2)
        self.assertEqual(frontier["0.02"], 4)
        self.assertEqual(frontier["0.05"], 6)
        self.assertEqual(frontier["0.1"], 8)
        self.assertEqual(frontier["0.2"], 8)

    def test_rare_event_sentinel_is_visible_and_qualified(self):
        sentinel = self.result["rare_event_sentinel"]
        self.assertEqual(sentinel["failure_count"], 30)
        self.assertEqual(
            sentinel["exact_rate"],
            0.996337890625,
        )
        self.assertGreaterEqual(
            sentinel["wilson95_lower"],
            0.95,
        )
        self.assertGreater(
            sentinel["captured_biopsy_count"],
            0,
        )

    def test_full_residency_recovers_every_surface_row(self):
        rows = [
            row
            for row in self.result["rows"]
            if row["budget"] == 8
        ]
        self.assertTrue(rows)
        self.assertTrue(
            all(row["exact_rate"] == 1.0 for row in rows)
        )

    def test_claim_ceiling_remains_synthetic(self):
        self.assertTrue(self.result["synthetic_only"])
        self.assertFalse(self.result["empirical_model_claim"])
        self.assertEqual(
            self.result["claim_ceiling"],
            "SYNTHETIC_RELIABILITY_RESIDENCY_SURFACE_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
