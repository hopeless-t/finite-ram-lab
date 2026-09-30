from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any

from .age_decoupling_stage_a import _prepare_refill_preverify
from .memcg005gc_controlled_spawn import _stop, environment_receipt
from .startup_stock_seed_phase import _delta_counts, _profile_counts
from .transaction_epoch_archive import EpochArchive
from .transaction_trace_observer import observer_receipt_for_window
from .transactional_reprime import State
from .transactional_spawn_native import observed_window
from .tx_perturbation_matrix import (
    TARGET_COMM,
    _close_owner_probe,
    _consume_segment,
    _fresh_epoch,
)


CONSUME_EVENT = "frl_consume_stock_ret"


def load_spec(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _probe_dir(trace_path: Path) -> Path:
    return trace_path.parent / "events" / "kprobes" / CONSUME_EVENT


def _bind_consume_probe(
    trace_path: Path,
    *,
    owner_memcg: str,
) -> None:
    probe = _probe_dir(trace_path)
    (probe / "enable").write_text("0\n", encoding="utf-8")
    (probe / "filter").write_text(
        f"memcg == {owner_memcg} && ret != 0\n",
        encoding="utf-8",
    )
    (probe / "enable").write_text("1\n", encoding="utf-8")


def _close_consume_probe(trace_path: Path) -> None:
    probe = _probe_dir(trace_path)
    try:
        (probe / "enable").write_text("0\n", encoding="utf-8")
        (probe / "filter").write_text(
            "memcg == 0\n",
            encoding="utf-8",
        )
    except OSError:
        pass


def classify_capability(
    *,
    normalized: bool,
    trace_complete: bool,
    worker_ok: bool,
    cpu_ok: bool,
    pte_ok: bool,
    probe_missed: int | None,
    target_receipt_count: int,
) -> str:
    if not normalized:
        return "PREVERIFY_HOLD"
    if not trace_complete or not worker_ok or not cpu_ok or not pte_ok:
        return "OBSERVATION_HOLD"
    if probe_missed is None or int(probe_missed) != 0:
        return "INSTRUMENTATION_HOLD"
    if int(target_receipt_count) > 0:
        return "CONSUME_STOCK_RET_CAPTURED"
    return "CAPABILITY_NOT_OBSERVED"


def run_trial(
    *,
    spec: dict[str, Any],
    worker: Path,
    out_root: Path,
    trace_marker: Path,
    trace_path: Path,
    block: int,
    prep_cpu: int,
    stock_cpu: int,
    worker_uid: int,
) -> dict[str, Any]:
    identity = 0
    trial_id = f"{block}:{identity}"
    archive = EpochArchive.start(max_reprimes=0)
    unit = None

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
            block=block,
            identity=identity,
            arm="CONSUME_STOCK_RET_CAPABILITY",
            prep_cpu=prep_cpu,
            stock_cpu=stock_cpu,
            worker_uid=worker_uid,
            safe_len=192,
            calibration_max=65,
        )

        normalized = (
            archive.tx.state is State.VERIFIED
            and archive.owner_counter is not None
            and archive.owner_memcg is not None
        )
        if not normalized:
            return {
                "experiment_id": spec["experiment_id"],
                "trial_id": trial_id,
                "block": block,
                "classification": "PREVERIFY_HOLD",
                "normalized": False,
                "archive": archive.as_dict(),
            }

        _bind_consume_probe(
            trace_path,
            owner_memcg=archive.owner_memcg,
        )
        profile_before = _profile_counts(
            trace_path,
            CONSUME_EVENT,
        )

        cursor, measured_count, rows = _consume_segment(
            archive=archive,
            unit=unit,
            sequence=sequence,
            cursor=cursor,
            start_touch=1,
            count=1,
            trace_marker=trace_marker,
            trace_path=trace_path,
            trial_id=trial_id,
            stock_cpu=stock_cpu,
            page_size=page_size,
            measured_count=measured_count,
        )

        profile_after = _profile_counts(
            trace_path,
            CONSUME_EVENT,
        )
        profile_delta = _delta_counts(
            profile_before,
            profile_after,
        )

        window = observed_window(
            trace_text=trace_path.read_text(
                encoding="utf-8",
                errors="replace",
            ),
            trial_id=trial_id,
            epoch=archive.tx.epoch,
            phase="CONSUME",
            touch_number=1,
        )
        receipt = observer_receipt_for_window(
            window,
            owner_counter=archive.owner_counter,
            owner_memcg=archive.owner_memcg,
            stock_cpu=stock_cpu,
            phase="CONSUME",
            target_comm=TARGET_COMM,
            owner_probe_filtered=True,
        )

        target_events = [
            event
            for event in receipt.get(
                "owner_consume_stock_success_events",
                [],
            )
            if (
                int(event.get("nr_pages", -1)) == 1
                and int(event.get("ret", 0)) != 0
                and event.get("comm") == TARGET_COMM
                and int(event.get("pid", -1)) == int(unit["pid"])
                and int(event.get("cpu", -1)) == int(stock_cpu)
            )
        ]

        touch_row = (
            rows[0].get("touch", {})
            if rows
            else {}
        )
        trace_complete = bool(receipt.get("trace_complete", False))
        worker_ok = int(touch_row.get("worker_error", 1)) == 0
        cpu_ok = int(touch_row.get("observed_cpu", -1)) == int(stock_cpu)
        pte_ok = int(touch_row.get("vmpte_delta_kib", 1)) == 0
        missed = (
            None
            if profile_delta is None
            else int(profile_delta.get("missed", -1))
        )

        classification = classify_capability(
            normalized=normalized,
            trace_complete=trace_complete,
            worker_ok=worker_ok,
            cpu_ok=cpu_ok,
            pte_ok=pte_ok,
            probe_missed=missed,
            target_receipt_count=len(target_events),
        )

        return {
            "experiment_id": spec["experiment_id"],
            "trial_id": trial_id,
            "block": block,
            "classification": classification,
            "normalized": normalized,
            "owner_counter": archive.owner_counter,
            "owner_memcg": archive.owner_memcg,
            "target_pid": int(unit["pid"]),
            "stock_cpu": int(stock_cpu),
            "geometry": geometry,
            "consume_rows": rows,
            "profile_delta": profile_delta,
            "receipt": receipt,
            "target_consume_stock_events": target_events,
            "target_consume_stock_event_count": len(target_events),
            "trace_complete": trace_complete,
            "worker_ok": worker_ok,
            "cpu_ok": cpu_ok,
            "pte_ok": pte_ok,
            "archive": archive.as_dict(),
        }
    finally:
        _close_consume_probe(trace_path)
        _close_owner_probe(trace_path)
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
        raise RuntimeError("consume_stock return pilot requires >=3 CPUs")
    controller_cpu, prep_cpu, stock_cpu = cpus[0], cpus[1], cpus[-1]
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

    row = run_trial(
        spec=spec,
        worker=worker,
        out_root=out_root,
        trace_marker=trace_marker,
        trace_path=trace_path,
        block=block,
        prep_cpu=prep_cpu,
        stock_cpu=stock_cpu,
        worker_uid=worker_uid,
    )
    (out_root / f"trial-{block}-0.json").write_text(
        json.dumps(row, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "experiment_id": spec["experiment_id"],
        "block": block,
        "classification": row["classification"],
        "target_consume_stock_event_count": row.get(
            "target_consume_stock_event_count",
            0,
        ),
        "profile_delta": row.get("profile_delta"),
    }


def aggregate(
    spec: dict[str, Any],
    input_root: Path,
) -> dict[str, Any]:
    trials = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(input_root.rglob("trial-*.json"))
    ]
    classifications = Counter(
        row.get("classification", "MISSING")
        for row in trials
    )
    captured = [
        row
        for row in trials
        if row.get("classification")
        == "CONSUME_STOCK_RET_CAPTURED"
    ]
    invalid = [
        row
        for row in trials
        if row.get("classification")
        in {
            "PREVERIFY_HOLD",
            "OBSERVATION_HOLD",
            "INSTRUMENTATION_HOLD",
        }
    ]

    pilot_pass = (
        len(trials) == int(spec["design"]["total_identities"])
        and len(invalid) == 0
        and len(captured) >= 1
    )

    return {
        "experiment_id": spec["experiment_id"],
        "trial_count": len(trials),
        "classifications": dict(classifications),
        "captured_count": len(captured),
        "captured_trials": [
            row["trial_id"] for row in captured
        ],
        "invalid_count": len(invalid),
        "pilot_pass": pilot_pass,
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
                "pilot_pass": result["pilot_pass"],
                "trial_count": result["trial_count"],
                "classifications": result["classifications"],
                "captured_count": result["captured_count"],
                "captured_trials": result["captured_trials"],
                "invalid_count": result["invalid_count"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
