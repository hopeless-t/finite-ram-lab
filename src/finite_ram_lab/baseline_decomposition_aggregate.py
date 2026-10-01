from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics
from typing import Any, Mapping

from finite_ram_lab.runner_block_aggregate import (
    _one_sided_sign_p,
    _two_sided_sign_p,
)


EXPECTED_BLOCKS = 8
FAMILY_ALPHA = 0.05
PER_TEST_ALPHA = FAMILY_ALPHA / 6.0


def _condition(block: Mapping[str, Any], q: int, seed: int) -> Mapping[str, Any]:
    return next(
        item for item in block["condition_summaries"]
        if int(item["q"]) == q and int(item["seed"]) == seed
    )


def analyze(blocks: list[Mapping[str, Any]]) -> dict[str, Any]:
    if len(blocks) != EXPECTED_BLOCKS:
        raise RuntimeError("runner_block_count_invalid")
    ids=sorted(int(block["block_id"]) for block in blocks)
    if ids != list(range(EXPECTED_BLOCKS)):
        raise RuntimeError("runner_block_ids_invalid")

    metric_names = (
        "median_baseline_vm_hwm_bytes",
        "median_work_peak_vm_hwm_bytes",
        "median_normalized_peak_growth_bytes",
    )
    rows=[]
    deltas={2:{name:[] for name in metric_names},4:{name:[] for name in metric_names}}

    for block in sorted(blocks,key=lambda item:int(item["block_id"])):
        row={
            "block_id":int(block["block_id"]),
            "runner_name":block["environment"].get("runner_name"),
            "cpu_model":block["environment"].get("cpu_model"),
        }
        for q in (2,4):
            left=_condition(block,q,474)
            right=_condition(block,q,476)
            for metric in metric_names:
                delta=float(right[metric])-float(left[metric])
                deltas[q][metric].append(delta)
                row[f"q{q}_{metric}_delta_476_minus_474_bytes"]=delta

            identity = (
                row[f"q{q}_median_work_peak_vm_hwm_bytes_delta_476_minus_474_bytes"]
                - row[f"q{q}_median_baseline_vm_hwm_bytes_delta_476_minus_474_bytes"]
            )
            row[f"q{q}_normalized_identity_residual_bytes"] = (
                row[f"q{q}_median_normalized_peak_growth_bytes_delta_476_minus_474_bytes"]
                - identity
            )
        rows.append(row)

    tests={}
    classifications={}
    for q in (2,4):
        normalized=_one_sided_sign_p(
            deltas[q]["median_normalized_peak_growth_bytes"],
            "negative",
        )
        baseline=_two_sided_sign_p(
            deltas[q]["median_baseline_vm_hwm_bytes"]
        )
        work=_two_sided_sign_p(
            deltas[q]["median_work_peak_vm_hwm_bytes"]
        )
        for result in (normalized,baseline,work):
            result["significant"]=result["p"] <= PER_TEST_ALPHA

        tests[f"q{q}_normalized_negative"]=normalized
        tests[f"q{q}_baseline_two_sided"]=baseline
        tests[f"q{q}_absolute_work_two_sided"]=work

        if work["significant"] and baseline["significant"]:
            label="MIXED_ABSOLUTE_AND_BASELINE_EFFECT"
        elif work["significant"]:
            label="ABSOLUTE_WORK_PEAK_EFFECT"
        elif baseline["significant"]:
            label="BASELINE_NORMALIZATION_EFFECT"
        elif normalized["significant"]:
            label="NORMALIZED_EFFECT_COMPONENT_UNRESOLVED"
        else:
            label="NO_SEED_EFFECT_RESOLVED"
        classifications[f"q{q}"]=label

    summaries={}
    for q in (2,4):
        summaries[f"q{q}"]={
            "median_baseline_delta_bytes":statistics.median(
                deltas[q]["median_baseline_vm_hwm_bytes"]
            ),
            "median_absolute_work_peak_delta_bytes":statistics.median(
                deltas[q]["median_work_peak_vm_hwm_bytes"]
            ),
            "median_normalized_peak_delta_bytes":statistics.median(
                deltas[q]["median_normalized_peak_growth_bytes"]
            ),
            "max_abs_identity_residual_bytes":max(
                abs(row[f"q{q}_normalized_identity_residual_bytes"])
                for row in rows
            ),
        }

    return {
        "schema":"finite-ram-lab.baseline-decomposition-aggregate/v0.1",
        "claim_ceiling":"GITHUB_HOSTED_BLOCK_NORMALIZATION_DECOMPOSITION",
        "runner_block_count":EXPECTED_BLOCKS,
        "family_alpha":FAMILY_ALPHA,
        "per_test_bonferroni_alpha":PER_TEST_ALPHA,
        "block_rows":rows,
        "delta_summaries":summaries,
        "tests":tests,
        "classifications":classifications,
    }


def main() -> int:
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
