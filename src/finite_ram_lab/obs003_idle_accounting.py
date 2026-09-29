from __future__ import annotations

import argparse
import json
import os
import time
from collections import Counter
from pathlib import Path
from typing import Any

from .memcg005gc_controlled_spawn import (
    _current,
    _start,
    _stop,
    _wait_cpu,
    environment_receipt,
    geometry_receipt,
)


STATUS_KEYS = (
    "VmRSS",
    "RssAnon",
    "RssFile",
    "RssShmem",
    "VmPTE",
)


def load_spec(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _status_kib(pid: int) -> dict[str, int]:
    wanted = set(STATUS_KEYS)
    result: dict[str, int] = {}
    for line in Path(f"/proc/{pid}/status").read_text(
        encoding="utf-8"
    ).splitlines():
        if ":" not in line:
            continue
        key, rest = line.split(":", 1)
        if key not in wanted:
            continue
        parts = rest.split()
        if not parts:
            continue
        result[key] = int(parts[0])
    missing = wanted - set(result)
    if missing:
        raise ValueError(
            f"missing /proc status keys for pid={pid}: {sorted(missing)}"
        )
    return result


def _memory_stat(cg: Path) -> dict[str, int]:
    result: dict[str, int] = {}
    for line in (cg / "memory.stat").read_text(
        encoding="utf-8"
    ).splitlines():
        key, value = line.split()
        result[key] = int(value)
    return result


def classify_start_mode(
    pre_current_pages: float,
    spec: dict[str, Any],
) -> str:
    for low, high in spec["plus17_ranges"]:
        if float(low) <= pre_current_pages <= float(high):
            return "PLUS17"
    return "OTHER"


def classify_idle(
    samples: list[dict[str, Any]],
    spec: dict[str, Any],
) -> dict[str, Any]:
    if not samples:
        raise ValueError("samples must not be empty")

    start = samples[0]
    page_kib = float(spec["required_page_size"]) / 1024.0
    start_current = float(start["current_pages"])

    min_sample = min(
        samples,
        key=lambda row: float(row["current_pages"]),
    )
    current_drop = start_current - float(
        min_sample["current_pages"]
    )

    rss_start = float(start["status_kib"]["VmRSS"]) / page_kib
    rss_min = float(min_sample["status_kib"]["VmRSS"]) / page_kib
    rss_drop = rss_start - rss_min

    category_drops: dict[str, float] = {}
    for key in ("RssAnon", "RssFile", "RssShmem"):
        category_drops[key] = (
            float(start["status_kib"][key])
            - float(min_sample["status_kib"][key])
        ) / page_kib

    low = float(spec["neg17_drop_min_pages"])
    high = float(spec["neg17_drop_max_pages"])
    stable = float(spec["rss_stable_tolerance_pages"])
    matching = float(spec["rss_matching_tolerance_pages"])

    neg17_like = low <= current_drop <= high

    if neg17_like and abs(rss_drop) <= stable:
        phenotype = "IDLE_NEG17_NO_RSS_DROP"
    elif (
        neg17_like
        and rss_drop > stable
        and abs(rss_drop - current_drop) <= matching
    ):
        phenotype = "IDLE_NEG17_WITH_RSS_DROP"
    elif current_drop < float(spec["meaningful_drop_pages"]):
        phenotype = "IDLE_NO_DROP"
    else:
        phenotype = "IDLE_OTHER_DROP"

    return {
        "phenotype": phenotype,
        "current_drop_pages": current_drop,
        "min_current_at_ms": float(min_sample["elapsed_ms"]),
        "rss_drop_pages_at_min_current": rss_drop,
        "rss_category_drops_pages_at_min_current": category_drops,
        "neg17_like": neg17_like,
    }


def _sample(
    unit: dict[str, Any],
    *,
    page_size: int,
    t0_ns: int,
) -> dict[str, Any]:
    current_bytes = _current(unit["cg"])
    return {
        "elapsed_ms": (time.monotonic_ns() - t0_ns) / 1_000_000.0,
        "current_bytes": current_bytes,
        "current_pages": current_bytes / page_size,
        "status_kib": _status_kib(unit["pid"]),
        "observed_cpu": int(
            Path(f"/proc/{unit['pid']}/stat")
            .read_text(encoding="utf-8")
            .rsplit(")", 1)[1]
            .split()[36]
        ),
    }


def run_probe(
    spec: dict[str, Any],
    worker: Path,
    root: Path,
    block: int,
    identity: int,
    prep_cpu: int,
    stock_cpu: int,
) -> dict[str, Any]:
    name = (
        f"fr-obs003-{os.getenv('GITHUB_RUN_ID', 'local')}"
        f"-{block}-{identity}"
    )
    unit = _start(
        worker,
        root,
        name,
        prep_cpu,
        int(spec["max_pages"]),
        int(spec["safe_len"]),
    )
    try:
        page_size = int(spec["required_page_size"])
        geometry = geometry_receipt(unit, prep_cpu)

        pre_migration_current = _current(unit["cg"])
        pre_migration_status = _status_kib(unit["pid"])

        os.sched_setaffinity(unit["pid"], {stock_cpu})
        _wait_cpu(unit["pid"], stock_cpu)

        post_migration_current = _current(unit["cg"])
        post_migration_status = _status_kib(unit["pid"])
        start_mode = classify_start_mode(
            post_migration_current / page_size,
            spec,
        )

        start_memory_stat = _memory_stat(unit["cg"])

        t0_ns = time.monotonic_ns()
        offsets_ms = [float(x) for x in spec["sample_offsets_ms"]]
        samples: list[dict[str, Any]] = []
        min_current = post_migration_current
        first_drop_memory_stat: dict[str, int] | None = None
        first_drop_elapsed_ms: float | None = None

        for offset_ms in offsets_ms:
            target_ns = t0_ns + int(offset_ms * 1_000_000.0)
            while True:
                now = time.monotonic_ns()
                if now >= target_ns:
                    break
                remaining = (target_ns - now) / 1_000_000_000.0
                time.sleep(min(remaining, 0.0005))

            row = _sample(
                unit,
                page_size=page_size,
                t0_ns=t0_ns,
            )
            samples.append(row)

            if int(row["current_bytes"]) < min_current:
                min_current = int(row["current_bytes"])
                if first_drop_memory_stat is None:
                    first_drop_memory_stat = _memory_stat(unit["cg"])
                    first_drop_elapsed_ms = float(row["elapsed_ms"])

        final_memory_stat = _memory_stat(unit["cg"])
        classification = classify_idle(samples, spec)

        return {
            "experiment_id": spec["experiment_id"],
            "block": block,
            "identity": identity,
            "prep_cpu": prep_cpu,
            "stock_cpu": stock_cpu,
            "geometry": geometry,
            "pre_migration_current_pages": (
                pre_migration_current / page_size
            ),
            "post_migration_current_pages": (
                post_migration_current / page_size
            ),
            "migration_delta_pages": (
                post_migration_current - pre_migration_current
            ) / page_size,
            "pre_migration_status_kib": pre_migration_status,
            "post_migration_status_kib": post_migration_status,
            "start_mode": start_mode,
            "samples": samples,
            "start_memory_stat": start_memory_stat,
            "first_drop_memory_stat": first_drop_memory_stat,
            "first_drop_elapsed_ms": first_drop_elapsed_ms,
            "final_memory_stat": final_memory_stat,
            **classification,
        }
    finally:
        _stop(unit)


def analyze(
    spec: dict[str, Any],
    trials: list[dict[str, Any]],
) -> dict[str, Any]:
    expected = {
        (block, identity)
        for block in range(int(spec["runner_blocks"]))
        for identity in range(int(spec["identities_per_block"]))
    }
    got = {
        (int(row["block"]), int(row["identity"]))
        for row in trials
    }
    if got != expected:
        raise ValueError("incomplete OBS-003 matrix")

    by_start: dict[str, dict[str, Any]] = {}
    for mode in ("PLUS17", "OTHER"):
        selected = [row for row in trials if row["start_mode"] == mode]
        by_start[mode] = {
            "n": len(selected),
            "phenotypes": dict(
                Counter(str(row["phenotype"]) for row in selected)
            ),
            "neg17_like": sum(
                bool(row["neg17_like"]) for row in selected
            ),
            "current_drop_pages": [
                float(row["current_drop_pages"])
                for row in selected
            ],
        }

    return {
        "experiment_id": spec["experiment_id"],
        "stage": spec["stage"],
        "n": len(trials),
        "by_start_mode": by_start,
        "phenotypes": dict(
            Counter(str(row["phenotype"]) for row in trials)
        ),
        "trials": trials,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run-block")
    run.add_argument("--spec", required=True)
    run.add_argument("--block", type=int, required=True)
    run.add_argument("--worker", required=True)
    run.add_argument("--out-root", required=True)

    agg = sub.add_parser("aggregate")
    agg.add_argument("--spec", required=True)
    agg.add_argument("--input-root", required=True)
    agg.add_argument("--json-out", required=True)

    args = parser.parse_args()
    spec = load_spec(args.spec)

    if args.cmd == "run-block":
        cpus = sorted(os.sched_getaffinity(0))
        if len(cpus) < 3:
            raise RuntimeError("OBS-003 requires at least 3 CPUs")
        controller_cpu, prep_cpu, stock_cpu = (
            cpus[0],
            cpus[1],
            cpus[-1],
        )
        os.sched_setaffinity(0, {controller_cpu})

        root = Path(args.out_root)
        root.mkdir(parents=True, exist_ok=True)
        worker = Path(args.worker).resolve()

        (root / "environment.json").write_text(
            json.dumps(
                environment_receipt(worker, cpus),
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

        for identity in range(int(spec["identities_per_block"])):
            trial_root = root / f"id-{identity}"
            trial_root.mkdir(parents=True, exist_ok=True)
            row = run_probe(
                spec,
                worker,
                trial_root,
                args.block,
                identity,
                prep_cpu,
                stock_cpu,
            )
            (root / f"trial-{args.block}-{identity}.json").write_text(
                json.dumps(row, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        return

    trials = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(
            Path(args.input_root).rglob("trial-*.json")
        )
    ]
    result = analyze(spec, trials)
    out = Path(args.json_out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "n": result["n"],
                "by_start_mode": result["by_start_mode"],
                "phenotypes": result["phenotypes"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
