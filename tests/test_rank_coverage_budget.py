from __future__ import annotations

import unittest

from finite_ram_lab.rank_coverage_budget import (
    build_sample_budget,
    minimum_samples_for_rank_max_coverage,
    rank_max_coverage_floor,
)


def b469() -> dict:
    return {
        "schema": "finite-ram-lab.b469-result/v0.1",
        "summary_rows": [
            {"q": 1, "samples": 4},
            {"q": 2, "samples": 4},
            {"q": 4, "samples": 4},
            {"q": 7, "samples": 4},
        ],
    }


def b471() -> dict:
    return {
        "schema": "finite-ram-lab.b471-result/v0.1",
        "summary_rows": [
            {"selected_q": 1, "samples": 4},
            {"selected_q": 2, "samples": 4},
            {"selected_q": 4, "samples": 4},
            {"selected_q": 7, "samples": 4},
        ],
    }


def b472() -> dict:
    return {
        "schema": "finite-ram-lab.b472-result/v0.1",
        "q": 1,
        "total_sample_count": 20,
    }


class RankCoverageBudgetTests(unittest.TestCase):
    def test_minimum_samples_for_common_targets(self):
        self.assertEqual(minimum_samples_for_rank_max_coverage(0.95), 19)
        self.assertEqual(minimum_samples_for_rank_max_coverage(0.99), 99)

    def test_rank_floor(self):
        self.assertAlmostEqual(rank_max_coverage_floor(19), 0.95)
        self.assertAlmostEqual(rank_max_coverage_floor(20), 20 / 21)

    def test_95_percent_budget_targets_other_qs(self):
        result = build_sample_budget(b469(), b471(), b472())
        rows = {row["q"]: row for row in result["rows"]}
        self.assertTrue(rows[1]["target_met"])
        self.assertEqual(rows[1]["additional_samples_required"], 0)
        for q in (2, 4, 7):
            self.assertFalse(rows[q]["target_met"])
            self.assertEqual(rows[q]["current_sample_count"], 8)
            self.assertEqual(rows[q]["additional_samples_required"], 11)
        self.assertEqual(result["total_additional_samples_required"], 33)

    def test_invalid_target_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "target_coverage_invalid"):
            minimum_samples_for_rank_max_coverage(1.0)


if __name__ == "__main__":
    unittest.main()
