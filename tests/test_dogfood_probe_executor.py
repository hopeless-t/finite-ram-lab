from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from finite_ram_lab.dogfood_probe_executor import (
    execute_probe,
    load_frozen_decision,
    validate_probe_decision,
)


def receipt() -> dict:
    return {
        "schema": "finite-ram-lab.runtime-decision/v0.1",
        "mode": "PROBE",
        "dataset_partition": "EXPERIMENTAL_INTERVENTION",
        "baseline_plan_id": "streamed_7_t64",
        "selected_plan_id": "streamed_7_t32",
        "intervention": True,
        "hypothesis_id": "H464_TILE_GRANULARITY_INFORMATION",
        "changed_variables": [["tile_rows", 64, 32]],
        "held_constant_variables": [
            ["lane_count", 7],
            ["strategy", "STREAMED_FOLD"],
        ],
    }


class DogfoodProbeExecutorTests(unittest.TestCase):
    def test_digest_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "decision.json"
            path.write_text(json.dumps(receipt()) + "\n")
            with self.assertRaisesRegex(RuntimeError, "decision_receipt_digest_mismatch"):
                load_frozen_decision(path, "0" * 64)

    def test_validate_probe_recovers_baseline_and_selected(self):
        baseline, selected = validate_probe_decision(receipt())
        self.assertEqual(
            baseline,
            {"lane_count": 7, "strategy": "STREAMED_FOLD", "tile_rows": 64},
        )
        self.assertEqual(
            selected,
            {"lane_count": 7, "strategy": "STREAMED_FOLD", "tile_rows": 32},
        )

    def test_disallowed_second_change_fails_closed(self):
        bad = receipt()
        bad["changed_variables"] = [
            ["strategy", "STREAMED_FOLD", "ALL_RESIDENT"],
            ["tile_rows", 64, 32],
        ]
        bad["held_constant_variables"] = [["lane_count", 7]]
        with self.assertRaisesRegex(RuntimeError, "b465_requires_tile_rows_only_probe"):
            validate_probe_decision(bad)

    def test_execute_probe_balances_order_and_preserves_partition(self):
        calls = []

        def fake_execute(variables, *, size, seed, value_limit):
            tile = int(variables["tile_rows"])
            calls.append(tile)
            return {
                "semantic_exact": True,
                "output_sha256": "same",
                "normalized_peak_growth_bytes": 40_000_000 + tile * 1000,
                "work_seconds": 1.0 + tile / 1000.0,
            }

        with patch(
            "finite_ram_lab.dogfood_probe_executor._execute_condition",
            side_effect=fake_execute,
        ):
            result = execute_probe(
                decision_receipt=receipt(),
                decision_sha256="a" * 64,
                pairs=4,
                size=64,
                seed=465,
                value_limit=10,
            )

        self.assertEqual(calls, [64, 32, 32, 64, 64, 32, 32, 64])
        self.assertEqual(result["dataset_partition"], "EXPERIMENTAL_INTERVENTION")
        self.assertFalse(result["same_run_model_update"])
        self.assertEqual(result["summary"]["semantic_match_count"], 4)
        self.assertEqual(result["summary"]["negative_peak_count"], 4)

    def test_non_probe_decision_rejected(self):
        bad = receipt()
        bad["mode"] = "OPTIMIZE"
        with self.assertRaisesRegex(RuntimeError, "decision_mode_not_probe"):
            validate_probe_decision(bad)


if __name__ == "__main__":
    unittest.main()
