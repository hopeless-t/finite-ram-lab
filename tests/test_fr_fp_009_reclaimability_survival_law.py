from __future__ import annotations

import unittest

from finite_ram_lab.fr_fp_002_semantic_oom import (
    _episodes,
)
from finite_ram_lab.fr_fp_009_reclaimability_survival_law import (
    analytic_oom_rate,
    run_panel,
    simulated_oom_rate,
)


class ReclaimabilitySurvivalLawTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()
        cls.trajectories = [
            trajectory
            for _family, trajectory
            in _episodes()
        ]

    def test_panel_passes(self) -> None:
        self.assertEqual(
            self.result[
                "status"
            ],
            "PASS",
        )
        self.assertTrue(
            all(
                self.result[
                    "checks"
                ].values()
            )
        )

    def test_expanded_grid_is_exact(self) -> None:
        self.assertEqual(
            self.result[
                "grid"
            ][
                "cells"
            ],
            252,
        )
        self.assertEqual(
            self.result[
                "grid"
            ][
                "max_abs_error"
            ],
            0.0,
        )

    def test_pipeline_feasible_case_is_zero(self) -> None:
        analytic = (
            analytic_oom_rate(
                self.trajectories,
                transfer_lead=3,
                hot_budget=4,
                safe_shift=0,
            )
        )
        simulated = (
            simulated_oom_rate(
                self.trajectories,
                transfer_lead=3,
                hot_budget=4,
                safe_shift=0,
            )
        )

        self.assertEqual(
            analytic,
            0.0,
        )
        self.assertEqual(
            simulated,
            0.0,
        )

    def test_survival_case_matches(self) -> None:
        analytic = (
            analytic_oom_rate(
                self.trajectories,
                transfer_lead=4,
                hot_budget=4,
                safe_shift=10,
            )
        )
        simulated = (
            simulated_oom_rate(
                self.trajectories,
                transfer_lead=4,
                hot_budget=4,
                safe_shift=10,
            )
        )

        self.assertAlmostEqual(
            analytic,
            0.194,
        )
        self.assertEqual(
            analytic,
            simulated,
        )

    def test_claim_ceiling_is_narrow(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "ANALYTIC_LAW_FOR_FROZEN_SYNTHETIC_TRANSFER_MODEL_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
