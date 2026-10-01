from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics
from typing import Any, Mapping

from finite_ram_lab.runner_block_aggregate import _one_sided_sign_p
from finite_ram_lab.three_phase_hwm_aggregate import holm_decisions


EXPECTED_BLOCKS=8
FAMILY_ALPHA=0.05


def _condition(block:Mapping[str,Any],q:int,seed:int)->Mapping[str,Any]:
    return next(
        row for row in block["condition_summaries"]
        if int(row["q"])==q and int(row["content_seed"])==seed
    )


def _trajectory_delta(
    blocks:list[Mapping[str,Any]],
    q:int,
)->list[dict[str,Any]]:
    first474=_condition(blocks[0],q,474)["milestones"]
    names=[item["name"] for item in first474]
    per_name={name:{"hwm":[],"rss":[]} for name in names}

    for block in blocks:
        a=_condition(block,q,474)["milestones"]
        b=_condition(block,q,476)["milestones"]
        if [item["name"] for item in a] != names or [item["name"] for item in b] != names:
            raise RuntimeError("milestone_schema_mismatch")
        for index,name in enumerate(names):
            per_name[name]["hwm"].append(
                float(b[index]["median_hwm_growth_bytes"])
                - float(a[index]["median_hwm_growth_bytes"])
            )
            per_name[name]["rss"].append(
                float(b[index]["median_rss_delta_bytes"])
                - float(a[index]["median_rss_delta_bytes"])
            )

    rows=[]
    for name in names:
        hwm=per_name[name]["hwm"]
        rss=per_name[name]["rss"]
        rows.append({
            "name":name,
            "median_hwm_growth_delta_bytes":statistics.median(hwm),
            "hwm_negative_blocks":sum(value<0 for value in hwm),
            "hwm_positive_blocks":sum(value>0 for value in hwm),
            "hwm_zero_blocks":sum(value==0 for value in hwm),
            "median_rss_delta_difference_bytes":statistics.median(rss),
            "rss_negative_blocks":sum(value<0 for value in rss),
            "rss_positive_blocks":sum(value>0 for value in rss),
            "rss_zero_blocks":sum(value==0 for value in rss),
        })
    return rows


def _first_unanimous_negative(
    rows:list[Mapping[str,Any]],
    *,
    metric_prefix:str,
)->str|None:
    if metric_prefix=="hwm":
        median_key="median_hwm_growth_delta_bytes"
        count_key="hwm_negative_blocks"
    elif metric_prefix=="rss":
        median_key="median_rss_delta_difference_bytes"
        count_key="rss_negative_blocks"
    else:
        raise ValueError("metric_prefix_invalid")

    for row in rows:
        if int(row[count_key])==EXPECTED_BLOCKS and float(row[median_key]) <= -4096:
            return str(row["name"])
    return None


def analyze(blocks:list[Mapping[str,Any]])->dict[str,Any]:
    if len(blocks)!=EXPECTED_BLOCKS:
        raise RuntimeError("runner_block_count_invalid")
    blocks=sorted(blocks,key=lambda item:int(item["block_id"]))
    if [int(block["block_id"]) for block in blocks] != list(range(EXPECTED_BLOCKS)):
        raise RuntimeError("runner_block_ids_invalid")

    trajectories={q:_trajectory_delta(blocks,q) for q in (2,4)}
    final_deltas={}
    raw_tests={}
    for q in (2,4):
        final_row=trajectories[q][-1]
        # Recover the per-block final HWM-growth delta directly for the confirmatory test.
        values=[]
        for block in blocks:
            a=_condition(block,q,474)["milestones"][-1]
            b=_condition(block,q,476)["milestones"][-1]
            values.append(
                float(b["median_hwm_growth_bytes"])
                - float(a["median_hwm_growth_bytes"])
            )
        final_deltas[q]=values
        raw_tests[f"q{q}_final_hwm_negative"]=_one_sided_sign_p(values,"negative")

    holm=holm_decisions(
        {name:float(value["p"]) for name,value in raw_tests.items()},
        FAMILY_ALPHA,
    )
    tests={
        name:{**value,"holm_significant":holm[name]}
        for name,value in raw_tests.items()
    }

    q_results={}
    for q in (2,4):
        hwm_first=_first_unanimous_negative(trajectories[q],metric_prefix="hwm")
        rss_first=_first_unanimous_negative(trajectories[q],metric_prefix="rss")
        q_results[f"q{q}"]={
            "final_effect_confirmed":holm[f"q{q}_final_hwm_negative"],
            "first_unanimous_hwm_divergence":hwm_first,
            "first_unanimous_rss_divergence":rss_first,
            "trajectory":trajectories[q],
        }

    return {
        "schema":"finite-ram-lab.stage-hwm-biopsy-aggregate/v0.1",
        "claim_ceiling":"DESCRIPTIVE_STAGE_HWM_BIOPSY",
        "runner_block_count":EXPECTED_BLOCKS,
        "family_alpha":FAMILY_ALPHA,
        "confirmatory_tests":tests,
        "q_results":q_results,
        "next_target": {
            "q2": q_results["q2"]["first_unanimous_hwm_divergence"],
            "q4": q_results["q4"]["first_unanimous_hwm_divergence"],
        },
    }


def main()->int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--blocks-dir",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    blocks=[
        json.loads(path.read_text())
        for path in sorted(args.blocks_dir.glob("block-*.json"))
    ]
    result=analyze(blocks)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
