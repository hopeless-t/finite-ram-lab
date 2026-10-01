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


def analyze(blocks:list[Mapping[str,Any]])->dict[str,Any]:
    if len(blocks)!=EXPECTED_BLOCKS:
        raise RuntimeError("runner_block_count_invalid")
    if sorted(int(block["block_id"]) for block in blocks)!=list(range(EXPECTED_BLOCKS)):
        raise RuntimeError("runner_block_ids_invalid")

    metrics=(
        "load_phase_hwm_growth_bytes",
        "work_phase_hwm_growth_bytes",
        "total_hwm_growth_bytes",
        "pre_load_vm_hwm_bytes",
        "work_peak_vm_hwm_bytes",
    )
    deltas={q:{metric:[] for metric in metrics} for q in (2,4)}
    rows=[]

    for block in sorted(blocks,key=lambda item:int(item["block_id"])):
        row={
            "block_id":int(block["block_id"]),
            "runner_name":block["environment"].get("runner_name"),
            "cpu_model":block["environment"].get("cpu_model"),
        }
        for q in (2,4):
            a=_condition(block,q,474)
            b=_condition(block,q,476)
            for metric in metrics:
                key=f"median_{metric}"
                delta=float(b[key])-float(a[key])
                deltas[q][metric].append(delta)
                row[f"q{q}_{metric}_delta_476_minus_474_bytes"]=delta
            residual=(
                row[f"q{q}_load_phase_hwm_growth_bytes_delta_476_minus_474_bytes"]
                + row[f"q{q}_work_phase_hwm_growth_bytes_delta_476_minus_474_bytes"]
                - row[f"q{q}_total_hwm_growth_bytes_delta_476_minus_474_bytes"]
            )
            row[f"q{q}_phase_identity_residual_bytes"]=residual
        rows.append(row)

    raw={
        "q2_work_negative":_one_sided_sign_p(deltas[2]["work_phase_hwm_growth_bytes"],"negative"),
        "q2_total_negative":_one_sided_sign_p(deltas[2]["total_hwm_growth_bytes"],"negative"),
        "q4_work_negative":_one_sided_sign_p(deltas[4]["work_phase_hwm_growth_bytes"],"negative"),
        "q4_total_negative":_one_sided_sign_p(deltas[4]["total_hwm_growth_bytes"],"negative"),
    }
    decisions=holm_decisions(
        {name:float(value["p"]) for name,value in raw.items()},
        FAMILY_ALPHA,
    )
    tests={
        name:{**value,"holm_significant":decisions[name]}
        for name,value in raw.items()
    }

    classifications={}
    for q in (2,4):
        work=decisions[f"q{q}_work_negative"]
        total=decisions[f"q{q}_total_negative"]
        if work and total:
            label="PREMATERIALIZED_CONTENT_EFFECT_REPLICATED"
        elif work:
            label="WORK_INCREMENT_ONLY"
        elif total:
            label="TOTAL_ONLY"
        else:
            label="CONTENT_EFFECT_NOT_REPLICATED"
        classifications[f"q{q}"]=label

    summaries={}
    for q in (2,4):
        summaries[f"q{q}"]={
            "median_load_phase_delta_bytes":statistics.median(
                deltas[q]["load_phase_hwm_growth_bytes"]
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
            "load_phase_negative_blocks":sum(
                value < 0 for value in deltas[q]["load_phase_hwm_growth_bytes"]
            ),
            "load_phase_positive_blocks":sum(
                value > 0 for value in deltas[q]["load_phase_hwm_growth_bytes"]
            ),
            "max_abs_phase_identity_residual_bytes":max(
                abs(row[f"q{q}_phase_identity_residual_bytes"]) for row in rows
            ),
        }

    return {
        "schema":"finite-ram-lab.prematerialized-input-aggregate/v0.1",
        "claim_ceiling":"GITHUB_HOSTED_PREMATERIALIZED_CONTENT_ISOLATION",
        "runner_block_count":EXPECTED_BLOCKS,
        "family_alpha":FAMILY_ALPHA,
        "multiple_testing":"Holm step-down across 4 directional content-effect tests",
        "block_rows":rows,
        "delta_summaries":summaries,
        "tests":tests,
        "classifications":classifications,
        "q2_content_feature_supported":(
            classifications["q2"]=="PREMATERIALIZED_CONTENT_EFFECT_REPLICATED"
        ),
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
