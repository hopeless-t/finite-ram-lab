from __future__ import annotations

import unittest
from unittest.mock import patch

from finite_ram_lab.coupled_numerical_residency import (
    _logical_bytes,
    run_child,
    run_matched_panel,
)


class CoupledNumericalResidencyTests(unittest.TestCase):
    def test_small_exact_all_resident_and_streamed_match(self):
        common = dict(size=24, lane_count=3, seed=463, value_limit=12, tile_rows=8)
        reference = run_child(strategy="ALL_RESIDENT", **common)
        treatment = run_child(strategy="STREAMED_FOLD", **common)
        self.assertTrue(reference["semantic_exact"])
        self.assertTrue(treatment["semantic_exact"])
        self.assertEqual(reference["output_sha256"], treatment["output_sha256"])
        self.assertEqual(reference["lane_sha256"], treatment["lane_sha256"])

    def test_logical_live_bytes_encode_residency_difference(self):
        self.assertEqual(_logical_bytes("ALL_RESIDENT", 2048, 7), 62_914_560)
        self.assertEqual(_logical_bytes("STREAMED_FOLD", 2048, 7), 37_748_736)
        self.assertEqual(
            _logical_bytes("ALL_RESIDENT", 2048, 7)
            - _logical_bytes("STREAMED_FOLD", 2048, 7),
            25_165_824,
        )

    def test_matched_panel_balances_order_and_gates_semantics(self):
        calls = []

        def fake_child(**kwargs):
            strategy = kwargs["strategy"]
            calls.append(strategy)
            return {
                "strategy": strategy,
                "semantic_exact": True,
                "output_sha256": "same",
                "normalized_peak_growth_bytes": (
                    80_000_000 if strategy == "ALL_RESIDENT" else 50_000_000
                ),
                "work_seconds": 2.0 if strategy == "ALL_RESIDENT" else 2.2,
            }

        with patch(
            "finite_ram_lab.coupled_numerical_residency._run_fresh_child",
            side_effect=fake_child,
        ):
            result = run_matched_panel(
                pairs=4,
                size=64,
                lane_count=3,
                seed=463,
                value_limit=10,
                tile_rows=8,
            )

        self.assertEqual(
            calls,
            [
                "ALL_RESIDENT", "STREAMED_FOLD",
                "STREAMED_FOLD", "ALL_RESIDENT",
                "ALL_RESIDENT", "STREAMED_FOLD",
                "STREAMED_FOLD", "ALL_RESIDENT",
            ],
        )
        self.assertEqual(result["summary"]["semantic_match_count"], 4)
        self.assertEqual(result["summary"]["negative_peak_count"], 4)
        self.assertEqual(
            result["summary"]["classification"],
            "COUPLED_EXACT_PEAK_EFFECT_REPLICATED",
        )


if __name__ == "__main__":
    unittest.main()
