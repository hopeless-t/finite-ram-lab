from __future__ import annotations

import argparse
import gc
import json
from pathlib import Path
import statistics
import subprocess
import sys
import time
from typing import Any

import numpy as np

from finite_ram_lab.coupled_numerical_residency import (
    DEFAULT_MODULI,
    _center_in_place,
    _conservative_bound,
    _fold_lane_in_place,
    _make_inputs,
    _modulus_product,
    _proc_status_kib,
    _produce_residue_lane,
    _validate_exact_rank1,
    _validate_moduli,
)
from finite_ram_lab.runner_block_probe import environment_fingerprint


BASE_ORDERS = (
    ((2,474),(2,476),(4,474),(4,476)),
    ((4,476),(4,474),(2,476),(2,474)),
    ((2,476),(2,474),(4,476),(4,474)),
    ((4,474),(4,476),(2,474),(2,476)),
)


def materialize_inputs(root: Path, *, size: int, value_limit: int) -> dict[int,dict[str,str]]:
    root.mkdir(parents=True,exist_ok=True)
    result={}
    for seed in (474,476):
        left,right=_make_inputs(size,seed,value_limit)
        left_path=root/f"seed-{seed}-left.i64"
        right_path=root/f"seed-{seed}-right.i64"
        left.astype("<i8",copy=False).tofile(left_path)
        right.astype("<i8",copy=False).tofile(right_path)
        result[seed]={"left":str(left_path),"right":str(right_path)}
    return result


def load_inputs(left_path:Path,right_path:Path,*,size:int)->tuple[np.ndarray,np.ndarray]:
    left=np.fromfile(left_path,dtype="<i8")
    right=np.fromfile(right_path,dtype="<i8")
    if left.shape!=(size,) or right.shape!=(size,):
        raise RuntimeError("prematerialized_input_shape_invalid")
    return left.astype(np.int64,copy=False),right.astype(np.int64,copy=False)


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
    if content_seed not in (474,476):
        raise ValueError("content_seed_invalid")

    moduli=_validate_moduli(DEFAULT_MODULI[:7])
    gc.collect()
    pre_load=_proc_status_kib()

    left,right=load_inputs(left_path,right_path,size=size)
    post_load=_proc_status_kib()

    bound=_conservative_bound(left,right)
    product=_modulus_product(moduli)
    if product <= 2*bound:
        raise RuntimeError("crt_uniqueness_not_proven")

    accumulator=np.zeros((size,size),dtype=np.int64)
    peak_kib=_proc_status_kib()["VmHWM"]
    current_modulus=1

    start=time.perf_counter()
    for group_start in range(0,7,q):
        group_moduli=moduli[group_start:group_start+q]
        lanes:list[np.ndarray]=[]
        for modulus in group_moduli:
            lane=_produce_residue_lane(left,right,modulus)
            lanes.append(lane)
            peak_kib=max(peak_kib,_proc_status_kib()["VmHWM"])
        for lane,modulus in zip(lanes,group_moduli,strict=True):
            current_modulus=_fold_lane_in_place(
                accumulator,
                lane,
                current_modulus=current_modulus,
                lane_modulus=modulus,
                tile_rows=tile_rows,
            )
            peak_kib=max(peak_kib,_proc_status_kib()["VmHWM"])
        lanes.clear()
        gc.collect()

    _center_in_place(accumulator,current_modulus)
    peak_kib=max(peak_kib,_proc_status_kib()["VmHWM"])
    work_seconds=time.perf_counter()-start

    exact,digest=_validate_exact_rank1(
        accumulator,left,right,tile_rows=tile_rows
    )
    if not exact:
        raise RuntimeError("semantic_gate_failed")

    pre=pre_load["VmHWM"]*1024
    post=post_load["VmHWM"]*1024
    work=peak_kib*1024
    if not (pre <= post <= work):
        raise RuntimeError("hwm_monotonicity_failed")

    load_growth=post-pre
    work_growth=work-post
    total_growth=work-pre
    if total_growth != load_growth+work_growth:
        raise RuntimeError("phase_identity_failed")

    return {
        "schema":"finite-ram-lab.prematerialized-input-child/v0.1",
        "q":q,
        "content_seed":content_seed,
        "size":size,
        "pre_load_vm_hwm_bytes":pre,
        "post_load_vm_hwm_bytes":post,
        "work_peak_vm_hwm_bytes":work,
        "load_phase_hwm_growth_bytes":load_growth,
        "work_phase_hwm_growth_bytes":work_growth,
        "total_hwm_growth_bytes":total_growth,
        "work_seconds":work_seconds,
        "semantic_exact":True,
        "output_sha256":digest,
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
            "-m","finite_ram_lab.prematerialized_input",
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
            f"child_failed:q={q}:content_seed={content_seed}:{completed.stderr[-3000:]}"
        )
    return json.loads(completed.stdout)


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
            row["results"].append(result)
        execution_rows.append(row)

    summaries=[]
    metrics=(
        "pre_load_vm_hwm_bytes",
        "post_load_vm_hwm_bytes",
        "work_peak_vm_hwm_bytes",
        "load_phase_hwm_growth_bytes",
        "work_phase_hwm_growth_bytes",
        "total_hwm_growth_bytes",
    )
    for (q,seed),values in sorted(observations.items()):
        digests={item["output_sha256"] for item in values}
        if len(digests)!=1:
            raise RuntimeError("condition_digest_mismatch")
        summary={"q":q,"content_seed":seed,"sample_count":len(values),"output_sha256":next(iter(digests))}
        for metric in metrics:
            summary[f"median_{metric}"]=statistics.median(
                int(item[metric]) for item in values
            )
        summary["median_work_seconds"]=statistics.median(
            float(item["work_seconds"]) for item in values
        )
        summaries.append(summary)

    return {
        "schema":"finite-ram-lab.prematerialized-input-block/v0.1",
        "claim_ceiling":"GITHUB_HOSTED_PREMATERIALIZED_CONTENT_ISOLATION",
        "block_id":block_id,
        "environment":environment_fingerprint(),
        "size":size,
        "input_materialization":"outside measured child; equal-size raw int64 loader",
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
        parser.error("--block-id --work-dir --out required in block mode")
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
