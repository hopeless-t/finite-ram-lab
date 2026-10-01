from __future__ import annotations

import unittest
from unittest.mock import patch

from finite_ram_lab.tail_vs_drift import (
    PER_Q_ALPHA,
    beta_binomial_upper_tail,
    run_tail_vs_drift_panel,
)


def b469() -> dict:
    return {
        "schema": "finite-ram-lab.b469-result/v0.1",
        "status": "PASS",
        "workflow_run_id": 469,
        "sweep_sha256": "a" * 64,
        "pareto_q": [1, 2, 4, 7],
        "semantic_exact_count_per_q": 4,
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
        "union_empirical_max_peak_bytes": 100,
        "total_sample_count": 20,
        "rank_max_one_step_predictive_coverage_floor": 20 / 21,
    }


def b474() -> dict:
    return {
        "schema": "finite-ram-lab.b474-result/v0.1",
        "summary_rows": [
            {
                "q": 2,
                "union_empirical_max_peak_bytes": 200,
                "union_sample_count": 19,
                "rank_max_one_step_predictive_coverage_floor": 0.95,
            },
            {
                "q": 4,
                "union_empirical_max_peak_bytes": 300,
                "union_sample_count": 19,
                "rank_max_one_step_predictive_coverage_floor": 0.95,
            },
            {
                "q": 7,
                "union_empirical_max_peak_bytes": 400,
                "union_sample_count": 19,
                "rank_max_one_step_predictive_coverage_floor": 0.95,
            },
        ],
    }


class TailVsDriftTests(unittest.TestCase):
    def test_reference_tail_requires_four_of_eight_at_familywise_alpha(self):
        for n in (19, 20):
            self.assertGreater(
                beta_binomial_upper_tail(
                    3,
                    8,
                    calibration_sample_count=n,
                ),
                PER_Q_ALPHA,
            )
            self.assertLess(
                beta_binomial_upper_tail(
                    4,
                    8,
                    calibration_sample_count=n,
                ),
                PER_Q_ALPHA,
            )

    def test_single_exceedance_is_tail_compatible(self):
        counters = {1: 0, 2: 0, 4: 0, 7: 0}
        boundaries = {1: 100, 2: 200, 4: 300, 7: 400}

        def fake_child(**kwargs):
            q = kwargs["q"]
            i = counters[q]
            counters[q] += 1
            peak = boundaries[q] + 1 if q == 2 and i == 0 else boundaries[q]
            return {
                "semantic_exact": True,
                "normalized_peak_growth_bytes": peak,
                "work_seconds": 1.0,
                "output_sha256": "same",
            }

        with patch(
            "finite_ram_lab.tail_vs_drift._run_fresh_child",
            side_effect=fake_child,
        ):
            result = run_tail_vs_drift_panel(
                b469(), b472(), b474(),
                size=64,
            )

        self.assertEqual(
            result["overall"]["classification"],
            "TAIL_COMPATIBLE_EXCEEDANCES",
        )
        q2 = next(row for row in result["q_rows"] if row["q"] == 2)
        self.assertEqual(q2["new_max_exceed_count"], 1)
        self.assertEqual(q2["classification"], "TAIL_COMPATIBLE_EXCEEDANCE")

    def test_four_of_eight_exceedances_flags_local_drift_suspect(self):
        counters = {1: 0, 2: 0, 4: 0, 7: 0}
        boundaries = {1: 100, 2: 200, 4: 300, 7: 400}

        def fake_child(**kwargs):
            q = kwargs["q"]
            i = counters[q]
            counters[q] += 1
            peak = boundaries[q] + 1 if q == 4 and i < 4 else boundaries[q]
            return {
                "semantic_exact": True,
                "normalized_peak_growth_bytes": peak,
                "work_seconds": 1.0,
                "output_sha256": "same",
            }

        with patch(
            "finite_ram_lab.tail_vs_drift._run_fresh_child",
            side_effect=fake_child,
        ):
            result = run_tail_vs_drift_panel(
                b469(), b472(), b474(),
                size=64,
            )

        self.assertEqual(result["overall"]["classification"], "DRIFT_SUSPECT")
        self.assertEqual(result["overall"]["suspect_q"], [4])

    def test_semantic_failure_blocks_diagnostic(self):
        def fake_child(**kwargs):
            return {
                "semantic_exact": False,
                "normalized_peak_growth_bytes": 1,
                "work_seconds": 1.0,
                "output_sha256": "bad",
            }

        with patch(
            "finite_ram_lab.tail_vs_drift._run_fresh_child",
            side_effect=fake_child,
        ):
            with self.assertRaisesRegex(RuntimeError, "semantic_gate_failed"):
                run_tail_vs_drift_panel(
                    b469(), b472(), b474(),
                    size=64,
                )


if __name__ == "__main__":
    unittest.main()
