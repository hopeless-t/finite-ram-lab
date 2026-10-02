from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from finite_ram_lab.local_adapter_bootstrap import FINGERPRINT_SCHEMA
from finite_ram_lab.local_one_shot_qualifier import (
    extend_calibration_state,
    qualify_local_governor,
    write_qualification_bundle,
)


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


def state() -> dict:
    rows=[]
    for q,peak,work,n in (
        (1,100,1.0,2),
        (2,90,.9,2),
        (4,120,.8,2),
        (7,140,.7,2),
    ):
        rows.append({
            "q":q,
            "sample_count":n,
            "median_peak_bytes":peak,
            "empirical_max_peak_bytes":peak,
            "median_work_seconds":work,
            "rank_max_one_step_predictive_coverage_floor":n/(n+1),
            "peak_samples_bytes":[peak]*n,
            "work_samples_seconds":[work]*n,
        })
    return {
        "schema":"finite-ram-lab.local-calibration-state/v0.1",
        "status":"CALIBRATION_STATE_UPDATED",
        "implementation":"TILED_WHERE",
        "host_binding":{
            "environment_fingerprint":fp(),
            "environment_fingerprint_sha256":"same",
        },
        "sample_unit":"fresh_local_process_on_bound_host",
        "size":64,
        "seed":469,
        "candidate_q":[1,2,4,7],
        "rows":rows,
        "pareto_q":[2,4,7],
        "promotion_target_rank_coverage":.75,
        "promotion_rows":[
            {"q":2,"current_sample_count":2,"required_sample_count":3,"additional_samples_required":1},
            {"q":4,"current_sample_count":2,"required_sample_count":3,"additional_samples_required":1},
            {"q":7,"current_sample_count":2,"required_sample_count":3,"additional_samples_required":1},
        ],
        "policy_promotion_allowed":False,
        "cross_q_output_sha256":"same",
        "hosted_threshold_imported":False,
    }


