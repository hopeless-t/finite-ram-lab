from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from finite_ram_lab.prematerialized_input import materialize_inputs
from finite_ram_lab.stage_hwm_biopsy import run_child
from finite_ram_lab.stage_hwm_biopsy_aggregate import analyze


def _milestones(delta:int)->list[dict]:
    names=["pre_load","post_load","post_accumulator","g0_produce_lane0","g0_fold_lane0","g0_release","post_center"]
    rows=[]
    for index,name in enumerate(names):
        effect=delta if index>=3 else 0
        rows.append({
            "name":name,
            "median_hwm_growth_bytes":1000*index + effect,
            "median_rss_delta_bytes":500*index + effect,
        })
    return rows


def block(block_id:int)->dict:
    return {
        "schema":"finite-ram-lab.stage-biopsy-block/v0.1",
        "block_id":block_id,
        "condition_summaries":[
            {"q":2,"content_seed":474,"milestones":_milestones(0)},
            {"q":2,"content_seed":476,"milestones":_milestones(-8192)},
            {"q":4,"content_seed":474,"milestones":_milestones(0)},
            {"q":4,"content_seed":476,"milestones":_milestones(-8192)},
        ],
    }


class StageHWMBiopsyTests(unittest.TestCase):
    def test_aggregate_localizes_first_unanimous_divergence(self):
        result=analyze([block(i) for i in range(8)])
        self.assertEqual(
            result["q_results"]["q2"]["first_unanimous_hwm_divergence"],
            "g0_produce_lane0",
        )
        self.assertEqual(
            result["q_results"]["q4"]["first_unanimous_hwm_divergence"],
            "g0_produce_lane0",
        )
        self.assertTrue(result["q_results"]["q2"]["final_effect_confirmed"])

    def test_small_child_is_exact_and_records_stages(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths=materialize_inputs(Path(tmp),size=24,value_limit=10)
            result=run_child(
                q=2,
                content_seed=474,
                left_path=Path(paths[474]["left"]),
                right_path=Path(paths[474]["right"]),
                size=24,
                tile_rows=8,
            )
            self.assertTrue(result["semantic_exact"])
            names=[row["name"] for row in result["milestones"]]
            self.assertEqual(names[0],"pre_load")
            self.assertIn("g0_produce_lane0",names)
            self.assertEqual(names[-1],"post_center")

    def test_missing_block_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError,"runner_block_count_invalid"):
            analyze([block(i) for i in range(7)])


if __name__=="__main__":
    unittest.main()
