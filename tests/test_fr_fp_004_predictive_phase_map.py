from __future__ import annotations

import unittest

from finite_ram_lab.fr_fp_004_predictive_phase_map import (
    run_panel,
)


class PredictivePhaseMapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()
        cls.matrix = cls.result["matrix"]

    def test_panel_passes(self) -> None:
        self.assertEqual(
            self.result["status"],
            "PASS",
        )
        self.assertTrue(
            all(
                self.result["checks"].values()
            )
        )

    def test_deadline_infeasible_region_exists(self) -> None:
        cell = self.matrix["4"]["4"]

        self.assertEqual(
            cell["phase"],
            "DEADLINE_INFEASIBLE",
        )
        self.assertGreater(
            cell["always_preemptive"][
                "semantic_oom_rate"
            ],
            0.99,
        )

    def test_prediction_saves_io_at_moderate_slack(self) -> None:
        cell = self.matrix["2"]["8"]
        best = cell[
            "best_zero_oom_predictive"
        ]

        self.assertEqual(
            cell["phase"],
            "PREDICTION_SAVES_IO",
        )
        self.assertEqual(
            best["semantic_oom_rate"],
            0.0,
        )
        self.assertGreater(
            best["io_saving_fraction"],
            0.40,
        )

    def test_lead2_savings_increase_with_budget(self) -> None:
        values = [
            self.matrix["2"][str(budget)][
                "best_zero_oom_predictive"
            ]["io_saving_fraction"]
            for budget in (
                4,
                6,
                8,
                10,
            )
        ]

        self.assertEqual(
            values,
            sorted(values),
        )
        self.assertEqual(
            len(set(values)),
            len(values),
        )

    def test_claim_ceiling_is_synthetic(self) -> None:
        self.assertEqual(
            self.result["claim_ceiling"],
            "SYNTHETIC_PREDICTIVE_RESIDENCY_PHASE_BOUNDARY_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
