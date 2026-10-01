from __future__ import annotations

import unittest
from unittest.mock import patch

from finite_ram_lab.representation_peak_probe import (
    expected_live_bytes,
    run_matched_panel,
)


class RepresentationPeakProbeTests(unittest.TestCase):
    def test_expected_live_bytes_match_b461_three_lane_toy(self):
        moduli = (127, 125, 121)
        self.assertEqual(expected_live_bytes("ALL_RESIDENT", 4, moduli), 24)
        self.assertEqual(expected_live_bytes("STREAMED_FOLD", 4, moduli), 16)

    def test_invalid_strategy_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "strategy_invalid"):
            expected_live_bytes("OTHER", 4, (127, 125))

    def test_matched_panel_balances_order_and_uses_peak_delta(self):
        calls = []

        def fake_child(strategy: str, element_count: int, lane_count: int):
            calls.append(strategy)
            peak = 60_000_000 if strategy == "ALL_RESIDENT" else 34_000_000
            return {
                "strategy": strategy,
                "normalized_peak_growth_bytes": peak,
                "semantic_exact": True,
            }

        with patch(
            "finite_ram_lab.representation_peak_probe._run_fresh_child",
            side_effect=fake_child,
        ):
            result = run_matched_panel(pairs=4, element_count=100, lane_count=3)

        self.assertEqual(
            calls,
            [
                "ALL_RESIDENT", "STREAMED_FOLD",
                "STREAMED_FOLD", "ALL_RESIDENT",
                "ALL_RESIDENT", "STREAMED_FOLD",
                "STREAMED_FOLD", "ALL_RESIDENT",
            ],
        )
        self.assertEqual(result["summary"]["negative_count"], 4)
        self.assertEqual(result["summary"]["positive_count"], 0)
        self.assertEqual(
            result["summary"]["classification"],
            "PHYSICAL_PEAK_SCHEDULE_EFFECT_REPLICATED",
        )
        self.assertEqual(
            result["summary"]["median_treatment_minus_reference_peak_bytes"],
            -26_000_000,
        )


if __name__ == "__main__":
    unittest.main()
