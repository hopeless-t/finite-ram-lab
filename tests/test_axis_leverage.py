from __future__ import annotations

import unittest

from finite_ram_lab.axis_leverage import analyze_axis_leverage


def b463():
    return {
        "schema": "finite-ram-lab.b463-result/v0.1",
        "pair_count": 6,
        "semantic_match_count": 6,
        "workflow_run_id": 463,
        "median_treatment_minus_reference_peak_bytes": -25_155_584,
        "median_latency_ratio_treatment_over_reference": 1.05799,
    }


def b465():
    return {
        "schema": "finite-ram-lab.b465-result/v0.1",
        "pair_count": 4,
        "semantic_match_count": 4,
        "workflow_run_id": 465,
        "median_selected_minus_baseline_peak_bytes": -2_048,
        "median_latency_ratio_selected_over_baseline": 1.01584,
    }


def b467():
    return {
        "schema": "finite-ram-lab.b467-result/v0.1",
        "pair_count": 4,
        "semantic_match_count": 4,
        "workflow_run_id": 467,
        "median_selected_minus_baseline_peak_bytes": 36_864,
        "median_latency_ratio_selected_over_baseline": 0.99219,
    }


class AxisLeverageTests(unittest.TestCase):
    def test_selects_lane_concurrency_axis(self):
        result = analyze_axis_leverage(b463(), b465(), b467())
        self.assertEqual(
            result["axis_decision"]["next_axis"],
            "residue_lane_concurrency_q",
        )
        self.assertEqual(
            result["next_experiment"]["coarse_sweep"],
            [1, 2, 4, 7],
        )
        self.assertFalse(result["next_experiment"]["execute_now"])

    def test_representation_effect_dominates_tested_tile_effect(self):
        result = analyze_axis_leverage(b463(), b465(), b467())
        ratio = result["peak_leverage"]["representation_over_tile_ratio"]
        self.assertGreater(ratio, 600.0)

    def test_semantic_incomplete_fails_closed(self):
        bad = b467()
        bad["semantic_match_count"] = 3
        with self.assertRaisesRegex(RuntimeError, "b467_semantic_incomplete"):
            analyze_axis_leverage(b463(), b465(), bad)


if __name__ == "__main__":
    unittest.main()
