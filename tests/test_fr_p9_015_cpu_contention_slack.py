from __future__ import annotations

import unittest

from finite_ram_lab.fr_p9_015_cpu_contention_slack import typed_slack


class CpuContentionSlackTests(unittest.TestCase):
    def test_typed_slack_preserves_resource_identity(self) -> None:
        self.assertEqual(typed_slack("CPU_YIELD", 40, "PINNED_CPU"), ("CPU_YIELD", 40, "PINNED_CPU"))
        self.assertEqual(typed_slack("CPU_BUSY", 40, "PINNED_CPU"), ("CPU_BUSY", 40, "PINNED_CPU"))

    def test_typed_slack_fails_closed(self) -> None:
        with self.assertRaises(ValueError):
            typed_slack("UNKNOWN", 40, "PINNED_CPU")
        with self.assertRaises(ValueError):
            typed_slack("CPU_BUSY", -1, "PINNED_CPU")
        with self.assertRaises(ValueError):
            typed_slack("CPU_BUSY", 40, "")


if __name__ == "__main__":
    unittest.main()
