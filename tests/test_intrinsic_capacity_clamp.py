from __future__ import annotations

import unittest

from finite_ram_lab.intrinsic_capacity_clamp import (
    ClampCell,
    classify_cells,
    pressure_classification_accuracy,
    robust_transient_base,
)


CELLS = (
    ClampCell(144, 48, 126.598, 0),
    ClampCell(144, 64, 142.609, 0),
    ClampCell(144, 80, 143.867, 7),
    ClampCell(144, 96, 143.869, 14),
    ClampCell(176, 48, 126.609, 0),
    ClampCell(176, 64, 142.734, 0),
    ClampCell(176, 80, 158.609, 0),
    ClampCell(176, 96, 172.736, 0),
)


class IntrinsicCapacityClampTests(unittest.TestCase):
    def test_robust_transient_base(self):
        self.assertAlmostEqual(robust_transient_base(CELLS), 78.609, places=6)

    def test_pressure_classification_is_exact_on_strata005_cells(self):
        base = robust_transient_base(CELLS)
        rows = classify_cells(CELLS, transient_base_mib=base)
        self.assertEqual(pressure_classification_accuracy(rows), 1.0)

    def test_seven_of_eight_peak_predictions_within_point_133_mib(self):
        base = robust_transient_base(CELLS)
        rows = classify_cells(CELLS, transient_base_mib=base)
        close = sum(abs(float(row["peak_residual_mib"])) <= 0.133001 for row in rows)
        self.assertEqual(close, 7)

    def test_h160_contextual_prediction_matches_strata004_bracket(self):
        base = robust_transient_base(CELLS)
        contextual = (
            ClampCell(160, 80, 157.86, 0),
            ClampCell(160, 88, 159.92, 2),
        )
        rows = classify_cells(contextual, transient_base_mib=base)
        self.assertEqual(pressure_classification_accuracy(rows), 1.0)


if __name__ == "__main__":
    unittest.main()
