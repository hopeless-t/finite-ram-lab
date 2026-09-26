from __future__ import annotations

import argparse
import csv
import json
import random
import re
from pathlib import Path
from statistics import median
from typing import Any

import numpy as np
import pandas as pd


FILENAME_RE = re.compile(
    r"timeline-(?P<order>\d+)-high(?P<high>\d+)-rep(?P<rep>\d+)\.json$"
)


def load_spec(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def make_schedule(spec: dict[str, Any]) -> list[dict[str, int]]:
    levels = [int(x) for x in spec["memory_high_mib"]]
    repeats = int(spec["repeats_per_level"])
    rng = random.Random(int(spec["schedule_seed"]))

    rows = [
        {"repeat": repeat, "memory_high_mib": level}
        for level in levels
        for repeat in range(repeats)
    ]
    rng.shuffle(rows)
    return [
        {"order": i, **row}
        for i, row in enumerate(rows)
    ]


def write_schedule(
    spec: dict[str, Any],
    out: str | Path,
) -> None:
    rows = make_schedule(spec)
    path = Path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "order",
                "repeat",
                "memory_high_mib",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def _phase(
    timeline: list[dict[str, Any]],
    name: str,
) -> dict[str, Any]:
    for event in timeline:
        if event["phase"] == name:
            return event
    raise ValueError(f"missing phase {name}")


def _psi_totals(text: str) -> dict[str, int]:
    out = {"some": 0, "full": 0}
    for line in text.splitlines():
        parts = line.split()
        if not parts:
            continue
        label = parts[0]
        if label not in out:
            continue
        for part in parts[1:]:
            if part.startswith("total="):
                out[label] = int(part.split("=", 1)[1])
    return out


def _metric_delta(
    baseline: dict[str, Any],
    later: dict[str, Any],
    key: str,
) -> int:
    return int(
        later["os"]["memory_stat"].get(key, 0)
        - baseline["os"]["memory_stat"].get(key, 0)
    )


def _event_delta(
    baseline: dict[str, Any],
    later: dict[str, Any],
    key: str,
) -> int:
    return int(
        later["os"]["memory_events"].get(key, 0)
        - baseline["os"]["memory_events"].get(key, 0)
    )


def trial_row(path: Path) -> dict[str, Any]:
    match = FILENAME_RE.search(path.name)
    if not match:
        raise ValueError(f"unexpected filename: {path.name}")

    data = json.loads(path.read_text())
    timeline = data["timeline"]
    baseline = _phase(timeline, "BASELINE")
    burst = _phase(timeline, "BURST_ALLOC")
    retouch = _phase(timeline, "HOTSET_RETOUCH")
    release = _phase(timeline, "BURST_RELEASE")

    psi0 = _psi_totals(baseline["os"]["memory_pressure"])
    psi1 = _psi_totals(retouch["os"]["memory_pressure"])

    return {
        "order": int(match.group("order")),
        "repeat": int(match.group("rep")),
        "memory_high_mib": int(match.group("high")),
        "status": data["status"],
        "retouch_latency_ms": float(
            retouch.get("phase_latency_ns", 0)
        )
        / 1e6,
        "burst_alloc_latency_ms": float(
            burst.get("phase_latency_ns", 0)
        )
        / 1e6,
        "release_latency_ms": float(
            release.get("phase_latency_ns", 0)
        )
        / 1e6,
        "retouch_memory_current_mib": (
            float(retouch["os"]["memory_current"])
            / (1024 * 1024)
        ),
        "swap_growth_mib": (
            float(
                retouch["os"]["memory_swap_current"]
                - baseline["os"]["memory_swap_current"]
            )
            / (1024 * 1024)
        ),
        "high_events_delta": _event_delta(
            baseline,
            retouch,
            "high",
        ),
        "oom_delta": _event_delta(
            baseline,
            retouch,
            "oom",
        ),
        "oom_kill_delta": _event_delta(
            baseline,
            retouch,
            "oom_kill",
        ),
        "pgscan_delta": _metric_delta(
            baseline,
            retouch,
            "pgscan",
        ),
        "pgsteal_delta": _metric_delta(
            baseline,
            retouch,
            "pgsteal",
        ),
        "pgfault_delta": _metric_delta(
            baseline,
            retouch,
            "pgfault",
        ),
        "pgmajfault_delta": _metric_delta(
            baseline,
            retouch,
            "pgmajfault",
        ),
        "psi_some_total_delta_us": int(
            psi1["some"] - psi0["some"]
        ),
        "psi_full_total_delta_us": int(
            psi1["full"] - psi0["full"]
        ),
    }


def _bootstrap_median_ci(
    values: np.ndarray,
    resamples: int,
    seed: int,
) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    n = len(values)
    estimates = np.empty(resamples, dtype=float)
    for i in range(resamples):
        sample = values[
            rng.integers(
                0,
                n,
                size=n,
            )
        ]
        estimates[i] = float(np.median(sample))
    lo, hi = np.quantile(
        estimates,
        [0.025, 0.975],
    )
    return float(lo), float(hi)


def aggregate(
    spec: dict[str, Any],
    input_dir: str | Path,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    root = Path(input_dir)
    rows = [
        trial_row(path)
        for path in sorted(root.glob("timeline-*.json"))
    ]
    trials = pd.DataFrame(rows)
    if trials.empty:
        raise ValueError("no trial evidence found")

    levels = [int(x) for x in spec["memory_high_mib"]]
    repeats = int(spec["repeats_per_level"])
    bootstrap_resamples = int(
        spec.get("bootstrap_resamples", 1000)
    )

    summary_rows = []
    for level in levels:
        group = trials[
            trials["memory_high_mib"] == level
        ].copy()
        if len(group) != repeats:
            raise ValueError(
                f"level {level} expected {repeats} "
                f"trials, got {len(group)}"
            )
        latency = group[
            "retouch_latency_ms"
        ].to_numpy(dtype=float)
        ci_lo, ci_hi = _bootstrap_median_ci(
            latency,
            bootstrap_resamples,
            int(spec["schedule_seed"]) + level,
        )
        summary_rows.append(
            {
                "memory_high_mib": level,
                "trials": len(group),
                "median_hotset_retouch_ms": float(
                    np.median(latency)
                ),
                "p90_hotset_retouch_ms": float(
                    np.quantile(latency, 0.90)
                ),
                "median_ci95_low_ms": ci_lo,
                "median_ci95_high_ms": ci_hi,
                "median_swap_growth_mib": float(
                    median(
                        group[
                            "swap_growth_mib"
                        ].tolist()
                    )
                ),
                "median_high_events_delta": float(
                    median(
                        group[
                            "high_events_delta"
                        ].tolist()
                    )
                ),
                "median_pgscan_delta": float(
                    median(
                        group[
                            "pgscan_delta"
                        ].tolist()
                    )
                ),
                "median_pgsteal_delta": float(
                    median(
                        group[
                            "pgsteal_delta"
                        ].tolist()
                    )
                ),
                "median_pgfault_delta": float(
                    median(
                        group[
                            "pgfault_delta"
                        ].tolist()
                    )
                ),
                "median_pgmajfault_delta": float(
                    median(
                        group[
                            "pgmajfault_delta"
                        ].tolist()
                    )
                ),
                "median_psi_some_delta_us": float(
                    median(
                        group[
                            "psi_some_total_delta_us"
                        ].tolist()
                    )
                ),
                "median_psi_full_delta_us": float(
                    median(
                        group[
                            "psi_full_total_delta_us"
                        ].tolist()
                    )
                ),
            }
        )

    summary = pd.DataFrame(summary_rows)

    checks = {
        "complete_schedule": len(trials)
        == len(levels) * repeats,
        "all_trials_pass": bool(
            (trials["status"] == "PASS").all()
        ),
        "no_oom": bool(
            (
                trials["oom_delta"]
                + trials["oom_kill_delta"]
            ).eq(0).all()
        ),
        "all_levels_present": set(
            trials["memory_high_mib"].astype(int)
        )
        == set(levels),
    }

    meta = {
        "experiment_id": "CHAR-001",
        "status": (
            "PASS"
            if all(checks.values())
            else "FAIL"
        ),
        "checks": checks,
        "levels_mib": levels,
        "repeats_per_level": repeats,
        "total_trials": len(trials),
        "bootstrap_resamples": bootstrap_resamples,
    }
    return trials, summary, meta


def write_aggregate(
    spec: dict[str, Any],
    input_dir: str | Path,
    trials_out: str | Path,
    summary_out: str | Path,
    meta_out: str | Path,
) -> dict[str, Any]:
    trials, summary, meta = aggregate(
        spec,
        input_dir,
    )
    Path(trials_out).parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    trials.sort_values("order").to_csv(
        trials_out,
        index=False,
    )
    summary.to_csv(
        summary_out,
        index=False,
    )
    Path(meta_out).write_text(
        json.dumps(
            meta,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    return meta


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(
        dest="command",
        required=True,
    )

    p = sub.add_parser("schedule")
    p.add_argument("--spec", required=True)
    p.add_argument("--out", required=True)

    p = sub.add_parser("aggregate")
    p.add_argument("--spec", required=True)
    p.add_argument("--input-dir", required=True)
    p.add_argument("--trials-out", required=True)
    p.add_argument("--summary-out", required=True)
    p.add_argument("--meta-out", required=True)

    args = parser.parse_args()
    spec = load_spec(args.spec)

    if args.command == "schedule":
        write_schedule(
            spec,
            args.out,
        )
        return

    meta = write_aggregate(
        spec,
        args.input_dir,
        args.trials_out,
        args.summary_out,
        args.meta_out,
    )
    print(
        json.dumps(
            meta,
            indent=2,
            sort_keys=True,
        )
    )
    if meta["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
