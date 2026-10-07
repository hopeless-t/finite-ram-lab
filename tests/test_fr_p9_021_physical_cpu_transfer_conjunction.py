from __future__ import annotations

import unittest

from finite_ram_lab.fr_p9_021_physical_cpu_transfer_conjunction import service_at_deadline


class PhysicalCpuTransferConjunctionTests(unittest.TestCase):
    def test_service_at_deadline_reads_monotone_cumulative_trace(self) -> None:
        samples = [(10, 1), (20, 2), (30, 4)]
        self.assertEqual(service_at_deadline(samples, 0), 0)
        self.assertEqual(service_at_deadline(samples, 10), 1)
        self.assertEqual(service_at_deadline(samples, 25), 2)
        self.assertEqual(service_at_deadline(samples, 30), 4)

    def test_service_trace_validation_fails_closed(self) -> None:
        with self.assertRaises(ValueError):
            service_at_deadline([(20, 2), (10, 3)], 30)
        with self.assertRaises(ValueError):
            service_at_deadline([(10, 3), (20, 2)], 30)
        with self.assertRaises(ValueError):
            service_at_deadline([(10, 1)], -1)


if __name__ == "__main__":
    unittest.main()
