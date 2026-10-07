from __future__ import annotations

import unittest

from finite_ram_lab.fr_p9_014_deadline_slack_fault_in import visible_stall_lower_bound_ns


class DeadlineSlackFaultInTests(unittest.TestCase):
    def test_visible_stall_is_reconstruction_minus_available_slack(self) -> None:
        self.assertEqual(visible_stall_lower_bound_ns(30_000_000, 0), 30_000_000)
        self.assertEqual(visible_stall_lower_bound_ns(30_000_000, 10_000_000), 20_000_000)
        self.assertEqual(visible_stall_lower_bound_ns(30_000_000, 30_000_000), 0)
        self.assertEqual(visible_stall_lower_bound_ns(30_000_000, 80_000_000), 0)

    def test_visible_stall_fails_closed_on_negative_duration(self) -> None:
        with self.assertRaises(ValueError):
            visible_stall_lower_bound_ns(-1, 0)
        with self.assertRaises(ValueError):
            visible_stall_lower_bound_ns(1, -1)


if __name__ == "__main__":
    unittest.main()
