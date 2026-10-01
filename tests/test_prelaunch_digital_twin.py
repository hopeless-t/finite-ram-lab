from __future__ import annotations

import unittest

from finite_ram_lab.prelaunch_digital_twin import (
    expected_candidate_frontier,
    expected_pressure_map,
)


class PrelaunchDigitalTwinTests(unittest.TestCase):
    def test_expected_frontier_is_constant_across_capacity_points(self):
        for high in (144, 160, 176):
            self.assertEqual(
                expected_candidate_frontier(high),
                (
                    "dontneed_32m",
                    "dontneed_48m",
                    "dontneed_96m",
                ),
            )

    def test_expected_pressure_maps(self):
        self.assertEqual(
            expected_pressure_map(144),
            {
                "dontneed_32m": False,
                "dontneed_48m": False,
                "dontneed_64m": False,
                "dontneed_80m": True,
                "dontneed_96m": True,
            },
        )
        self.assertEqual(
            expected_pressure_map(160),
            {
                "dontneed_32m": False,
                "dontneed_48m": False,
                "dontneed_64m": False,
                "dontneed_80m": False,
                "dontneed_96m": True,
            },
        )
        self.assertEqual(
            expected_pressure_map(176),
            {
                "dontneed_32m": False,
                "dontneed_48m": False,
                "dontneed_64m": False,
                "dontneed_80m": False,
                "dontneed_96m": False,
            },
        )


if __name__ == "__main__":
    unittest.main()
