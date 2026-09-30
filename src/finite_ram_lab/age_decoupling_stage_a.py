from __future__ import annotations

import argparse
import json
import os
import statistics
import time
from collections import Counter
from pathlib import Path
from typing import Any

from .epoch_continuity import scan_interwindow_continuity
from .memcg005gc_controlled_spawn import _stop, environment_receipt
from .startup_stock_seed_phase import _delta_counts, _profile_counts
from .transaction_epoch_archive import EpochArchive
from .transaction_trace_observer import (
    observer_receipt_for_window,
    parse_transaction_trace,
)
from .transactional_reprime import State
from .transactional_spawn_native import (
    touch_with_transaction_marker,
    write_marker,
)
from .transactional_spawn_pilot import (
    _target_bundle,
    _trace_window,
    _tag_touch_sequence,
)
from .tx_perturbation_matrix import (
    TARGET_COMM,
    _close_owner_probe,
    _consume_segment,
    _fresh_epoch,
)


Q64_EVENT = "frl_pc_try64"
REFILL_EVENT = "frl_refill_stock"
OWNER_UNCHARGE_EVENT = "frl_pc_uncharge_owner"
DWELL_MARKER_TOUCH = 3200


def load_spec(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _probe_dir(trace_path: Path, event: str) -> Path:
    return trace_path.parent / "events" / "kprobes" / event


def _prepare_refill_preverify(trace_path: Path) -> None:
    probe = _probe_dir(trace_path, REFILL_EVENT)
    (probe / "enable").write_text("0\n", encoding="utf-8")
    (probe / "filter").write_text(
        f'comm == "{TARGET_COMM}" && nr_pages == 63\n',
        encoding="utf-8",
    )
    (probe / "enable").write_text("1\n", encoding="utf-8")


def _bind_refill_owner(
    trace_path: Path,
    owner_memcg: str,
) -> None:
    probe = _probe_dir(trace_path, REFILL_EVENT)
    (probe / "enable").write_text("0\n", encoding="utf-8")
    (probe / "filter").write_text(
        f"memcg == {owner_memcg}\n",
        encoding="utf-8",
    )
    (probe / "enable").write_text("1\n", encoding="utf-8")


def _close_refill_probe(trace_path: Path) -> None:
    probe = _probe_dir(trace_path, REFILL_EVENT)
    try:
        (probe / "enable").write_text("0\n", encoding="utf-8")
        (probe / "filter").write_text(
            "memcg == 0\n",
            encoding="utf-8",
        )
    except OSError:
        pass


def _profile_snapshot(trace_path: Path) -> dict[str, Any]:
    return {
        name: _profile_counts(trace_path, name)
        for name in (
            Q64_EVENT,
            REFILL_EVENT,
            OWNER_UNCHARGE_EVENT,
        )
    }


def _profile_delta(
    before: dict[str, Any],
    after: dict[str, Any],
) -> dict[str, Any]:
    return {
        name: _delta_counts(before.get(name), after.get(name))
        for name in before
    }


def _coverage_ok(delta: dict[str, Any]) -> bool:
    return all(
        row is not None and int(row.get("missed", -1)) == 0
        for row in delta.values()
    )


def _dwell_checkpoint(
    *,
    archive: EpochArchive,
    trace_marker: Path,
    trace_path: Path,
    trial_id: str,
    stock_cpu: int,
    dwell_ns: int,
    arm: str,
) -> dict[str, Any]:
    write_marker(
        trace_marker,
        trial_id=trial_id,
        epoch=archive.tx.epoch,
        phase="OBSERVE",
        touch_number=DWELL_MARKER_TOUCH,
        edge="PRE",
    )
    if int(dwell_ns) > 0:
        time.sleep(int(dwell_ns) / 1_000_000_000)
    write_marker(
        trace_marker,
        trial_id=trial_id,
        epoch=archive.tx.epoch,
        phase="OBSERVE",
        touch_number=DWELL_MARKER_TOUCH,
        edge="POST",
    )

    window = _trace_window(
        trace_path,
        trial_id=trial_id,
        epoch=archive.tx.epoch,
        phase="OBSERVE",
        touch_number=DWELL_MARKER_TOUCH,
    )
    receipt = observer_receipt_for_window(
        window,
        owner_counter=archive.owner_counter,
        owner_memcg=archive.owner_memcg,
        stock_cpu=stock_cpu,
        phase="OBSERVE",
        owner_probe_filtered=True,
    )
    event = archive.apply_neutral_window(
        epoch=archive.tx.epoch,
        touch_number=DWELL_MARKER_TOUCH,
        window=window,
        stock_cpu=stock_cpu,
        label=f"AGE_{arm}_CHECKPOINT",
        owner_probe_filtered=True,
    )
    pre_ns = receipt.get("marker_pre_ns")
    post_ns = receipt.get("marker_post_ns")
    return {
        "requested_ns": int(dwell_ns),
        "observed_ns": (
            None
            if pre_ns is None or post_ns is None
            else int(post_ns) - int(pre_ns)
        ),
        "receipt": receipt,
        "event": event,
    }


def _first_measured_q64(
    trace_text: str,
    *,
    trial_id: str,
    epoch: int,
    owner_counter: str,
    stock_cpu: int,
) -> dict[str, Any] | None:
    windows = parse_transaction_trace(trace_text)
    found: list[dict[str, Any]] = []

    for key, window in windows.items():
        trial, item_epoch, phase, touch = key
        if trial != trial_id or int(item_epoch) != int(epoch):
            continue
        if phase not in {"CONSUME", "TARGET"}:
            continue

        if phase == "CONSUME":
            measured_touch = int(touch)
        else:
            measured_touch = 62 + int(touch)

        for event in window.get("pc_try64", []):
            if (
                str(event.get("counter", "")).lower()
                != owner_counter.lower()
            ):
                continue
            if int(event.get("cpu", -1)) != int(stock_cpu):
                continue
            if event.get("timestamp_ns") is None:
                continue
            found.append(
                {
                    "T": measured_touch,
                    "timestamp_ns": int(event["timestamp_ns"]),
                    "phase": phase,
                    "phase_touch": int(touch),
                    "event": event,
                }
            )

    if not found:
        return None
    return min(found, key=lambda row: int(row["timestamp_ns"]))


def _late_boundary_scan(
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
    owner_memcg: str,
    max_extra: int,
) -> tuple[int, int, dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    located: dict[str, Any] | None = None
    stop_reason: str | None = None

    for target_touch in range(3, 3 + int(max_extra)):
        if cursor >= len(sequence):
            stop_reason = "SAFE_SPAN_EXHAUSTED"
            break

        measured_count += 1
        row = touch_with_transaction_marker(
            unit=unit,
            stock_cpu=stock_cpu,
            page_size=page_size,
            page_index=sequence[cursor],
            phase="TARGET",
            touch_number=target_touch,
            trial_id=trial_id,
            epoch=epoch,
            trace_marker=trace_marker,
        )
        row = _tag_touch_sequence(row, measured_count)
        cursor += 1

        window = _trace_window(
            trace_path,
            trial_id=trial_id,
            epoch=epoch,
            phase="TARGET",
            touch_number=target_touch,
        )
        receipt = observer_receipt_for_window(
            window,
            owner_counter=owner_counter,
            owner_memcg=owner_memcg,
            stock_cpu=stock_cpu,
            phase="TARGET",
            target_comm=TARGET_COMM,
            owner_probe_filtered=True,
        )
        item = {
            "touch": row,
            "receipt": receipt,
            "T": 62 + target_touch,
        }
        rows.append(item)

        if not bool(receipt.get("trace_complete", False)):
            stop_reason = "TRACE_GAP"
            break
        if int(row.get("worker_error", 0)) != 0:
            stop_reason = "WORKER_ERROR"
            break
        if int(row.get("observed_cpu", -1)) != int(stock_cpu):
            stop_reason = "CPU_MISMATCH"
            break
        if int(row.get("vmpte_delta_kib", 0)) != 0:
            stop_reason = "PTE_GROWTH"
            break
        if int(receipt.get("unknown_emission_count", 0)) > 0:
            stop_reason = "UNKNOWN_EMISSION"
            break
        if int(receipt.get("drain_stock_count", 0)) > 0:
            stop_reason = "TARGET_STOCK_EVICTION"
            break
        if int(receipt.get("owner_refill_non63_count", 0)) > 0:
            stop_reason = "OWNER_REFILL_NON63"
            break

        if int(receipt.get("page_counter_try_charge_64_count", 0)) > 0:
            located = {
                "T": 62 + target_touch,
                "timestamp_ns": next(
                    (
                        int(event["timestamp_ns"])
                        for event in window.get("pc_try64", [])
                        if (
                            str(event.get("counter", "")).lower()
                            == owner_counter.lower()
                            and int(event.get("cpu", -1))
                            == int(stock_cpu)
                            and event.get("timestamp_ns") is not None
                        )
                    ),
                    None,
                ),
                "phase": "TARGET",
                "phase_touch": target_touch,
            }
            stop_reason = "Q64_LOCATED"
            break

        if int(receipt.get("refill_stock_63_count", 0)) > 0:
            stop_reason = "REFILL63_WITHOUT_Q64"
            break

    return cursor, measured_count, {
        "rows": rows,
        "located": located,
        "stop_reason": stop_reason,
    }


def _continuity(
    *,
    archive: EpochArchive,
    trace_path: Path,
    trial_id: str,
    stock_cpu: int,
) -> dict[str, Any]:
    if (
        archive.owner_counter is None
        or archive.owner_memcg is None
        or archive.verified_at_ns is None
    ):
        return {
            "schema_version": "epoch-gap-continuity-v5",
            "coverage": "OWNER_OR_VERIFIED_TIME_MISSING",
            "gap_clean": False,
            "unknown_count": 1,
        }
    return scan_interwindow_continuity(
        trace_path.read_text(
            encoding="utf-8",
            errors="replace",
        ),
        trial_id=trial_id,
        epoch=archive.tx.epoch,
        owner_counter=archive.owner_counter,
        owner_memcg=archive.owner_memcg,
        stock_cpu=stock_cpu,
        verified_at_ns=archive.verified_at_ns,
    )


def _packet_totals(archive: EpochArchive) -> dict[str, int]:
    return {
        "owner_refill_non63": sum(
            int(packet.get("owner_refill_non63_count", 0))
            for packet in archive.packets
        ),
        "drain_stock": sum(
            int(packet.get("drain_stock_count", 0))
            for packet in archive.packets
        ),
        "unknown": sum(
            int(packet.get("unknown_emission_count", 0))
            for packet in archive.packets
        ),
        "release_only": sum(
            int(packet.get("classified_release_only_count", 0))
            for packet in archive.packets
        ),
    }


def _known_hazard(
    *,
    archive: EpochArchive,
    dwell: dict[str, Any] | None,
    continuity: dict[str, Any],
) -> str | None:
    totals = _packet_totals(archive)

    if int(continuity.get("target_drain_count", 0)) > 0:
        return "TARGET_STOCK_EVICTION"
    if int(totals["drain_stock"]) > 0:
        return "TARGET_STOCK_EVICTION"

    if int(continuity.get("target_refill_non63_count", 0)) > 0:
        return "OWNER_REFILL_NON63"
    if int(totals["owner_refill_non63"]) > 0:
        return "OWNER_REFILL_NON63"

    if (
        int(continuity.get("target_charge64_count", 0)) > 0
        or int(continuity.get("target_refill_count", 0)) > 0
    ):
        return "OWNER_Q64_OR_REFILL"

    if dwell is not None:
        receipt = dwell.get("receipt", {})
        if int(receipt.get("drain_stock_count", 0)) > 0:
            return "TARGET_STOCK_EVICTION"
        if int(receipt.get("owner_refill_non63_count", 0)) > 0:
            return "OWNER_REFILL_NON63"
        if (
            int(receipt.get("page_counter_try_charge_64_count", 0)) > 0
            or int(receipt.get("owner_refill_any_count", 0)) > 0
        ):
            return "OWNER_Q64_OR_REFILL"

    if archive.tx.invalidation_reason == "PTE_GROWTH":
        return "PTE_GROWTH"
    return None


def _classify(
    *,
    archive: EpochArchive,
    normalized: bool,
    coverage_ok: bool,
    continuity: dict[str, Any],
    dwell: dict[str, Any] | None,
    first_q64: dict[str, Any] | None,
    late_scan: dict[str, Any] | None,
) -> tuple[str, str | None]:
    if not normalized:
        return "PREVERIFY_HOLD", archive.tx.invalidation_reason

    if not coverage_ok:
        return "INSTRUMENTATION_HOLD", "CRITICAL_PROBE_MISS"

    hazard = _known_hazard(
        archive=archive,
        dwell=dwell,
        continuity=continuity,
    )
    if hazard is not None:
        return "KNOWN_STATE_CHANGE", hazard

    packet_unknown = int(_packet_totals(archive)["unknown"])
    dwell_unknown = (
        0
        if dwell is None
        else int(
            dwell.get("receipt", {}).get(
                "unknown_emission_count",
                0,
            )
        )
    )
    dwell_trace_complete = (
        True
        if dwell is None
        else bool(
            dwell.get("receipt", {}).get(
                "trace_complete",
                False,
            )
        )
    )
    if (
        int(continuity.get("unknown_count", 0)) > 0
        or packet_unknown > 0
        or (dwell_unknown > 0 and dwell_trace_complete)
    ):
        return "UNKNOWN_COMPLETE_EMISSION", "OWNER_EVENT_UNCLASSIFIED"

    if archive.tx.invalidation_reason in {
        "CPU_MISMATCH",
        "WORKER_ERROR",
        "TRACE_GAP",
    }:
        return "INSTRUMENTATION_HOLD", archive.tx.invalidation_reason

    if first_q64 is None and late_scan is not None:
        first_q64 = late_scan.get("located")

    T = None if first_q64 is None else int(first_q64["T"])

    if archive.tx.state is State.SUCCESS:
        if T == 64:
            return "CANONICAL_SUCCESS", None
        return "UNEXPLAINED_BOUNDARY_DEVIATION", "SUCCESS_WITH_NONCANONICAL_T"

    if archive.tx.state is State.TARGET_FAIL:
        if T == 64:
            return "TRUE_TARGET_FAIL", "TARGET_MISMATCH_AT_CANONICAL_T"
        return "UNEXPLAINED_BOUNDARY_DEVIATION", (
            "LATE_OR_EARLY_BOUNDARY"
            if T is not None
            else "BOUNDARY_NOT_LOCATED"
        )

    if archive.tx.state is State.INVALIDATED:
        return "KNOWN_STATE_CHANGE", archive.tx.invalidation_reason

    return "INSTRUMENTATION_HOLD", f"UNEXPECTED_STATE:{archive.tx.state.value}"


def run_trial(
    *,
    spec: dict[str, Any],
    worker: Path,
    out_root: Path,
    trace_marker: Path,
    trace_path: Path,
    block: int,
    identity: int,
    arm: str,
    prep_cpu: int,
    stock_cpu: int,
    worker_uid: int,
) -> dict[str, Any]:
    trial_id = f"{block}:{identity}"
    archive = EpochArchive.start(max_reprimes=0)
    unit = None
    dwell: dict[str, Any] | None = None
    late_scan: dict[str, Any] | None = None
    normalized = False

    before_profile = _profile_snapshot(trace_path)
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
            arm=arm,
            prep_cpu=prep_cpu,
            stock_cpu=stock_cpu,
            worker_uid=worker_uid,
            safe_len=256,
            calibration_max=64,
        )

        normalized = (
            archive.tx.state is State.VERIFIED
            and archive.owner_counter is not None
            and archive.owner_memcg is not None
        )
        if normalized:
            # _fresh_epoch() already binds the owner-uncharge probe.
            _bind_refill_owner(trace_path, archive.owner_memcg)

            cursor, measured_count, consume_a = _consume_segment(
                archive=archive,
                unit=unit,
                sequence=sequence,
                cursor=cursor,
                start_touch=1,
                count=32,
                trace_marker=trace_marker,
                trace_path=trace_path,
                trial_id=trial_id,
                stock_cpu=stock_cpu,
                page_size=page_size,
                measured_count=measured_count,
            )
            epoch_row["consume_before_hold"] = consume_a

            if archive.tx.state in {State.VERIFIED, State.EXECUTING}:
                dwell_ns = (
                    0
                    if arm == "FAST"
                    else int(spec["timing_reference"]["dwell_ns"])
                )
                dwell = _dwell_checkpoint(
                    archive=archive,
                    trace_marker=trace_marker,
                    trace_path=trace_path,
                    trial_id=trial_id,
                    stock_cpu=stock_cpu,
                    dwell_ns=dwell_ns,
                    arm=arm,
                )
                epoch_row["checkpoint"] = dwell

            if archive.tx.state in {State.VERIFIED, State.EXECUTING}:
                cursor, measured_count, consume_b = _consume_segment(
                    archive=archive,
                    unit=unit,
                    sequence=sequence,
                    cursor=cursor,
                    start_touch=33,
                    count=30,
                    trace_marker=trace_marker,
                    trace_path=trace_path,
                    trial_id=trial_id,
                    stock_cpu=stock_cpu,
                    page_size=page_size,
                    measured_count=measured_count,
                )
                epoch_row["consume_after_hold"] = consume_b

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
                    target_comm=TARGET_COMM,
                    owner_probe_filtered=True,
                )
                epoch_row["target"] = target

            prediagnostic_continuity = _continuity(
                archive=archive,
                trace_path=trace_path,
                trial_id=trial_id,
                stock_cpu=stock_cpu,
            )

            trace_text = trace_path.read_text(
                encoding="utf-8",
                errors="replace",
            )
            first_q64 = _first_measured_q64(
                trace_text,
                trial_id=trial_id,
                epoch=archive.tx.epoch,
                owner_counter=archive.owner_counter,
                stock_cpu=stock_cpu,
            )

            if (
                archive.tx.state is State.TARGET_FAIL
                and first_q64 is None
                and int(
                    spec["stage_a"][
                        "late_boundary_diagnostic_max_extra_touches"
                    ]
                )
                > 0
            ):
                cursor, measured_count, late_scan = _late_boundary_scan(
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
                    owner_memcg=archive.owner_memcg,
                    max_extra=int(
                        spec["stage_a"][
                            "late_boundary_diagnostic_max_extra_touches"
                        ]
                    ),
                )
                epoch_row["late_scan"] = late_scan
                if late_scan.get("located") is not None:
                    first_q64 = late_scan["located"]

            if archive.tx.state is State.COMMIT_READY:
                archive.commit()

        else:
            prediagnostic_continuity = _continuity(
                archive=archive,
                trace_path=trace_path,
                trial_id=trial_id,
                stock_cpu=stock_cpu,
            )
            first_q64 = None

        after_profile = _profile_snapshot(trace_path)
        coverage_delta = _profile_delta(
            before_profile,
            after_profile,
        )
        critical_coverage_ok = _coverage_ok(coverage_delta)

        classification, detail = _classify(
            archive=archive,
            normalized=normalized,
            coverage_ok=critical_coverage_ok,
            continuity=prediagnostic_continuity,
            dwell=dwell,
            first_q64=first_q64,
            late_scan=late_scan,
        )

        T = None if first_q64 is None else int(first_q64["T"])
        first_q64_at_ns = (
            None
            if first_q64 is None
            else first_q64.get("timestamp_ns")
        )
        verified_at_ns = archive.verified_at_ns
        elapsed_ns = (
            None
            if (
                first_q64_at_ns is None
                or verified_at_ns is None
            )
            else int(first_q64_at_ns) - int(verified_at_ns)
        )

        epoch_row["state_after"] = archive.tx.state.value
        epoch_row["invalidation_reason"] = archive.tx.invalidation_reason
        epoch_row["measured_count"] = measured_count
        epoch_row["cursor"] = cursor
        epoch_row["continuity"] = prediagnostic_continuity

        return {
            "experiment_id": spec["experiment_id"],
            "trial_id": trial_id,
            "block": block,
            "identity": identity,
            "arm": arm,
            "prep_cpu": prep_cpu,
            "stock_cpu": stock_cpu,
            "normalized": normalized,
            "owner_counter": archive.owner_counter,
            "owner_memcg": archive.owner_memcg,
            "verified_at_ns": verified_at_ns,
            "first_q64": first_q64,
            "T_first_post_primer_direct_q64": T,
            "Delta_T_minus_64": None if T is None else T - 64,
            "first_q64_at_ns": first_q64_at_ns,
            "elapsed_ns_verified_to_q64": elapsed_ns,
            "dwell": dwell,
            "continuity": prediagnostic_continuity,
            "critical_probe_delta": coverage_delta,
            "critical_probe_coverage_ok": critical_coverage_ok,
            "packet_totals": _packet_totals(archive),
            "release_only_count": archive.tx.release_only_count,
            "classification": classification,
            "classification_detail": detail,
            "known_hazard_kind": (
                detail
                if classification == "KNOWN_STATE_CHANGE"
                else None
            ),
            "final_state": archive.tx.state.value,
            "invalidation_reason": archive.tx.invalidation_reason,
            "target_result": archive.tx.target_result,
            "late_scan": late_scan,
            "epoch": epoch_row,
            "archive": archive.as_dict(),
        }
    finally:
        _close_owner_probe(trace_path)
        _close_refill_probe(trace_path)
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
        raise RuntimeError("age decoupling requires >=3 CPUs")
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

    order = list(
        spec["stage_a"]["frozen_randomization"]["orders"][
            str(block)
        ]
    )
    rows: list[dict[str, Any]] = []

    for identity, arm in enumerate(order):
        row = run_trial(
            spec=spec,
            worker=worker,
            out_root=out_root,
            trace_marker=trace_marker,
            trace_path=trace_path,
            block=block,
            identity=identity,
            arm=arm,
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
        "order": order,
        "trial_count": len(rows),
        "classifications": dict(
            Counter(row["classification"] for row in rows)
        ),
        "by_arm": {
            arm: {
                "n": sum(row["arm"] == arm for row in rows),
                "classifications": dict(
                    Counter(
                        row["classification"]
                        for row in rows
                        if row["arm"] == arm
                    )
                ),
                "T": [
                    row["T_first_post_primer_direct_q64"]
                    for row in rows
                    if (
                        row["arm"] == arm
                        and row[
                            "T_first_post_primer_direct_q64"
                        ]
                        is not None
                    )
                ],
            }
            for arm in ("FAST", "HOLD32")
        },
    }


