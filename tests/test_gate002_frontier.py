from __future__ import annotations

import json
import unittest
from pathlib import Path

from finite_ram_lab.gate002_frontier import analyze, required_specificity


class Gate002FrontierTests(unittest.TestCase):
    def test_symmetric_accuracy_reduces_to_gate001_threshold(self) -> None:
        h = 2.0
        b = 8.0
        q = 0.25
        a = ((1.0 - q) * h) / (((1.0 - q) * h) + q * b)
        self.assertAlmostEqual(required_specificity(h, b, q, a), a)

    def test_required_specificity_falls_with_sensitivity_and_q(self) -> None:
        h = 2.0
        b = 8.0
        low_t = required_specificity(h, b, 0.10, 0.60)
        high_t = required_specificity(h, b, 0.10, 0.90)
        high_q = required_specificity(h, b, 0.50, 0.60)
        assert low_t is not None and high_t is not None and high_q is not None
        self.assertLess(high_t, low_t)
        self.assertLess(high_q, low_t)

    def test_invalid_empirical_sign_returns_none(self) -> None:
        self.assertIsNone(required_specificity(-1.0, 2.0, 0.25, 0.9))
        self.assertIsNone(required_specificity(1.0, -2.0, 0.25, 0.9))

    def test_analysis_smoke(self) -> None:
        spec = json.loads(Path("specs/GATE-002-DESIGN.json").read_text())
        spec["bootstrap_resamples"] = 256
        spec["q_grid"] = [0.10]
        spec["sensitivity_grid"] = [0.80]
        result = analyze(spec)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["runner_blocks"], 16)
        row = result["frontier"]["0.100"]["0.800"]
        for metric in ("arithmetic_total_work", "log_total_work"):
            self.assertIsNotNone(row[metric]["point"]["raw_required_specificity"])
            self.assertGreater(row[metric]["bootstrap"]["valid_fraction"], 0.9)


if __name__ == "__main__":
    unittest.main()
