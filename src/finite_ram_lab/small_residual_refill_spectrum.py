from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any

from .memcg005gc_controlled_spawn import (
    _stop,
    _wait_cpu,
    environment_receipt,
    geometry_receipt,
)
from .startup_stock_seed_cpuset_falsifier import (
    _cpuset_effective,
    _expand_cpuset,
    _start_cpuset_constrained,
)
from .startup_stock_seed_phase import (
    Q64_EVENT,
    _delta_counts,
    _profile_counts,
)
from .transaction_trace_observer import (
    TX_MARKER_RE,
    _event_row,
)
from .transactional_spawn_native import (
    observed_window,
    touch_with_transaction_marker,
    write_marker,
)


REFILL_EVENT = "frl_refill_spectrum"
STARTUP_TOUCH = 91
RELEASE_TOUCH = 92


def load_spec(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _probe_dir(trace_path: Path, event: str) -> Path:
    return trace_path.parent / "events" / "kprobes" / event


def prepare_probes(trace_path: Path) -> None:
    q64 = _probe_dir(trace_path, Q64_EVENT)
    refill = _probe_dir(trace_path, REFILL_EVENT)

    (q64 / "enable").write_text("0\n", encoding="utf-8")
    (q64 / "filter").write_text(
        "nr_pages == 64\n",
        encoding="utf-8",
    )
    (q64 / "enable").write_text("1\n", encoding="utf-8")

    (refill / "enable").write_text("0\n", encoding="utf-8")
    (refill / "filter").write_text(
        "nr_pages <= 8 || nr_pages == 63\n",
        encoding="utf-8",
    )
    (refill / "enable").write_text("1\n", encoding="utf-8")


def close_probes(trace_path: Path) -> None:
    for event in (Q64_EVENT, REFILL_EVENT):
        try:
            (_probe_dir(trace_path, event) / "enable").write_text(
                "0\n",
                encoding="utf-8",
            )
        except OSError:
            pass


def _marker_intervals(
    text: str,
    *,
    trial_id: str,
) -> dict[tuple[str, int], dict[str, int]]:
    out: dict[tuple[str, int], dict[str, int]] = {}
    for line in text.splitlines():
        match = TX_MARKER_RE.search(line)
        if not match or match.group("trial") != trial_id:
            continue
        row = _event_row(line)
        ts = row.get("timestamp_ns")
        if ts is None:
            continue
        key = (
            match.group("phase"),
            int(match.group("touch")),
        )
        item = out.setdefault(key, {})
        item[match.group("edge").lower()] = int(ts)
    return out


def _refill_rows(text: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in text.splitlines():
        if f"{REFILL_EVENT}:" not in line:
            continue
        row = _event_row(line)
        if row.get("timestamp_ns") is not None:
            rows.append(row)
    return rows


def _target_q64(
    window: dict[str, Any],
    *,
    target_pid: int,
    stock_cpu: int,
) -> list[dict[str, Any]]:
    return [
        row
        for row in window.get("pc_try64", [])
        if (
            int(row.get("pid", -1)) == int(target_pid)
            and int(row.get("cpu", -1)) == int(stock_cpu)
            and int(row.get("nr_pages", 0)) == 64
        )
    ]


def _boundary_owner_memcg(
    trace_text: str,
    *,
    target_pid: int,
    stock_cpu: int,
    boundary_pre_ns: int,
    boundary_post_ns: int,
) -> list[str]:
    memcgs: list[str] = []
    for row in _refill_rows(trace_text):
        ts = int(row["timestamp_ns"])
        if not (boundary_pre_ns <= ts <= boundary_post_ns):
            continue
        if int(row.get("pid", -1)) != int(target_pid):
            continue
        if int(row.get("cpu", -1)) != int(stock_cpu):
            continue
        if int(row.get("nr_pages", 0)) != 63:
            continue
        memcg = row.get("memcg")
        if memcg:
            memcgs.append(str(memcg).lower())
    return sorted(set(memcgs))


def _phase_bucket(
    *,
    timestamp_ns: int,
    intervals: dict[tuple[str, int], dict[str, int]],
    first_q64_touch: int,
) -> str:
    startup = intervals.get(("OBSERVE", STARTUP_TOUCH), {})
    if (
        startup.get("pre") is not None
        and startup.get("post") is not None
        and startup["pre"] <= timestamp_ns <= startup["post"]
    ):
        return "STARTUP"

    release = intervals.get(("OBSERVE", RELEASE_TOUCH), {})
    if (
        release.get("pre") is not None
        and release.get("post") is not None
        and release["pre"] <= timestamp_ns <= release["post"]
    ):
        return "RELEASE_GAP"

    first = intervals.get(("NORMALIZE", 1), {})
    boundary = intervals.get(("NORMALIZE", first_q64_touch), {})
    if (
        release.get("post") is not None
        and first.get("pre") is not None
        and release["post"] < timestamp_ns < first["pre"]
    ):
        return "TAIL_GAP_AFTER_RELEASE"

    if (
        first.get("pre") is not None
        and boundary.get("pre") is not None
        and first["pre"] <= timestamp_ns < boundary["pre"]
    ):
        return "MEASURED_PREBOUNDARY_TOUCHES"

    return "OTHER"


def classify_small_residual(
    *,
    first_q64_touch: int,
    owner_small_refills: list[dict[str, Any]],
    owner_refill63_preboundary: list[dict[str, Any]],
) -> str:
    if owner_refill63_preboundary:
        return "CLASSIC_REFILL63_LEAK"

    s0 = int(first_q64_touch) - 1
    if s0 == 0:
        return (
            "T1_NO_SMALL_REFILL"
            if not owner_small_refills
            else "T1_WITH_SMALL_REFILL_HISTORY"
        )

    if not owner_small_refills:
        return "HIGH_T_WITHOUT_SMALL_REFILL"

    refill_sum = sum(
        int(row["nr_pages"]) for row in owner_small_refills
    )
    if refill_sum >= s0:
        return "SMALL_REFILL_EXPLAINS_DELAY"
    return "SMALL_REFILL_PARTIAL"


def run_identity(
    *,
    spec: dict[str, Any],
    worker: Path,
    out_root: Path,
    trace_marker: Path,
    trace_path: Path,
    block: int,
    identity: int,
    prep_cpu: int,
    stock_cpu: int,
    worker_uid: int,
) -> dict[str, Any]:
    design = spec["design"]
    trial_id = f"{block}:{identity}"
    root = out_root / f"trial-{block}-{identity}"
    root.mkdir(parents=True, exist_ok=True)
    name = (
        f"fr-smallref-{os.getenv('GITHUB_RUN_ID', 'local')}-"
        f"{block}-{identity}"
    )

    before_q64 = _profile_counts(trace_path, Q64_EVENT)
    before_refill = _profile_counts(trace_path, REFILL_EVENT)
    prepare_probes(trace_path)

    unit = None
    try:
        write_marker(
            trace_marker,
            trial_id=trial_id,
            epoch=0,
            phase="OBSERVE",
            touch_number=STARTUP_TOUCH,
            edge="PRE",
        )
        unit = _start_cpuset_constrained(
            worker=worker,
            root=root,
            name=name,
            prep_cpu=prep_cpu,
            max_pages=int(design["max_pages"]),
            safe_len=int(design["safe_len_pages"]),
            worker_uid=worker_uid,
        )
        write_marker(
            trace_marker,
            trial_id=trial_id,
            epoch=0,
            phase="OBSERVE",
            touch_number=STARTUP_TOUCH,
            edge="POST",
        )

        target_pid = int(unit["pid"])
        startup_effective = _cpuset_effective(unit["cg"])

        write_marker(
            trace_marker,
            trial_id=trial_id,
            epoch=0,
            phase="OBSERVE",
            touch_number=RELEASE_TOUCH,
            edge="PRE",
        )
        release_effective = _expand_cpuset(
            unit,
            prep_cpu=prep_cpu,
            stock_cpu=stock_cpu,
        )
        os.sched_setaffinity(target_pid, {stock_cpu})
        _wait_cpu(target_pid, stock_cpu)
        write_marker(
            trace_marker,
            trial_id=trial_id,
            epoch=0,
            phase="OBSERVE",
            touch_number=RELEASE_TOUCH,
            edge="POST",
        )

        geometry = geometry_receipt(unit, prep_cpu)
        geometry_valid = (
            bool(geometry["guard_cpu_match"])
            and bool(geometry["same_pte_table"])
        )

        page_size = int(geometry["page_size"])
        sequence = list(
            range(
                int(geometry["safe_start"]) + 1,
                int(geometry["safe_start"])
                + int(geometry["safe_len"]),
            )
        )

        touches: list[dict[str, Any]] = []
        first_q64_touch: int | None = None
        boundary_q64: list[dict[str, Any]] = []
        invalidation_reason: str | None = None

        if geometry_valid:
            for touch_number in range(
                1,
                int(design["primary_bound_touch"]) + 1,
            ):
                row = touch_with_transaction_marker(
                    unit=unit,
                    stock_cpu=stock_cpu,
                    page_size=page_size,
                    page_index=sequence[touch_number - 1],
                    phase="NORMALIZE",
                    touch_number=touch_number,
                    trial_id=trial_id,
                    epoch=0,
                    trace_marker=trace_marker,
                )
                trace_text = trace_path.read_text(
                    encoding="utf-8",
                    errors="replace",
                )
                window = observed_window(
                    trace_text=trace_text,
                    trial_id=trial_id,
                    epoch=0,
                    phase="NORMALIZE",
                    touch_number=touch_number,
                )
                q64 = _target_q64(
                    window,
                    target_pid=target_pid,
                    stock_cpu=stock_cpu,
                )
                complete = (
                    int(window.get("pre_count", 0)) == 1
                    and int(window.get("post_count", 0)) == 1
                    and int(window.get("marker_error_count", 0)) == 0
                )
                touches.append(
                    {
                        **row,
                        "touch_number": touch_number,
                        "trace_complete": complete,
                        "target_q64_count": len(q64),
                    }
                )

                if not complete:
                    invalidation_reason = "TRACE_GAP"
                    break
                if int(row.get("worker_error", 0)) != 0:
                    invalidation_reason = "WORKER_ERROR"
                    break
                if int(row.get("worker_touched", -1)) != touch_number:
                    invalidation_reason = (
                        "WORKER_TOUCH_SEQUENCE_MISMATCH"
                    )
                    break
                if int(row.get("observed_cpu", -1)) != stock_cpu:
                    invalidation_reason = "CPU_MISMATCH"
                    break
                if int(row.get("vmpte_delta_kib", 0)) != 0:
                    invalidation_reason = "PTE_GROWTH"
                    break
                if len(q64) > 1:
                    invalidation_reason = (
                        "MULTIPLE_TARGET_Q64_IN_TOUCH"
                    )
                    break
                if len(q64) == 1:
                    first_q64_touch = touch_number
                    boundary_q64 = q64
                    break
        else:
            invalidation_reason = "GEOMETRY_INVALID"

        final_text = trace_path.read_text(
            encoding="utf-8",
            errors="replace",
        )
        after_q64 = _profile_counts(trace_path, Q64_EVENT)
        after_refill = _profile_counts(trace_path, REFILL_EVENT)
        q64_profile = _delta_counts(before_q64, after_q64)
        refill_profile = _delta_counts(
            before_refill,
            after_refill,
        )

        intervals = _marker_intervals(
            final_text,
            trial_id=trial_id,
        )

        owner_counter: str | None = None
        owner_memcg: str | None = None
        owner_small_refills: list[dict[str, Any]] = []
        owner_refill63_preboundary: list[dict[str, Any]] = []
        refill_spectrum: list[dict[str, Any]] = []

        if first_q64_touch is not None and len(boundary_q64) == 1:
            counter = boundary_q64[0].get("counter")
            if counter:
                owner_counter = str(counter).lower()

            boundary_interval = intervals.get(
                ("NORMALIZE", first_q64_touch),
                {},
            )
            pre_ns = boundary_interval.get("pre")
            post_ns = boundary_interval.get("post")
            if pre_ns is not None and post_ns is not None:
                memcgs = _boundary_owner_memcg(
                    final_text,
                    target_pid=target_pid,
                    stock_cpu=stock_cpu,
                    boundary_pre_ns=int(pre_ns),
                    boundary_post_ns=int(post_ns),
                )
                if len(memcgs) == 1:
                    owner_memcg = memcgs[0]

            if owner_memcg is not None:
                boundary_pre_ns = int(
                    intervals[
                        ("NORMALIZE", first_q64_touch)
                    ]["pre"]
                )
                for row in _refill_rows(final_text):
                    if (
                        str(row.get("memcg", "")).lower()
                        != owner_memcg
                    ):
                        continue
                    if int(row.get("cpu", -1)) != stock_cpu:
                        continue
                    ts = int(row["timestamp_ns"])
                    if ts >= boundary_pre_ns:
                        continue
                    size = int(row.get("nr_pages", -1))
                    enriched = {
                        **row,
                        "phase_bucket": _phase_bucket(
                            timestamp_ns=ts,
                            intervals=intervals,
                            first_q64_touch=first_q64_touch,
                        ),
                    }
                    refill_spectrum.append(enriched)
                    if 1 <= size <= 8:
                        owner_small_refills.append(enriched)
                    elif size == 63:
                        owner_refill63_preboundary.append(
                            enriched
                        )

        cgroup_procs = sorted(
            int(x)
            for x in (unit["cg"] / "cgroup.procs")
            .read_text(encoding="utf-8")
            .split()
        )
        single_process = cgroup_procs == [target_pid]

        coverage_ok = all(
            profile is not None
            and int(profile.get("missed", -1)) == 0
            for profile in (q64_profile, refill_profile)
        )
        cpuset_ok = (
            startup_effective == {prep_cpu}
            and {prep_cpu, stock_cpu}.issubset(
                release_effective
            )
        )
        owner_ok = (
            first_q64_touch is not None
            and owner_counter is not None
            and owner_memcg is not None
        )
        valid = (
            invalidation_reason is None
            and first_q64_touch is not None
            and coverage_ok
            and cpuset_ok
            and single_process
            and owner_ok
        )

        if not valid:
            classification = "INVALID_OBSERVER"
        else:
            classification = classify_small_residual(
                first_q64_touch=first_q64_touch,
                owner_small_refills=owner_small_refills,
                owner_refill63_preboundary=(
                    owner_refill63_preboundary
                ),
            )

        return {
            "experiment_id": spec["experiment_id"],
            "trial_id": trial_id,
            "block": block,
            "identity": identity,
            "pid": target_pid,
            "prep_cpu": prep_cpu,
            "stock_cpu": stock_cpu,
            "startup_cpuset_effective": sorted(
                startup_effective
            ),
            "release_cpuset_effective": sorted(
                release_effective
            ),
            "cgroup_procs": cgroup_procs,
            "single_process": single_process,
            "geometry": geometry,
            "q64_profile": q64_profile,
            "refill_profile": refill_profile,
            "coverage_ok": coverage_ok,
            "first_q64_touch": first_q64_touch,
            "initial_residual_estimate": (
                None
                if first_q64_touch is None
                else first_q64_touch - 1
            ),
            "owner_counter": owner_counter,
            "owner_memcg": owner_memcg,
            "owner_refill_spectrum_preboundary": refill_spectrum,
            "owner_small_refills_preboundary": (
                owner_small_refills
            ),
            "owner_small_refill_sizes": [
                int(row["nr_pages"])
                for row in owner_small_refills
            ],
            "owner_small_refill_sum": sum(
                int(row["nr_pages"])
                for row in owner_small_refills
            ),
            "owner_refill63_preboundary": (
                owner_refill63_preboundary
            ),
            "touches": touches,
            "invalidation_reason": invalidation_reason,
            "valid": valid,
            "classification": classification,
        }
    finally:
        close_probes(trace_path)
        if unit is not None:
            _stop(unit)


def run_block(
    *,
    spec: dict[str, Any],
    worker: Path,
    out_root: Path,
    trace_marker: Path,
    trace_path: Path,
    block: int,
    worker_uid: int,
) -> dict[str, Any]:
    cpus = sorted(os.sched_getaffinity(0))
    if len(cpus) < 3:
        raise RuntimeError(
            "small residual refill spectrum requires >=3 CPUs"
        )
    controller_cpu, prep_cpu, stock_cpu = (
        cpus[0],
        cpus[1],
        cpus[-1],
    )
    os.sched_setaffinity(0, {controller_cpu})

    out_root.mkdir(parents=True, exist_ok=True)
    (out_root / "environment.json").write_text(
        json.dumps(
            environment_receipt(worker, cpus),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    rows: list[dict[str, Any]] = []
    for identity in range(
        int(spec["design"]["identities_per_block"])
    ):
        row = run_identity(
            spec=spec,
            worker=worker,
            out_root=out_root,
            trace_marker=trace_marker,
            trace_path=trace_path,
            block=block,
            identity=identity,
            prep_cpu=prep_cpu,
            stock_cpu=stock_cpu,
            worker_uid=worker_uid,
        )
        (out_root / f"trial-{block}-{identity}.json").write_text(
            json.dumps(row, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        rows.append(row)

    return {
        "experiment_id": spec["experiment_id"],
        "block": block,
        "trial_count": len(rows),
        "classifications": dict(
            Counter(row["classification"] for row in rows)
        ),
        "first_q64_touches": [
            row["first_q64_touch"]
            for row in rows
            if row.get("first_q64_touch") is not None
        ],
        "small_refill_sizes": list(
            sorted(
                size
                for row in rows
                for size in row.get(
                    "owner_small_refill_sizes",
                    [],
                )
            )
        ),
    }


def aggregate(
    spec: dict[str, Any],
    input_root: Path,
) -> dict[str, Any]:
    trials = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(input_root.rglob("trial-*.json"))
    ]
    valid = [row for row in trials if row.get("valid")]
    promoted = [
        row
        for row in valid
        if row.get("classification")
        == "SMALL_REFILL_EXPLAINS_DELAY"
    ]
    delayed = [
        row
        for row in valid
        if int(row.get("first_q64_touch") or 0) > 1
    ]

    spectrum = Counter(
        int(size)
        for row in valid
        for size in row.get(
            "owner_small_refill_sizes",
            [],
        )
    )
    phase_spectrum = Counter(
        refill.get("phase_bucket", "UNKNOWN")
        for row in valid
        for refill in row.get(
            "owner_small_refills_preboundary",
            [],
        )
    )
    t_hist = Counter(
        int(row["first_q64_touch"])
        for row in valid
        if row.get("first_q64_touch") is not None
    )

    panel_coverage_pass = (
        len(trials) == int(spec["design"]["total_identities"])
        and len(valid) == len(trials)
    )
    discovery_pass = len(promoted) >= 1

    return {
        "experiment_id": spec["experiment_id"],
        "trial_count": len(trials),
        "valid_trial_count": len(valid),
        "panel_coverage_pass": panel_coverage_pass,
        "discovery_pass": discovery_pass,
        "classifications": dict(
            Counter(
                row.get("classification", "MISSING")
                for row in trials
            )
        ),
        "first_q64_histogram": dict(t_hist),
        "delayed_t_gt1_count": len(delayed),
        "small_refill_promoted_count": len(promoted),
        "small_refill_promoted_trials": [
            row["trial_id"] for row in promoted
        ],
        "owner_small_refill_size_histogram": dict(spectrum),
        "owner_small_refill_phase_histogram": dict(
            phase_spectrum
        ),
        "classic_refill63_leak_count": sum(
            row.get("classification")
            == "CLASSIC_REFILL63_LEAK"
            for row in valid
        ),
        "high_t_without_small_refill_count": sum(
            row.get("classification")
            == "HIGH_T_WITHOUT_SMALL_REFILL"
            for row in valid
        ),
        "small_refill_partial_count": sum(
            row.get("classification")
            == "SMALL_REFILL_PARTIAL"
            for row in valid
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
    run.add_argument("--trace-marker", required=True)
    run.add_argument("--trace-path", required=True)
    run.add_argument("--worker-uid", type=int, required=True)

    agg = sub.add_parser("aggregate")
    agg.add_argument("--spec", required=True)
    agg.add_argument("--input-root", required=True)
    agg.add_argument("--json-out", required=True)

    args = parser.parse_args()
    spec = load_spec(args.spec)

    if args.cmd == "run-block":
        result = run_block(
            spec=spec,
            worker=Path(args.worker).resolve(),
            out_root=Path(args.out_root),
            trace_marker=Path(args.trace_marker),
            trace_path=Path(args.trace_path),
            block=args.block,
            worker_uid=args.worker_uid,
        )
        print(json.dumps(result, sort_keys=True))
        return

    result = aggregate(spec, Path(args.input_root))
    out = Path(args.json_out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "discovery_pass": result["discovery_pass"],
                "panel_coverage_pass": result[
                    "panel_coverage_pass"
                ],
                "trial_count": result["trial_count"],
                "valid_trial_count": result[
                    "valid_trial_count"
                ],
                "delayed_t_gt1_count": result[
                    "delayed_t_gt1_count"
                ],
                "small_refill_promoted_count": result[
                    "small_refill_promoted_count"
                ],
                "small_refill_promoted_trials": result[
                    "small_refill_promoted_trials"
                ],
                "owner_small_refill_size_histogram": result[
                    "owner_small_refill_size_histogram"
                ],
                "owner_small_refill_phase_histogram": result[
                    "owner_small_refill_phase_histogram"
                ],
                "classifications": result[
                    "classifications"
                ],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
