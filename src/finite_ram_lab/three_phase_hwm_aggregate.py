from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics
from typing import Any, Mapping

from finite_ram_lab.runner_block_aggregate import (
    _one_sided_sign_p,
    _two_sided_sign_p,
)


EXPECTED_BLOCKS=8
FAMILY_ALPHA=0.05
TEST_NAMES=(
    "q2_input_two_sided",
    "q2_work_negative",
    "q2_total_negative",
    "q4_input_two_sided",
    "q4_work_negative",
    "q4_total_negative",
)


def _condition(block:Mapping[str,Any],q:int,seed:int)->Mapping[str,Any]:
    return next(
        row for row in block["condition_summaries"]
        if int(row["q"])==q and int(row["seed"])==seed
    )


def holm_decisions(p_values:dict[str,float],alpha:float)->dict[str,bool]:
    ordered=sorted(p_values.items(),key=lambda item:(item[1],item[0]))
    decisions={name:False for name in p_values}
    m=len(ordered)
    for index,(name,p) in enumerate(ordered):
        threshold=alpha/(m-index)
        if p <= threshold:
            decisions[name]=True
        else:
            break
    return decisions


def analyze(blocks:list[Mapping[str,Any]])->dict[str,Any]:
    if len(blocks)!=EXPECTED_BLOCKS:
        raise RuntimeError("runner_block_count_invalid")
    if sorted(int(block["block_id"]) for block in blocks)!=list(range(EXPECTED_BLOCKS)):
        raise RuntimeError("runner_block_ids_invalid")

    phase_metrics=(
        "input_phase_hwm_growth_bytes",
        "work_phase_hwm_growth_bytes",
        "total_hwm_growth_bytes",
        "pre_input_vm_hwm_bytes",
        "post_input_vm_hwm_bytes",
        "work_peak_vm_hwm_bytes",
    )
    deltas={q:{metric:[] for metric in phase_metrics} for q in (2,4)}
    rows=[]

    for block in sorted(blocks,key=lambda item:int(item["block_id"])):
        row={
            "block_id":int(block["block_id"]),
            "runner_name":block["environment"].get("runner_name"),
            "cpu_model":block["environment"].get("cpu_model"),
        }
        for q in (2,4):
            s474=_condition(block,q,474)
            s476=_condition(block,q,476)
            for metric in phase_metrics:
                key=f"median_{metric}"
                delta=float(s476[key])-float(s474[key])
                deltas[q][metric].append(delta)
                row[f"q{q}_{metric}_delta_476_minus_474_bytes"]=delta

            phase_identity=(
                row[f"q{q}_input_phase_hwm_growth_bytes_delta_476_minus_474_bytes"]
                + row[f"q{q}_work_phase_hwm_growth_bytes_delta_476_minus_474_bytes"]
                - row[f"q{q}_total_hwm_growth_bytes_delta_476_minus_474_bytes"]
            )
            row[f"q{q}_phase_identity_residual_bytes"]=phase_identity
        rows.append(row)

    raw_tests={
        "q2_input_two_sided":_two_sided_sign_p(deltas[2]["input_phase_hwm_growth_bytes"]),
        "q2_work_negative":_one_sided_sign_p(deltas[2]["work_phase_hwm_growth_bytes"],"negative"),
        "q2_total_negative":_one_sided_sign_p(deltas[2]["total_hwm_growth_bytes"],"negative"),
        "q4_input_two_sided":_two_sided_sign_p(deltas[4]["input_phase_hwm_growth_bytes"]),
        "q4_work_negative":_one_sided_sign_p(deltas[4]["work_phase_hwm_growth_bytes"],"negative"),
        "q4_total_negative":_one_sided_sign_p(deltas[4]["total_hwm_growth_bytes"],"negative"),
    }
    p_values={name:float(result["p"]) for name,result in raw_tests.items()}
    holm=holm_decisions(p_values,FAMILY_ALPHA)
    tests={}
    for name,result in raw_tests.items():
        tests[name]={**result,"holm_significant":holm[name]}

    classifications={}
    for q in (2,4):
        input_sig=holm[f"q{q}_input_two_sided"]
        work_sig=holm[f"q{q}_work_negative"]
        total_sig=holm[f"q{q}_total_negative"]
        if total_sig and input_sig and work_sig:
            label="MIXED_PHASE_TOTAL_EFFECT"
        elif total_sig and work_sig:
            label="WORK_PHASE_TOTAL_EFFECT"
        elif total_sig and input_sig:
            label="INPUT_PHASE_TOTAL_EFFECT"
        elif total_sig:
            label="TOTAL_EFFECT_COMPONENT_UNRESOLVED"
        elif work_sig:
            label="POST_INPUT_INCREMENT_ONLY"
        elif input_sig:
            label="INPUT_INCREMENT_ONLY"
        else:
            label="NO_PHASE_EFFECT_RESOLVED"
        classifications[f"q{q}"]=label

    summaries={}
    for q in (2,4):
        summaries[f"q{q}"]={
            "median_input_phase_delta_bytes":statistics.median(
                deltas[q]["input_phase_hwm_growth_bytes"]
            ),
            "median_work_phase_delta_bytes":statistics.median(
                deltas[q]["work_phase_hwm_growth_bytes"]
            ),
            "median_total_growth_delta_bytes":statistics.median(
                deltas[q]["total_hwm_growth_bytes"]
            ),
            "median_absolute_work_peak_delta_bytes":statistics.median(
                deltas[q]["work_peak_vm_hwm_bytes"]
            ),
            "median_pre_input_hwm_delta_bytes":statistics.median(
                deltas[q]["pre_input_vm_hwm_bytes"]
            ),
            "max_abs_phase_identity_residual_bytes":max(
                abs(row[f"q{q}_phase_identity_residual_bytes"]) for row in rows
            ),
        }

    governor_seed_feature_allowed=all(
        classifications[f"q{q}"] in {
            "MIXED_PHASE_TOTAL_EFFECT",
            "WORK_PHASE_TOTAL_EFFECT",
            "INPUT_PHASE_TOTAL_EFFECT",
            "TOTAL_EFFECT_COMPONENT_UNRESOLVED",
        }
        for q in (2,4)
    )

    return {
        "schema":"finite-ram-lab.three-phase-hwm-aggregate/v0.1",
        "claim_ceiling":"GITHUB_HOSTED_THREE_PHASE_HWM_DECOMPOSITION",
        "runner_block_count":EXPECTED_BLOCKS,
        "family_alpha":FAMILY_ALPHA,
        "multiple_testing":"Holm step-down across 6 predeclared phase tests",
        "block_rows":rows,
        "delta_summaries":summaries,
        "tests":tests,
        "classifications":classifications,
        "governor_seed_feature_allowed":governor_seed_feature_allowed,
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
