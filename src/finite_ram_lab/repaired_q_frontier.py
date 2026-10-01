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

from finite_ram_lab.center_repair import center_tiled_where
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


Q_VALUES=(1,2,4,7)
STRATEGIES=("BOOLEAN_INDEX","TILED_WHERE")
CONDITIONS=tuple((strategy,q) for strategy in STRATEGIES for q in Q_VALUES)
SEED=469


def run_child(
    *,
    strategy:str,
    q:int,
    size:int=2048,
    seed:int=SEED,
    value_limit:int=50,
    tile_rows:int=64,
)->dict[str,Any]:
    if strategy not in STRATEGIES:
        raise ValueError("strategy_invalid")
    if q not in Q_VALUES:
        raise ValueError("q_invalid")

    moduli=_validate_moduli(DEFAULT_MODULI[:7])
    left,right=_make_inputs(size,seed,value_limit)
    bound=_conservative_bound(left,right)
    product=_modulus_product(moduli)
    if product <= 2*bound:
        raise RuntimeError("crt_uniqueness_not_proven")

    gc.collect()
    baseline=_proc_status_kib()
    base_hwm=baseline["VmHWM"]*1024

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

    if strategy=="BOOLEAN_INDEX":
        _center_in_place(accumulator,current_modulus)
    else:
        center_tiled_where(accumulator,current_modulus)
    peak_kib=max(peak_kib,_proc_status_kib()["VmHWM"])
    elapsed=time.perf_counter()-start

    exact,digest=_validate_exact_rank1(
        accumulator,left,right,tile_rows=tile_rows
    )
    if not exact:
        raise RuntimeError("semantic_gate_failed")

    return {
        "schema":"finite-ram-lab.repaired-q-child/v0.1",
        "strategy":strategy,
        "q":q,
        "size":size,
        "seed":seed,
        "semantic_exact":True,
        "output_sha256":digest,
        "baseline_vm_hwm_bytes":base_hwm,
        "work_peak_vm_hwm_bytes":peak_kib*1024,
        "normalized_peak_growth_bytes":max(0,peak_kib*1024-base_hwm),
        "work_seconds":elapsed,
    }


def _run_fresh_child(
    *,
    strategy:str,
    q:int,
    size:int,
)->dict[str,Any]:
    completed=subprocess.run(
        [
            sys.executable,
            "-m","finite_ram_lab.repaired_q_frontier",
            "--child",
            "--strategy",strategy,
            "--q",str(q),
            "--size",str(size),
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=180,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"child_failed:{strategy}:q={q}:{completed.stderr[-3000:]}"
        )
    return json.loads(completed.stdout)


def run_block(*,block_id:int,size:int=2048)->dict[str,Any]:
    if not (0 <= block_id < 8):
        raise ValueError("block_id_invalid")
    order=CONDITIONS[block_id:]+CONDITIONS[:block_id]
    results=[]
    for strategy,q in order:
        observed=_run_fresh_child(strategy=strategy,q=q,size=size)
        if not observed["semantic_exact"]:
            raise RuntimeError("semantic_gate_failed")
        results.append(observed)

    digests={item["output_sha256"] for item in results}
    if len(digests)!=1:
        raise RuntimeError("condition_output_digest_mismatch")

    return {
        "schema":"finite-ram-lab.repaired-q-block/v0.1",
        "claim_ceiling":"HOSTED_PAIRED_OLD_VS_REPAIRED_Q_FRONTIER",
        "block_id":block_id,
        "environment":environment_fingerprint(),
        "size":size,
        "seed":SEED,
        "execution_order":[{"strategy":s,"q":q} for s,q in order],
        "results":results,
        "output_sha256":next(iter(digests)),
    }


def main()->int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--child",action="store_true")
    parser.add_argument("--strategy",choices=STRATEGIES)
    parser.add_argument("--q",type=int)
    parser.add_argument("--block-id",type=int)
    parser.add_argument("--size",type=int,default=2048)
    parser.add_argument("--out",type=Path)
    args=parser.parse_args()

    if args.child:
        if args.strategy is None or args.q is None:
            parser.error("--strategy and --q required with --child")
        print(json.dumps(run_child(
            strategy=args.strategy,q=args.q,size=args.size
        ),sort_keys=True))
        return 0

    if args.block_id is None or args.out is None:
        parser.error("--block-id and --out required")
    payload=run_block(block_id=args.block_id,size=args.size)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
    print(json.dumps(payload,sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
