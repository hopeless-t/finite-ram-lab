from __future__ import annotations

import json
import unittest
from pathlib import Path

import numpy as np

from finite_ram_lab.sig001_design_mc import (
    _required_specificity,
    analyze,
    clopper_pearson_lower,
    simulate_cell,
)


class Sig001DesignMcTests(unittest.TestCase):
    def test_clopper_pearson_lower_fail_closed_at_zero(self) -> None:
        out = clopper_pearson_lower(
            np.array([0, 5, 10]),
            np.array([10, 10, 10]),
            0.05,
        )
        self.assertEqual(out[0], 0.0)
        self.assertGreater(out[1], 0.0)
        self.assertGreater(out[2], out[1])
        self.assertLess(out[2], 1.0)

    def test_required_specificity_monotone(self) -> None:
        low = _required_specificity(
            np.array([0.10]),
            np.array([0.60]),
            2.0,
        )[0]
        high_t = _required_specificity(
            np.array([0.10]),
            np.array([0.90]),
            2.0,
        )[0]
        high_q = _required_specificity(
            np.array([0.25]),
            np.array([0.60]),
            2.0,
        )[0]
        self.assertLess(high_t, low)
        self.assertLess(high_q, low)

    def test_safe_provider_certifies_more_often_than_unsafe(self) -> None:
        safe_rng = np.random.default_rng(1)
        unsafe_rng = np.random.default_rng(2)
        safe = simulate_cell(
            n=4096,
            q=0.10,
            sensitivity=0.90,
            specificity=0.95,
            repetitions=512,
            rng=safe_rng,
            alpha_component=0.0125,
            primary_cost_ratio_lower=1.5,
            secondary_cost_ratio_lower=1.5,
        )
        unsafe = simulate_cell(
            n=4096,
            q=0.10,
            sensitivity=0.90,
            specificity=0.50,
            repetitions=512,
            rng=unsafe_rng,
            alpha_component=0.0125,
            primary_cost_ratio_lower=1.5,
            secondary_cost_ratio_lower=1.5,
        )
        self.assertGreater(
            safe["primary_certification_rate"],
            unsafe["primary_certification_rate"],
        )

    def test_analysis_smoke(self) -> None:
        spec = json.loads(
            Path("specs/SIG-001-DESIGN-MC.json").read_text()
        )
        spec["action_cost_bootstrap_resamples"] = 512
        spec["simulation_repetitions"] = 128
        spec["sample_sizes"] = [128, 512]
        spec["scenarios"] = [
            spec["scenarios"][0],
            spec["scenarios"][-1],
        ]
        result = analyze(spec)
        self.assertEqual(result["status"], "PASS")
        self.assertGreater(
            result["primary_action_cost"]["lower_ratio"],
            0.0,
        )
        self.assertGreater(
            result["secondary_action_cost"]["lower_ratio"],
            0.0,
        )
        self.assertIn("LQ_BORDERLINE", result["scenarios"])
        self.assertIn("MQ_UNSAFE", result["scenarios"])


if __name__ == "__main__":
    unittest.main()
