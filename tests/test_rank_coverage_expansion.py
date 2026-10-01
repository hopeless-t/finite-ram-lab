from __future__ import annotations

import unittest
from unittest.mock import patch

from finite_ram_lab.rank_coverage_expansion import (
    BALANCED_ORDERS,
    run_expansion,
)


def b469() -> dict:
    return {
        "schema": "finite-ram-lab.b469-result/v0.1",
        "summary_rows": [
            {"q": 2, "samples": 4, "max_peak_bytes": 100},
            {"q": 4, "samples": 4, "max_peak_bytes": 200},
            {"q": 7, "samples": 4, "max_peak_bytes": 300},
        ],
    }


def b471() -> dict:
    return {
        "schema": "finite-ram-lab.b471-result/v0.1",
        "summary_rows": [
            {"selected_q": 2, "samples": 4, "max_observed_peak_bytes": 90},
            {"selected_q": 4, "samples": 4, "max_observed_peak_bytes": 210},
            {"selected_q": 7, "samples": 4, "max_observed_peak_bytes": 300},
        ],
    }


class RankCoverageExpansionTests(unittest.TestCase):
    def test_balanced_order_length_and_surface(self):
        self.assertEqual(len(BALANCED_ORDERS), 11)
        self.assertTrue(all(set(order) == {2, 4, 7} for order in BALANCED_ORDERS))

    def test_expansion_reaches_n19_per_q(self):
        def fake_child(**kwargs):
            q = kwargs["q"]
            peaks = {2: 95, 4: 205, 7: 299}
            return {
                "semantic_exact": True,
                "normalized_peak_growth_bytes": peaks[q],
                "work_seconds": 1.0,
                "output_sha256": "same",
            }

        with patch(
            "finite_ram_lab.rank_coverage_expansion._run_fresh_child",
            side_effect=fake_child,
        ):
            result = run_expansion(b469(), b471())

        self.assertTrue(result["all_q_at_least_95pct_rank_floor"])
        self.assertEqual(result["total_new_observations"], 33)
        for row in result["summary_rows"]:
            self.assertEqual(row["union_sample_count"], 19)
            self.assertAlmostEqual(
                row["rank_max_one_step_predictive_coverage_floor"],
                0.95,
            )

    def test_moving_q4_max_is_preserved(self):
        def fake_child(**kwargs):
            q = kwargs["q"]
            peak = 250 if q == 4 else {2: 95, 7: 299}[q]
            return {
                "semantic_exact": True,
                "normalized_peak_growth_bytes": peak,
                "work_seconds": 1.0,
                "output_sha256": "same",
            }

        with patch(
            "finite_ram_lab.rank_coverage_expansion._run_fresh_child",
            side_effect=fake_child,
        ):
            result = run_expansion(b469(), b471())

        q4 = next(row for row in result["summary_rows"] if row["q"] == 4)
        self.assertEqual(q4["union_empirical_max_peak_bytes"], 250)
        self.assertEqual(q4["union_max_moved_bytes"], 40)
        self.assertEqual(q4["prior_boundary_exceed_count"], 11)

    def test_semantic_failure_blocks_panel(self):
        def fake_child(**kwargs):
            return {
                "semantic_exact": False,
                "normalized_peak_growth_bytes": 1,
                "work_seconds": 1.0,
                "output_sha256": "bad",
            }

        with patch(
            "finite_ram_lab.rank_coverage_expansion._run_fresh_child",
            side_effect=fake_child,
        ):
            with self.assertRaisesRegex(RuntimeError, "semantic_gate_failed"):
                run_expansion(b469(), b471())


if __name__ == "__main__":
    unittest.main()
