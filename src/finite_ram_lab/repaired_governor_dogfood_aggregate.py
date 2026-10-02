from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics
from typing import Any, Mapping

from finite_ram_lab.tail_vs_drift import beta_binomial_upper_tail


Q_VALUES=(2,4,7)
EXPECTED_BLOCKS=8
FAMILY_ALPHA=0.05
PER_Q_ALPHA=FAMILY_ALPHA/len(Q_VALUES)
CALIBRATION_N=19


def analyze(blocks:list[Mapping[str,Any]])->dict[str,Any]:
    if len(blocks)!=EXPECTED_BLOCKS:
        raise RuntimeError("runner_block_count_invalid")
    blocks=sorted(blocks,key=lambda item:int(item["block_id"]))
    if [int(block["block_id"]) for block in blocks] != list(range(EXPECTED_BLOCKS)):
        raise RuntimeError("runner_block_ids_invalid")

    if not all(
        check["pass"]
        for block in blocks
        for check in block["boundary_checks"]
    ):
        raise RuntimeError("boundary_dispatch_gate_failed")

    rows=[]
    suspect_q=[]
    total_exceedances=0

    for q in Q_VALUES:
        values=[]
        times=[]
        budget=None
        for block in blocks:
            row=next(item for item in block["results"] if int(item["q"])==q)
            values.append(int(row["observed_peak_bytes"]))
            times.append(float(row["work_seconds"]))
            current_budget=int(row["declared_peak_budget_bytes"])
            if budget is None:
                budget=current_budget
            elif budget!=current_budget:
                raise RuntimeError("budget_mismatch_across_blocks")

        exceedances=[value for value in values if value>budget]
        count=len(exceedances)
        total_exceedances+=count
        tail_p=beta_binomial_upper_tail(
            count,
            len(values),
            calibration_sample_count=CALIBRATION_N,
        )
        if count==0:
            classification="NO_EXCEEDANCE"
        elif tail_p<=PER_Q_ALPHA:
            classification="DRIFT_SUSPECT"
            suspect_q.append(q)
        else:
            classification="TAIL_COMPATIBLE_EXCEEDANCE"

        rows.append({
            "q":q,
            "declared_peak_budget_bytes":budget,
            "future_sample_count":len(values),
            "observed_peak_bytes":values,
            "max_observed_peak_bytes":max(values),
            "exceedance_count":count,
            "max_overrun_bytes":max([max(0,value-budget) for value in values],default=0),
            "beta_binomial_upper_tail_probability":tail_p,
            "per_q_alpha":PER_Q_ALPHA,
            "median_work_seconds":statistics.median(times),
            "classification":classification,
        })

    if suspect_q:
        overall="DRIFT_SUSPECT"
    elif total_exceedances:
        overall="TAIL_COMPATIBLE_EXCEEDANCES"
    else:
        overall="ALL_BOUNDARIES_COMPLIANT"

    return {
        "schema":"finite-ram-lab.repaired-governor-dogfood-result/v0.1",
        "claim_ceiling":"REPAIRED_GOVERNOR_V2_BOUNDARY_DOGFOOD",
        "runner_block_count":EXPECTED_BLOCKS,
        "physical_observations":EXPECTED_BLOCKS*len(Q_VALUES),
        "family_alpha":FAMILY_ALPHA,
        "per_q_alpha":PER_Q_ALPHA,
        "boundary_dispatch_checks_pass":True,
        "rows":rows,
        "overall":{
            "classification":overall,
            "total_exceedances":total_exceedances,
            "suspect_q":suspect_q,
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
