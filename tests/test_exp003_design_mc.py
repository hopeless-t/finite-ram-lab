import unittest

import numpy as np

from finite_ram_lab.exp003_design_mc import (
    DESIGNS,
    choose_design,
    empirical_pair,
)


class Exp003DesignMcTests(unittest.TestCase):
    def test_empirical_pair_reconstructs_n2_summary(self):
        mean = np.array([5.0])
        sd = np.array([2.0])
        lo, hi = empirical_pair(mean, sd)
        values = np.array([lo[0], hi[0]])
        self.assertAlmostEqual(values.mean(), 5.0)
        self.assertAlmostEqual(values.std(ddof=1), 2.0)

    def test_trial_budgets(self):
        expected = {
            "D1_16x1": 384,
            "D2_24x1": 576,
            "D3_32x1": 768,
            "D4_16x2": 768,
            "D5_24x2": 1152,
        }
        self.assertEqual(
            {d.name: d.total_trials for d in DESIGNS},
            expected,
        )

    def test_selection_is_fail_closed(self):
        designs = {
            "D": {
                "total_trials": 10,
                "blocks": 10,
                "cells": {
                    "null_0pct": {"screen_detection_rate": 0.05},
                    "weak_25pct": {"screen_detection_rate": 0.40},
                    "moderate_50pct": {"screen_detection_rate": 0.99},
                },
            }
        }
        result = choose_design(designs, 0.065, 0.70, 0.90)
        self.assertEqual(
            result["status"],
            "NO_DESIGN_MEETS_FROZEN_RULE",
        )
        self.assertIsNone(result["selected"])


if __name__ == "__main__":
    unittest.main()
