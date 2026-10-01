from __future__ import annotations

import unittest
from unittest.mock import patch

from finite_ram_lab.q1_tail_calibration import (
    rank_max_predictive_coverage_floor,
    run_q1_tail_panel,
)


def b469() -> dict:
    return {
        "schema": "finite-ram-lab.b469-result/v0.1",
        "summary_rows": [
            {
                "q": 1,
                "samples": 4,
                "max_peak_bytes": 67_022_848,
            }
        ],
    }


def b471() -> dict:
    return {
        "schema": "finite-ram-lab.b471-result/v0.1",
        "summary_rows": [
            {
                "selected_q": 1,
                "samples": 4,
                "max_observed_peak_bytes": 67_117_056,
            }
        ],
    }


class Q1TailCalibrationTests(unittest.TestCase):
    def test_rank_max_coverage_floor(self):
        self.assertAlmostEqual(
            rank_max_predictive_coverage_floor(20),
            20 / 21,
        )

    def test_stable_panel_preserves_prior_union_max(self):
        peaks = [67_100_000] * 12
        cursor = {"i": 0}

        def fake_child(**kwargs):
            i = cursor["i"]
            cursor["i"] += 1
            return {
                "semantic_exact": True,
                "normalized_peak_growth_bytes": peaks[i],
                "work_seconds": 0.4,
                "output_sha256": "same",
            }

        with patch(
            "finite_ram_lab.q1_tail_calibration._run_fresh_child",
            side_effect=fake_child,
        ):
            result = run_q1_tail_panel(b469(), b471())

        self.assertEqual(
            result["classification"],
            "Q1_EMPIRICAL_MAX_STABLE_IN_TARGETED_PANEL",
        )
        self.assertEqual(
            result["union"]["empirical_max_peak_bytes"],
            67_117_056,
        )
        self.assertEqual(result["union"]["sample_count"], 20)

    def test_moving_panel_updates_union_max(self):
        peaks = [67_100_000] * 11 + [67_200_000]
        cursor = {"i": 0}

        def fake_child(**kwargs):
            i = cursor["i"]
            cursor["i"] += 1
            return {
                "semantic_exact": True,
                "normalized_peak_growth_bytes": peaks[i],
                "work_seconds": 0.4,
                "output_sha256": "same",
            }

        with patch(
            "finite_ram_lab.q1_tail_calibration._run_fresh_child",
            side_effect=fake_child,
        ):
            result = run_q1_tail_panel(b469(), b471())

        self.assertEqual(result["classification"], "Q1_EMPIRICAL_MAX_MOVED")
        self.assertEqual(
            result["union"]["empirical_max_peak_bytes"],
            67_200_000,
        )
        self.assertEqual(
            result["new_panel"]["prior_boundary_exceed_count"],
            1,
        )

    def test_semantic_failure_blocks_panel(self):
        def fake_child(**kwargs):
            return {
                "semantic_exact": False,
                "normalized_peak_growth_bytes": 1,
                "work_seconds": 0.4,
                "output_sha256": "bad",
            }

        with patch(
            "finite_ram_lab.q1_tail_calibration._run_fresh_child",
            side_effect=fake_child,
        ):
            with self.assertRaisesRegex(RuntimeError, "semantic_gate_failed"):
                run_q1_tail_panel(b469(), b471())


if __name__ == "__main__":
    unittest.main()
