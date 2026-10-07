from __future__ import annotations

import unittest

from finite_ram_lab.fr_p9_018_service_curve_deadline_admission import REPLAN
from finite_ram_lab.fr_p9_019_service_curve_epoch_replan import epoch_guard


class ServiceCurveEpochReplanTests(unittest.TestCase):
    def test_current_epoch_keeps_plan_current(self) -> None:
        self.assertEqual(epoch_guard(plan_epoch=7, observed_epoch=7), "CURRENT")

    def test_epoch_change_requires_replan(self) -> None:
        self.assertEqual(epoch_guard(plan_epoch=7, observed_epoch=8), REPLAN)

    def test_negative_epoch_fails_closed(self) -> None:
        with self.assertRaises(ValueError):
            epoch_guard(plan_epoch=-1, observed_epoch=1)
        with self.assertRaises(ValueError):
            epoch_guard(plan_epoch=1, observed_epoch=-1)


if __name__ == "__main__":
    unittest.main()
