from __future__ import annotations

import unittest

from finite_ram_lab.fr_p9_011_repeated_phase_frontier import _linear_fit, pareto_modes


class RepeatedPhaseFrontierTests(unittest.TestCase):
    def test_tradeoff_keeps_both_modes_on_typed_frontier(self) -> None:
        rows = [
            {"mode": "KEEP_WARM", "memory_peak_bytes": 140, "materialize_ns_total": 10},
            {"mode": "FAULT_IN", "memory_peak_bytes": 100, "materialize_ns_total": 40},
        ]
        self.assertEqual(pareto_modes(rows), ["FAULT_IN", "KEEP_WARM"])

    def test_strictly_better_mode_dominates(self) -> None:
        rows = [
            {"mode": "KEEP_WARM", "memory_peak_bytes": 140, "materialize_ns_total": 40},
            {"mode": "FAULT_IN", "memory_peak_bytes": 100, "materialize_ns_total": 20},
        ]
        self.assertEqual(pareto_modes(rows), ["FAULT_IN"])

    def test_linear_fit_recovers_positive_slope(self) -> None:
        fit = _linear_fit([1, 2, 4, 8], [10, 20, 40, 80])
        self.assertAlmostEqual(float(fit["slope"]), 10.0)
        self.assertAlmostEqual(float(fit["intercept"]), 0.0)
        self.assertAlmostEqual(float(fit["r2"]), 1.0)

    def test_linear_fit_fails_closed_on_insufficient_points(self) -> None:
        self.assertEqual(
            _linear_fit([1], [10]),
            {"slope": None, "intercept": None, "r2": None},
        )


if __name__ == "__main__":
    unittest.main()
