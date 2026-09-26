from __future__ import annotations

import argparse
import json
from pathlib import Path

from .exp002_workload import run as run_exp002


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--arm", choices=("correct_pageout", "no_hint"), required=True)
    p.add_argument("--hot-identity", choices=("A", "B"), required=True)
    p.add_argument("--region-mib", type=int, required=True)
    p.add_argument("--pageout-mib", type=int, required=True)
    p.add_argument("--burst-mib", type=int, required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    result = run_exp002(
        args.arm,
        args.hot_identity,
        args.region_mib,
        args.pageout_mib,
        args.burst_mib,
    )
    result["experiment_id"] = "VAL-003"
    result["source_workload"] = "EXP-002 matched semantic PAGEOUT workload"

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    print(json.dumps({
        "status": result["status"],
        "arm": result["arm"],
        "hot_identity": result["hot_identity"],
        "hot_retouch_ms": result["hot_retouch_ns"] / 1e6,
    }, indent=2, sort_keys=True))

    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
