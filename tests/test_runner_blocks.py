from __future__ import annotations

import unittest
from unittest.mock import patch

from finite_ram_lab.runner_block_aggregate import analyze_runner_blocks
from finite_ram_lab.runner_block_probe import run_block


def reference_input() -> dict:
    return {
        "schema": "finite-ram-lab.location-shift-input/v0.1",
        "reference_batches": {
            "2": [100] * 11,
            "4": [200] * 11,
        },
    }


def block(block_id: int) -> dict:
    # q2: seed effect negative and temporal positive in every block.
    # q4: seed effect negative; seed474 alternates around historical median.
    q2_474 = 120 + block_id
    q2_476 = 80 + block_id
    q4_474 = 210 if block_id % 2 == 0 else 190
    q4_476 = q4_474 - 40
    return {
        "schema": "finite-ram-lab.runner-block/v0.1",
        "block_id": block_id,
        "environment": {
            "runner_name": f"runner-{block_id}",
            "image_os": "ubuntu24",
            "image_version": "test",
            "cpu_model": "cpu",
            "mem_total": "16 GB",
        },
        "condition_summaries": [
            {"q":2,"seed":474,"median_peak_bytes":q2_474},
            {"q":2,"seed":476,"median_peak_bytes":q2_476},
            {"q":4,"seed":474,"median_peak_bytes":q4_474},
            {"q":4,"seed":476,"median_peak_bytes":q4_476},
        ],
    }


class RunnerBlockTests(unittest.TestCase):
    def test_aggregate_replicates_expected_block_effects(self):
        result=analyze_runner_blocks(
            [block(i) for i in range(8)],
            reference_input(),
        )
        c=result["classifications"]
        self.assertTrue(c["q2_seed_effect_replicated"])
        self.assertTrue(c["q4_seed_effect_replicated"])
        self.assertTrue(c["q2_temporal_shift_replicated"])
        self.assertFalse(c["q4_temporal_shift_detected"])

    def test_probe_balances_two_replicates_and_preserves_semantics(self):
        calls=[]
        def fake_child(**kwargs):
            calls.append((kwargs["q"],kwargs["seed"]))
            return {
                "semantic_exact":True,
                "normalized_peak_growth_bytes":1000+kwargs["q"]+kwargs["seed"],
                "work_seconds":1.0,
                "output_sha256":f"seed-{kwargs['seed']}",
            }

        with patch(
            "finite_ram_lab.runner_block_probe._run_fresh_child",
            side_effect=fake_child,
        ), patch(
            "finite_ram_lab.runner_block_probe.environment_fingerprint",
            return_value={"runner_name":"test"},
        ):
            result=run_block(block_id=0,size=64)

        self.assertEqual(len(calls),8)
        self.assertEqual(len(result["condition_summaries"]),4)
        self.assertTrue(all(row["sample_count"]==2 for row in result["condition_summaries"]))

    def test_missing_block_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError,"runner_block_count_invalid"):
            analyze_runner_blocks(
                [block(i) for i in range(7)],
                reference_input(),
            )


if __name__=="__main__":
    unittest.main()
