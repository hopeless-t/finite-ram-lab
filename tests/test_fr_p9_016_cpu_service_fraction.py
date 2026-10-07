from __future__ import annotations

import unittest

from finite_ram_lab.fr_p9_016_cpu_service_fraction import _pearson, service_budget


class CpuServiceFractionTests(unittest.TestCase):
    def test_service_budget_converts_duration_and_busy_fraction(self) -> None:
        self.assertEqual(service_budget(40, 0), 40_000_000)
        self.assertEqual(service_budget(40, 25), 30_000_000)
        self.assertEqual(service_budget(40, 50), 20_000_000)
        self.assertEqual(service_budget(40, 75), 10_000_000)
        self.assertEqual(service_budget(40, 100), 0)

    def test_service_budget_fails_closed(self) -> None:
        for args in ((-1, 0), (40, -1), (40, 101)):
            with self.assertRaises(ValueError):
                service_budget(*args)

    def test_pearson_detects_monotone_signal(self) -> None:
        self.assertAlmostEqual(_pearson([0, 1, 2], [0, 2, 4]), 1.0)
        self.assertAlmostEqual(_pearson([0, 1, 2], [4, 2, 0]), -1.0)


if __name__ == "__main__":
    unittest.main()
