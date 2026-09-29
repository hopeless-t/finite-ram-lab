from __future__ import annotations

import unittest

import numpy as np

from finite_ram_lab.tx_age_decoupling_mc import (
    Design,
    evaluate_design,
    hold_probability,
)


class TxAgeDecouplingMCTests(unittest.TestCase):
    def test_exposure_factor_one_is_identity(self) -> None:
        p = np.array([0.001, 0.01, 0.2])
        np.testing.assert_allclose(hold_probability(p, 1), p)

    def test_more_time_never_lowers_probability(self) -> None:
        p = np.array([0.001, 0.01, 0.05])
        p8 = hold_probability(p, 8)
        p16 = hold_probability(p, 16)
        self.assertTrue(np.all(p16 >= p8))
        self.assertTrue(np.all(p8 >= p))

    def test_time_model_is_more_detectable_with_large_hold(self) -> None:
        short = evaluate_design(
            Design("short", 4, 12, 4),
            p_low=0.002,
            p_high=0.05,
            draws=4000,
            seed=7,
            grid_points=250,
        )
        long = evaluate_design(
            Design("long", 4, 12, 16),
            p_low=0.002,
            p_high=0.05,
            draws=4000,
            seed=7,
            grid_points=250,
        )
        self.assertGreater(
            long["TIME"]["any_detection"],
            short["TIME"]["any_detection"],
        )


if __name__ == "__main__":
    unittest.main()
