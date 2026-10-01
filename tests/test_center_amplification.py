from __future__ import annotations

import unittest
from unittest.mock import patch

from finite_ram_lab.center_amplification_aggregate import analyze
from finite_ram_lab.center_amplification_probe import (
    BASE_DIFF,
    CONDITIONS,
    MULTIPLIERS,
    count_pair,
    run_block,
)


def block(block_id: int) -> dict:
    results = []
    for multiplier in MULTIPLIERS:
        low, high = count_pair(multiplier)
        for side, count in (("low", low), ("high", high)):
            results.append({
                "multiplier": multiplier,
                "side": side,
                "selected_count": count,
                "hwm_growth_bytes": 4_000_000 + count * 8,
                "rss_delta_bytes": 0,
            })
    return {
        "schema": "finite-ram-lab.center-amplification-block/v0.1",
        "block_id": block_id,
        "results": results,
    }


class CenterAmplificationTests(unittest.TestCase):
    def test_count_pairs_scale_exactly(self):
        for multiplier in MULTIPLIERS:
            low, high = count_pair(multiplier)
            self.assertEqual(high - low, BASE_DIFF * multiplier)

    def test_aggregate_confirms_exact_linear_fixture(self):
        result = analyze([block(i) for i in range(8)])
        self.assertEqual(
            result["classification"],
            "BOOLEAN_INDEX_TEMPORARY_MECHANISM_CONFIRMED",
        )
        self.assertTrue(result["summary"]["mechanism_supported"])
        self.assertAlmostEqual(
            result["summary"]["median_slope_bytes_per_selected_element"],
            8.0,
        )

    def test_each_condition_occupies_each_position_across_blocks(self):
        positions = {condition: set() for condition in CONDITIONS}
        for block_id in range(8):
            order = CONDITIONS[block_id:] + CONDITIONS[:block_id]
            for position, condition in enumerate(order):
                positions[condition].add(position)
        self.assertTrue(all(value == set(range(8)) for value in positions.values()))

    def test_block_uses_one_fresh_child_per_condition(self):
        calls = []
        def fake_child(**kwargs):
            count = kwargs["selected_count"]
            calls.append(count)
            return {
                "semantic_count_exact": True,
                "hwm_growth_bytes": count * 8,
                "rss_delta_bytes": 0,
            }

        with patch(
            "finite_ram_lab.center_amplification_probe._run_fresh_child",
            side_effect=fake_child,
        ), patch(
            "finite_ram_lab.center_amplification_probe.environment_fingerprint",
            return_value={"runner_name": "test"},
        ):
            result = run_block(block_id=0)

        self.assertEqual(len(calls), 8)
        self.assertEqual(len(result["results"]), 8)


if __name__ == "__main__":
    unittest.main()
