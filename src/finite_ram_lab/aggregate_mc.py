from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from .mc import percentile


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--markdown")
    args = parser.parse_args()

    files = sorted(Path(args.input).rglob("mc-*.json"))
    if not files:
        raise SystemExit("no MC shard files found")

    by_family: dict[str, list[dict]] = defaultdict(list)
    sources = []
    for path in files:
        data = json.loads(path.read_text())
        by_family[data["family"]].extend(data["rows"])
        sources.append(str(path))

    families = {}
    for family, rows in sorted(by_family.items()):
        gaps = [float(r["fault_rate_gap"]) for r in rows]
        families[family] = {
            "trials": len(rows),
            "mean_fault_rate_gap": sum(gaps) / len(gaps),
            "p50_fault_rate_gap": percentile(gaps, 0.50),
            "p90_fault_rate_gap": percentile(gaps, 0.90),
            "p99_fault_rate_gap": percentile(gaps, 0.99),
            "max_fault_rate_gap": max(gaps),
        }

    result = {
        "experiment_id": "MC-001",
        "source_files": sources,
        "families": families,
        "total_trials": sum(v["trials"] for v in families.values()),
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    if args.markdown:
        lines = [
            "# MC-001 aggregate",
            "",
            f"Total trials: **{result['total_trials']}**",
            "",
            "| Family | Trials | Mean gap | P90 gap | P99 gap | Max gap |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
        for family, s in families.items():
            lines.append(
                f"| {family} | {s['trials']} | {s['mean_fault_rate_gap']:.4f} | "
                f"{s['p90_fault_rate_gap']:.4f} | {s['p99_fault_rate_gap']:.4f} | "
                f"{s['max_fault_rate_gap']:.4f} |"
            )
        Path(args.markdown).write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
