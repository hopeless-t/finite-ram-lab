from __future__ import annotations

from pathlib import Path
from typing import Any


CRITICAL_B405_PROBES = (
    "frl_pc_try64",
    "frl_pc_uncharge_owner",
)


def parse_kprobe_profile_text(text: str) -> dict[str, dict[str, int]]:
    rows: dict[str, dict[str, int]] = {}
    for raw in text.splitlines():
        parts = raw.split()
        if len(parts) != 3:
            continue
        name, hits, missed = parts
        try:
            rows[name] = {
                "hits": int(hits),
                "missed": int(missed),
            }
        except ValueError:
            continue
    return rows


def summarize_probe_coverage(
    profile_paths: list[Path],
    *,
    critical_probes: tuple[str, ...] = CRITICAL_B405_PROBES,
) -> dict[str, Any]:
    profiles: list[dict[str, Any]] = []
    totals: dict[str, dict[str, int]] = {}

    for path in sorted(profile_paths):
        rows = parse_kprobe_profile_text(
            path.read_text(encoding="utf-8", errors="replace")
        )
        profiles.append(
            {
                "path": path.as_posix(),
                "probes": rows,
            }
        )
        for name, values in rows.items():
            item = totals.setdefault(name, {"hits": 0, "missed": 0})
            item["hits"] += int(values["hits"])
            item["missed"] += int(values["missed"])

    missing_critical = [
        name for name in critical_probes if name not in totals
    ]
    critical_missed = {
        name: int(totals.get(name, {}).get("missed", 0))
        for name in critical_probes
    }
    missed_total = sum(critical_missed.values())

    return {
        "schema_version": "probe-coverage-summary-v1",
        "profile_count": len(profiles),
        "critical_probes": list(critical_probes),
        "missing_critical_probes": missing_critical,
        "critical_missed": critical_missed,
        "critical_missed_total": missed_total,
        "coverage_pass": (
            len(profiles) > 0
            and not missing_critical
            and missed_total == 0
        ),
        "totals": totals,
        "profiles": profiles,
    }
