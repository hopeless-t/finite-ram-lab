from __future__ import annotations

import unittest

from finite_ram_lab.repaired_governor_v2_1 import (
    build_policy,
    select_q,
)


def b490() -> dict:
    return {
        "schema":"finite-ram-lab.b490-result/v0.1",
        "breakpoints":[
            {"selected_q":2,"median_latency_seconds":0.3956},
            {"selected_q":4,"median_latency_seconds":0.3878},
            {"selected_q":7,"median_latency_seconds":0.3864},
        ],
    }


def b492() -> dict:
    return {
        "schema":"finite-ram-lab.b492-result/v0.1",
        "rows":[
            {"q":2,"updated_sample_count":27,"updated_empirical_max_peak_bytes":100,"updated_rank_max_one_step_predictive_coverage_floor":27/28},
            {"q":4,"updated_sample_count":27,"updated_empirical_max_peak_bytes":200,"updated_rank_max_one_step_predictive_coverage_floor":27/28},
            {"q":7,"updated_sample_count":27,"updated_empirical_max_peak_bytes":304,"updated_rank_max_one_step_predictive_coverage_floor":27/28},
        ],
    }


class RepairedGovernorV21Tests(unittest.TestCase):
    def test_policy_uses_updated_evidence_state(self):
        policy=build_policy(b490(),b492())
        self.assertEqual(policy["policy_version"],"v2.1")
        self.assertEqual(
            [row["minimum_peak_budget_bytes"] for row in policy["breakpoints"]],
            [100,200,304],
        )
        self.assertTrue(all(row["sample_count"]==27 for row in policy["breakpoints"]))
        self.assertTrue(all(
            abs(row["rank_max_one_step_predictive_coverage_floor"]-27/28)<1e-12
            for row in policy["breakpoints"]
        ))

    def test_q7_one_page_update_is_reflected(self):
        decision=select_q(
            b490(),b492(),
            peak_budget_bytes=304,
            minimum_rank_coverage=0.95,
        )
        self.assertEqual(decision["selected_q"],7)
        self.assertEqual(decision["selected_empirical_max_peak_bytes"],304)

    def test_old_q7_boundary_no_longer_admits_q7(self):
        decision=select_q(
            b490(),b492(),
            peak_budget_bytes=300,
            minimum_rank_coverage=0.95,
        )
        self.assertEqual(decision["selected_q"],4)

    def test_99_percent_still_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError,"no_updated_repaired_q_fits_budget"):
            select_q(
                b490(),b492(),
                peak_budget_bytes=1000,
                minimum_rank_coverage=0.99,
            )


if __name__=="__main__":
    unittest.main()
