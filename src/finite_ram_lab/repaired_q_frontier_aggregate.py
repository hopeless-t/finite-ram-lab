from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics
from typing import Any, Mapping

from finite_ram_lab.repaired_q_frontier import Q_VALUES
from finite_ram_lab.runner_block_aggregate import _one_sided_sign_p
from finite_ram_lab.three_phase_hwm_aggregate import holm_decisions


EXPECTED_BLOCKS=8
FAMILY_ALPHA=0.05


def _result(block:Mapping[str,Any],strategy:str,q:int)->Mapping[str,Any]:
    return next(
        row for row in block["results"]
        if row["strategy"]==strategy and int(row["q"])==q
    )


def _pareto(rows:list[dict[str,Any]])->list[int]:
    out=[]
    for candidate in rows:
        dominated=False
        for other in rows:
            if other["q"]==candidate["q"]:
                continue
            no_worse=(
                other["median_peak_bytes"] <= candidate["median_peak_bytes"]
                and other["median_work_seconds"] <= candidate["median_work_seconds"]
            )
            better=(
                other["median_peak_bytes"] < candidate["median_peak_bytes"]
                or other["median_work_seconds"] < candidate["median_work_seconds"]
            )
            if no_worse and better:
                dominated=True
                break
        if not dominated:
            out.append(int(candidate["q"]))
    return sorted(out)


def analyze(blocks:list[Mapping[str,Any]])->dict[str,Any]:
    if len(blocks)!=EXPECTED_BLOCKS:
        raise RuntimeError("runner_block_count_invalid")
    blocks=sorted(blocks,key=lambda item:int(item["block_id"]))
    if [int(b["block_id"]) for b in blocks] != list(range(EXPECTED_BLOCKS)):
        raise RuntimeError("runner_block_ids_invalid")

    rows=[]
    savings_by_q={}
    latency_ratios_by_q={}
    raw_tests={}

    for q in Q_VALUES:
        old_peaks=[]; new_peaks=[]; old_times=[]; new_times=[]; savings=[]
        for block in blocks:
            old=_result(block,"BOOLEAN_INDEX",q)
            new=_result(block,"TILED_WHERE",q)
            old_peak=int(old["normalized_peak_growth_bytes"])
            new_peak=int(new["normalized_peak_growth_bytes"])
            old_time=float(old["work_seconds"])
            new_time=float(new["work_seconds"])
            old_peaks.append(old_peak); new_peaks.append(new_peak)
            old_times.append(old_time); new_times.append(new_time)
            savings.append(old_peak-new_peak)
        savings_by_q[q]=savings
        latency_ratios_by_q[q]=[
            n/max(o,1e-12) for n,o in zip(new_times,old_times,strict=True)
        ]
        raw_tests[f"q{q}_repair_saves_peak"]=_one_sided_sign_p(savings,"positive")

        rows.append({
            "q":q,
            "old_median_peak_bytes":statistics.median(old_peaks),
            "new_median_peak_bytes":statistics.median(new_peaks),
            "median_peak_savings_bytes":statistics.median(savings),
            "old_median_work_seconds":statistics.median(old_times),
            "new_median_work_seconds":statistics.median(new_times),
            "median_latency_ratio_new_over_old":statistics.median(
                latency_ratios_by_q[q]
            ),
        })

    holm=holm_decisions(
        {name:float(value["p"]) for name,value in raw_tests.items()},
        FAMILY_ALPHA,
    )
    tests={
        name:{**value,"holm_significant":holm[name]}
        for name,value in raw_tests.items()
    }

    repaired_rows=[
        {
            "q":row["q"],
            "median_peak_bytes":row["new_median_peak_bytes"],
            "median_work_seconds":row["new_median_work_seconds"],
        }
        for row in rows
    ]
    q1=next(row for row in repaired_rows if row["q"]==1)
    for row in repaired_rows:
        row["peak_delta_vs_q1_bytes"]=row["median_peak_bytes"]-q1["median_peak_bytes"]
        row["latency_ratio_vs_q1"]=row["median_work_seconds"]/q1["median_work_seconds"]

    pareto=_pareto(repaired_rows)
    all_peak_tests=all(
        tests[f"q{q}_repair_saves_peak"]["holm_significant"] for q in Q_VALUES
    )
    minimum_saving=min(statistics.median(savings_by_q[q]) for q in Q_VALUES)

    integrated_qualified=all_peak_tests and minimum_saving >= 12*1024*1024

    return {
        "schema":"finite-ram-lab.repaired-q-frontier-aggregate/v0.1",
        "claim_ceiling":"HOSTED_PAIRED_OLD_VS_REPAIRED_Q_FRONTIER",
        "runner_block_count":EXPECTED_BLOCKS,
        "family_alpha":FAMILY_ALPHA,
        "tests":tests,
        "old_vs_new_rows":rows,
        "repaired_frontier_rows":repaired_rows,
        "repaired_pareto_q":pareto,
        "summary":{
            "minimum_median_peak_saving_bytes_across_q":minimum_saving,
            "all_q_peak_savings_holm_significant":all_peak_tests,
            "integrated_repair_qualified":integrated_qualified,
        },
        "classification":(
            "INTEGRATED_CENTER_REPAIR_QUALIFIED"
            if integrated_qualified else "INTEGRATED_REPAIR_HOLD"
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
