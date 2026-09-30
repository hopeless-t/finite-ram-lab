from __future__ import annotations

import unittest

from finite_ram_lab.age_stage_a_no_event_sensitivity import (
    analyze,
    no_event_marginals,
)


class AgeStageANoEventSensitivityTests(unittest.TestCase):
    def test_time_model_no_event_probability_is_lower(self) -> None:
        result = no_event_marginals(
            p_low=0.002,
            p_high=0.05,
            exposure_factor=13.0,
            fast_n=3,
            hold_n=9,
            grid_points=20_000,
        )
        self.assertGreater(
            result["p_no_event_given_TOUCH"],
            result["p_no_event_given_TIME"],
        )
        self.assertGreater(
            result["bayes_factor_TOUCH_over_TIME"],
            1.0,
        )

    def test_zero_hold_collapses_models(self) -> None:
        result = no_event_marginals(
            p_low=0.002,
            p_high=0.05,
            exposure_factor=16.0,
            fast_n=3,
            hold_n=0,
            grid_points=20_000,
        )
        self.assertAlmostEqual(
            result["p_no_event_given_TOUCH"],
            result["p_no_event_given_TIME"],
            places=12,
        )

    def test_age_r2_shape(self) -> None:
        result = analyze(
            exposure_factor=13.3793209552819,
            fast_n=3,
            hold_n=9,
            grid_points=20_000,
        )
        self.assertEqual(
            result["observed_complete_panel"]["FAST"],
            3,
        )
        self.assertEqual(
            result["observed_complete_panel"]["HOLD32"],
            9,
        )
        self.assertEqual(
            set(result["results"]),
            {"low", "central", "high"},
        )


if __name__ == "__main__":
    unittest.main()
