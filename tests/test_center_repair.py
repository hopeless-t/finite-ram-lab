from __future__ import annotations

import unittest
from unittest.mock import patch

import numpy as np

from finite_ram_lab.center_repair import (
    COUNT_HIGH,
    COUNT_SEED474,
    COUNT_SEED476,
    center_tiled_where,
    run_block,
    run_child,
)
from finite_ram_lab.center_repair_aggregate import analyze
from finite_ram_lab.coupled_numerical_residency import DEFAULT_MODULI, _modulus_product


def block(block_id: int) -> dict:
    def item(strategy: str, count: int) -> dict:
        if strategy == "BOOLEAN_INDEX":
            hwm = 4_000_000 + count * 8
            elapsed = 1.0
        else:
            hwm = 300_000
            elapsed = 1.2
        return {
            "strategy": strategy,
            "selected_count": count,
            "semantic_exact": True,
            "hwm_growth_bytes": hwm,
            "rss_delta_bytes": 0,
            "elapsed_seconds": elapsed,
        }
    return {
        "schema": "finite-ram-lab.center-repair-block/v0.1",
        "block_id": block_id,
        "environment": {"runner_name": f"r{block_id}", "cpu_model": "cpu"},
        "results": [
            item(strategy, count)
            for strategy in ("BOOLEAN_INDEX", "TILED_WHERE")
            for count in (COUNT_SEED476, COUNT_SEED474, COUNT_HIGH)
        ],
    }


class CenterRepairTests(unittest.TestCase):
    def test_tiled_center_matches_expected_values(self):
        product = _modulus_product(DEFAULT_MODULI)
        values = np.array([1, product - 1, 2, product - 2], dtype=np.int64)
        center_tiled_where(values, product, tile_elements=2)
        self.assertEqual(values.tolist(), [1, -1, 2, -2])

    def test_small_child_is_exact(self):
        for strategy in ("BOOLEAN_INDEX", "TILED_WHERE"):
            result = run_child(
                strategy=strategy,
                selected_count=100,
                element_count=1000,
                tile_elements=64,
            )
            self.assertTrue(result["semantic_exact"])

    def test_aggregate_qualifies_repair_fixture(self):
        result = analyze([block(i) for i in range(8)])
        self.assertEqual(
            result["classification"],
            "EXACT_TILED_CENTER_REPAIR_QUALIFIED",
        )
        self.assertTrue(result["summary"]["repair_qualified"])

    def test_block_uses_all_conditions(self):
        calls = []
        def fake_child(**kwargs):
            calls.append((kwargs["strategy"], kwargs["selected_count"]))
            return {
                "semantic_exact": True,
                "hwm_growth_bytes": 1,
                "rss_delta_bytes": 0,
                "elapsed_seconds": 1.0,
            }
        with patch(
            "finite_ram_lab.center_repair._run_fresh_child",
            side_effect=fake_child,
        ), patch(
            "finite_ram_lab.center_repair.environment_fingerprint",
            return_value={"runner_name": "test"},
        ):
            result = run_block(block_id=0)
        self.assertEqual(len(calls), 6)
        self.assertEqual(len(result["results"]), 6)


if __name__ == "__main__":
    unittest.main()
