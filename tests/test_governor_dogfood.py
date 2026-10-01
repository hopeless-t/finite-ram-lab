from __future__ import annotations

import unittest
from unittest.mock import patch

from finite_ram_lab.governor_dogfood import (
    BALANCED_PROFILE_ORDERS,
    PROFILES,
    run_governor_dogfood,
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
                "median_work_seconds": 0.4144,
            },
            {
                "q": 2,
                "samples": 4,
                "semantic_exact_count": 4,
                "median_peak_bytes": 67_024_896,
                "max_peak_bytes": 67_108_864,
                "median_work_seconds": 0.4007,
            },
            {
                "q": 4,
                "samples": 4,
                "semantic_exact_count": 4,
                "median_peak_bytes": 71_217_152,
                "max_peak_bytes": 71_303_168,
                "median_work_seconds": 0.3922,
            },
            {
                "q": 7,
                "samples": 4,
                "semantic_exact_count": 4,
                "median_peak_bytes": 71_507_968,
                "max_peak_bytes": 71_507_968,
                "median_work_seconds": 0.3886,
            },
        ],
    }


class GovernorDogfoodTests(unittest.TestCase):
    def test_profiles_select_q12347_shape(self):
        self.assertEqual([name for name, _, _ in PROFILES], [
            "upper_q1_boundary",
            "upper_q2_boundary",
            "upper_q4_boundary",
            "upper_q7_boundary",
        ])

    def test_balanced_orders_place_each_profile_in_each_position(self):
        for profile_index in range(4):
            positions = {
                order.index(profile_index)
                for order in BALANCED_PROFILE_ORDERS
            }
            self.assertEqual(positions, {0, 1, 2, 3})

    def test_dogfood_counts_compliance_and_misses(self):
        calls = []

        def fake_child(**kwargs):
            q = kwargs["q"]
            calls.append(q)
            peaks = {1: 67_020_000, 2: 67_200_000, 4: 71_200_000, 7: 71_500_000}
            return {
                "q": q,
                "semantic_exact": True,
                "output_sha256": "same",
                "normalized_peak_growth_bytes": peaks[q],
                "work_seconds": 1.0 / q,
            }

        with patch(
            "finite_ram_lab.governor_dogfood._run_fresh_child",
            side_effect=fake_child,
        ):
            result = run_governor_dogfood(
                source(),
                repetitions=4,
                size=64,
                seed=471,
            )

        self.assertEqual(len(calls), 16)
        self.assertEqual(result["overall"]["budget_miss_count"], 4)
        self.assertEqual(
            result["overall"]["classification"],
            "BOUNDARY_BUDGET_CALIBRATION_REQUIRED",
        )
        q2 = next(
            row for row in result["summary_rows"]
            if row["selected_q"] == 2
        )
        self.assertEqual(q2["budget_miss_count"], 4)

    def test_semantic_failure_blocks_interpretation(self):
        def fake_child(**kwargs):
            return {
                "q": kwargs["q"],
                "semantic_exact": False,
                "output_sha256": "x",
                "normalized_peak_growth_bytes": 1,
                "work_seconds": 1.0,
            }

        with patch(
            "finite_ram_lab.governor_dogfood._run_fresh_child",
            side_effect=fake_child,
        ):
            with self.assertRaisesRegex(RuntimeError, "semantic_gate_failed"):
                run_governor_dogfood(
                    source(),
                    repetitions=4,
                    size=64,
                    seed=471,
                )


if __name__ == "__main__":
    unittest.main()
