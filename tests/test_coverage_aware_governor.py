from __future__ import annotations

import unittest

from finite_ram_lab.coverage_aware_governor import (
    build_policy,
    calibrated_points,
    select_q,
)


def b469() -> dict:
    return {
        "schema": "finite-ram-lab.b469-result/v0.1",
        "summary_rows": [
            {"q": 1, "median_work_seconds": 0.4144},
            {"q": 2, "median_work_seconds": 0.4007},
            {"q": 4, "median_work_seconds": 0.3922},
            {"q": 7, "median_work_seconds": 0.3886},
        ],
    }


def b472() -> dict:
    return {
        "schema": "finite-ram-lab.b472-result/v0.1",
        "union_empirical_max_peak_bytes": 67_117_056,
        "total_sample_count": 20,
        "rank_max_one_step_predictive_coverage_floor": 20 / 21,
    }


def b474() -> dict:
    return {
        "schema": "finite-ram-lab.b474-result/v0.1",
        "summary_rows": [
            {
                "q": 2,
                "union_empirical_max_peak_bytes": 67_194_880,
                "union_sample_count": 19,
                "rank_max_one_step_predictive_coverage_floor": 0.95,
            },
            {
                "q": 4,
                "union_empirical_max_peak_bytes": 71_389_184,
                "union_sample_count": 19,
                "rank_max_one_step_predictive_coverage_floor": 0.95,
            },
            {
                "q": 7,
                "union_empirical_max_peak_bytes": 71_544_832,
                "union_sample_count": 19,
                "rank_max_one_step_predictive_coverage_floor": 0.95,
            },
        ],
    }


class CoverageAwareGovernorTests(unittest.TestCase):
    def test_points_include_coverage_metadata(self):
        points = calibrated_points(b469(), b472(), b474())
        q1 = next(row for row in points if row["q"] == 1)
        self.assertEqual(q1["sample_count"], 20)
        self.assertGreater(q1["rank_max_one_step_predictive_coverage_floor"], 0.95)

    def test_budget_breakpoints_select_expected_q(self):
        self.assertEqual(
            select_q(
                b469(), b472(), b474(),
                peak_budget_bytes=67_117_056,
            )["selected_q"],
            1,
        )
        self.assertEqual(
            select_q(
                b469(), b472(), b474(),
                peak_budget_bytes=67_194_880,
            )["selected_q"],
            2,
        )
        self.assertEqual(
            select_q(
                b469(), b472(), b474(),
                peak_budget_bytes=71_389_184,
            )["selected_q"],
            4,
        )
        self.assertEqual(
            select_q(
                b469(), b472(), b474(),
                peak_budget_bytes=71_544_832,
            )["selected_q"],
            7,
        )

    def test_higher_coverage_requirement_can_reject_all(self):
        with self.assertRaisesRegex(
            RuntimeError,
            "no_coverage_qualified_q_fits_budget",
        ):
            select_q(
                b469(), b472(), b474(),
                peak_budget_bytes=100_000_000,
                minimum_rank_coverage=0.99,
            )

    def test_policy_contains_all_breakpoints_at_95pct(self):
        policy = build_policy(b469(), b472(), b474())
        self.assertEqual(
            [row["selected_q"] for row in policy["breakpoints"]],
            [1, 2, 4, 7],
        )
        self.assertTrue(
            all(
                row["rank_max_one_step_predictive_coverage_floor"] >= 0.95
                for row in policy["breakpoints"]
            )
        )


if __name__ == "__main__":
    unittest.main()
