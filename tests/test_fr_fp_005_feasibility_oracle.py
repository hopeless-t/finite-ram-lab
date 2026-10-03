from __future__ import annotations

import unittest

from finite_ram_lab.fr_fp_005_feasibility_oracle import (
    route,
    run_panel,
)


class FeasibilityOracleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()

    def test_panel_passes(self) -> None:
        self.assertEqual(
            self.result["status"],
            "PASS",
        )
        self.assertTrue(
            all(
                self.result[
                    "checks"
                ].values()
            )
        )

    def test_policy_value_region(self) -> None:
        row = route(
            transfer_lead=2,
            hot_budget=8,
        )

        self.assertEqual(
            row["classification"],
            "POLICY_VALUE_REGION",
        )
        self.assertFalse(
            row["stop_policy_search"]
        )
        self.assertGreater(
            row[
                "best_predictive_io_saving_fraction"
            ],
            0.40,
        )

    def test_deadline_infeasible_stops_policy_search(self) -> None:
        row = route(
            transfer_lead=4,
            hot_budget=4,
        )

        self.assertEqual(
            row["classification"],
            "TRANSFER_SURFACE_CAPABILITY_GAP",
        )
        self.assertEqual(
            row["northstar_gap"],
            "CAPABILITY_GAP",
        )
        self.assertTrue(
            row["stop_policy_search"]
        )

    def test_simple_policy_sufficiency_stops_predictor_tuning(self) -> None:
        row = route(
            transfer_lead=3,
            hot_budget=4,
        )

        self.assertEqual(
            row["classification"],
            "SIMPLE_POLICY_SUFFICIENT",
        )
        self.assertTrue(
            row["stop_policy_search"]
        )

    def test_out_of_grid_is_not_interpolated(self) -> None:
        row = route(
            transfer_lead=9,
            hot_budget=8,
        )

        self.assertEqual(
            row["classification"],
            "OUT_OF_CALIBRATION",
        )
        self.assertTrue(
            row["stop_policy_search"]
        )

    def test_claim_ceiling_is_synthetic(self) -> None:
        self.assertEqual(
            self.result["claim_ceiling"],
            "SYNTHETIC_PHASE_MAP_ROUTING_ORACLE_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
