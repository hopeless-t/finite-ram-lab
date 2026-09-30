from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import time
from typing import Any, Callable

from .age_decoupling_stage_a import (
    _close_refill_probe,
    _prepare_refill_preverify,
)
from .ambient_stock_log_reducer import reduce_catcher_records
from .ambient_stock_tracefs_backend import (
    EVENTS,
    cleanup_owner_count_only,
    configure_owner_count_only,
    configure_owner_q64_only,
    event_dir,
    histogram_receipt,
    parse_histogram,
)
from .memcg005gc_controlled_spawn import _stop, environment_receipt
from .startup_stock_seed_phase import _delta_counts, _profile_counts
from .transaction_epoch_archive import EpochArchive
from .transactional_reprime import State
from .transactional_spawn_native import (
    observed_window,
    touch_with_transaction_marker,
    write_marker,
)
from .tx_perturbation_matrix import (
    TARGET_COMM,
    _close_owner_probe,
    _consume_segment,
    _fresh_epoch,
)

AMBIENT_MARKER_TOUCH = 8600
SETUP_TOUCHES = 32
EXPECTED_RESIDUAL = 31
BOUNDARY_BASELINE_T = 64


def load_spec(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _profile_snapshot(trace_path: Path) -> dict[str, Any]:
    return {
        logical: _profile_counts(trace_path, event)
        for logical, event in EVENTS.items()
    }


def _profile_delta(
    before: dict[str, Any],
    after: dict[str, Any],
) -> dict[str, Any]:
    return {
        logical: _delta_counts(
            before.get(logical),
            after.get(logical),
        )
        for logical in EVENTS
    }


def _miss_value(row: dict[str, int] | None) -> int | None:
    if row is None:
        return None
    try:
        return int(row["missed"])
    except (KeyError, TypeError, ValueError):
        return None


def _histogram_summary(
    trace_path: Path,
    logical_name: str,
):
    path = event_dir(trace_path, logical_name) / "hist"
    return parse_histogram(
        path.read_text(encoding="utf-8", errors="replace")
    )


def _owner_q64_events(
    window: dict[str, Any],
    *,
    owner_counter: str,
    stock_cpu: int,
) -> list[dict[str, Any]]:
    return [
        row
        for row in window.get("pc_try64", [])
        if (
            str(row.get("counter", "")).lower()
            == owner_counter.lower()
            and int(row.get("cpu", -1)) == int(stock_cpu)
            and int(row.get("nr_pages", -1)) == 64
        )
    ]


def _trace_window_complete(window: dict[str, Any]) -> bool:
    return (
        int(window.get("pre_count", 0)) == 1
        and int(window.get("post_count", 0)) == 1
        and int(window.get("marker_error_count", 0)) == 0
    )


def _jsonl(rows: list[dict[str, Any]]) -> str:
    return "".join(
        json.dumps(
            row,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
        for row in rows
    )


def _preverify_rows(
    *,
    session_id: str,
    normalized: bool,
    initial_residual: int | None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = [
        {
            "kind": "SESSION_START",
            "session_id": session_id,
            "normalized": bool(normalized),
            "initial_residual": (
                0 if initial_residual is None else int(initial_residual)
            ),
        },
        {
            "kind": "HEALTH",
            "session_id": session_id,
            "trace_complete": False,
            "worker_ok": False,
            "cpu_stable": False,
            "pte_stable": False,
        },
    ]
    for probe in ("consume", "refill", "uncharge", "q64"):
        rows.append({
            "kind": "COVERAGE",
            "session_id": session_id,
            "probe": probe,
            "missed": None,
        })
    rows.extend([
        {
            "kind": "HISTOGRAM",
            "session_id": session_id,
            "dropped": 0,
            "source": "PREVERIFY_HOLD",
        },
        {
            "kind": "BOUNDARY",
            "session_id": session_id,
            "observed": False,
            "T": None,
        },
        {
            "kind": "SESSION_END",
            "session_id": session_id,
        },
    ])
    return rows


def _boundary_chase(
    *,
    unit: dict[str, Any],
    sequence: list[int],
    cursor: int,
    measured_count: int,
    trace_marker: Path,
    trace_path: Path,
    trial_id: str,
    epoch: int,
    stock_cpu: int,
    page_size: int,
    owner_counter: str,
    max_extra: int,
) -> tuple[int, int, dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    trace_complete = True
    worker_ok = True
    cpu_stable = True
    pte_stable = True
    boundary_T: int | None = None

    for diagnostic_touch in range(1, int(max_extra) + 1):
        if cursor >= len(sequence):
            trace_complete = False
            break

        measured_count += 1
        touch = touch_with_transaction_marker(
            unit=unit,
            stock_cpu=stock_cpu,
            page_size=page_size,
            page_index=sequence[cursor],
            phase="TARGET",
            touch_number=diagnostic_touch,
            trial_id=trial_id,
            epoch=epoch,
            trace_marker=trace_marker,
        )
        cursor += 1

        window = observed_window(
            trace_text=trace_path.read_text(
                encoding="utf-8",
                errors="replace",
            ),
            trial_id=trial_id,
            epoch=epoch,
            phase="TARGET",
            touch_number=diagnostic_touch,
        )
        complete = _trace_window_complete(window)
        q64 = _owner_q64_events(
            window,
            owner_counter=owner_counter,
            stock_cpu=stock_cpu,
        )

        this_worker_ok = (
            int(touch.get("worker_error", 1)) == 0
            and int(touch.get("worker_touched", -1))
            == int(measured_count)
        )
        this_cpu_ok = (
            int(touch.get("observed_cpu", -1)) == int(stock_cpu)
        )
        this_pte_ok = int(touch.get("vmpte_delta_kib", 1)) == 0

        trace_complete = trace_complete and complete and len(q64) <= 1
        worker_ok = worker_ok and this_worker_ok
        cpu_stable = cpu_stable and this_cpu_ok
        pte_stable = pte_stable and this_pte_ok

        rows.append({
            "diagnostic_touch": diagnostic_touch,
            "T": SETUP_TOUCHES + diagnostic_touch,
            "touch": touch,
            "trace_complete": complete,
            "owner_q64_count": len(q64),
        })

        if not (
            complete
            and this_worker_ok
            and this_cpu_ok
            and this_pte_ok
            and len(q64) <= 1
        ):
            break

        if len(q64) == 1:
            boundary_T = SETUP_TOUCHES + diagnostic_touch
            break

    return cursor, measured_count, {
        "boundary_observed": boundary_T is not None,
        "final_boundary_T": boundary_T,
        "trace_complete": trace_complete,
        "worker_ok": worker_ok,
        "cpu_stable": cpu_stable,
        "pte_stable": pte_stable,
        "rows": rows,
    }


def run_session(
    *,
    spec: dict[str, Any],
    worker: Path,
    out_root: Path,
    trace_marker: Path,
    trace_path: Path,
    worker_uid: int,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    cpus = sorted(os.sched_getaffinity(0))
    if len(cpus) < 3:
        raise RuntimeError("ambient catcher requires >=3 CPUs")
    controller_cpu, prep_cpu, stock_cpu = cpus[0], cpus[1], cpus[-1]
    os.sched_setaffinity(0, {controller_cpu})

    ambient_spec = spec["design"]["ambient_window"]
    ambient_seconds = float(ambient_spec["default_seconds"])
    maximum_seconds = float(ambient_spec["maximum_seconds"])
    if ambient_seconds < 0 or ambient_seconds > maximum_seconds:
        raise ValueError("ambient_duration_out_of_bounds")

    max_extra = int(
        spec["design"]["end_diagnostic"][
            "maximum_additional_target_touches"
        ]
    )
    if max_extra < 1 or max_extra > 64:
        raise ValueError("diagnostic_touch_bound_invalid")

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

    session_id = f"ambient-{os.getenv('GITHUB_RUN_ID', 'local')}-{os.getpid()}"
    trial_id = "0:0"
    archive = EpochArchive.start(max_reprimes=0)
    unit = None
    records: list[dict[str, Any]] = []
    ambient_detail: dict[str, Any] | None = None
    diagnostic: dict[str, Any] | None = None

    _prepare_refill_preverify(trace_path)

    try:
        (
            unit,
            geometry,
            sequence,
            page_size,
            cursor,
            measured_count,
            epoch_row,
        ) = _fresh_epoch(
            archive=archive,
            worker=worker,
            out_root=out_root,
            trace_marker=trace_marker,
            trace_path=trace_path,
            trial_id=trial_id,
            block=0,
            identity=0,
            arm="AMBIENT_STOCK_CATCHER",
            prep_cpu=prep_cpu,
            stock_cpu=stock_cpu,
            worker_uid=worker_uid,
            safe_len=256,
            calibration_max=65,
        )

        normalized = (
            archive.tx.state is State.VERIFIED
            and archive.owner_counter is not None
            and archive.owner_memcg is not None
        )
        initial_residual = archive.tx.expected_residual

        if normalized:
            cursor, measured_count, setup_rows = _consume_segment(
                archive=archive,
                unit=unit,
                sequence=sequence,
                cursor=cursor,
                start_touch=1,
                count=SETUP_TOUCHES,
                trace_marker=trace_marker,
                trace_path=trace_path,
                trial_id=trial_id,
                stock_cpu=stock_cpu,
                page_size=page_size,
                measured_count=measured_count,
            )
            epoch_row["ambient_setup_consume"] = setup_rows
            initial_residual = archive.tx.expected_residual

        precondition_ok = (
            normalized
            and archive.tx.state in {State.VERIFIED, State.EXECUTING}
            and initial_residual == EXPECTED_RESIDUAL
        )

        if not precondition_ok:
            records = _preverify_rows(
                session_id=session_id,
                normalized=normalized,
                initial_residual=initial_residual,
            )
            reduction = reduce_catcher_records(records)
            (out_root / "session.jsonl").write_text(
                _jsonl(records),
                encoding="utf-8",
            )
            (out_root / "reduction.json").write_text(
                json.dumps(reduction, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            return {
                "experiment_id": spec["experiment_id"],
                "session_id": session_id,
                "classification": reduction["classification"],
                "reduction": reduction,
                "archive": archive.as_dict(),
            }

        assert archive.owner_counter is not None
        assert archive.owner_memcg is not None

        # Remove the setup stacktrace trigger before switching the same
        # qualified owner probe to a long-window histogram.
        _close_owner_probe(trace_path)
        configure_owner_count_only(
            trace_path,
            owner_memcg=archive.owner_memcg,
            owner_counter=archive.owner_counter,
        )

        profile_before = _profile_snapshot(trace_path)

        write_marker(
            trace_marker,
            trial_id=trial_id,
            epoch=archive.tx.epoch,
            phase="OBSERVE",
            touch_number=AMBIENT_MARKER_TOUCH,
            edge="PRE",
        )
        sleep_fn(ambient_seconds)
        write_marker(
            trace_marker,
            trial_id=trial_id,
            epoch=archive.tx.epoch,
            phase="OBSERVE",
            touch_number=AMBIENT_MARKER_TOUCH,
            edge="POST",
        )

        ambient_window = observed_window(
            trace_text=trace_path.read_text(
                encoding="utf-8",
                errors="replace",
            ),
            trial_id=trial_id,
            epoch=archive.tx.epoch,
            phase="OBSERVE",
            touch_number=AMBIENT_MARKER_TOUCH,
        )
        ambient_q64 = _owner_q64_events(
            ambient_window,
            owner_counter=archive.owner_counter,
            stock_cpu=stock_cpu,
        )

        histograms = {
            logical: _histogram_summary(trace_path, logical)
            for logical in ("consume", "refill", "uncharge")
        }

        # Freeze ambient counters before target touches resume.
        configure_owner_q64_only(
            trace_path,
            owner_memcg=archive.owner_memcg,
            owner_counter=archive.owner_counter,
        )

        cursor, measured_count, diagnostic = _boundary_chase(
            unit=unit,
            sequence=sequence,
            cursor=cursor,
            measured_count=measured_count,
            trace_marker=trace_marker,
            trace_path=trace_path,
            trial_id=trial_id,
            epoch=archive.tx.epoch,
            stock_cpu=stock_cpu,
            page_size=page_size,
            owner_counter=archive.owner_counter,
            max_extra=max_extra,
        )

        profile_after = _profile_snapshot(trace_path)
        profile_delta = _profile_delta(profile_before, profile_after)

        ambient_detail = {
            "seconds": ambient_seconds,
            "trace_complete": _trace_window_complete(ambient_window),
            "owner_q64_count": len(ambient_q64),
            "histograms": {
                key: {
                    "hits": value.hits,
                    "entries": value.entries,
                    "dropped": value.dropped,
                    "pages": value.pages,
                    "buckets": value.buckets,
                }
                for key, value in histograms.items()
            },
            "profile_delta": profile_delta,
        }

        records = [{
            "kind": "SESSION_START",
            "session_id": session_id,
            "normalized": True,
            "initial_residual": int(initial_residual),
        }]

        health = {
            "kind": "HEALTH",
            "session_id": session_id,
            "trace_complete": (
                bool(ambient_detail["trace_complete"])
                and bool(diagnostic["trace_complete"])
            ),
            "worker_ok": bool(diagnostic["worker_ok"]),
            "cpu_stable": bool(diagnostic["cpu_stable"]),
            "pte_stable": bool(diagnostic["pte_stable"]),
        }
        records.append(health)

        for logical in ("consume", "refill", "uncharge", "q64"):
            records.append({
                "kind": "COVERAGE",
                "session_id": session_id,
                "probe": logical,
                "missed": _miss_value(profile_delta.get(logical)),
            })

        records.extend(
            histogram_receipt(
                session_id=session_id,
                kind="CONSUME_SUCCESS",
                summary=histograms["consume"],
            )
        )
        records.extend(
            histogram_receipt(
                session_id=session_id,
                kind="REFILL",
                summary=histograms["refill"],
            )
        )
        records.extend(
            histogram_receipt(
                session_id=session_id,
                kind="OWNER_UNCHARGE",
                summary=histograms["uncharge"],
            )
        )

        if ambient_q64:
            records.append({
                "kind": "AMBIENT_OWNER_Q64",
                "session_id": session_id,
                "count": len(ambient_q64),
            })

        records.append({
            "kind": "BOUNDARY",
            "session_id": session_id,
            "observed": bool(diagnostic["boundary_observed"]),
            "T": diagnostic["final_boundary_T"],
        })
        records.append({
            "kind": "SESSION_END",
            "session_id": session_id,
        })

        reduction = reduce_catcher_records(records)
        (out_root / "session.jsonl").write_text(
            _jsonl(records),
            encoding="utf-8",
        )
        (out_root / "reduction.json").write_text(
            json.dumps(reduction, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (out_root / "ambient-detail.json").write_text(
            json.dumps(ambient_detail, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (out_root / "diagnostic.json").write_text(
            json.dumps(diagnostic, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        return {
            "experiment_id": spec["experiment_id"],
            "session_id": session_id,
            "classification": reduction["classification"],
            "boundary_T": diagnostic["final_boundary_T"],
            "ambient_owner_q64_count": len(ambient_q64),
            "ambient_detail": ambient_detail,
            "diagnostic": diagnostic,
            "reduction": reduction,
            "geometry": geometry,
            "archive": archive.as_dict(),
        }
    finally:
        cleanup_owner_count_only(trace_path)
        _close_owner_probe(trace_path)
        _close_refill_probe(trace_path)
        if unit is not None:
            _stop(unit)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=True)
    parser.add_argument("--worker", required=True)
    parser.add_argument("--out-root", required=True)
    parser.add_argument("--trace-marker", required=True)
    parser.add_argument("--trace-path", required=True)
    parser.add_argument("--worker-uid", type=int, required=True)
    args = parser.parse_args()

    result = run_session(
        spec=load_spec(args.spec),
        worker=Path(args.worker).resolve(),
        out_root=Path(args.out_root),
        trace_marker=Path(args.trace_marker),
        trace_path=Path(args.trace_path),
        worker_uid=args.worker_uid,
    )
    print(json.dumps({
        "experiment_id": result["experiment_id"],
        "session_id": result["session_id"],
        "classification": result["classification"],
        "boundary_T": result.get("boundary_T"),
        "ambient_owner_q64_count": result.get(
            "ambient_owner_q64_count",
            0,
        ),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
