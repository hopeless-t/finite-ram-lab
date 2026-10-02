from __future__ import annotations

import unittest
from unittest.mock import patch

from finite_ram_lab.local_adapter_bootstrap import FINGERPRINT_SCHEMA
from finite_ram_lab.local_calibration_extend import extend_local_calibration


def fp() -> dict:
    return {
        "schema": FINGERPRINT_SCHEMA,
        "system": "Linux",
        "kernel_release": "k1",
        "machine": "x86_64",
        "python_version": "3.12.0",
        "page_size_bytes": 4096,
        "cpu_model": "cpu",
        "mem_total": "16000000 kB",
        "libc": {"name": "glibc", "version": "2.39"},
        "cgroup_v2_present": True,
    }


def exploration() -> dict:
    rows=[]
    profiles={
        1:(100,1.0),
        2:(100,0.9),
        4:(120,0.8),
        7:(140,0.7),
    }
    for block_id in range(2):
        block={"block_id":block_id,"execution_order":[1,2,4,7],"results":[]}
        for q,(peak,work) in profiles.items():
            block["results"].append({
                "q":q,
                "normalized_peak_growth_bytes":peak,
                "work_seconds":work,
                "output_sha256":"same",
            })
        rows.append(block)
    return {
        "schema":"finite-ram-lab.local-calibration-exploration/v0.1",
        "implementation":"TILED_WHERE",
        "host_binding":{
            "environment_fingerprint":fp(),
            "environment_fingerprint_sha256":"same",
            "stable_across_panel":True,
        },
        "sample_unit":"fresh_local_process_on_bound_host",
        "size":64,
        "seed":469,
        "samples_per_q":2,
        "candidate_q":[1,2,4,7],
        "execution_blocks":rows,
        "local_pareto_q":[2,4,7],
        "cross_q_output_sha256":"same",
    }


class LocalCalibrationExtendTests(unittest.TestCase):
    def test_extends_only_initial_pareto_q(self):
        calls=[]
        def fake_child(**kwargs):
            calls.append(kwargs["q"])
            return {
                "semantic_exact":True,
                "normalized_peak_growth_bytes":{2:100,4:120,7:140}[kwargs["q"]],
                "work_seconds":{2:.9,4:.8,7:.7}[kwargs["q"]],
                "output_sha256":"same",
            }

        with patch(
            "finite_ram_lab.local_calibration_extend.local_host_fingerprint",
            return_value=fp(),
        ), patch(
            "finite_ram_lab.local_calibration_extend.fingerprint_sha256",
            return_value="same",
        ), patch(
            "finite_ram_lab.local_calibration_extend._run_fresh_child",
            side_effect=fake_child,
        ):
            result=extend_local_calibration(
                exploration(),
                additional_samples_per_q=1,
                size=64,
                target_rank_coverage=.95,
            )

        self.assertEqual(sorted(calls),[2,4,7])
        self.assertEqual(result["physical_observations_added"],3)
        rows={row["q"]:row for row in result["rows"]}
        self.assertEqual(rows[1]["sample_count"],2)
        self.assertEqual(rows[2]["sample_count"],3)
        self.assertFalse(result["policy_promotion_allowed"])

    def test_recomputes_pareto_and_blocks_if_unextended_q_reappears(self):
        # Make q2 much slower/higher during extension so q1 can re-enter final Pareto.
        def fake_child(**kwargs):
            q=kwargs["q"]
            if q==2:
                return {
                    "semantic_exact":True,
                    "normalized_peak_growth_bytes":500,
                    "work_seconds":2.0,
                    "output_sha256":"same",
                }
            return {
                "semantic_exact":True,
                "normalized_peak_growth_bytes":{4:120,7:140}[q],
                "work_seconds":{4:.8,7:.7}[q],
                "output_sha256":"same",
            }

        with patch(
            "finite_ram_lab.local_calibration_extend.local_host_fingerprint",
            return_value=fp(),
        ), patch(
            "finite_ram_lab.local_calibration_extend.fingerprint_sha256",
            return_value="same",
        ), patch(
            "finite_ram_lab.local_calibration_extend._run_fresh_child",
            side_effect=fake_child,
        ):
            result=extend_local_calibration(
                exploration(),
                additional_samples_per_q=3,
                size=64,
                target_rank_coverage=.8,
            )

        self.assertIn(1,result["pareto_q"])
        q1=next(row for row in result["promotion_rows"] if row["q"]==1)
        self.assertGreater(q1["additional_samples_required"],0)
        self.assertFalse(result["policy_promotion_allowed"])

    def test_sufficient_extended_pareto_can_promote(self):
        # With n2 exploration + n2 extension => n4, target .75 requires n3.
        def fake_child(**kwargs):
            q=kwargs["q"]
            return {
                "semantic_exact":True,
                "normalized_peak_growth_bytes":{2:100,4:120,7:140}[q],
                "work_seconds":{2:.9,4:.8,7:.7}[q],
                "output_sha256":"same",
            }

        with patch(
            "finite_ram_lab.local_calibration_extend.local_host_fingerprint",
            return_value=fp(),
        ), patch(
            "finite_ram_lab.local_calibration_extend.fingerprint_sha256",
            return_value="same",
        ), patch(
            "finite_ram_lab.local_calibration_extend._run_fresh_child",
            side_effect=fake_child,
        ):
            result=extend_local_calibration(
                exploration(),
                additional_samples_per_q=2,
                size=64,
                target_rank_coverage=.75,
            )

        self.assertTrue(result["policy_promotion_allowed"])
        self.assertEqual(result["pareto_q"],[2,4,7])

    def test_fingerprint_mismatch_blocks_extension(self):
        with patch(
            "finite_ram_lab.local_calibration_extend.local_host_fingerprint",
            return_value=fp(),
        ), patch(
            "finite_ram_lab.local_calibration_extend.fingerprint_sha256",
            return_value="different",
        ):
            with self.assertRaisesRegex(RuntimeError,"local_environment_fingerprint_mismatch"):
                extend_local_calibration(
                    exploration(),
                    additional_samples_per_q=1,
                    size=64,
                )


if __name__=="__main__":
    unittest.main()
