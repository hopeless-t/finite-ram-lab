"""Rebuild the rare-state trial census from four immutable Actions downloads.

Input directories are gh-run-download extractions, never experiment launchers.
Usage: python analysis/rare_specimens.py --raw /tmp/frl-rare-raw
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

RUNS = {"ga": "36563233676", "gf": "36577573774", "g0": "36591417373", "spawn": "36595481746"}
FIELDS = [
    "specimen_id", "experiment", "run", "block", "identity", "arm", "capacity_pages",
    "argv_token_width", "stratum", "phase", "valid", "pre_current_pages",
    "pre_current_semantics", "migration_delta_pages", "first_touch_delta_pages",
    "first_touch_semantics", "exact_zero", "q64_first", "depth_to_next_q64",
    "depth_semantics", "VmPTE_delta_kib", "PTE_growth", "cpu_match",
    "prep_cpu", "stock_cpu", "primer_qualified", "primer_touch_number",
    "strict_exact_recovery", "terminal_pattern_match", "negative_accounting_delta",
    "negative_delta_min_pages", "THP_receipt", "mTHP_receipt", "source_path", "source_sha256",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def row_for(family: str, path: Path, raw_root: Path) -> dict:
    x = json.loads(path.read_text())
    r = {key: None for key in FIELDS}
    r.update(experiment=family.upper(), run=RUNS[family], block=x["block"], identity=x["identity"],
             specimen_id=f"{family}:{RUNS[family]}:{x['block']}:{x['identity']}",
             source_path=str(path.relative_to(raw_root)), source_sha256=sha(path),
             migration_delta_pages=x.get("migration_delta_pages"), prep_cpu=x.get("prep_cpu"),
             stock_cpu=x.get("stock_cpu"))
    if family == "spawn":
        touches = x.get("observed_pattern_touches", [])
        first = touches[0] if touches else None
        all_touches = x.get("calibration_touches", []) + x.get("bait_touches", []) + touches
        negatives = [t["delta_pages"] for t in all_touches if t.get("delta_pages", 0) < 0]
        r.update(arm=x["arm_id"], capacity_pages=None, argv_token_width=None,
                 stratum="CONSTRUCTED", phase="POST_PRIMER", valid=True,
                 pre_current_pages=x.get("post_migration_current_pages"),
                 pre_current_semantics="post_migration_before_calibration",
                 first_touch_delta_pages=first.get("delta_pages") if first else None,
                 first_touch_semantics="constructed_terminal_target_after_primer_and_bait",
                 exact_zero=first.get("delta_pages") == 0 if first else None,
                 q64_first=first.get("delta_pages") == 64 if first else None,
                 depth_to_next_q64=next((i for i,t in enumerate(touches) if t.get("delta_pages") == 64), None),
                 depth_semantics="terminal_pattern_index_zero_based; conditional_on_observed_primer",
                 VmPTE_delta_kib=first.get("vmpte_delta_kib") if first else None,
                 PTE_growth=any(t.get("vmpte_delta_kib", 0) > 0 for t in all_touches),
                 cpu_match=all(t.get("observed_cpu") == x.get("stock_cpu") and t.get("worker_error") == 0 for t in all_touches),
                 primer_qualified=x.get("primer_status") == "FOUND", primer_touch_number=x.get("primer_touch_number"),
                 strict_exact_recovery=x.get("exact_recovery"),
                 terminal_pattern_match=["ZERO" if t.get("delta_pages") == 0 else "Q64" if t.get("delta_pages") == 64 else "OTHER" for t in touches] == x.get("expected_pattern") if touches else None,
                 negative_accounting_delta=bool(negatives), negative_delta_min_pages=min(negatives) if negatives else None)
    else:
        delta = x.get("first_touch_delta_pages")
        depth = x.get("residual_depth_candidate") if family == "ga" else None
        if family == "g0" and delta == 0 and x.get("biopsy_valid"):
            depth = 1 if x.get("second_q64_pass") else None
        r.update(arm=x.get("arm_id") or (f"CAP{x['capacity_pages']}" if family == "gf" else "CAP70"),
                 capacity_pages=x.get("capacity_pages", 70 if family == "ga" else None),
                 argv_token_width=len(x["argv_token"]) if family == "g0" else (len(str(x["capacity_pages"])) if family == "gf" else 2),
                 stratum=x.get("stratum"), phase=x.get("phase"), valid=x.get("valid"),
                 pre_current_pages=x.get("pre_current_pages"), pre_current_semantics="before_first_fault_gate",
                 first_touch_delta_pages=delta, first_touch_semantics="natural_first_fault",
                 exact_zero=delta == 0 if delta is not None else None,
                 q64_first=x.get("first_q64_pass", x.get("q64_pass")),
                 depth_to_next_q64=depth,
                 depth_semantics=("later_Q64_touch_minus_one_candidate" if family == "ga" else
                                  "exact_1" if family == "g0" and depth == 1 else
                                  "at_least_2_second_touch_zero" if family == "g0" and delta == 0 and x.get("second_touch_delta_pages") == 0 else None),
                 VmPTE_delta_kib=x.get("first_vmpte_delta_kib"),
                 PTE_growth=x.get("first_vmpte_delta_kib", 0) > 0 if family == "g0" else None,
                 cpu_match=x.get("cpu_match"),
                 negative_accounting_delta=(any(v < 0 for v in x["biopsy_delta_sequence"] if isinstance(v, (int,float)))
                                            if family == "ga" and x.get("biopsy_delta_sequence") else None))
    return r


def build(raw_root: Path, output: Path) -> list[dict]:
    rows = []
    for family in RUNS:
        files = sorted((raw_root / family).glob("*/trial-*.json"))
        if not files:
            raise FileNotFoundError(f"no trial JSON for {family}")
        for p in files:
            row = row_for(family, p, raw_root)
            env_path = p.parent / "environment.json"
            if env_path.exists():
                thp = json.loads(env_path.read_text()).get("transparent_hugepage")
                if thp:
                    row["THP_receipt"] = thp.get("enabled")
                    row["mTHP_receipt"] = ";".join(f"{k}={v}" for k, v in sorted(thp.items()) if k != "enabled")
            rows.append(row)
    ids = [r["specimen_id"] for r in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate specimen identity")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return rows


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--raw", type=Path, required=True)
    p.add_argument("--out", type=Path, default=Path("analysis/inputs/RARE-SPECIMEN-CENSUS-v1.csv"))
    args = p.parse_args()
    rows = build(args.raw, args.out)
    print(json.dumps({"rows": len(rows), "by_experiment": Counter(r["experiment"] for r in rows),
                      "valid_low_exact_zero": Counter(r["experiment"] for r in rows if r["stratum"] == "LOW" and r["valid"] and r["exact_zero"]),
                      "output_sha256": sha(args.out)}, indent=2))


if __name__ == "__main__":
    main()
