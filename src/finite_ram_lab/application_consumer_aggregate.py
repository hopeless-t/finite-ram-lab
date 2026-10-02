from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping


EXPECTED_Q=(2,4,7)


def aggregate_receipts(receipts:list[Mapping[str,Any]])->dict[str,Any]:
    if len(receipts)!=len(EXPECTED_Q):
        raise RuntimeError("application_receipt_count_invalid")

    by_q={}
    for receipt in receipts:
        if receipt.get("schema")!="finite-ram-lab.application-execution-receipt/v0.1":
            raise RuntimeError("application_receipt_schema_invalid")
        if not receipt.get("contract_consistent"):
            raise RuntimeError("application_contract_inconsistent")
        if not receipt["execution"].get("semantic_exact"):
            raise RuntimeError("application_semantic_gate_failed")
        q=int(receipt["decision"]["selected_q"])
        if q in by_q:
            raise RuntimeError("duplicate_selected_q")
        by_q[q]=receipt

    if tuple(sorted(by_q))!=EXPECTED_Q:
        raise RuntimeError("expected_q_coverage_invalid")

    rows=[]
    exceedance_q=[]
    for q in EXPECTED_Q:
        receipt=by_q[q]
        boundary=receipt["boundary_check"]
        classification=boundary["classification"]
        if classification=="EXCEEDS_CALIBRATED_BOUNDARY":
            exceedance_q.append(q)
        rows.append({
            "q":q,
            "requested_peak_budget_bytes":int(receipt["request"]["peak_budget_bytes"]),
            "declared_empirical_max_peak_bytes":int(boundary["declared_empirical_max_peak_bytes"]),
            "observed_peak_bytes":int(boundary["observed_peak_bytes"]),
            "overrun_bytes":int(boundary["overrun_bytes"]),
            "headroom_bytes":int(boundary["headroom_bytes"]),
            "boundary_classification":classification,
            "sample_count":int(receipt["decision"]["sample_count"]),
            "rank_coverage_floor":float(
                receipt["decision"]["rank_max_one_step_predictive_coverage_floor"]
            ),
            "work_seconds":float(receipt["execution"]["work_seconds"]),
            "output_sha256":receipt["execution"]["output_sha256"],
        })

    digests={row["output_sha256"] for row in rows}
    if len(digests)!=1:
        raise RuntimeError("cross_q_output_digest_mismatch")

    return {
        "schema":"finite-ram-lab.application-consumer-dogfood/v0.1",
        "status":"PASS",
        "claim_ceiling":"APPLICATION_LEVEL_REPAIRED_GOVERNOR_DOGFOOD",
        "consumer_count":len(rows),
        "selected_q":list(EXPECTED_Q),
        "rows":rows,
        "exceedance_q":exceedance_q,
        "all_contracts_consistent":True,
        "all_semantics_exact":True,
        "cross_q_output_digest":next(iter(digests)),
        "classification":(
            "APPLICATION_CONSUMER_LOOP_PASS"
            if not exceedance_q
            else "APPLICATION_CONSUMER_LOOP_PASS_WITH_BOUNDARY_EXCEEDANCE"
        ),
    }


def main()->int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--receipts-dir",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()

    receipts=[
        json.loads(path.read_text())
        for path in sorted(args.receipts_dir.glob("*-application-receipt.json"))
    ]
    result=aggregate_receipts(receipts)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
