from __future__ import annotations

import unittest

from finite_ram_lab.q_budget_governor import (
    RiskMode,
    build_governor,
    policy_breakpoints,
    select_q,
)


def source() -> dict:
    return {
        "schema": "finite-ram-lab.b469-result/v0.1",
        "status": "PASS",
        "workflow_run_id": 469,
        "sweep_sha256": "a" * 64,
        "pareto_q": [1, 2, 4, 7],
        "semantic_exact_count_per_q": 4,
        "summary_rows": [
            {
                "q": 1,
                "samples": 4,
                "semantic_exact_count": 4,
                "median_peak_bytes": 67_014_656,
                "max_peak_bytes": 67_022_848,
                "median_work_seconds": 0.4144076,
            },
            {
                "q": 2,
                "samples": 4,
                "semantic_exact_count": 4,
                "median_peak_bytes": 67_024_896,
                "max_peak_bytes": 67_108_864,
                "median_work_seconds": 0.4006967,
            },
            {
                "q": 4,
                "samples": 4,
                "semantic_exact_count": 4,
                "median_peak_bytes": 71_217_152,
                "max_peak_bytes": 71_303_168,
                "median_work_seconds": 0.3921726,
            },
            {
                "q": 7,
                "samples": 4,
                "semantic_exact_count": 4,
                "median_peak_bytes": 71_507_968,
                "max_peak_bytes": 71_507_968,
                "median_work_seconds": 0.3885800,
            },
        ],
    }


class QBudgetGovernorTests(unittest.TestCase):
    def test_median_budget_selects_expected_q(self):
        data = source()
        self.assertEqual(
            select_q(
                data,
                peak_budget_bytes=67_014_656,
                mode=RiskMode.MEDIAN,
            )["selected_q"],
            1,
        )
        self.assertEqual(
            select_q(
                data,
                peak_budget_bytes=67_024_896,
                mode=RiskMode.MEDIAN,
            )["selected_q"],
            2,
        )
        self.assertEqual(
            select_q(
                data,
                peak_budget_bytes=71_217_152,
                mode=RiskMode.MEDIAN,
            )["selected_q"],
            4,
        )
        self.assertEqual(
            select_q(
                data,
                peak_budget_bytes=71_507_968,
                mode=RiskMode.MEDIAN,
            )["selected_q"],
            7,
        )

    def test_observed_upper_mode_is_more_conservative_for_q2(self):
        data = source()
        budget = 67_050_000
        self.assertEqual(
            select_q(data, peak_budget_bytes=budget, mode=RiskMode.MEDIAN)[
                "selected_q"
            ],
            2,
        )
        self.assertEqual(
            select_q(
                data,
                peak_budget_bytes=budget,
                mode=RiskMode.OBSERVED_UPPER,
            )["selected_q"],
            1,
        )

    def test_no_candidate_under_budget_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError, "no_q_fits_peak_budget"):
            select_q(
                source(),
                peak_budget_bytes=1,
                mode=RiskMode.MEDIAN,
            )

    def test_policy_breakpoints_preserve_all_pareto_q(self):
        policy = policy_breakpoints(source(), mode=RiskMode.MEDIAN)
        self.assertEqual(
            [row["selected_q"] for row in policy["breakpoints"]],
            [1, 2, 4, 7],
        )

    def test_build_governor_contains_both_risk_modes(self):
        governor = build_governor(source())
        self.assertEqual(
            set(governor["policy"]),
            {"median", "observed_upper"},
        )


if __name__ == "__main__":
    unittest.main()
