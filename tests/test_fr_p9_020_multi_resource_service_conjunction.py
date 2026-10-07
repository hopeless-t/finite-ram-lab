from __future__ import annotations

import unittest

from finite_ram_lab.fr_p9_018_service_curve_deadline_admission import ADMIT, REPLAN
from finite_ram_lab.fr_p9_020_multi_resource_service_conjunction import (
    MULTI_INSUFFICIENT,
    UNIT_MISMATCH,
    TypedCurve,
    TypedDemand,
    _pair_fixture,
    multi_resource_admit,
    run_panel,
    scalarization_adversary,
)


class MultiResourceServiceConjunctionTests(unittest.TestCase):
    def test_both_resources_must_meet_their_own_constraint(self) -> None:
        demands, curves, epochs = _pair_fixture(
            (3, 3, 0), (3, 3, 0), epoch=1, cpu_required=4, io_required=4
        )
        self.assertEqual(multi_resource_admit(demands, curves, observed_epochs=epochs)["status"], ADMIT)

        demands, curves, epochs = _pair_fixture(
            (3, 3, 0), (0, 0, 6), epoch=1, cpu_required=4, io_required=4
        )
        self.assertEqual(
            multi_resource_admit(demands, curves, observed_epochs=epochs)["status"],
            MULTI_INSUFFICIENT,
        )

    def test_scalarization_counterexample_is_explicit(self) -> None:
        result = scalarization_adversary()
        self.assertTrue(result["naive_illegal_cross_unit_sum_admits"])
        self.assertEqual(result["typed_conjunction_status"], MULTI_INSUFFICIENT)

    def test_one_stale_resource_forces_replan(self) -> None:
        demands, curves, epochs = _pair_fixture(
            (3, 3, 0), (3, 3, 0), epoch=4, cpu_required=4, io_required=4
        )
        epochs[("TRANSFER", "storage-link0")] = 5
        self.assertEqual(multi_resource_admit(demands, curves, observed_epochs=epochs)["status"], REPLAN)

    def test_unit_mismatch_fails_closed(self) -> None:
        demands, curves, epochs = _pair_fixture(
            (3, 3, 0), (3, 3, 0), epoch=4, cpu_required=4, io_required=4
        )
        bad = (curves[0], TypedCurve(curves[1].curve, "milliseconds"))
        self.assertEqual(multi_resource_admit(demands, bad, observed_epochs=epochs)["status"], UNIT_MISMATCH)

    def test_frozen_analytic_panel_passes(self) -> None:
        result = run_panel(seed=20261008, trials=1000)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["exhaustive"]["mismatches"], 0)
        self.assertGreater(result["monte_carlo"]["naive_scalar_false_admits"], 0)
        self.assertEqual(result["monte_carlo"]["typed_false_admits"], 0)
        self.assertIsNone(result["scalar_gain"])


if __name__ == "__main__":
    unittest.main()
