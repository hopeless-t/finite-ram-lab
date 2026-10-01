from __future__ import annotations

import unittest
from unittest.mock import patch

from finite_ram_lab.three_phase_hwm import run_block, run_child
from finite_ram_lab.three_phase_hwm_aggregate import (
    analyze,
    holm_decisions,
)


def block(block_id:int)->dict:
    return {
        "schema":"finite-ram-lab.three-phase-block/v0.1",
        "block_id":block_id,
        "environment":{"runner_name":f"r{block_id}","cpu_model":"cpu"},
        "condition_summaries":[
            {
                "q":2,"seed":474,
                "median_pre_input_vm_hwm_bytes":1000,
                "median_post_input_vm_hwm_bytes":1100,
                "median_work_peak_vm_hwm_bytes":2100,
                "median_input_phase_hwm_growth_bytes":100,
                "median_work_phase_hwm_growth_bytes":1000,
                "median_total_hwm_growth_bytes":1100,
            },
            {
                "q":2,"seed":476,
                "median_pre_input_vm_hwm_bytes":1000,
                "median_post_input_vm_hwm_bytes":1100,
                "median_work_peak_vm_hwm_bytes":2000,
                "median_input_phase_hwm_growth_bytes":100,
                "median_work_phase_hwm_growth_bytes":900,
                "median_total_hwm_growth_bytes":1000,
            },
            {
                "q":4,"seed":474,
                "median_pre_input_vm_hwm_bytes":1000,
                "median_post_input_vm_hwm_bytes":1100,
                "median_work_peak_vm_hwm_bytes":5100,
                "median_input_phase_hwm_growth_bytes":100,
                "median_work_phase_hwm_growth_bytes":4000,
                "median_total_hwm_growth_bytes":4100,
            },
            {
                "q":4,"seed":476,
                "median_pre_input_vm_hwm_bytes":1000,
                "median_post_input_vm_hwm_bytes":1100,
                "median_work_peak_vm_hwm_bytes":5000,
                "median_input_phase_hwm_growth_bytes":100,
                "median_work_phase_hwm_growth_bytes":3900,
                "median_total_hwm_growth_bytes":4000,
            },
        ],
    }


class ThreePhaseHWMTests(unittest.TestCase):
    def test_holm_stepdown(self):
        decisions=holm_decisions(
            {"a":0.001,"b":0.009,"c":0.06},
            0.05,
        )
        self.assertTrue(decisions["a"])
        self.assertTrue(decisions["b"])
        self.assertFalse(decisions["c"])

    def test_aggregate_resolves_work_phase_total_effect(self):
        result=analyze([block(i) for i in range(8)])
        self.assertEqual(result["classifications"]["q2"],"WORK_PHASE_TOTAL_EFFECT")
        self.assertEqual(result["classifications"]["q4"],"WORK_PHASE_TOTAL_EFFECT")
        self.assertTrue(result["governor_seed_feature_allowed"])
        self.assertEqual(
            result["delta_summaries"]["q2"]["max_abs_phase_identity_residual_bytes"],
            0,
        )

    def test_child_phase_identity_on_small_workload(self):
        result=run_child(q=2,seed=474,size=24,value_limit=10,tile_rows=8)
        self.assertTrue(result["semantic_exact"])
        self.assertEqual(
            result["total_hwm_growth_bytes"],
            result["input_phase_hwm_growth_bytes"]
            + result["work_phase_hwm_growth_bytes"],
        )

    def test_block_uses_fresh_child_surface(self):
        def fake_child(**kwargs):
            seed=kwargs["seed"]
            return {
                "schema":"finite-ram-lab.three-phase-child/v0.1",
                "q":kwargs["q"],
                "seed":seed,
                "size":64,
                "pre_input_vm_hwm_bytes":1000,
                "post_input_vm_hwm_bytes":1100,
                "work_peak_vm_hwm_bytes":2000,
                "input_phase_hwm_growth_bytes":100,
                "work_phase_hwm_growth_bytes":900,
                "total_hwm_growth_bytes":1000,
                "work_seconds":1.0,
                "semantic_exact":True,
                "output_sha256":f"seed-{seed}",
            }
        with patch(
            "finite_ram_lab.three_phase_hwm._run_fresh_child",
            side_effect=fake_child,
        ), patch(
            "finite_ram_lab.three_phase_hwm.environment_fingerprint",
            return_value={"runner_name":"test"},
        ):
            result=run_block(block_id=0,size=64)
        self.assertEqual(len(result["condition_summaries"]),4)


if __name__=="__main__":
    unittest.main()