class LocalOneShotQualifierTests(unittest.TestCase):
    def test_extend_state_adds_only_requested_q(self):
        calls=[]
        def fake_child(**kwargs):
            q=kwargs["q"]
            calls.append(q)
            return {
                "semantic_exact":True,
                "normalized_peak_growth_bytes":{2:90,4:120}[q],
                "work_seconds":{2:.9,4:.8}[q],
                "output_sha256":"same",
            }

        with patch(
            "finite_ram_lab.local_one_shot_qualifier.local_host_fingerprint",
            return_value=fp(),
        ), patch(
            "finite_ram_lab.local_one_shot_qualifier.fingerprint_sha256",
            return_value="same",
        ), patch(
            "finite_ram_lab.local_one_shot_qualifier._run_fresh_child",
            side_effect=fake_child,
        ):
            out=extend_calibration_state(
                state(),
                sample_additions={2:1,4:1},
                size=64,
                target_rank_coverage=.75,
            )

        self.assertEqual(sorted(calls),[2,4])
        rows={row["q"]:row for row in out["rows"]}
        self.assertEqual(rows[1]["sample_count"],2)
        self.assertEqual(rows[2]["sample_count"],3)
        self.assertEqual(rows[4]["sample_count"],3)

    def test_adaptive_qualification_handles_reemergent_q(self):
        exploration={
            "physical_observations":8,
        }
        s0=state()
        s0["pareto_q"]=[2]
        s0["promotion_rows"]=[
            {"q":2,"current_sample_count":2,"required_sample_count":3,"additional_samples_required":1},
        ]

        s1=state()
        s1["pareto_q"]=[1,2]
        s1["promotion_rows"]=[
            {"q":1,"current_sample_count":2,"required_sample_count":3,"additional_samples_required":1},
            {"q":2,"current_sample_count":3,"required_sample_count":3,"additional_samples_required":0},
        ]
        s1["policy_promotion_allowed"]=False
        for row in s1["rows"]:
            if row["q"]==2:
                row["sample_count"]=3
                row["rank_max_one_step_predictive_coverage_floor"]=.75
                row["peak_samples_bytes"]=[90,90,90]
                row["work_samples_seconds"]=[.9,.9,.9]

        s2=state()
        s2["pareto_q"]=[1,2]
        s2["promotion_rows"]=[
            {"q":1,"current_sample_count":3,"required_sample_count":3,"additional_samples_required":0},
            {"q":2,"current_sample_count":3,"required_sample_count":3,"additional_samples_required":0},
        ]
        s2["policy_promotion_allowed"]=True
        for row in s2["rows"]:
            if row["q"] in (1,2):
                row["sample_count"]=3
                row["rank_max_one_step_predictive_coverage_floor"]=.75
                row["peak_samples_bytes"]=[row["empirical_max_peak_bytes"]]*3
                row["work_samples_seconds"]=[row["median_work_seconds"]]*3

        fake_policy={
            "schema":"finite-ram-lab.governor-policy/v0.1",
            "policy_id":"local-test",
            "policy_version":"local-v1",
            "scope":"LOCAL_HOST_BOUND",
            "implementation":"TILED_WHERE",
            "claim_ceiling":"HOST_BOUND_LOCAL_GOVERNOR",
            "environment_binding":s2["host_binding"],
            "evidence_state":{"source_result":"LOCAL_CALIBRATION","source_result_schema":s2["schema"],"governor_sha256":"x","sample_unit":s2["sample_unit"],"exchangeability_required":True},
            "pareto_q":[1,2],
            "dominated_q_excluded":[4,7],
            "points":[
                {"q":1,"minimum_peak_budget_bytes":100,"sample_count":3,"rank_max_one_step_predictive_coverage_floor":.75,"median_latency_seconds":1.0},
                {"q":2,"minimum_peak_budget_bytes":90,"sample_count":3,"rank_max_one_step_predictive_coverage_floor":.75,"median_latency_seconds":.9},
            ],
            "assumption":"host bound",
        }

        with patch(
            "finite_ram_lab.local_one_shot_qualifier.run_local_exploration",
            return_value=exploration,
        ), patch(
            "finite_ram_lab.local_one_shot_qualifier.extend_local_calibration",
            return_value=s0,
        ), patch(
            "finite_ram_lab.local_one_shot_qualifier.extend_calibration_state",
            side_effect=[s1,s2],
        ) as extend_mock, patch(
            "finite_ram_lab.local_one_shot_qualifier.local_host_fingerprint",
            return_value=fp(),
        ), patch(
            "finite_ram_lab.local_one_shot_qualifier.promote_local_policy",
            return_value=fake_policy,
        ):
            bundle=qualify_local_governor(
                exploration_samples_per_q=2,
                size=64,
                target_rank_coverage=.75,
                max_extension_cycles=4,
            )

        receipt=bundle["qualification_receipt"]
        self.assertEqual(len(receipt["extension_cycles"]),2)
        self.assertEqual(
            receipt["extension_cycles"][0]["sample_additions"],
            {2:1},
        )
        self.assertEqual(
            receipt["extension_cycles"][1]["sample_additions"],
            {1:1},
        )
        self.assertEqual(extend_mock.call_count,2)
        self.assertEqual(receipt["final_pareto_q"],[1,2])

    def test_bundle_writes_hash_manifest(self):
        bundle={
            "exploration":{"schema":"x"},
            "calibration_state":{"schema":"y"},
            "policy":{"policy_id":"p","schema":"z"},
            "qualification_receipt":{
                "environment_fingerprint_sha256":"fp",
                "schema":"r",
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            written=write_qualification_bundle(bundle,tmp)
            manifest=json.loads(Path(written["manifest_path"]).read_text())
            self.assertEqual(manifest["policy_id"],"p")
            self.assertEqual(
                set(manifest["files"]),
                {"exploration","calibration_state","policy","qualification_receipt"},
            )
            self.assertEqual(len(written["manifest_sha256"]),64)

    def test_digest_mismatch_fails_closed(self):
        def fake_child(**kwargs):
            return {
                "semantic_exact":True,
                "normalized_peak_growth_bytes":90,
                "work_seconds":.9,
                "output_sha256":"different",
            }
        with patch(
            "finite_ram_lab.local_one_shot_qualifier.local_host_fingerprint",
            return_value=fp(),
        ), patch(
            "finite_ram_lab.local_one_shot_qualifier.fingerprint_sha256",
            return_value="same",
        ), patch(
            "finite_ram_lab.local_one_shot_qualifier._run_fresh_child",
            side_effect=fake_child,
        ):
            with self.assertRaisesRegex(RuntimeError,"output_digest_mismatch"):
                extend_calibration_state(
                    state(),
                    sample_additions={2:1},
                    size=64,
                    target_rank_coverage=.75,
                )


if __name__=="__main__":
    unittest.main()
