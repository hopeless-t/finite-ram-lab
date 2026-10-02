from __future__ import annotations

import unittest
from unittest.mock import patch

from finite_ram_lab.app_surface import select_configuration
from finite_ram_lab.local_adapter_bootstrap import FINGERPRINT_SCHEMA
from finite_ram_lab.local_policy_adapter import (
    promote_local_policy,
    select_local_configuration,
)


def fp(kernel: str = "k1") -> dict:
    return {
        "schema": FINGERPRINT_SCHEMA,
        "system": "Linux",
        "kernel_release": kernel,
        "machine": "x86_64",
        "python_version": "3.12.0",
        "page_size_bytes": 4096,
        "cpu_model": "cpu",
        "mem_total": "16000000 kB",
        "libc": {"name": "glibc", "version": "2.39"},
        "cgroup_v2_present": True,
    }


def state(n: int = 19) -> dict:
    coverage = n / (n + 1)
    return {
        "schema": "finite-ram-lab.local-calibration-state/v0.1",
        "implementation": "TILED_WHERE",
        "host_binding": {
            "environment_fingerprint": fp(),
            "environment_fingerprint_sha256": (
                "e616223f6b89798088b0336e1e4c491ca398ef9dba477fe9ba7ddc33457b6984"
            ),
        },
        "sample_unit": "fresh_local_process_on_bound_host",
        "pareto_q": [1,2,4],
        "rows": [
            {"q":1,"sample_count":n,"empirical_max_peak_bytes":100,"median_work_seconds":0.90,"rank_max_one_step_predictive_coverage_floor":coverage},
            {"q":2,"sample_count":n,"empirical_max_peak_bytes":90,"median_work_seconds":1.00,"rank_max_one_step_predictive_coverage_floor":coverage},
            {"q":4,"sample_count":n,"empirical_max_peak_bytes":120,"median_work_seconds":0.80,"rank_max_one_step_predictive_coverage_floor":coverage},
            {"q":7,"sample_count":8,"empirical_max_peak_bytes":140,"median_work_seconds":0.70,"rank_max_one_step_predictive_coverage_floor":8/9},
        ],
    }


class LocalPolicyPromoterTests(unittest.TestCase):
    def test_promotes_sufficient_host_bound_state(self):
        with patch(
            "finite_ram_lab.local_policy_adapter.local_host_fingerprint",
            return_value=fp(),
        ), patch(
            "finite_ram_lab.local_policy_adapter.fingerprint_sha256",
            return_value=state()["host_binding"]["environment_fingerprint_sha256"],
        ):
            policy = promote_local_policy(state(), target_rank_coverage=0.95)

        self.assertEqual(policy["scope"],"LOCAL_HOST_BOUND")
        self.assertEqual(policy["pareto_q"],[1,2,4])
        self.assertEqual(policy["dominated_q_excluded"],[7])
        self.assertEqual([row["q"] for row in policy["points"]],[1,2,4])

    def test_insufficient_pareto_evidence_fails_closed(self):
        payload=state(n=18)
        payload["host_binding"]["environment_fingerprint_sha256"]="same"
        with patch(
            "finite_ram_lab.local_policy_adapter.local_host_fingerprint",
            return_value=fp(),
        ), patch(
            "finite_ram_lab.local_policy_adapter.fingerprint_sha256",
            return_value="same",
        ):
            with self.assertRaisesRegex(RuntimeError,"local_evidence_insufficient"):
                promote_local_policy(payload,target_rank_coverage=0.95)

    def test_generic_selector_cannot_bypass_local_binding(self):
        payload=state()
        payload["host_binding"]["environment_fingerprint_sha256"]="same"
        with patch(
            "finite_ram_lab.local_policy_adapter.local_host_fingerprint",
            return_value=fp(),
        ), patch(
            "finite_ram_lab.local_policy_adapter.fingerprint_sha256",
            return_value="same",
        ):
            policy=promote_local_policy(payload)

        with self.assertRaisesRegex(RuntimeError,"local_policy_requires_bound_selector"):
            select_configuration(
                policy,
                peak_budget_bytes=100,
                minimum_rank_coverage=0.95,
            )

    def test_local_selector_validates_binding_and_handles_nonmonotonic_q_budget_order(self):
        payload=state()
        payload["host_binding"]["environment_fingerprint_sha256"]="same"
        with patch(
            "finite_ram_lab.local_policy_adapter.local_host_fingerprint",
            return_value=fp(),
        ), patch(
            "finite_ram_lab.local_policy_adapter.fingerprint_sha256",
            return_value="same",
        ):
            policy=promote_local_policy(payload)
            receipt90=select_local_configuration(
                policy,
                peak_budget_bytes=90,
                minimum_rank_coverage=0.95,
                fingerprint=fp(),
            )
            receipt100=select_local_configuration(
                policy,
                peak_budget_bytes=100,
                minimum_rank_coverage=0.95,
                fingerprint=fp(),
            )
            receipt120=select_local_configuration(
                policy,
                peak_budget_bytes=120,
                minimum_rank_coverage=0.95,
                fingerprint=fp(),
            )

        self.assertEqual(receipt90["decision"]["selected_q"],2)
        self.assertEqual(receipt100["decision"]["selected_q"],1)
        self.assertEqual(receipt120["decision"]["selected_q"],4)
        self.assertTrue(receipt120["environment_binding"]["validated"])

    def test_local_selector_rejects_fingerprint_mismatch(self):
        payload=state()
        payload["host_binding"]["environment_fingerprint_sha256"]="expected"
        policy=dict(payload)
        policy={
            "schema":"finite-ram-lab.governor-policy/v0.1",
            "policy_id":"local-x",
            "policy_version":"local-v1",
            "scope":"LOCAL_HOST_BOUND",
            "implementation":"TILED_WHERE",
            "claim_ceiling":"HOST_BOUND_LOCAL_GOVERNOR",
            "environment_binding":payload["host_binding"],
            "evidence_state":{"source_result":"LOCAL_CALIBRATION","source_result_schema":payload["schema"],"governor_sha256":"x","sample_unit":"fresh_local_process_on_bound_host","exchangeability_required":True},
            "pareto_q":[1],
            "dominated_q_excluded":[2,4,7],
            "points":[{"q":1,"minimum_peak_budget_bytes":100,"sample_count":19,"rank_max_one_step_predictive_coverage_floor":0.95,"median_latency_seconds":1.0}],
            "assumption":"host bound",
        }
        with patch(
            "finite_ram_lab.local_policy_adapter.fingerprint_sha256",
            return_value="observed",
        ):
            with self.assertRaisesRegex(RuntimeError,"local_environment_fingerprint_mismatch"):
                select_local_configuration(
                    policy,
                    peak_budget_bytes=100,
                    minimum_rank_coverage=0.95,
                    fingerprint=fp("different"),
                )


if __name__=="__main__":
    unittest.main()
