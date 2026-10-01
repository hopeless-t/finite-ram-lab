from __future__ import annotations

import unittest
from unittest.mock import patch

from finite_ram_lab.lane_concurrency_sweep import (
    BALANCED_ORDERS,
    logical_live_bytes,
    run_child,
    run_sweep,
)


class LaneConcurrencySweepTests(unittest.TestCase):
    def test_logical_live_bytes_scale_with_q(self):
        self.assertEqual(logical_live_bytes(2048, 1), 37_748_736)
        self.assertEqual(logical_live_bytes(2048, 2), 41_943_040)
        self.assertEqual(logical_live_bytes(2048, 4), 50_331_648)
        self.assertEqual(logical_live_bytes(2048, 7), 62_914_560)

    def test_small_exact_outputs_match_across_q(self):
        digests = set()
        for q in (1, 2, 4, 7):
            result = run_child(
                q=q,
                size=24,
                lane_count=7,
                seed=469,
                value_limit=10,
                tile_rows=8,
            )
            self.assertTrue(result["semantic_exact"])
            digests.add(result["output_sha256"])
        self.assertEqual(len(digests), 1)

    def test_balanced_orders_place_each_q_in_every_position(self):
        for q in (1, 2, 4, 7):
            positions = {
                order.index(q)
                for order in BALANCED_ORDERS
            }
            self.assertEqual(positions, {0, 1, 2, 3})

    def test_sweep_builds_pareto_from_balanced_fresh_results(self):
        calls = []

        def fake_child(**kwargs):
            q = kwargs["q"]
            calls.append(q)
            return {
                "q": q,
                "semantic_exact": True,
                "output_sha256": "same",
                "normalized_peak_growth_bytes": q * 10,
                "work_seconds": 10.0 / q,
            }

        with patch(
            "finite_ram_lab.lane_concurrency_sweep._run_fresh_child",
            side_effect=fake_child,
        ):
            result = run_sweep(
                repetitions=4,
                size=64,
                lane_count=7,
                seed=469,
                value_limit=10,
                tile_rows=8,
            )

        self.assertEqual(len(calls), 16)
        self.assertEqual(result["pareto_q"], [1, 2, 4, 7])
        self.assertEqual(
            [row["q"] for row in result["summary_rows"]],
            [1, 2, 4, 7],
        )


if __name__ == "__main__":
    unittest.main()
