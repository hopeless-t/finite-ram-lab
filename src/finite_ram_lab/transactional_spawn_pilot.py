from __future__ import annotations

import argparse
import json
import os
import time
from collections import Counter
from pathlib import Path
from typing import Any

from .memcg005gc_controlled_spawn import (
    _start,
    _stop,
    _vmpte_kib,
    _wait_cpu,
    environment_receipt,
    geometry_receipt,
)
from .transaction_epoch_archive import EpochArchive
from .transactional_reprime import Event, State, reduce
from .transactional_spawn_native import (
    observed_window,
    touch_with_transaction_marker,
)


ARM_ORDER = ("b62", "b63", "b64")
BAIT_COUNT = {"b62": 61, "b63": 62, "b64": 63}
TARGET_LEN = {"b62": 3, "b63": 2, "b64": 1}
RETRIABLE_INVALIDATIONS = {
    "UNEXPECTED_REFILL",
    "DRAIN_STOCK",
    "PTE_GROWTH",
    "NORMALIZE_EXHAUSTED",
}
INSTRUMENTATION_HOLDS = {
    "TRACE_GAP",
    "CPU_MISMATCH",
    "WORKER_ERROR",
}


def load_spec(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _trace_window(
    trace_path: Path,
    *,
    trial_id: str,
    epoch: int,
    phase: str,
    touch_number: int,
) -> dict[str, Any]:
    # A tiny delay lets tracefs publish the just-closed marker window.
    time.sleep(0.001)
    return observed_window(
        trace_text=trace_path.read_text(
            encoding="utf-8",
            errors="replace",
        ),
        trial_id=trial_id,
        epoch=epoch,
        phase=phase,
        touch_number=touch_number,
    )


def _tag_touch_sequence(
    row: dict[str, Any],
    expected_worker_touched: int,
) -> dict[str, Any]:
    out = dict(row)
    out["worker_touched_expected"] = int(expected_worker_touched)
    if (
        int(out.get("worker_error", 0)) == 0
        and int(out.get("worker_touched", -1))
        != int(expected_worker_touched)
    ):
        # Synthetic runner-side error code. The C worker error space is 1..5.
        out["worker_error"] = 9001
        out["runner_error"] = "WORKER_TOUCH_SEQUENCE_MISMATCH"
    return out


def _one_touch(
    *,
    archive: EpochArchive,
    unit: dict[str, Any],
    trace_marker: Path,
    trace_path: Path,
    trial_id: str,
    epoch: int,
    phase: str,
    touch_number: int,
    page_index: int,
    stock_cpu: int,
    page_size: int,
    expected_worker_touched: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    row = touch_with_transaction_marker(
        unit=unit,
        stock_cpu=stock_cpu,
        page_size=page_size,
        page_index=page_index,
        phase=phase,
        touch_number=touch_number,
        trial_id=trial_id,
        epoch=epoch,
        trace_marker=trace_marker,
    )
    row = _tag_touch_sequence(row, expected_worker_touched)
    window = _trace_window(
        trace_path,
        trial_id=trial_id,
        epoch=epoch,
        phase=phase,
        touch_number=touch_number,
    )
    packet = archive.apply_touch(
        epoch=epoch,
        phase=phase,
        touch_number=touch_number,
        touch=row,
        window=window,
        stock_cpu=stock_cpu,
    )
    return row, packet


def _normalize(
    *,
    archive: EpochArchive,
    unit: dict[str, Any],
    sequence: list[int],
    cursor: int,
    trace_marker: Path,
    trace_path: Path,
    trial_id: str,
    stock_cpu: int,
    page_size: int,
    calibration_max: int,
    measured_count: int,
) -> tuple[int, int, list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    for touch_number in range(1, calibration_max + 1):
        if cursor >= len(sequence):
            break
        measured_count += 1
        row, packet = _one_touch(
            archive=archive,
            unit=unit,
            trace_marker=trace_marker,
            trace_path=trace_path,
            trial_id=trial_id,
            epoch=archive.tx.epoch,
            phase="NORMALIZE",
            touch_number=touch_number,
            page_index=sequence[cursor],
            stock_cpu=stock_cpu,
            page_size=page_size,
            expected_worker_touched=measured_count,
        )
        cursor += 1
        rows.append({"touch": row, "packet": packet})
        if archive.tx.state in {State.VERIFIED, State.INVALIDATED}:
            break

    if archive.tx.state is State.NORMALIZING:
        before = archive.tx.state.value
        archive.tx = reduce(archive.tx, Event.NORMALIZE_EXHAUSTED)
        archive.control_events.append(
            {
                "event": "NORMALIZE_EXHAUSTED",
                "epoch": archive.tx.epoch,
                "from_state": before,
                "result_state": archive.tx.state.value,
            }
        )
        archive.verified_at_ns = None
        archive.next_touch_index_since_verified = None

    return cursor, measured_count, rows


def _consume(
    *,
    archive: EpochArchive,
    unit: dict[str, Any],
    sequence: list[int],
    cursor: int,
    count: int,
    trace_marker: Path,
    trace_path: Path,
    trial_id: str,
    stock_cpu: int,
    page_size: int,
    measured_count: int,
) -> tuple[int, int, list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    for touch_number in range(1, count + 1):
        if cursor >= len(sequence):
            raise RuntimeError("safe span exhausted during CONSUME")
        measured_count += 1
        row, packet = _one_touch(
            archive=archive,
            unit=unit,
            trace_marker=trace_marker,
            trace_path=trace_path,
            trial_id=trial_id,
            epoch=archive.tx.epoch,
            phase="CONSUME",
            touch_number=touch_number,
            page_index=sequence[cursor],
            stock_cpu=stock_cpu,
            page_size=page_size,
            expected_worker_touched=measured_count,
        )
        cursor += 1
        rows.append({"touch": row, "packet": packet})
        if archive.tx.state in {
            State.INVALIDATED,
            State.TARGET_FAIL,
            State.ABORTED,
        }:
            break
    return cursor, measured_count, rows


def _target_bundle(
    *,
    archive: EpochArchive,
    arm_id: str,
    unit: dict[str, Any],
    sequence: list[int],
    cursor: int,
    trace_marker: Path,
    trace_path: Path,
    trial_id: str,
    stock_cpu: int,
    page_size: int,
    measured_count: int,
) -> tuple[int, int, dict[str, Any]]:
    touches: list[dict[str, Any]] = []
    windows: list[dict[str, Any]] = []

    for target_index in range(1, TARGET_LEN[arm_id] + 1):
        if cursor >= len(sequence):
            raise RuntimeError("safe span exhausted during TARGET")
        measured_count += 1
        row = touch_with_transaction_marker(
            unit=unit,
            stock_cpu=stock_cpu,
            page_size=page_size,
            page_index=sequence[cursor],
            phase="TARGET",
            touch_number=target_index,
            trial_id=trial_id,
            epoch=archive.tx.epoch,
            trace_marker=trace_marker,
        )
        row = _tag_touch_sequence(row, measured_count)
        cursor += 1
        touches.append(row)
        windows.append(
            _trace_window(
                trace_path,
                trial_id=trial_id,
                epoch=archive.tx.epoch,
                phase="TARGET",
                touch_number=target_index,
            )
        )

    packet = archive.apply_target_bundle(
        epoch=archive.tx.epoch,
        arm_id=arm_id,
        touch_number=TARGET_LEN[arm_id],
        touches=touches,
        windows=windows,
        stock_cpu=stock_cpu,
    )
    return cursor, measured_count, {
        "touches": touches,
        "packet": packet,
    }


def _start_epoch_worker(
    *,
    worker: Path,
    root: Path,
    name: str,
    prep_cpu: int,
    stock_cpu: int,
    worker_uid: int,
    safe_len: int,
) -> tuple[dict[str, Any], dict[str, Any], list[int], int]:
    unit = _start(
        worker,
        root,
        name,
        prep_cpu,
        1024,
        safe_len,
        worker_uid=worker_uid,
    )
    geometry = geometry_receipt(unit, prep_cpu)
    if not geometry["guard_cpu_match"] or not geometry["same_pte_table"]:
        _stop(unit)
        raise RuntimeError(f"invalid PTE precondition geometry: {geometry}")

    page_size = int(geometry["page_size"])
    os.sched_setaffinity(unit["pid"], {stock_cpu})
    _wait_cpu(unit["pid"], stock_cpu)

    sequence = list(
        range(
            int(geometry["safe_start"]) + 1,
            int(geometry["safe_start"]) + int(geometry["safe_len"]),
        )
    )
    return unit, geometry, sequence, page_size


def _should_reprime(archive: EpochArchive) -> bool:
    return (
        archive.tx.state is State.INVALIDATED
        and archive.tx.invalidation_reason in RETRIABLE_INVALIDATIONS
    )


def _instrumentation_hold(archive: EpochArchive) -> bool:
    return (
        archive.tx.state is State.INVALIDATED
        and archive.tx.invalidation_reason in INSTRUMENTATION_HOLDS
    )


def _run_normal_identity(
    *,
    spec: dict[str, Any],
    worker: Path,
    out_root: Path,
    trace_marker: Path,
    trace_path: Path,
    block: int,
    identity: int,
    arm_id: str,
    prep_cpu: int,
    stock_cpu: int,
    worker_uid: int,
) -> dict[str, Any]:
    trial_id = f"{block}:{identity}"
    archive = EpochArchive.start(
        max_reprimes=int(spec["transaction"]["max_reprimes"])
    )
    epochs: list[dict[str, Any]] = []

    while archive.tx.state not in {
        State.SUCCESS,
        State.TARGET_FAIL,
        State.ABORTED,
    }:
        epoch = archive.tx.epoch
        name = (
            f"fr-tx-{os.getenv('GITHUB_RUN_ID', 'local')}-"
            f"{block}-{identity}-e{epoch}"
        )
        epoch_root = out_root / f"trial-{block}-{identity}" / f"epoch-{epoch}"
        epoch_root.mkdir(parents=True, exist_ok=True)
        unit = None
        epoch_row: dict[str, Any] = {
            "epoch": epoch,
            "arm_id": arm_id,
        }
        try:
            unit, geometry, sequence, page_size = _start_epoch_worker(
                worker=worker,
                root=epoch_root,
                name=name,
                prep_cpu=prep_cpu,
                stock_cpu=stock_cpu,
                worker_uid=worker_uid,
                safe_len=int(spec["transaction"]["safe_len_pages"]),
            )
            epoch_row["geometry"] = geometry
            epoch_row["vmpte_after_guard_kib"] = _vmpte_kib(unit["pid"])

            cursor = 0
            measured_count = 0
            cursor, measured_count, normalization = _normalize(
                archive=archive,
                unit=unit,
                sequence=sequence,
                cursor=cursor,
                trace_marker=trace_marker,
                trace_path=trace_path,
                trial_id=trial_id,
                stock_cpu=stock_cpu,
                page_size=page_size,
                calibration_max=int(
                    spec["transaction"]["calibration_max_touches_per_epoch"]
                ),
                measured_count=measured_count,
            )
            epoch_row["normalization"] = normalization

            if archive.tx.state is State.VERIFIED:
                cursor, measured_count, consume = _consume(
                    archive=archive,
                    unit=unit,
                    sequence=sequence,
                    cursor=cursor,
                    count=BAIT_COUNT[arm_id],
                    trace_marker=trace_marker,
                    trace_path=trace_path,
                    trial_id=trial_id,
                    stock_cpu=stock_cpu,
                    page_size=page_size,
                    measured_count=measured_count,
                )
                epoch_row["consume"] = consume

            if archive.tx.state in {State.VERIFIED, State.EXECUTING}:
                cursor, measured_count, target = _target_bundle(
                    archive=archive,
                    arm_id=arm_id,
                    unit=unit,
                    sequence=sequence,
                    cursor=cursor,
                    trace_marker=trace_marker,
                    trace_path=trace_path,
                    trial_id=trial_id,
                    stock_cpu=stock_cpu,
                    page_size=page_size,
                    measured_count=measured_count,
                )
                epoch_row["target"] = target

            if archive.tx.state is State.COMMIT_READY:
                archive.commit()

            epoch_row["state_after"] = archive.tx.state.value
            epoch_row["invalidation_reason"] = archive.tx.invalidation_reason
            epoch_row["measured_count"] = measured_count
            epoch_row["cursor"] = cursor
        finally:
            if unit is not None:
                _stop(unit)

        epochs.append(epoch_row)

        if _instrumentation_hold(archive):
            break
        if _should_reprime(archive):
            archive.reprime()
            if archive.tx.state is State.ABORTED:
                break
            continue
        break

    result = {
        "experiment_id": spec["experiment_id"],
        "kind": "NORMAL",
        "block": block,
        "identity": identity,
        "trial_id": trial_id,
        "arm_id": arm_id,
        "prep_cpu": prep_cpu,
        "stock_cpu": stock_cpu,
        "epochs": epochs,
        "archive": archive.as_dict(),
        "final_state": archive.tx.state.value,
        "reprimes": archive.tx.reprimes,
        "invalidation_reason": archive.tx.invalidation_reason,
        "target_result": archive.tx.target_result,
    }
    return result


def _run_sentinel(
    *,
    spec: dict[str, Any],
    worker: Path,
    out_root: Path,
    trace_marker: Path,
    trace_path: Path,
    prep_cpu: int,
    stock_cpu: int,
    worker_uid: int,
) -> dict[str, Any]:
    block = 0
    identity = 99
    trial_id = "0:99"
    archive = EpochArchive.start(
        max_reprimes=int(spec["transaction"]["max_reprimes"])
    )
    epochs: list[dict[str, Any]] = []
    expected_epoch0_seen = False

    # Epoch 0: verify, then deliberately drive one extra CONSUME until Q64.
    epoch = archive.tx.epoch
    name = f"fr-tx-{os.getenv('GITHUB_RUN_ID', 'local')}-sentinel-e{epoch}"
    epoch_root = out_root / "sentinel" / f"epoch-{epoch}"
    epoch_root.mkdir(parents=True, exist_ok=True)
    unit = None
    try:
        unit, geometry, sequence, page_size = _start_epoch_worker(
            worker=worker,
            root=epoch_root,
            name=name,
            prep_cpu=prep_cpu,
            stock_cpu=stock_cpu,
            worker_uid=worker_uid,
            safe_len=int(spec["transaction"]["safe_len_pages"]),
        )
        cursor = 0
        measured_count = 0
        cursor, measured_count, normalization = _normalize(
            archive=archive,
            unit=unit,
            sequence=sequence,
            cursor=cursor,
            trace_marker=trace_marker,
            trace_path=trace_path,
            trial_id=trial_id,
            stock_cpu=stock_cpu,
            page_size=page_size,
            calibration_max=int(
                spec["transaction"]["calibration_max_touches_per_epoch"]
            ),
            measured_count=measured_count,
        )
        consume: list[dict[str, Any]] = []
        if archive.tx.state is State.VERIFIED:
            cursor, measured_count, consume = _consume(
                archive=archive,
                unit=unit,
                sequence=sequence,
                cursor=cursor,
                count=64,
                trace_marker=trace_marker,
                trace_path=trace_path,
                trial_id=trial_id,
                stock_cpu=stock_cpu,
                page_size=page_size,
                measured_count=measured_count,
            )
        expected_epoch0_seen = (
            archive.tx.state is State.INVALIDATED
            and archive.tx.invalidation_reason == "UNEXPECTED_REFILL"
        )
        epochs.append(
            {
                "epoch": 0,
                "geometry": geometry,
                "normalization": normalization,
                "consume": consume,
                "state_after": archive.tx.state.value,
                "invalidation_reason": archive.tx.invalidation_reason,
                "measured_count": measured_count,
            }
        )
    finally:
        if unit is not None:
            _stop(unit)

    if expected_epoch0_seen:
        archive.reprime()

    # Epoch 1: fresh worker, fresh Q64, then canonical b63 target.
    if archive.tx.state is State.NORMALIZING and archive.tx.epoch == 1:
        epoch = archive.tx.epoch
        name = (
            f"fr-tx-{os.getenv('GITHUB_RUN_ID', 'local')}-sentinel-e{epoch}"
        )
        epoch_root = out_root / "sentinel" / f"epoch-{epoch}"
        epoch_root.mkdir(parents=True, exist_ok=True)
        unit = None
        try:
            unit, geometry, sequence, page_size = _start_epoch_worker(
                worker=worker,
                root=epoch_root,
                name=name,
                prep_cpu=prep_cpu,
                stock_cpu=stock_cpu,
                worker_uid=worker_uid,
                safe_len=int(spec["transaction"]["safe_len_pages"]),
            )
            cursor = 0
            measured_count = 0
            cursor, measured_count, normalization = _normalize(
                archive=archive,
                unit=unit,
                sequence=sequence,
                cursor=cursor,
                trace_marker=trace_marker,
                trace_path=trace_path,
                trial_id=trial_id,
                stock_cpu=stock_cpu,
                page_size=page_size,
                calibration_max=int(
                    spec["transaction"]["calibration_max_touches_per_epoch"]
                ),
                measured_count=measured_count,
            )
            consume: list[dict[str, Any]] = []
            target: dict[str, Any] | None = None
            if archive.tx.state is State.VERIFIED:
                cursor, measured_count, consume = _consume(
                    archive=archive,
                    unit=unit,
                    sequence=sequence,
                    cursor=cursor,
                    count=BAIT_COUNT["b63"],
                    trace_marker=trace_marker,
                    trace_path=trace_path,
                    trial_id=trial_id,
                    stock_cpu=stock_cpu,
                    page_size=page_size,
                    measured_count=measured_count,
                )
            if archive.tx.state in {State.VERIFIED, State.EXECUTING}:
                cursor, measured_count, target = _target_bundle(
                    archive=archive,
                    arm_id="b63",
                    unit=unit,
                    sequence=sequence,
                    cursor=cursor,
                    trace_marker=trace_marker,
                    trace_path=trace_path,
                    trial_id=trial_id,
                    stock_cpu=stock_cpu,
                    page_size=page_size,
                    measured_count=measured_count,
                )
            if archive.tx.state is State.COMMIT_READY:
                archive.commit()
            epochs.append(
                {
                    "epoch": 1,
                    "geometry": geometry,
                    "normalization": normalization,
                    "consume": consume,
                    "target": target,
                    "state_after": archive.tx.state.value,
                    "invalidation_reason": archive.tx.invalidation_reason,
                    "measured_count": measured_count,
                }
            )
        finally:
            if unit is not None:
                _stop(unit)

    packets = archive.as_dict()["packets"]
    fresh_epoch1_q64 = any(
        int(packet["epoch"]) == 1
        and packet["phase"] == "NORMALIZE"
        and int(packet["page_counter_try_charge_64_count"]) == 1
        and int(packet["refill_stock_63_count"]) == 1
        and packet["expected_residual_after"] == 63
        for packet in packets
    )

    return {
        "experiment_id": spec["experiment_id"],
        "kind": "SENTINEL",
        "block": 0,
        "identity": 99,
        "trial_id": trial_id,
        "prep_cpu": prep_cpu,
        "stock_cpu": stock_cpu,
        "epochs": epochs,
        "archive": archive.as_dict(),
        "epoch0_expected_unexpected_refill": expected_epoch0_seen,
        "epoch1_fresh_q64": fresh_epoch1_q64,
        "final_state": archive.tx.state.value,
        "reprimes": archive.tx.reprimes,
    }


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
        raise RuntimeError("transactional spawn pilot requires >=3 CPUs")
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

    trials: list[dict[str, Any]] = []
    for identity, arm_id in enumerate(ARM_ORDER):
        row = _run_normal_identity(
            spec=spec,
            worker=worker,
            out_root=out_root,
            trace_marker=trace_marker,
            trace_path=trace_path,
            block=block,
            identity=identity,
            arm_id=arm_id,
            prep_cpu=prep_cpu,
            stock_cpu=stock_cpu,
            worker_uid=worker_uid,
        )
        path = out_root / f"trial-{block}-{identity}.json"
        path.write_text(
            json.dumps(row, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        trials.append(row)

    if block == 0:
        sentinel = _run_sentinel(
            spec=spec,
            worker=worker,
            out_root=out_root,
            trace_marker=trace_marker,
            trace_path=trace_path,
            prep_cpu=prep_cpu,
            stock_cpu=stock_cpu,
            worker_uid=worker_uid,
        )
        (out_root / "trial-0-99-sentinel.json").write_text(
            json.dumps(sentinel, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        trials.append(sentinel)

    return {
        "experiment_id": spec["experiment_id"],
        "block": block,
        "trial_count": len(trials),
        "final_states": dict(Counter(t["final_state"] for t in trials)),
    }


def aggregate(spec: dict[str, Any], input_root: Path) -> dict[str, Any]:
    trials = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(input_root.rglob("trial-*.json"))
    ]
    normals = [t for t in trials if t["kind"] == "NORMAL"]
    sentinels = [t for t in trials if t["kind"] == "SENTINEL"]

    by_arm = {}
    for arm in ARM_ORDER:
        rows = [t for t in normals if t["arm_id"] == arm]
        by_arm[arm] = {
            "n": len(rows),
            "success": sum(t["final_state"] == "SUCCESS" for t in rows),
            "target_fail": sum(
                t["final_state"] == "TARGET_FAIL" for t in rows
            ),
            "aborted": sum(t["final_state"] == "ABORTED" for t in rows),
            "reprimes": sum(int(t["reprimes"]) for t in rows),
        }

    invalidations = Counter()
    for trial in trials:
        for epoch in trial.get("epochs", []):
            reason = epoch.get("invalidation_reason")
            if reason:
                invalidations[str(reason)] += 1

    sentinel_ok = (
        len(sentinels) == 1
        and sentinels[0].get("epoch0_expected_unexpected_refill") is True
        and sentinels[0].get("epoch1_fresh_q64") is True
        and sentinels[0].get("final_state") == "SUCCESS"
    )

    expected_normal_count = int(spec["normal_lane"]["raw_identities"])
    normal_success = sum(t["final_state"] == "SUCCESS" for t in normals)
    target_fail = sum(t["final_state"] == "TARGET_FAIL" for t in normals)
    instrumentation_hold = sum(
        any(
            epoch.get("invalidation_reason") in INSTRUMENTATION_HOLDS
            for epoch in t.get("epochs", [])
        )
        for t in normals
    )

    return {
        "experiment_id": spec["experiment_id"],
        "trial_count": len(trials),
        "normal_count": len(normals),
        "normal_success": normal_success,
        "target_fail": target_fail,
        "instrumentation_hold": instrumentation_hold,
        "sentinel_count": len(sentinels),
        "sentinel_pass": sentinel_ok,
        "invalidation_counts": dict(invalidations),
        "reprimes_total": sum(int(t["reprimes"]) for t in trials),
        "by_arm": by_arm,
        "protocol_smoke_pass": (
            len(normals) == expected_normal_count
            and normal_success == expected_normal_count
            and target_fail == 0
            and instrumentation_hold == 0
            and sentinel_ok
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
                "protocol_smoke_pass": result["protocol_smoke_pass"],
                "normal_success": result["normal_success"],
                "target_fail": result["target_fail"],
                "instrumentation_hold": result["instrumentation_hold"],
                "sentinel_pass": result["sentinel_pass"],
                "invalidation_counts": result["invalidation_counts"],
                "reprimes_total": result["reprimes_total"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
