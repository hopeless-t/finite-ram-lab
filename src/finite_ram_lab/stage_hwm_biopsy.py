from __future__ import annotations

import argparse
import gc
import json
from pathlib import Path
import statistics
import subprocess
import sys
from typing import Any

import numpy as np

from finite_ram_lab.coupled_numerical_residency import (
    DEFAULT_MODULI,
    _center_in_place,
    _conservative_bound,
    _fold_lane_in_place,
    _modulus_product,
    _proc_status_kib,
    _produce_residue_lane,
    _validate_exact_rank1,
    _validate_moduli,
)
from finite_ram_lab.prematerialized_input import (
    BASE_ORDERS,
    load_inputs,
    materialize_inputs,
)
from finite_ram_lab.runner_block_probe import environment_fingerprint


def _snapshot(
    name: str,
    *,
    base_hwm_bytes: int,
    base_rss_bytes: int,
) -> dict[str, Any]:
    status=_proc_status_kib()
    hwm=status["VmHWM"]*1024
    rss=status["VmRSS"]*1024
    return {
        "name":name,
        "vm_hwm_bytes":hwm,
        "vm_rss_bytes":rss,
        "hwm_growth_from_preload_bytes":hwm-base_hwm_bytes,
        "rss_delta_from_preload_bytes":rss-base_rss_bytes,
    }


def run_child(
    *,
    q:int,
    content_seed:int,
    left_path:Path,
    right_path:Path,
    size:int,
    tile_rows:int=64,
)->dict[str,Any]:
    if q not in (2,4):
        raise ValueError("q_invalid")

    moduli=_validate_moduli(DEFAULT_MODULI[:7])
    gc.collect()
    pre=_proc_status_kib()
    base_hwm=pre["VmHWM"]*1024
    base_rss=pre["VmRSS"]*1024
    milestones=[{
        "name":"pre_load",
        "vm_hwm_bytes":base_hwm,
        "vm_rss_bytes":base_rss,
        "hwm_growth_from_preload_bytes":0,
        "rss_delta_from_preload_bytes":0,
    }]

    left,right=load_inputs(left_path,right_path,size=size)
    milestones.append(_snapshot(
        "post_load",
        base_hwm_bytes=base_hwm,
        base_rss_bytes=base_rss,
    ))

    bound=_conservative_bound(left,right)
    product=_modulus_product(moduli)
    if product <= 2*bound:
        raise RuntimeError("crt_uniqueness_not_proven")

    accumulator=np.zeros((size,size),dtype=np.int64)
    milestones.append(_snapshot(
        "post_accumulator",
        base_hwm_bytes=base_hwm,
        base_rss_bytes=base_rss,
    ))

    current_modulus=1
    global_lane=0

    for group_index,group_start in enumerate(range(0,7,q)):
        group_moduli=moduli[group_start:group_start+q]
        lanes:list[np.ndarray]=[]

        for modulus in group_moduli:
            lane=_produce_residue_lane(left,right,modulus)
            lanes.append(lane)
            milestones.append(_snapshot(
                f"g{group_index}_produce_lane{global_lane}",
                base_hwm_bytes=base_hwm,
                base_rss_bytes=base_rss,
            ))
            global_lane += 1

        first_global=global_lane-len(lanes)
        for offset,(lane,modulus) in enumerate(zip(lanes,group_moduli,strict=True)):
            current_modulus=_fold_lane_in_place(
                accumulator,
                lane,
                current_modulus=current_modulus,
                lane_modulus=modulus,
                tile_rows=tile_rows,
            )
            milestones.append(_snapshot(
                f"g{group_index}_fold_lane{first_global+offset}",
                base_hwm_bytes=base_hwm,
                base_rss_bytes=base_rss,
            ))

        lanes.clear()
        gc.collect()
        milestones.append(_snapshot(
            f"g{group_index}_release",
            base_hwm_bytes=base_hwm,
            base_rss_bytes=base_rss,
        ))

    _center_in_place(accumulator,current_modulus)
    milestones.append(_snapshot(
        "post_center",
        base_hwm_bytes=base_hwm,
        base_rss_bytes=base_rss,
    ))

    exact,digest=_validate_exact_rank1(
        accumulator,left,right,tile_rows=tile_rows
    )
    if not exact:
        raise RuntimeError("semantic_gate_failed")

    return {
        "schema":"finite-ram-lab.stage-biopsy-child/v0.1",
        "q":q,
        "content_seed":content_seed,
        "size":size,
        "semantic_exact":True,
        "output_sha256":digest,
        "milestones":milestones,
        "final_hwm_growth_bytes":milestones[-1]["hwm_growth_from_preload_bytes"],
        "final_rss_delta_bytes":milestones[-1]["rss_delta_from_preload_bytes"],
    }


