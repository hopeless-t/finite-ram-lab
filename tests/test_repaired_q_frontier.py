from __future__ import annotations

import unittest
from unittest.mock import patch

from finite_ram_lab.repaired_q_frontier import CONDITIONS, Q_VALUES, run_block
from finite_ram_lab.repaired_q_frontier_aggregate import analyze


def block(block_id:int)->dict:
    rows=[]
    for strategy,q in CONDITIONS:
        if strategy=="BOOLEAN_INDEX":
            peak={1:70,2:71,4:75,7:76}[q]
            work={1:1.00,2:.97,4:.95,7:.94}[q]
        else:
            peak={1:50,2:51,4:55,7:56}[q]
            work={1:.98,2:.95,4:.93,7:.92}[q]
        rows.append({
            "strategy":strategy,
            "q":q,
            "semantic_exact":True,
            "output_sha256":"same",
            "normalized_peak_growth_bytes":peak,
            "work_seconds":work,
        })
    return {
        "schema":"finite-ram-lab.repaired-q-block/v0.1",
        "block_id":block_id,
        "results":rows,
    }


class RepairedQFrontierTests(unittest.TestCase):
    def test_aggregate_qualifies_integrated_repair(self):
        # Scale fixture values to satisfy 12 MiB savings gate.
        blocks=[]
        for i in range(8):
            b=block(i)
            for row in b["results"]:
                row["normalized_peak_growth_bytes"] *= 1024*1024
            blocks.append(b)
        result=analyze(blocks)
        self.assertEqual(result["classification"],"INTEGRATED_CENTER_REPAIR_QUALIFIED")
        self.assertTrue(result["summary"]["integrated_repair_qualified"])

    def test_repaired_pareto_contains_all_tradeoff_points(self):
        blocks=[]
        for i in range(8):
            b=block(i)
            for row in b["results"]:
                row["normalized_peak_growth_bytes"] *= 1024*1024
            blocks.append(b)
        result=analyze(blocks)
        self.assertEqual(result["repaired_pareto_q"],[1,2,4,7])

    def test_each_condition_occupies_each_position(self):
        positions={condition:set() for condition in CONDITIONS}
        for block_id in range(8):
            order=CONDITIONS[block_id:]+CONDITIONS[:block_id]
            for position,condition in enumerate(order):
                positions[condition].add(position)
        self.assertTrue(all(value==set(range(8)) for value in positions.values()))

    def test_block_requires_shared_exact_output(self):
        counter={"i":0}
        def fake_child(**kwargs):
            counter["i"]+=1
            return {
                "semantic_exact":True,
                "output_sha256":"same" if counter["i"]<8 else "different",
                "normalized_peak_growth_bytes":1,
                "work_seconds":1.0,
            }
        with patch(
            "finite_ram_lab.repaired_q_frontier._run_fresh_child",
            side_effect=fake_child,
        ), patch(
            "finite_ram_lab.repaired_q_frontier.environment_fingerprint",
            return_value={"runner_name":"test"},
        ):
            with self.assertRaisesRegex(RuntimeError,"condition_output_digest_mismatch"):
                run_block(block_id=0,size=64)


if __name__=="__main__":
    unittest.main()
