from __future__ import annotations

import unittest

from finite_ram_lab.fr_p9_017_service_curve_timing import service_curve_contract


class ServiceCurveTimingTests(unittest.TestCase):
    def test_contract_keeps_resource_deadline_and_delivered_service(self) -> None:
        self.assertEqual(service_curve_contract("CPU", 30, 12_000_000), ("CPU", 30, 12_000_000))

    def test_contract_fails_closed(self) -> None:
        with self.assertRaises(ValueError):
            service_curve_contract("", 30, 1)
        with self.assertRaises(ValueError):
            service_curve_contract("CPU", 0, 1)
        with self.assertRaises(ValueError):
            service_curve_contract("CPU", 30, -1)


if __name__ == "__main__":
    unittest.main()
