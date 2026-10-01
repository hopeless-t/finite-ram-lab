from __future__ import annotations

import unittest

from finite_ram_lab.quotient_beam_benchmark import (
    fixed_mixed_panel,
    synthetic_beam_panel,
    width_needed_for_target,
)


class QuotientBeamBenchmarkTests(unittest.TestCase):
    def test_fixed_mixed_panel_preserves_same_beam_coverage(self):
        result = fixed_mixed_panel(widths=(4, 8, 16))
        self.assertEqual(
            result["compilation"]["raw_combination_count"],
            640,
        )
        self.assertEqual(
            result["compilation"]["compiled_combination_count"],
            384,
        )
        for row in result["rows"]:
            self.assertEqual(
                row["raw_exact_point_coverage"],
                row["quotient_exact_point_coverage"],
            )

    def test_seeded_synthetic_panel_shows_no_coverage_regression(self):
        result = synthetic_beam_panel(
            cases=50,
            seed=45602,
            widths=(4, 8, 16),
        )
        for row in result["comparisons"]:
            self.assertGreaterEqual(
                row.quotient_mean_coverage,
                row.raw_mean_coverage,
            )
            self.assertEqual(row.quotient_worse_cases, 0)

    def test_width_target_helper(self):
        result = synthetic_beam_panel(
            cases=20,
            seed=45602,
            widths=(4, 8, 16, 32),
        )
        rows = result["comparisons"]
        self.assertIsNotNone(
            width_needed_for_target(
                rows,
                target_coverage=0.5,
                mode="raw",
            )
        )
        self.assertIsNotNone(
            width_needed_for_target(
                rows,
                target_coverage=0.5,
                mode="quotient",
            )
        )


if __name__ == "__main__":
    unittest.main()