def _median(values: list[int]) -> float | None:
    if not values:
        return None
    return float(statistics.median(values))


def aggregate(
    spec: dict[str, Any],
    input_root: Path,
) -> dict[str, Any]:
    trials = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(input_root.rglob("trial-*.json"))
    ]

    by_arm: dict[str, Any] = {}
    for arm in ("FAST", "HOLD32"):
        rows = [row for row in trials if row["arm"] == arm]
        canonical = [
            row
            for row in rows
            if row["classification"] == "CANONICAL_SUCCESS"
        ]
        elapsed = [
            int(row["elapsed_ns_verified_to_q64"])
            for row in canonical
            if row.get("elapsed_ns_verified_to_q64") is not None
        ]
        dwell_observed = [
            int(row["dwell"]["observed_ns"])
            for row in rows
            if (
                row.get("dwell") is not None
                and row["dwell"].get("observed_ns") is not None
            )
        ]
        by_arm[arm] = {
            "n": len(rows),
            "classifications": dict(
                Counter(row["classification"] for row in rows)
            ),
            "canonical_n": len(canonical),
            "known_state_change_n": sum(
                row["classification"] == "KNOWN_STATE_CHANGE"
                for row in rows
            ),
            "unexplained_boundary_deviation_n": sum(
                row["classification"]
                == "UNEXPLAINED_BOUNDARY_DEVIATION"
                for row in rows
            ),
            "true_target_fail_n": sum(
                row["classification"] == "TRUE_TARGET_FAIL"
                for row in rows
            ),
            "unknown_complete_emission_n": sum(
                row["classification"] == "UNKNOWN_COMPLETE_EMISSION"
                for row in rows
            ),
            "instrumentation_hold_n": sum(
                row["classification"] == "INSTRUMENTATION_HOLD"
                for row in rows
            ),
            "preverify_hold_n": sum(
                row["classification"] == "PREVERIFY_HOLD"
                for row in rows
            ),
            "T_histogram": dict(
                Counter(
                    int(row["T_first_post_primer_direct_q64"])
                    for row in rows
                    if row.get(
                        "T_first_post_primer_direct_q64"
                    )
                    is not None
                )
            ),
            "median_elapsed_ns_canonical": _median(elapsed),
            "median_checkpoint_ns": _median(dwell_observed),
            "known_hazards": dict(
                Counter(
                    str(row["known_hazard_kind"])
                    for row in rows
                    if row.get("known_hazard_kind") is not None
                )
            ),
        }

    fast_median = by_arm["FAST"]["median_elapsed_ns_canonical"]
    hold_median = by_arm["HOLD32"]["median_elapsed_ns_canonical"]
    realized_factor = (
        None
        if (
            fast_median is None
            or hold_median is None
            or float(fast_median) <= 0
        )
        else float(hold_median) / float(fast_median)
    )

    stage_b_trigger = any(
        row["arm"] == "HOLD32"
        and row["classification"]
        == "UNEXPLAINED_BOUNDARY_DEVIATION"
        for row in trials
    )
    known_hold_hazard = any(
        row["arm"] == "HOLD32"
        and row["classification"] == "KNOWN_STATE_CHANGE"
        for row in trials
    )
    unknown_hold = any(
        row["arm"] == "HOLD32"
        and row["classification"] == "UNKNOWN_COMPLETE_EMISSION"
        for row in trials
    )

    return {
        "experiment_id": spec["experiment_id"],
        "trial_count": len(trials),
        "expected_trial_count": int(
            spec["stage_a"]["total_identities"]
        ),
        "classifications": dict(
            Counter(row["classification"] for row in trials)
        ),
        "by_arm": by_arm,
        "nominal_exposure_factor": int(
            spec["timing_reference"][
                "nominal_total_exposure_factor"
            ]
        ),
        "realized_exposure_factor_canonical_medians": (
            realized_factor
        ),
        "stage_b_trigger": stage_b_trigger,
        "known_hold_hazard_requires_council": known_hold_hazard,
        "unknown_hold_requires_council": unknown_hold,
        "true_target_fail_count": sum(
            row["classification"] == "TRUE_TARGET_FAIL"
            for row in trials
        ),
        "critical_probe_miss_trials": [
            row["trial_id"]
            for row in trials
            if not bool(row["critical_probe_coverage_ok"])
        ],
        "evidence_panel_complete": (
            len(trials)
            == int(spec["stage_a"]["total_identities"])
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
                "trial_count": result["trial_count"],
                "classifications": result["classifications"],
                "by_arm": result["by_arm"],
                "realized_exposure_factor": result[
                    "realized_exposure_factor_canonical_medians"
                ],
                "stage_b_trigger": result["stage_b_trigger"],
                "known_hold_hazard_requires_council": result[
                    "known_hold_hazard_requires_council"
                ],
                "unknown_hold_requires_council": result[
                    "unknown_hold_requires_council"
                ],
                "true_target_fail_count": result[
                    "true_target_fail_count"
                ],
                "critical_probe_miss_trials": result[
                    "critical_probe_miss_trials"
                ],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
