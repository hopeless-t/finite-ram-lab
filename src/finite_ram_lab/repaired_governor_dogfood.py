from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

from finite_ram_lab.repaired_governor_v2 import select_q
from finite_ram_lab.repaired_q_frontier import _run_fresh_child
from finite_ram_lab.runner_block_probe import environment_fingerprint


Q_VALUES=(2,4,7)
RUNNER_BLOCKS=8
ORDERS=((2,4,7),(7,4,2),(4,2,7),(7,2,4))


def _load(path:Path)->dict[str,Any]:
    return json.loads(path.read_text())


def _boundary_map(b490:Mapping[str,Any])->dict[int,int]:
    if b490.get("schema")!="finite-ram-lab.b490-result/v0.1":
        raise RuntimeError("b490_schema_invalid")
    return {
        int(row["selected_q"]):int(row["minimum_peak_budget_bytes"])
        for row in b490["breakpoints"]
    }


def boundary_checks(b489:Mapping[str,Any],b490:Mapping[str,Any])->list[dict[str,Any]]:
    boundaries=_boundary_map(b490)
    checks=[]

    # Below q2: no 95%-qualified repaired q fits.
    try:
        select_q(
            b489,
            peak_budget_bytes=boundaries[2]-1,
            minimum_rank_coverage=0.95,
        )
    except RuntimeError as exc:
        if str(exc)!="no_coverage_qualified_repaired_q_fits_budget":
            raise
        checks.append({
            "budget_bytes":boundaries[2]-1,
            "expected":"NO_ELIGIBLE_Q",
            "observed":"NO_ELIGIBLE_Q",
            "pass":True,
        })
    else:
        raise RuntimeError("below_q2_boundary_did_not_fail_closed")

    expected=(
        (boundaries[2],2),
        (boundaries[4]-1,2),
        (boundaries[4],4),
        (boundaries[7]-1,4),
        (boundaries[7],7),
    )
    for budget,q in expected:
        decision=select_q(
            b489,
            peak_budget_bytes=budget,
            minimum_rank_coverage=0.95,
        )
        observed=int(decision["selected_q"])
        checks.append({
            "budget_bytes":budget,
            "expected_q":q,
            "observed_q":observed,
            "pass":observed==q,
        })
        if observed!=q:
            raise RuntimeError(
                f"boundary_dispatch_mismatch:budget={budget}:expected={q}:observed={observed}"
            )
    return checks


def run_block(
    b489:Mapping[str,Any],
    b490:Mapping[str,Any],
    *,
    block_id:int,
    size:int=2048,
)->dict[str,Any]:
    if not (0<=block_id<RUNNER_BLOCKS):
        raise ValueError("block_id_invalid")

    checks=boundary_checks(b489,b490)
    boundaries=_boundary_map(b490)
    order=ORDERS[block_id % len(ORDERS)]
    results=[]

    for q in order:
        observed=_run_fresh_child(
            strategy="TILED_WHERE",
            q=q,
            size=size,
        )
        if not observed["semantic_exact"]:
            raise RuntimeError(f"semantic_gate_failed:q={q}:block={block_id}")
        results.append({
            "q":q,
            "declared_peak_budget_bytes":boundaries[q],
            "observed_peak_bytes":int(observed["normalized_peak_growth_bytes"]),
            "within_declared_budget":int(observed["normalized_peak_growth_bytes"])<=boundaries[q],
            "work_seconds":float(observed["work_seconds"]),
            "output_sha256":observed["output_sha256"],
        })

    digests={row["output_sha256"] for row in results}
    if len(digests)!=1:
        raise RuntimeError("cross_q_output_digest_mismatch")

    return {
        "schema":"finite-ram-lab.repaired-governor-dogfood-block/v0.1",
        "claim_ceiling":"REPAIRED_GOVERNOR_V2_BOUNDARY_DOGFOOD",
        "block_id":block_id,
        "environment":environment_fingerprint(),
        "boundary_checks":checks,
        "execution_order":list(order),
        "results":results,
        "output_sha256":next(iter(digests)),
    }


def main()->int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--b489",type=Path,required=True)
    parser.add_argument("--b490",type=Path,required=True)
    parser.add_argument("--block-id",type=int,required=True)
    parser.add_argument("--size",type=int,default=2048)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()

    payload=run_block(
        _load(args.b489),
        _load(args.b490),
        block_id=args.block_id,
        size=args.size,
    )
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
    print(json.dumps(payload,sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
