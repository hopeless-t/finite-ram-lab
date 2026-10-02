from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping


PARETO_Q=(2,4,7)


def _load(path:Path)->dict[str,Any]:
    return json.loads(path.read_text())


def calibrated_points(
    b490:Mapping[str,Any],
    b492:Mapping[str,Any],
)->list[dict[str,Any]]:
    if b490.get("schema")!="finite-ram-lab.b490-result/v0.1":
        raise RuntimeError("b490_schema_invalid")
    if b492.get("schema")!="finite-ram-lab.b492-result/v0.1":
        raise RuntimeError("b492_schema_invalid")

    latency={
        int(row["selected_q"]):float(row["median_latency_seconds"])
        for row in b490["breakpoints"]
    }
    points=[]
    for q in PARETO_Q:
        row=next(item for item in b492["rows"] if int(item["q"])==q)
        points.append({
            "q":q,
            "empirical_max_peak_bytes":int(row["updated_empirical_max_peak_bytes"]),
            "sample_count":int(row["updated_sample_count"]),
            "rank_max_one_step_predictive_coverage_floor":float(
                row["updated_rank_max_one_step_predictive_coverage_floor"]
            ),
            "median_latency_seconds":latency[q],
        })
    return points


def select_q(
    b490:Mapping[str,Any],
    b492:Mapping[str,Any],
    *,
    peak_budget_bytes:int,
    minimum_rank_coverage:float=0.95,
)->dict[str,Any]:
    if peak_budget_bytes<0:
        raise ValueError("peak_budget_invalid")
    if not (0.0<minimum_rank_coverage<1.0):
        raise ValueError("minimum_rank_coverage_invalid")

    points=calibrated_points(b490,b492)
    eligible=[
        row for row in points
        if row["empirical_max_peak_bytes"]<=peak_budget_bytes
        and row["rank_max_one_step_predictive_coverage_floor"]>=minimum_rank_coverage
    ]
    if not eligible:
        raise RuntimeError("no_updated_repaired_q_fits_budget")

    selected=min(
        eligible,
        key=lambda row:(
            row["median_latency_seconds"],
            row["empirical_max_peak_bytes"],
            row["q"],
        ),
    )
    return {
        "schema":"finite-ram-lab.repaired-coverage-aware-decision/v0.2",
        "implementation":"TILED_WHERE",
        "policy_version":"v2.1",
        "claim_ceiling":"NON_DRIFT_UPDATED_REPAIRED_GOVERNOR_V2_1",
        "peak_budget_bytes":peak_budget_bytes,
        "minimum_rank_coverage":minimum_rank_coverage,
        "selected_q":selected["q"],
        "selected_empirical_max_peak_bytes":selected["empirical_max_peak_bytes"],
        "selected_sample_count":selected["sample_count"],
        "selected_rank_max_one_step_predictive_coverage_floor":selected[
            "rank_max_one_step_predictive_coverage_floor"
        ],
        "selected_median_latency_seconds":selected["median_latency_seconds"],
        "latency_source":"B490",
        "evidence_state_source":"B492",
    }


def build_policy(
    b490:Mapping[str,Any],
    b492:Mapping[str,Any],
    *,
    minimum_rank_coverage:float=0.95,
)->dict[str,Any]:
    points=calibrated_points(b490,b492)
    breakpoints=[]
    last_q=None
    for budget in sorted({row["empirical_max_peak_bytes"] for row in points}):
        decision=select_q(
            b490,b492,
            peak_budget_bytes=budget,
            minimum_rank_coverage=minimum_rank_coverage,
        )
        if decision["selected_q"]!=last_q:
            breakpoints.append({
                "minimum_peak_budget_bytes":budget,
                "selected_q":decision["selected_q"],
                "sample_count":decision["selected_sample_count"],
                "rank_max_one_step_predictive_coverage_floor":decision[
                    "selected_rank_max_one_step_predictive_coverage_floor"
                ],
                "median_latency_seconds":decision["selected_median_latency_seconds"],
            })
            last_q=decision["selected_q"]

    return {
        "schema":"finite-ram-lab.repaired-coverage-aware-governor/v0.2",
        "status":"SOFTWARE_GOVERNOR",
        "implementation":"TILED_WHERE",
        "policy_version":"v2.1",
        "claim_ceiling":"NON_DRIFT_UPDATED_REPAIRED_GOVERNOR_V2_1",
        "minimum_rank_coverage":minimum_rank_coverage,
        "pareto_q":list(PARETO_Q),
        "dominated_q_excluded":[1],
        "points":points,
        "breakpoints":breakpoints,
        "latency_source":"B490",
        "evidence_state_source":"B492",
    }


def main()->int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--b490",type=Path,required=True)
    parser.add_argument("--b492",type=Path,required=True)
    parser.add_argument("--minimum-rank-coverage",type=float,default=0.95)
    parser.add_argument("--peak-budget-bytes",type=int)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()

    b490=_load(args.b490)
    b492=_load(args.b492)
    if args.peak_budget_bytes is None:
        payload=build_policy(
            b490,b492,
            minimum_rank_coverage=args.minimum_rank_coverage,
        )
    else:
        payload=select_q(
            b490,b492,
            peak_budget_bytes=args.peak_budget_bytes,
            minimum_rank_coverage=args.minimum_rank_coverage,
        )

    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
    print(json.dumps(payload,sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