def _run_fresh_child(
    *,
    q:int,
    content_seed:int,
    left_path:Path,
    right_path:Path,
    size:int,
    tile_rows:int,
)->dict[str,Any]:
    completed=subprocess.run(
        [
            sys.executable,
            "-m","finite_ram_lab.stage_hwm_biopsy",
            "--child",
            "--q",str(q),
            "--content-seed",str(content_seed),
            "--left-path",str(left_path),
            "--right-path",str(right_path),
            "--size",str(size),
            "--tile-rows",str(tile_rows),
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=180,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"child_failed:q={q}:seed={content_seed}:{completed.stderr[-3000:]}"
        )
    return json.loads(completed.stdout)


def _median_milestones(values:list[dict[str,Any]])->list[dict[str,Any]]:
    names=[item["name"] for item in values[0]["milestones"]]
    for value in values[1:]:
        if [item["name"] for item in value["milestones"]] != names:
            raise RuntimeError("milestone_schema_mismatch")

    result=[]
    for index,name in enumerate(names):
        result.append({
            "name":name,
            "median_hwm_growth_bytes":statistics.median(
                int(value["milestones"][index]["hwm_growth_from_preload_bytes"])
                for value in values
            ),
            "median_rss_delta_bytes":statistics.median(
                int(value["milestones"][index]["rss_delta_from_preload_bytes"])
                for value in values
            ),
        })
    return result


def run_block(
    *,
    block_id:int,
    work_dir:Path,
    size:int=2048,
    value_limit:int=50,
    tile_rows:int=64,
)->dict[str,Any]:
    if not (0 <= block_id < 8):
        raise ValueError("block_id_invalid")

    paths=materialize_inputs(work_dir/"inputs",size=size,value_limit=value_limit)
    first=BASE_ORDERS[block_id % len(BASE_ORDERS)]
    orders=(first,tuple(reversed(first)))
    observations={(2,474):[],(2,476):[],(4,474):[],(4,476):[]}
    execution_rows=[]

    for replicate,order in enumerate(orders):
        row={"replicate":replicate,"order":[{"q":q,"content_seed":seed} for q,seed in order],"results":[]}
        for q,seed in order:
            result=_run_fresh_child(
                q=q,
                content_seed=seed,
                left_path=Path(paths[seed]["left"]),
                right_path=Path(paths[seed]["right"]),
                size=size,
                tile_rows=tile_rows,
            )
            observations[(q,seed)].append(result)
            row["results"].append({
                "q":q,
                "content_seed":seed,
                "final_hwm_growth_bytes":result["final_hwm_growth_bytes"],
                "final_rss_delta_bytes":result["final_rss_delta_bytes"],
                "output_sha256":result["output_sha256"],
            })
        execution_rows.append(row)

    summaries=[]
    for (q,seed),values in sorted(observations.items()):
        digests={value["output_sha256"] for value in values}
        if len(digests)!=1:
            raise RuntimeError("condition_digest_mismatch")
        summaries.append({
            "q":q,
            "content_seed":seed,
            "sample_count":len(values),
            "output_sha256":next(iter(digests)),
            "milestones":_median_milestones(values),
        })

    return {
        "schema":"finite-ram-lab.stage-biopsy-block/v0.1",
        "claim_ceiling":"DESCRIPTIVE_STAGE_HWM_BIOPSY",
        "block_id":block_id,
        "environment":environment_fingerprint(),
        "size":size,
        "execution_rows":execution_rows,
        "condition_summaries":summaries,
    }


def main()->int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--child",action="store_true")
    parser.add_argument("--q",type=int)
    parser.add_argument("--content-seed",type=int)
    parser.add_argument("--left-path",type=Path)
    parser.add_argument("--right-path",type=Path)
    parser.add_argument("--block-id",type=int)
    parser.add_argument("--work-dir",type=Path)
    parser.add_argument("--size",type=int,default=2048)
    parser.add_argument("--value-limit",type=int,default=50)
    parser.add_argument("--tile-rows",type=int,default=64)
    parser.add_argument("--out",type=Path)
    args=parser.parse_args()

    if args.child:
        if None in (args.q,args.content_seed,args.left_path,args.right_path):
            parser.error("child args missing")
        print(json.dumps(run_child(
            q=args.q,
            content_seed=args.content_seed,
            left_path=args.left_path,
            right_path=args.right_path,
            size=args.size,
            tile_rows=args.tile_rows,
        ),sort_keys=True))
        return 0

    if args.block_id is None or args.work_dir is None or args.out is None:
        parser.error("block args missing")
    payload=run_block(
        block_id=args.block_id,
        work_dir=args.work_dir,
        size=args.size,
        value_limit=args.value_limit,
        tile_rows=args.tile_rows,
    )
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
        "block_id":payload["block_id"],
        "environment":payload["environment"],
        "condition_summaries":payload["condition_summaries"],
    },sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
