from __future__ import annotations

import unittest

from finite_ram_lab.fr_p9_018_service_curve_deadline_admission import (
    ADMIT,
    INSUFFICIENT,
    REPLAN,
    ServiceCurveSnapshot,
    ServiceDemand,
    ServiceSample,
    curve_from_increments,
    deadline_admit,
    equal_total_timing_adversary,
    run_panel,
    service_at,
    stale_epoch_adversary,
    validate_curve,
)


class ServiceCurveDeadlineAdmissionTests(unittest.TestCase):
    def test_service_at_uses_cumulative_service_available_by_deadline(self) -> None:
        curve = curve_from_increments((2, 3, 0, 4), epoch=1)
        self.assertEqual(service_at(curve, 0), 0)
        self.assertEqual(service_at(curve, 1), 2)
        self.assertEqual(service_at(curve, 2), 5)
        self.assertEqual(service_at(curve, 4), 9)

    def test_equal_total_does_not_imply_deadline_equivalence(self) -> None:
        result = equal_total_timing_adversary()
        self.assertEqual(result["front_horizon_total"], result["back_horizon_total"])
        self.assertEqual(result["front_status"], ADMIT)
        self.assertEqual(result["back_status"], INSUFFICIENT)

    def test_stale_epoch_fails_to_replan(self) -> None:
        result = stale_epoch_adversary()
        self.assertEqual(result["naive_forecast_status"], ADMIT)
        self.assertEqual(result["stale_aware_status"], REPLAN)
        self.assertEqual(result["actual_status"], INSUFFICIENT)

    def test_curve_validation_fails_closed_on_nonmonotone_input(self) -> None:
        bad = ServiceCurveSnapshot(
            "CPU",
            "cpu0",
            1,
            (ServiceSample(1, 4), ServiceSample(2, 3)),
        )
        with self.assertRaises(ValueError):
            validate_curve(bad)

    def test_resource_mismatch_never_admits(self) -> None:
        curve = curve_from_increments((4, 4), epoch=2)
        demand = ServiceDemand("x", "IO", "cpu0", 2, 1)
        self.assertNotEqual(deadline_admit(demand, curve, observed_epoch=2).status, ADMIT)

    def test_frozen_analytic_panel_passes(self) -> None:
        result = run_panel(seed=20261008, trials=1000)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["exhaustive"]["mismatches"], 0)
        self.assertGreater(result["monte_carlo"]["naive_false_admits"], 0)
        self.assertEqual(result["monte_carlo"]["epoch_aware_false_admits"], 0)
        self.assertIsNone(result["scalar_gain"])
        self.assertEqual(result["authority_effect"], "NONE")
        self.assertFalse(result["retry_authority"])


if __name__ == "__main__":
    unittest.main()
