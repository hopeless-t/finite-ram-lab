from __future__ import annotations

import unittest
from unittest.mock import patch

from finite_ram_lab.center_temporary_aggregate import analyze
from finite_ram_lab.center_temporary_probe import (
    COUNT_HIGH,
    COUNT_LOW,
    COUNT_SEED474,
    COUNT_SEED476,
    EXPECTED_ACTUAL_PAIR_PAYLOAD_DELTA_BYTES,
    run_block,
    run_child,
)


def block(block_id: int) -> dict:
    def row(count: int) -> dict:
        # Exact 8 bytes HWM per selected element plus a constant mask term.
        return {
            "selected_count": count,
            "median_hwm_growth_bytes": 4_194_304 + count * 8,
            "median_rss_delta_bytes": 1000,
        }

    return {
        "schema": "finite-ram-lab.center-temporary-block/v0.1",
        "block_id": block_id,
        "environment": {"runner_name": f"r{block_id}", "cpu_model": "cpu"},
        "condition_summaries": [
            row(COUNT_LOW),
            row(COUNT_SEED476),
            row(COUNT_SEED474),
            row(COUNT_HIGH),
        ],
    }


class CenterTemporaryTests(unittest.TestCase):
    def test_actual_payload_prediction(self):
        self.assertEqual(
            EXPECTED_ACTUAL_PAIR_PAYLOAD_DELTA_BYTES,
            -135_520,
        )

    def test_small_child_preserves_selected_count(self):
        result = run_child(selected_count=100, element_count=1000)
        self.assertTrue(result["semantic_count_exact"])
        self.assertEqual(result["centered_negative_count"], 100)

    def test_aggregate_supports_boolean_index_mechanism(self):
        result = analyze([block(i) for i in range(8)])
        self.assertEqual(
            result["classification"],
            "BOOLEAN_INDEX_TEMPORARY_MECHANISM_SUPPORTED",
        )
        self.assertTrue(result["summary"]["mechanism_supported"])
        self.assertAlmostEqual(
            result["summary"]["median_bytes_hwm_per_selected_element"],
            8.0,
        )
        self.assertEqual(
            result["summary"]["median_actual_pair_hwm_delta_bytes"],
            EXPECTED_ACTUAL_PAIR_PAYLOAD_DELTA_BYTES,
        )

    def test_block_uses_fresh_children(self):
        calls = []
        def fake_child(**kwargs):
            count = kwargs["selected_count"]
            calls.append(count)
            return {
                "semantic_count_exact": True,
                "hwm_growth_bytes": 4_000_000 + count * 8,
                "rss_delta_bytes": 0,
            }

        with patch(
            "finite_ram_lab.center_temporary_probe._run_fresh_child",
            side_effect=fake_child,
        ), patch(
            "finite_ram_lab.center_temporary_probe.environment_fingerprint",
            return_value={"runner_name": "test"},
        ):
            result = run_block(block_id=0, element_count=4_000_000)

        self.assertEqual(len(calls), 8)
        self.assertEqual(len(result["condition_summaries"]), 4)


if __name__ == "__main__":
    unittest.main()
