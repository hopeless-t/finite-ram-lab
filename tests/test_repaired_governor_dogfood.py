from __future__ import annotations

import unittest
from unittest.mock import patch

from finite_ram_lab.repaired_governor_dogfood import (
    boundary_checks,
    run_block,
)
from finite_ram_lab.repaired_governor_dogfood_aggregate import analyze


def b489() -> dict:
    return {
        "schema":"finite-ram-lab.b489-result/v0.1",
        "implementation":"TILED_WHERE",
        "summary_rows":[
            {"q":2,"pooled_sample_count":19,"pooled_empirical_max_peak_bytes":100,"rank_max_one_step_predictive_coverage_floor":0.95,"median_new_work_seconds":3.0},
            {"q":4,"pooled_sample_count":19,"pooled_empirical_max_peak_bytes":200,"rank_max_one_step_predictive_coverage_floor":0.95,"median_new_work_seconds":2.0},
            {"q":7,"pooled_sample_count":19,"pooled_empirical_max_peak_bytes":300,"rank_max_one_step_predictive_coverage_floor":0.95,"median_new_work_seconds":1.0},
        ],
    }


def b490() -> dict:
    return {
        "schema":"finite-ram-lab.b490-result/v0.1",
        "breakpoints":[
            {"minimum_peak_budget_bytes":100,"selected_q":2},
            {"minimum_peak_budget_bytes":200,"selected_q":4},
            {"minimum_peak_budget_bytes":300,"selected_q":7},
        ],
    }


def block(block_id:int, exceed_q:int|None=None)->dict:
    results=[]
    for q,budget in ((2,100),(4,200),(7,300)):
        peak=budget+1 if q==exceed_q else budget
        results.append({
            "q":q,
            "declared_peak_budget_bytes":budget,
            "observed_peak_bytes":peak,
            "within_declared_budget":peak<=budget,
            "work_seconds":1.0,
            "output_sha256":"same",
        })
    return {
        "schema":"finite-ram-lab.repaired-governor-dogfood-block/v0.1",
        "block_id":block_id,
        "boundary_checks":[{"pass":True}],
        "results":results,
    }


class RepairedGovernorDogfoodTests(unittest.TestCase):
    def test_boundary_checks_cover_below_and_exact_transitions(self):
        checks=boundary_checks(b489(),b490())
        self.assertEqual(len(checks),6)
        self.assertTrue(all(row["pass"] for row in checks))
        self.assertEqual(checks[0]["observed"],"NO_ELIGIBLE_Q")

    def test_no_exceedance_panel_is_compliant(self):
        result=analyze([block(i) for i in range(8)])
        self.assertEqual(result["overall"]["classification"],"ALL_BOUNDARIES_COMPLIANT")
        self.assertEqual(result["overall"]["total_exceedances"],0)

    def test_single_exceedance_is_tail_compatible(self):
        blocks=[block(i,exceed_q=2 if i==0 else None) for i in range(8)]
        result=analyze(blocks)
        q2=next(row for row in result["rows"] if row["q"]==2)
        self.assertEqual(q2["classification"],"TAIL_COMPATIBLE_EXCEEDANCE")

    def test_probe_executes_selected_q_values_exactly(self):
        def fake_child(**kwargs):
            q=kwargs["q"]
            peaks={2:100,4:200,7:300}
            return {
                "semantic_exact":True,
                "normalized_peak_growth_bytes":peaks[q],
                "work_seconds":1.0,
                "output_sha256":"same",
            }
        with patch(
            "finite_ram_lab.repaired_governor_dogfood._run_fresh_child",
            side_effect=fake_child,
        ), patch(
            "finite_ram_lab.repaired_governor_dogfood.environment_fingerprint",
            return_value={"runner_name":"test"},
        ):
            result=run_block(b489(),b490(),block_id=0,size=64)
        self.assertEqual(len(result["results"]),3)
        self.assertTrue(all(row["within_declared_budget"] for row in result["results"]))


if __name__=="__main__":
    unittest.main()
