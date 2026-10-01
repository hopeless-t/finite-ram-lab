from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from finite_ram_lab.prematerialized_input import (
    load_inputs,
    materialize_inputs,
    run_block,
    run_child,
)
from finite_ram_lab.prematerialized_input_aggregate import analyze


def block(block_id:int)->dict:
    return {
        "schema":"finite-ram-lab.prematerialized-input-block/v0.1",
        "block_id":block_id,
        "environment":{"runner_name":f"r{block_id}","cpu_model":"cpu"},
        "condition_summaries":[
            {"q":2,"content_seed":474,"median_pre_load_vm_hwm_bytes":1000,"median_work_peak_vm_hwm_bytes":2200,"median_load_phase_hwm_growth_bytes":100,"median_work_phase_hwm_growth_bytes":1100,"median_total_hwm_growth_bytes":1200},
            {"q":2,"content_seed":476,"median_pre_load_vm_hwm_bytes":1000,"median_work_peak_vm_hwm_bytes":2100,"median_load_phase_hwm_growth_bytes":100,"median_work_phase_hwm_growth_bytes":1000,"median_total_hwm_growth_bytes":1100},
            {"q":4,"content_seed":474,"median_pre_load_vm_hwm_bytes":1000,"median_work_peak_vm_hwm_bytes":5200,"median_load_phase_hwm_growth_bytes":100,"median_work_phase_hwm_growth_bytes":4100,"median_total_hwm_growth_bytes":4200},
            {"q":4,"content_seed":476,"median_pre_load_vm_hwm_bytes":1000,"median_work_peak_vm_hwm_bytes":5100,"median_load_phase_hwm_growth_bytes":100,"median_work_phase_hwm_growth_bytes":4000,"median_total_hwm_growth_bytes":4100},
        ],
    }


class PrematerializedInputTests(unittest.TestCase):
    def test_materialized_loader_preserves_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            paths=materialize_inputs(root,size=24,value_limit=10)
            left,right=load_inputs(
                Path(paths[474]["left"]),
                Path(paths[474]["right"]),
                size=24,
            )
            self.assertEqual(left.shape,(24,))
            self.assertEqual(right.shape,(24,))

    def test_small_child_is_exact(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            paths=materialize_inputs(root,size=24,value_limit=10)
            result=run_child(
                q=2,
                content_seed=474,
                left_path=Path(paths[474]["left"]),
                right_path=Path(paths[474]["right"]),
                size=24,
                tile_rows=8,
            )
            self.assertTrue(result["semantic_exact"])
            self.assertEqual(
                result["total_hwm_growth_bytes"],
                result["load_phase_hwm_growth_bytes"]
                + result["work_phase_hwm_growth_bytes"],
            )

    def test_aggregate_resolves_prematerialized_content_effect(self):
        result=analyze([block(i) for i in range(8)])
        self.assertEqual(
            result["classifications"]["q2"],
            "PREMATERIALIZED_CONTENT_EFFECT_REPLICATED",
        )
        self.assertEqual(
            result["classifications"]["q4"],
            "PREMATERIALIZED_CONTENT_EFFECT_REPLICATED",
        )
        self.assertTrue(result["q2_content_feature_supported"])

    def test_block_surface_uses_fresh_child(self):
        def fake_child(**kwargs):
            seed=kwargs["content_seed"]
            return {
                "semantic_exact":True,
                "output_sha256":f"seed-{seed}",
                "pre_load_vm_hwm_bytes":1000,
                "post_load_vm_hwm_bytes":1100,
                "work_peak_vm_hwm_bytes":2000,
                "load_phase_hwm_growth_bytes":100,
                "work_phase_hwm_growth_bytes":900,
                "total_hwm_growth_bytes":1000,
                "work_seconds":1.0,
            }

        with tempfile.TemporaryDirectory() as tmp, patch(
            "finite_ram_lab.prematerialized_input._run_fresh_child",
            side_effect=fake_child,
        ), patch(
            "finite_ram_lab.prematerialized_input.environment_fingerprint",
            return_value={"runner_name":"test"},
        ):
            result=run_block(block_id=0,work_dir=Path(tmp),size=24,value_limit=10)
        self.assertEqual(len(result["condition_summaries"]),4)


if __name__=="__main__":
    unittest.main()
