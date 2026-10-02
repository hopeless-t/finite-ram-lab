from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping


Q_VALUES=(2,4,7)


def _load(path:Path)->dict[str,Any]:
    return json.loads(path.read_text())


def update_calibration(
    b489:Mapping[str,Any],
    b491:Mapping[str,Any],
)->dict[str,Any]:
    if b489.get("schema")!="finite-ram-lab.b489-result/v0.1":
        raise RuntimeError("b489_schema_invalid")
    if b491.get("schema")!="finite-ram-lab.b491-result/v0.1":
        raise RuntimeError("b491_schema_invalid")
    if b491.get("suspect_q"):
        raise RuntimeError("drift_suspect_blocks_online_update")
    if not b491.get("boundary_dispatch_checks_pass"):
        raise RuntimeError("boundary_dispatch_invalid")

    future_n=int(b491["runner_block_count"])
    rows=[]
    for q in Q_VALUES:
        old=next(row for row in b489["summary_rows"] if int(row["q"])==q)
        future=next(row for row in b491["rows"] if int(row["q"])==q)

        old_n=int(old["pooled_sample_count"])
        new_n=old_n+future_n
        old_max=int(old["pooled_empirical_max_peak_bytes"])
        future_max=int(future["max_observed_peak_bytes"])
        new_max=max(old_max,future_max)
        coverage=new_n/(new_n+1)

        rows.append({
            "q":q,
            "previous_sample_count":old_n,
            "absorbed_sample_count":future_n,
            "updated_sample_count":new_n,
            "previous_empirical_max_peak_bytes":old_max,
            "future_panel_max_peak_bytes":future_max,
            "updated_empirical_max_peak_bytes":new_max,
            "empirical_max_moved_bytes":new_max-old_max,
            "updated_rank_max_one_step_predictive_coverage_floor":coverage,
            "source_future_classification":future["classification"],
        })

    return {
        "schema":"finite-ram-lab.online-calibration-update/v0.1",
        "status":"UPDATED",
        "claim_ceiling":"NON_DRIFT_ONLINE_SAMPLE_MAX_UPDATE",
        "implementation":"TILED_WHERE",
        "pareto_q":list(Q_VALUES),
        "source_calibration":"B489",
        "source_runtime_panel":"B491",
        "rows":rows,
        "minimum_updated_coverage_floor":min(
            row["updated_rank_max_one_step_predictive_coverage_floor"]
            for row in rows
        ),
        "assumption":(
            "B491 was not drift-suspect and its runner observations are absorbed "
            "as exchangeable repaired-runtime samples"
        ),
    }


def main()->int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--b489",type=Path,required=True)
    parser.add_argument("--b491",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()

    payload=update_calibration(_load(args.b489),_load(args.b491))
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
    print(json.dumps(payload,sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
