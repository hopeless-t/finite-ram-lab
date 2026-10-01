from __future__ import annotations

import unittest
from unittest.mock import patch

from finite_ram_lab.baseline_decomposition_aggregate import analyze
from finite_ram_lab.baseline_decomposition_probe import run_block


def block(block_id:int)->dict:
    # q2: normalized difference is entirely baseline-driven.
    # seed474 baseline=1000 work=2000 norm=1000
    # seed476 baseline=1100 work=2000 norm=900
    # q4: normalized difference is absolute-work driven.
    # seed474 baseline=3000 work=5000 norm=2000
    # seed476 baseline=3000 work=4900 norm=1900
    return {
        "schema":"finite-ram-lab.baseline-decomposition-block/v0.1",
        "block_id":block_id,
        "environment":{"runner_name":f"r{block_id}","cpu_model":"cpu"},
        "condition_summaries":[
            {"q":2,"seed":474,"median_baseline_vm_hwm_bytes":1000,"median_work_peak_vm_hwm_bytes":2000,"median_normalized_peak_growth_bytes":1000},
            {"q":2,"seed":476,"median_baseline_vm_hwm_bytes":1100,"median_work_peak_vm_hwm_bytes":2000,"median_normalized_peak_growth_bytes":900},
            {"q":4,"seed":474,"median_baseline_vm_hwm_bytes":3000,"median_work_peak_vm_hwm_bytes":5000,"median_normalized_peak_growth_bytes":2000},
            {"q":4,"seed":476,"median_baseline_vm_hwm_bytes":3000,"median_work_peak_vm_hwm_bytes":4900,"median_normalized_peak_growth_bytes":1900},
        ],
    }


class BaselineDecompositionTests(unittest.TestCase):
    def test_aggregate_distinguishes_baseline_from_work_peak_effect(self):
        result=analyze([block(i) for i in range(8)])
        self.assertEqual(result["classifications"]["q2"],"BASELINE_NORMALIZATION_EFFECT")
        self.assertEqual(result["classifications"]["q4"],"ABSOLUTE_WORK_PEAK_EFFECT")
        self.assertEqual(result["delta_summaries"]["q2"]["max_abs_identity_residual_bytes"],0)
        self.assertEqual(result["delta_summaries"]["q4"]["max_abs_identity_residual_bytes"],0)

    def test_probe_enforces_normalized_identity(self):
        def fake_child(**kwargs):
            seed=kwargs["seed"]
            baseline=1000 + (100 if seed==476 else 0)
            work=2000
            return {
                "semantic_exact":True,
                "baseline_vm_hwm_bytes":baseline,
                "work_peak_vm_hwm_bytes":work,
                "normalized_peak_growth_bytes":work-baseline,
                "work_seconds":1.0,
                "output_sha256":f"seed-{seed}",
            }

        with patch(
            "finite_ram_lab.baseline_decomposition_probe._run_fresh_child",
            side_effect=fake_child,
        ), patch(
            "finite_ram_lab.baseline_decomposition_probe.environment_fingerprint",
            return_value={"runner_name":"test"},
        ):
            result=run_block(block_id=0,size=64)

        self.assertEqual(len(result["condition_summaries"]),4)

    def test_bad_normalized_identity_fails_closed(self):
        def fake_child(**kwargs):
            return {
                "semantic_exact":True,
                "baseline_vm_hwm_bytes":1000,
                "work_peak_vm_hwm_bytes":2000,
                "normalized_peak_growth_bytes":999,
                "work_seconds":1.0,
                "output_sha256":"x",
            }

        with patch(
            "finite_ram_lab.baseline_decomposition_probe._run_fresh_child",
            side_effect=fake_child,
        ), patch(
            "finite_ram_lab.baseline_decomposition_probe.environment_fingerprint",
            return_value={"runner_name":"test"},
        ):
            with self.assertRaisesRegex(RuntimeError,"normalized_peak_identity_failed"):
                run_block(block_id=0,size=64)


if __name__=="__main__":
    unittest.main()
