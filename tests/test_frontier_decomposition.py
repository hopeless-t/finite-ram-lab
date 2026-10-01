from __future__ import annotations

import unittest

from finite_ram_lab.frontier_decomposition import (
    FloorCell,
    legacy_post_observer_floor,
    partially_identified_frontier,
    transient_excess_over_legacy_floor,
)


CELLS = (
    FloorCell(76.609375),
    FloorCell(76.734375),
    FloorCell(76.609375),
    FloorCell(76.705078125),
    FloorCell(76.609375),
    FloorCell(76.734375),
    FloorCell(76.732421875),
    FloorCell(76.736328125),
)


class FrontierDecompositionTests(unittest.TestCase):
    def test_legacy_floor_median(self):
        self.assertAlmostEqual(
            legacy_post_observer_floor(CELLS),
            76.71875,
            places=8,
        )

    def test_transient_excess_over_legacy(self):
        self.assertAlmostEqual(
            transient_excess_over_legacy_floor(
                transient_base_mib=78.609,
                legacy_floor_mib=76.71875,
            ),
            1.89025,
            places=8,
        )

    def test_partial_identification_keeps_clean_and_observer_separate(self):
        result = partially_identified_frontier(
            transient_base_mib=78.609,
            legacy_post_observer_floor_mib=76.71875,
        )
        self.assertEqual(
            result["not_identified_from_same_historical_trials"],
            (
                "B_clean_mib",
                "O_observer_mib",
                "E_transient_relative_to_clean_mib",
            ),
        )


if __name__ == "__main__":
    unittest.main()
