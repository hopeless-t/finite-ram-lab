from __future__ import annotations

import unittest

from finite_ram_lab.application_execution_receipt import build_execution_receipt
from finite_ram_lab.application_consumer_aggregate import aggregate_receipts


def decision(q:int,boundary:int)->dict:
    return {
        "schema":"finite-ram-lab.governor-decision-receipt/v0.1",
        "status":"SELECTED",
        "policy_id":"repaired-governor-v2.1",
        "policy_version":"v2.1",
        "policy_manifest_sha256":"policy",
        "implementation":"TILED_WHERE",
        "claim_ceiling":"x",
        "request":{"peak_budget_bytes":boundary,"minimum_rank_coverage":0.95},
        "decision":{
            "selected_q":q,
            "selected_empirical_max_peak_bytes":boundary,
            "budget_slack_bytes":0,
            "sample_count":27,
            "rank_max_one_step_predictive_coverage_floor":27/28,
            "median_latency_seconds":1.0,
        },
        "evidence":{"source_result":"B493"},
        "assumption":"exchangeable",
    }


def execution(q:int,peak:int)->dict:
    return {
        "schema":"finite-ram-lab.repaired-q-child/v0.1",
        "strategy":"TILED_WHERE",
        "q":q,
        "semantic_exact":True,
        "output_sha256":"same",
        "normalized_peak_growth_bytes":peak,
        "work_seconds":1.0,
    }


class ApplicationConsumerDogfoodTests(unittest.TestCase):
    def test_execution_receipt_binds_decision_to_execution(self):
        r=build_execution_receipt(decision(4,200),execution(4,190))
        self.assertTrue(r["contract_consistent"])
        self.assertEqual(r["boundary_check"]["classification"],"WITHIN_CALIBRATED_BOUNDARY")
        self.assertEqual(r["boundary_check"]["headroom_bytes"],10)

    def test_q_mismatch_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError,"selected_q_execution_q_mismatch"):
            build_execution_receipt(decision(4,200),execution(2,190))

    def test_aggregate_requires_q2_q4_q7(self):
        receipts=[
            build_execution_receipt(decision(2,100),execution(2,90)),
            build_execution_receipt(decision(4,200),execution(4,190)),
            build_execution_receipt(decision(7,300),execution(7,290)),
        ]
        result=aggregate_receipts(receipts)
        self.assertEqual(result["classification"],"APPLICATION_CONSUMER_LOOP_PASS")
        self.assertEqual(result["selected_q"],[2,4,7])
        self.assertEqual(result["exceedance_q"],[])

    def test_aggregate_preserves_boundary_exceedance_without_hiding_it(self):
        receipts=[
            build_execution_receipt(decision(2,100),execution(2,90)),
            build_execution_receipt(decision(4,200),execution(4,201)),
            build_execution_receipt(decision(7,300),execution(7,290)),
        ]
        result=aggregate_receipts(receipts)
        self.assertEqual(
            result["classification"],
            "APPLICATION_CONSUMER_LOOP_PASS_WITH_BOUNDARY_EXCEEDANCE",
        )
        self.assertEqual(result["exceedance_q"],[4])


if __name__=="__main__":
    unittest.main()
