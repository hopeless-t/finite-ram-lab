from __future__ import annotations

import unittest

from finite_ram_lab.repaired_governor_v2 import (
    build_policy,
    calibrated_points,
    select_q,
)


def b489() -> dict:
    return {
        "schema": "finite-ram-lab.b489-result/v0.1",
        "implementation": "TILED_WHERE",
        "summary_rows": [
            {
                "q": 2,
                "pooled_sample_count": 19,
                "pooled_empirical_max_peak_bytes": 50_696_192,
                "rank_max_one_step_predictive_coverage_floor": 0.95,
                "median_new_work_seconds": 0.3956,
            },
            {
                "q": 4,
                "pooled_sample_count": 19,
                "pooled_empirical_max_peak_bytes": 58_941_440,
                "rank_max_one_step_predictive_coverage_floor": 0.95,
                "median_new_work_seconds": 0.3878,
            },
            {
                "q": 7,
                "pooled_sample_count": 19,
                "pooled_empirical_max_peak_bytes": 71_507_968,
                "rank_max_one_step_predictive_coverage_floor": 0.95,
                "median_new_work_seconds": 0.3864,
            },
        ],
    }


class RepairedGovernorV2Tests(unittest.TestCase):
    def test_points_are_repaired_only(self):
        points = calibrated_points(b489())
        self.assertEqual([row["q"] for row in points], [2, 4, 7])
        self.assertTrue(all(row["sample_count"] == 19 for row in points))

    def test_breakpoints_select_expected_q(self):
        self.assertEqual(
            select_q(b489(), peak_budget_bytes=50_696_192)["selected_q"],
            2,
        )
        self.assertEqual(
            select_q(b489(), peak_budget_bytes=58_941_440)["selected_q"],
            4,
        )
        self.assertEqual(
            select_q(b489(), peak_budget_bytes=71_507_968)["selected_q"],
            7,
        )

    def test_q1_is_absent_from_policy(self):
        policy = build_policy(b489())
        self.assertEqual(policy["dominated_q_excluded"], [1])
        self.assertEqual(
            [row["selected_q"] for row in policy["breakpoints"]],
            [2, 4, 7],
        )

    def test_99_percent_request_fails_closed(self):
        with self.assertRaisesRegex(
            RuntimeError,
            "no_coverage_qualified_repaired_q_fits_budget",
        ):
            select_q(
                b489(),
                peak_budget_bytes=100_000_000,
                minimum_rank_coverage=0.99,
            )


if __name__ == "__main__":
    unittest.main()
