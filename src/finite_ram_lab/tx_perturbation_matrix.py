from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any

from .memcg005gc_controlled_spawn import (
    OFF_DONE,
    OFF_ERROR,
    OFF_GO,
    OFF_MODE,
    OFF_OBS_CPU,
    OFF_PAGE_INDEX,
    OFF_TARGET,
    OFF_TOUCHED,
    _current,
    _set_u32,
    _stop,
    _u32,
    _vmpte_kib,
    _wait,
    environment_receipt,
)
from .obs005_cross_cgroup_lru import (
    CMD_TOUCH,
    _command as _handoff_command,
    _event_count,
    _start_role,
    _stop_role,
)
from .obs006_charge_side_q64 import _discard
from .epoch_continuity import scan_interwindow_continuity
from .probe_coverage import summarize_probe_coverage
from .transaction_epoch_archive import EpochArchive
from .transactional_reprime import State
from .transactional_spawn_native import write_marker
from .transactional_spawn_pilot import (
    _normalize,
    _one_touch,
    _start_epoch_worker,
    _target_bundle,
    _trace_window,
    _tag_touch_sequence,
)

ARM_ORDER = ("CLEAN", "RELEASE_ONLY", "UNEXPECTED_REFILL", "PTE_GROWTH")
MODE_PTE_ESCAPE = 4
TARGET_COMM = "frltx405"
OWNER_UNCHARGE_EVENT = "frl_pc_uncharge_owner"


def _owner_probe_dir(trace_path: Path) -> Path:
    return trace_path.parent / "events" / "kprobes" / OWNER_UNCHARGE_EVENT


def _prepare_owner_probe_global(trace_path: Path) -> None:
    """Observe all uncharges only during NORMALIZE so owner identity can be bound."""
    probe = _owner_probe_dir(trace_path)
    (probe / "filter").write_text("0\n", encoding="utf-8")
    (probe / "enable").write_text("1\n", encoding="utf-8")


def _bind_owner_probe(trace_path: Path, owner_counter: str) -> None:
    """Narrow the already-enabled probe to the verified epoch owner counter."""
    probe = _owner_probe_dir(trace_path)
    (probe / "filter").write_text(
        f"counter == {owner_counter}\n",
        encoding="utf-8",
    )


def load_spec(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _consume_segment(
    *,
    archive: EpochArchive,
    unit: dict[str, Any],
    sequence: list[int],
    cursor: int,
    start_touch: int,
    count: int,
    trace_marker: Path,
    trace_path: Path,
    trial_id: str,
    stock_cpu: int,
    page_size: int,
    measured_count: int,
) -> tuple[int, int, list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    for offset in range(count):
        touch_number = start_touch + offset
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
            target_comm=TARGET_COMM,
            owner_probe_filtered=True,
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


def _pte_escape_index(geometry: dict[str, Any], *, max_pages: int = 1024) -> int:
    page_size = int(geometry["page_size"])
    if page_size != 4096:
        raise RuntimeError("PTE escape selector requires 4096-byte pages")
    region_addr = int(geometry["region_addr"])
    guard_index = int(geometry["guard_index"])
    base_page = region_addr // page_size
    guard_table = (base_page + guard_index) // 512
    safe_start = int(geometry["safe_start"])
    safe_end = safe_start + int(geometry["safe_len"])
    for index in range(max_pages):
        if safe_start <= index < safe_end:
            continue
        if (base_page + index) // 512 != guard_table:
            return index
    raise RuntimeError("no distinct PTE-table page available")


def _pte_escape_touch(
    *,
    archive: EpochArchive,
    unit: dict[str, Any],
    stock_cpu: int,
    page_size: int,
    page_index: int,
    trace_marker: Path,
    trace_path: Path,
    trial_id: str,
    epoch: int,
    touch_number: int,
    expected_worker_touched: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    write_marker(
        trace_marker,
        trial_id=trial_id,
        epoch=epoch,
        phase="CONSUME",
        touch_number=touch_number,
        edge="PRE",
    )
    _set_u32(unit["mm"], OFF_MODE, MODE_PTE_ESCAPE)
    _set_u32(unit["mm"], OFF_TARGET, stock_cpu)
    _set_u32(unit["mm"], OFF_PAGE_INDEX, page_index)
    _set_u32(unit["mm"], OFF_DONE, 0)
    _set_u32(unit["mm"], OFF_ERROR, 0)

    current_pre = _current(unit["cg"])
    vmpte_pre = _vmpte_kib(unit["pid"])
    _set_u32(unit["mm"], OFF_GO, 1)
    _wait(lambda: _u32(unit["mm"], OFF_DONE) == 1)
    current_post = _current(unit["cg"])
    vmpte_post = _vmpte_kib(unit["pid"])

    write_marker(
        trace_marker,
        trial_id=trial_id,
        epoch=epoch,
        phase="CONSUME",
        touch_number=touch_number,
        edge="POST",
    )
    row = {
        "phase": "CONSUME",
        "page_index": page_index,
        "current_pre_bytes": current_pre,
        "current_post_bytes": current_post,
        "delta_pages": (current_post - current_pre) / page_size,
        "vmpte_pre_kib": vmpte_pre,
        "vmpte_post_kib": vmpte_post,
        "vmpte_delta_kib": vmpte_post - vmpte_pre,
        "observed_cpu": _u32(unit["mm"], OFF_OBS_CPU),
        "worker_error": _u32(unit["mm"], OFF_ERROR),
        "worker_touched": _u32(unit["mm"], OFF_TOUCHED),
    }
    row = _tag_touch_sequence(row, expected_worker_touched)
    window = _trace_window(
        trace_path,
        trial_id=trial_id,
        epoch=epoch,
        phase="CONSUME",
        touch_number=touch_number,
    )
    packet = archive.apply_touch(
        epoch=epoch,
        phase="CONSUME",
        touch_number=touch_number,
        touch=row,
        window=window,
        stock_cpu=stock_cpu,
        target_comm=TARGET_COMM,
        owner_probe_filtered=True,
    )
    return row, packet


def _postverify_prime_helper_stock(
    *,
    archive: EpochArchive,
    helper: dict[str, Any],
    helper_comm: str,
    trace_marker: Path,
    trace_path: Path,
    trial_id: str,
    stock_cpu: int,
    max_touches: int,
    touch_number: int,
    label: str,
) -> dict[str, Any]:
    """Force a helper Q64 after VERIFY while proving target state is neutral."""
    baseline = _event_count(
        trace_path,
        "frl_pc_try64:",
        helper_comm,
    )
    rows: list[dict[str, Any]] = []
    q64_touch: int | None = None

    write_marker(
        trace_marker,
        trial_id=trial_id,
        epoch=archive.tx.epoch,
        phase="OBSERVE",
        touch_number=touch_number,
        edge="PRE",
    )
    try:
        for touch in range(1, max_touches + 1):
            row = _handoff_command(helper, CMD_TOUCH)
            rows.append({"touch": touch, **row})
            if (
                _event_count(
                    trace_path,
                    "frl_pc_try64:",
                    helper_comm,
                )
                > baseline
            ):
                q64_touch = touch
                break
    finally:
        write_marker(
            trace_marker,
            trial_id=trial_id,
            epoch=archive.tx.epoch,
            phase="OBSERVE",
            touch_number=touch_number,
            edge="POST",
        )

    window = _trace_window(
        trace_path,
        trial_id=trial_id,
        epoch=archive.tx.epoch,
        phase="OBSERVE",
        touch_number=touch_number,
    )
    event = archive.apply_neutral_window(
        epoch=archive.tx.epoch,
        touch_number=touch_number,
        window=window,
        stock_cpu=stock_cpu,
        label=label,
        owner_probe_filtered=True,
    )
    passed = (
        q64_touch is not None
        and event.get("result") == "NEUTRAL"
        and archive.tx.state in {State.VERIFIED, State.EXECUTING}
    )
    return {
        "q64_touch": q64_touch,
        "rows": rows,
        "event": event,
        "pass": passed,
    }


def _scrub_shared_lru(
    *,
    helper: dict[str, Any],
    helper_comm: str,
    trace_path: Path,
    max_touches: int,
) -> dict[str, Any]:
    baseline = _event_count(trace_path, "frl_lru_flush:", helper_comm)
    rows: list[dict[str, Any]] = []
    flush_touch: int | None = None
    for touch in range(1, max_touches + 1):
        row = _handoff_command(helper, CMD_TOUCH)
        rows.append({"touch": touch, **row})
        if _event_count(trace_path, "frl_lru_flush:", helper_comm) > baseline:
            flush_touch = touch
            break
    return {
        "flush_touch": flush_touch,
        "rows": rows,
        "pass": flush_touch is not None,
    }


def _postverify_scrub_reset(
    *,
    archive: EpochArchive,
    helper: dict[str, Any],
    helper_comm: str,
    trace_marker: Path,
    trace_path: Path,
    trial_id: str,
    stock_cpu: int,
    max_touches: int,
) -> dict[str, Any]:
    charge64_before = _event_count(
        trace_path,
        "frl_pc_try64:",
        helper_comm,
    )
    write_marker(
        trace_marker,
        trial_id=trial_id,
        epoch=archive.tx.epoch,
        phase="OBSERVE",
        touch_number=0,
        edge="PRE",
    )
    try:
        scrub = _scrub_shared_lru(
            helper=helper,
            helper_comm=helper_comm,
            trace_path=trace_path,
            max_touches=max_touches,
        )
    finally:
        write_marker(
            trace_marker,
            trial_id=trial_id,
            epoch=archive.tx.epoch,
            phase="OBSERVE",
            touch_number=0,
            edge="POST",
        )

    charge64_after = _event_count(
        trace_path,
        "frl_pc_try64:",
        helper_comm,
    )
    window = _trace_window(
        trace_path,
        trial_id=trial_id,
        epoch=archive.tx.epoch,
        phase="OBSERVE",
        touch_number=0,
    )
    event = archive.apply_neutral_window(
        epoch=archive.tx.epoch,
        touch_number=0,
        window=window,
        stock_cpu=stock_cpu,
        label="POST_VERIFY_LRU_RESET",
        owner_probe_filtered=True,
    )
    helper_charge64 = charge64_after - charge64_before
    pure = (
        scrub.get("pass") is True
        and helper_charge64 == 0
        and event.get("result") == "NEUTRAL"
        and archive.tx.state in {State.VERIFIED, State.EXECUTING}
    )
    return {
        "scrub": scrub,
        "helper_charge64_count": helper_charge64,
        "event": event,
        "pass": pure,
    }


def _observe_external_release(
    *,
    archive: EpochArchive,
    trigger: dict[str, Any],
    trigger_pages: int,
    trace_marker: Path,
    trace_path: Path,
    trial_id: str,
    stock_cpu: int,
) -> dict[str, Any]:
    helper_charge64_before = _event_count(
        trace_path,
        "frl_pc_try64:",
        "frltrig",
    )
    write_marker(
        trace_marker,
        trial_id=trial_id,
        epoch=archive.tx.epoch,
        phase="OBSERVE",
        touch_number=1,
        edge="PRE",
    )
    rows: list[dict[str, Any]] = []
    try:
        for touch in range(1, trigger_pages + 1):
            rows.append({"touch": touch, **_handoff_command(trigger, CMD_TOUCH)})
    finally:
        write_marker(
            trace_marker,
            trial_id=trial_id,
            epoch=archive.tx.epoch,
            phase="OBSERVE",
            touch_number=1,
            edge="POST",
        )

    window = _trace_window(
        trace_path,
        trial_id=trial_id,
        epoch=archive.tx.epoch,
        phase="OBSERVE",
        touch_number=1,
    )
    event = archive.apply_release_only_window(
        epoch=archive.tx.epoch,
        touch_number=1,
        window=window,
        stock_cpu=stock_cpu,
        owner_probe_filtered=True,
    )
    helper_charge64_after = _event_count(
        trace_path,
        "frl_pc_try64:",
        "frltrig",
    )
    return {
        "trigger_rows": rows,
        "event": event,
        "helper_charge64_count": (
            helper_charge64_after - helper_charge64_before
        ),
    }


def _fresh_epoch(
    *,
    archive: EpochArchive,
    worker: Path,
    out_root: Path,
    trace_marker: Path,
    trace_path: Path,
    trial_id: str,
    block: int,
    identity: int,
    arm: str,
    prep_cpu: int,
    stock_cpu: int,
    worker_uid: int,
    safe_len: int,
    calibration_max: int,
) -> tuple[dict[str, Any], dict[str, Any], list[int], int, int, int, dict[str, Any]]:
    epoch = archive.tx.epoch
    epoch_root = out_root / f"trial-{block}-{identity}" / f"epoch-{epoch}"
    epoch_root.mkdir(parents=True, exist_ok=True)
    name = (
        f"fr-b405-{os.getenv('GITHUB_RUN_ID', 'local')}-"
        f"{block}-{identity}-e{epoch}"
    )
    unit, geometry, sequence, page_size = _start_epoch_worker(
        worker=worker,
        root=epoch_root,
        name=name,
        prep_cpu=prep_cpu,
        stock_cpu=stock_cpu,
        worker_uid=worker_uid,
        safe_len=safe_len,
    )
    cursor = 0
    measured_count = 0
    _prepare_owner_probe_global(trace_path)
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
        calibration_max=calibration_max,
        measured_count=measured_count,
        target_comm=TARGET_COMM,
        owner_probe_filtered=False,
    )
    if archive.tx.state is State.VERIFIED and archive.owner_counter is not None:
        _bind_owner_probe(trace_path, archive.owner_counter)
    else:
        (_owner_probe_dir(trace_path) / "filter").write_text(
            "counter == 0\n",
            encoding="utf-8",
        )
    epoch_row = {
        "epoch": epoch,
        "arm": arm,
        "geometry": geometry,
        "normalization": normalization,
        "vmpte_after_normalize_kib": _vmpte_kib(unit["pid"]),
    }
    return unit, geometry, sequence, page_size, cursor, measured_count, epoch_row


def _finish_b63(
    *,
    archive: EpochArchive,
    unit: dict[str, Any],
    sequence: list[int],
    cursor: int,
    consume_start: int,
    consume_count: int,
    trace_marker: Path,
    trace_path: Path,
    trial_id: str,
    stock_cpu: int,
    page_size: int,
    measured_count: int,
) -> tuple[int, int, dict[str, Any]]:
    cursor, measured_count, consume = _consume_segment(
        archive=archive,
        unit=unit,
        sequence=sequence,
        cursor=cursor,
        start_touch=consume_start,
        count=consume_count,
        trace_marker=trace_marker,
        trace_path=trace_path,
        trial_id=trial_id,
        stock_cpu=stock_cpu,
        page_size=page_size,
        measured_count=measured_count,
    )
    target: dict[str, Any] | None = None
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
    if archive.tx.state is State.COMMIT_READY:
        archive.commit()
    return cursor, measured_count, {"consume": consume, "target": target}


def _continuity_snapshot(
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
            "schema_version": "epoch-gap-continuity-v1",
            "trial_id": trial_id,
            "epoch": archive.tx.epoch,
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


def _recovery_epoch(
    *,
    archive: EpochArchive,
    worker: Path,
    out_root: Path,
    trace_marker: Path,
    trace_path: Path,
    trial_id: str,
    block: int,
    identity: int,
    arm: str,
    prep_cpu: int,
    stock_cpu: int,
    worker_uid: int,
    safe_len: int,
    calibration_max: int,
) -> dict[str, Any]:
    archive.reprime()
    if archive.tx.state is State.ABORTED:
        return {"state_after": State.ABORTED.value}

    unit = None
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
            safe_len=safe_len,
            calibration_max=calibration_max,
        )
        if archive.tx.state is State.VERIFIED:
            cursor, measured_count, finish = _finish_b63(
                archive=archive,
                unit=unit,
                sequence=sequence,
                cursor=cursor,
                consume_start=1,
                consume_count=62,
                trace_marker=trace_marker,
                trace_path=trace_path,
                trial_id=trial_id,
                stock_cpu=stock_cpu,
                page_size=page_size,
                measured_count=measured_count,
            )
            epoch_row.update(finish)
        epoch_row["continuity"] = _continuity_snapshot(
            archive=archive,
            trace_path=trace_path,
            trial_id=trial_id,
            stock_cpu=stock_cpu,
        )
        epoch_row["state_after"] = archive.tx.state.value
        epoch_row["invalidation_reason"] = archive.tx.invalidation_reason
        epoch_row["measured_count"] = measured_count
        epoch_row["cursor"] = cursor
        return epoch_row
    finally:
        if unit is not None:
            _stop(unit)


def run_trial(
    *,
    spec: dict[str, Any],
    worker: Path,
    handoff_worker: Path,
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
    tx_spec = spec["transaction"]
    release_spec = spec["release_only"]
    trial_id = f"{block}:{identity}"
    archive = EpochArchive.start(max_reprimes=int(tx_spec["max_reprimes"]))
    epochs: list[dict[str, Any]] = []
    challenge: dict[str, Any] = {"arm": arm}
    unit = helper = None

    try:
        if arm == "RELEASE_ONLY":
            setup_root = out_root / f"trial-{block}-{identity}" / "release-setup"
            (setup_root / "helper").mkdir(parents=True, exist_ok=True)
            helper = _start_role(
                worker=handoff_worker,
                root=setup_root / "helper",
                name=(
                    f"fr-b405-{os.getenv('GITHUB_RUN_ID', 'local')}-"
                    f"{block}-{identity}-h"
                ),
                role="trigger",
                cpu=stock_cpu,
                max_pages=max(
                    256,
                    int(release_spec["trigger_prime_max_touches"])
                    + int(release_spec["scrub_max_touches"])
                    + int(release_spec["trigger_pages"]),
                ),
                worker_uid=worker_uid,
            )
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
            safe_len=int(tx_spec["safe_len_pages"]),
            calibration_max=int(tx_spec["calibration_max_touches_per_epoch"]),
        )

        if archive.tx.state is not State.VERIFIED:
            challenge["result"] = "NORMALIZE_FAILED"
        elif arm == "CLEAN":
            cursor, measured_count, finish = _finish_b63(
                archive=archive,
                unit=unit,
                sequence=sequence,
                cursor=cursor,
                consume_start=1,
                consume_count=62,
                trace_marker=trace_marker,
                trace_path=trace_path,
                trial_id=trial_id,
                stock_cpu=stock_cpu,
                page_size=page_size,
                measured_count=measured_count,
            )
            epoch_row.update(finish)
            challenge["result"] = (
                "CLEAN_COMMIT" if archive.tx.state is State.SUCCESS
                else "CLEAN_FAILED"
            )

        elif arm == "RELEASE_ONLY":
            helper_ready = _postverify_prime_helper_stock(
                archive=archive,
                helper=helper,
                helper_comm="frltrig",
                trace_marker=trace_marker,
                trace_path=trace_path,
                trial_id=trial_id,
                stock_cpu=stock_cpu,
                max_touches=int(release_spec["trigger_prime_max_touches"]),
                touch_number=10,
                label="POST_VERIFY_HELPER_STOCK_PREP",
            )
            challenge["postverify_helper_prime"] = helper_ready
            epoch_row["postverify_helper_prime"] = helper_ready

            reset = None
            if helper_ready["pass"]:
                reset = _postverify_scrub_reset(
                    archive=archive,
                    helper=helper,
                    helper_comm="frltrig",
                    trace_marker=trace_marker,
                    trace_path=trace_path,
                    trial_id=trial_id,
                    stock_cpu=stock_cpu,
                    max_touches=int(release_spec["scrub_max_touches"]),
                )
                challenge["postverify_lru_reset"] = reset
                epoch_row["postverify_lru_reset"] = reset

            if (
                not helper_ready["pass"]
                or not reset
                or not reset["pass"]
            ):
                challenge["result"] = "INTERVENTION_SETUP_NOT_REALIZED"
            else:
                producer_pages = int(release_spec["producer_pages"])
                producer_start = sequence[cursor]
                cursor, measured_count, producer = _consume_segment(
                    archive=archive,
                    unit=unit,
                    sequence=sequence,
                    cursor=cursor,
                    start_touch=1,
                    count=producer_pages,
                    trace_marker=trace_marker,
                    trace_path=trace_path,
                    trial_id=trial_id,
                    stock_cpu=stock_cpu,
                    page_size=page_size,
                    measured_count=measured_count,
                )
                epoch_row["producer_consume"] = producer

                if archive.tx.state in {State.VERIFIED, State.EXECUTING}:
                    discard = _discard(
                        unit,
                        stock_cpu,
                        page_size,
                        producer_start,
                        producer_pages,
                    )
                    epoch_row["discard"] = discard
                    observe = _observe_external_release(
                        archive=archive,
                        trigger=helper,
                        trigger_pages=int(release_spec["trigger_pages"]),
                        trace_marker=trace_marker,
                        trace_path=trace_path,
                        trial_id=trial_id,
                        stock_cpu=stock_cpu,
                    )
                    epoch_row["release_observe"] = observe
                    event = observe["event"]
                    challenge["release_event"] = event

                    remaining = (
                        int(tx_spec["canonical_consume_before_target"])
                        - producer_pages
                    )
                    if archive.tx.state in {State.VERIFIED, State.EXECUTING}:
                        cursor, measured_count, finish = _finish_b63(
                            archive=archive,
                            unit=unit,
                            sequence=sequence,
                            cursor=cursor,
                            consume_start=producer_pages + 1,
                            consume_count=remaining,
                            trace_marker=trace_marker,
                            trace_path=trace_path,
                            trial_id=trial_id,
                            stock_cpu=stock_cpu,
                            page_size=page_size,
                            measured_count=measured_count,
                        )
                        epoch_row.update(finish)

                    challenge["result"] = (
                        "RELEASE_PRESERVED_AND_COMMITTED"
                        if (
                            event.get("result") == "RELEASE_ONLY"
                            and observe.get("helper_charge64_count") == 0
                            and event.get("expected_residual_before")
                            == event.get("expected_residual_after")
                            and archive.tx.state is State.SUCCESS
                        )
                        else "RELEASE_ONLY_FAILED"
                    )

        elif arm == "UNEXPECTED_REFILL":
            cursor, measured_count, consume = _consume_segment(
                archive=archive,
                unit=unit,
                sequence=sequence,
                cursor=cursor,
                start_touch=1,
                count=64,
                trace_marker=trace_marker,
                trace_path=trace_path,
                trial_id=trial_id,
                stock_cpu=stock_cpu,
                page_size=page_size,
                measured_count=measured_count,
            )
            epoch_row["challenge_consume"] = consume
            challenge["challenge_epoch_state"] = archive.tx.state.value
            challenge["challenge_invalidation_reason"] = (
                archive.tx.invalidation_reason
            )
            challenge["challenge_epoch_commit_seen"] = any(
                event.get("event") == "COMMIT"
                and int(event.get("epoch", -1)) == 0
                for event in archive.control_events
            )
            challenge["result"] = (
                "UNEXPECTED_REFILL_INVALIDATED"
                if (
                    archive.tx.state is State.INVALIDATED
                    and archive.tx.invalidation_reason == "UNEXPECTED_REFILL"
                    and not challenge["challenge_epoch_commit_seen"]
                )
                else "UNEXPECTED_REFILL_FAILED"
            )

        elif arm == "PTE_GROWTH":
            escape_index = _pte_escape_index(geometry)
            measured_count += 1
            row, packet = _pte_escape_touch(
                archive=archive,
                unit=unit,
                stock_cpu=stock_cpu,
                page_size=page_size,
                page_index=escape_index,
                trace_marker=trace_marker,
                trace_path=trace_path,
                trial_id=trial_id,
                epoch=archive.tx.epoch,
                touch_number=1,
                expected_worker_touched=measured_count,
            )
            epoch_row["pte_escape"] = {
                "touch": row,
                "packet": packet,
                "escape_index": escape_index,
            }
            challenge["vmpte_delta_kib"] = row["vmpte_delta_kib"]
            challenge["challenge_epoch_state"] = archive.tx.state.value
            challenge["challenge_invalidation_reason"] = (
                archive.tx.invalidation_reason
            )
            challenge["challenge_epoch_commit_seen"] = any(
                event.get("event") == "COMMIT"
                and int(event.get("epoch", -1)) == 0
                for event in archive.control_events
            )
            challenge["result"] = (
                "PTE_GROWTH_INVALIDATED"
                if (
                    int(row["vmpte_delta_kib"]) != 0
                    and archive.tx.state is State.INVALIDATED
                    and archive.tx.invalidation_reason == "PTE_GROWTH"
                    and not challenge["challenge_epoch_commit_seen"]
                )
                else "PTE_GROWTH_FAILED"
            )

        else:
            raise ValueError(f"unsupported arm {arm}")

        challenge["continuity"] = _continuity_snapshot(
            archive=archive,
            trace_path=trace_path,
            trial_id=trial_id,
            stock_cpu=stock_cpu,
        )
        epoch_row["continuity"] = challenge["continuity"]
        epoch_row["state_after"] = archive.tx.state.value
        epoch_row["invalidation_reason"] = archive.tx.invalidation_reason
        epoch_row["measured_count"] = measured_count
        epoch_row["cursor"] = cursor
        epochs.append(epoch_row)

    finally:
        if unit is not None:
            _stop(unit)
            unit = None

    recovery_required = arm in {"UNEXPECTED_REFILL", "PTE_GROWTH"}
    recovery: dict[str, Any] | None = None
    if (
        recovery_required
        and challenge["result"]
        in {"UNEXPECTED_REFILL_INVALIDATED", "PTE_GROWTH_INVALIDATED"}
    ):
        recovery = _recovery_epoch(
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
            safe_len=int(tx_spec["safe_len_pages"]),
            calibration_max=int(tx_spec["calibration_max_touches_per_epoch"]),
        )
        epochs.append(recovery)

    if helper is not None:
        _stop_role(helper)

    packets = archive.as_dict()["packets"]
    fresh_recovery_q64 = (
        not recovery_required
        or any(
            int(packet["epoch"]) == 1
            and packet["phase"] == "NORMALIZE"
            and int(packet["page_counter_try_charge_64_count"]) == 1
            and int(packet["refill_stock_63_count"]) == 1
            and packet["expected_residual_after"] == 63
            for packet in packets
        )
    )

    continuity_clean = bool(
        challenge.get("continuity", {}).get("gap_clean", False)
    )

    if arm == "CLEAN":
        challenge_classification_pass = (
            challenge.get("result") == "CLEAN_COMMIT"
            and continuity_clean
        )
    elif arm == "RELEASE_ONLY":
        challenge_classification_pass = (
            challenge.get("result") == "RELEASE_PRESERVED_AND_COMMITTED"
            and archive.tx.release_only_count >= 1
            and continuity_clean
        )
    elif arm == "UNEXPECTED_REFILL":
        challenge_classification_pass = (
            challenge.get("result") == "UNEXPECTED_REFILL_INVALIDATED"
            and continuity_clean
        )
    else:
        challenge_classification_pass = (
            challenge.get("result") == "PTE_GROWTH_INVALIDATED"
            and continuity_clean
        )

    recovery_continuity_clean = (
        not recovery_required
        or bool(
            (recovery or {}).get("continuity", {}).get(
                "gap_clean",
                False,
            )
        )
    )
    recovery_pass = (
        not recovery_required
        or (
            fresh_recovery_q64
            and archive.tx.state is State.SUCCESS
            and archive.tx.reprimes == 1
            and recovery_continuity_clean
        )
    )
    completion_pass = (
        challenge_classification_pass
        and recovery_pass
        and (
            recovery_required
            or archive.tx.state is State.SUCCESS
        )
    )
    challenge_pass = challenge_classification_pass

    return {
        "experiment_id": spec["experiment_id"],
        "kind": "PERTURBATION",
        "block": block,
        "identity": identity,
        "trial_id": trial_id,
        "arm": arm,
        "prep_cpu": prep_cpu,
        "stock_cpu": stock_cpu,
        "challenge": challenge,
        "recovery": recovery,
        "fresh_recovery_q64": fresh_recovery_q64,
        "epochs": epochs,
        "archive": archive.as_dict(),
        "final_state": archive.tx.state.value,
        "reprimes": archive.tx.reprimes,
        "challenge_classification_pass": challenge_classification_pass,
        "challenge_continuity_clean": continuity_clean,
        "recovery_continuity_clean": recovery_continuity_clean,
        "recovery_pass": recovery_pass,
        "completion_pass": completion_pass,
        "challenge_pass": challenge_pass,
    }


def run_block(
    *,
    spec: dict[str, Any],
    worker: Path,
    handoff_worker: Path,
    out_root: Path,
    trace_marker: Path,
    trace_path: Path,
    block: int,
    worker_uid: int,
) -> dict[str, Any]:
    cpus = sorted(os.sched_getaffinity(0))
    if len(cpus) < 3:
        raise RuntimeError("B405 requires >=3 CPUs")
    controller_cpu, prep_cpu, stock_cpu = cpus[0], cpus[1], cpus[-1]
    os.sched_setaffinity(0, {controller_cpu})

    out_root.mkdir(parents=True, exist_ok=True)
    (out_root / "environment.json").write_text(
        json.dumps(
            environment_receipt(worker, cpus),
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )

    trials: list[dict[str, Any]] = []
    for identity, arm in enumerate(ARM_ORDER):
        row = run_trial(
            spec=spec,
            worker=worker,
            handoff_worker=handoff_worker,
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
        trials.append(row)

    return {
        "experiment_id": spec["experiment_id"],
        "block": block,
        "trial_count": len(trials),
        "challenge_pass": sum(
            bool(t["challenge_classification_pass"]) for t in trials
        ),
        "completion_pass": sum(bool(t["completion_pass"]) for t in trials),
        "by_arm": {
            t["arm"]: {
                "pass": bool(t["challenge_classification_pass"]),
                "completion_pass": bool(t["completion_pass"]),
                "recovery_pass": bool(t["recovery_pass"]),
                "final_state": t["final_state"],
                "reprimes": t["reprimes"],
                "result": t["challenge"].get("result"),
            }
            for t in trials
        },
    }


def aggregate(spec: dict[str, Any], input_root: Path) -> dict[str, Any]:
    trials = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(input_root.rglob("trial-*.json"))
    ]
    by_arm: dict[str, dict[str, Any]] = {}
    for arm in ARM_ORDER:
        rows = [t for t in trials if t["arm"] == arm]
        by_arm[arm] = {
            "n": len(rows),
            "pass": sum(
                bool(t["challenge_classification_pass"]) for t in rows
            ),
            "completion_pass": sum(
                bool(t["completion_pass"]) for t in rows
            ),
            "recovery_pass": sum(
                bool(t["recovery_pass"]) for t in rows
            ),
            "success": sum(t["final_state"] == "SUCCESS" for t in rows),
            "target_fail": sum(
                any(
                    epoch.get("state_after") == "TARGET_FAIL"
                    for epoch in t.get("epochs", [])
                )
                for t in rows
            ),
            "reprimes": sum(int(t["reprimes"]) for t in rows),
        }

    target_fail = sum(
        any(
            epoch.get("state_after") == "TARGET_FAIL"
            for epoch in trial.get("epochs", [])
        )
        for trial in trials
    )
    challenge_pass = sum(
        bool(t["challenge_classification_pass"]) for t in trials
    )
    completion_pass = sum(bool(t["completion_pass"]) for t in trials)
    probe_coverage = summarize_probe_coverage(
        sorted(input_root.rglob("kprobe-profile.txt"))
    )

    matrix_pass = (
        len(trials) == 16
        and challenge_pass == 16
        and target_fail == 0
        and all(
            by_arm[arm]["n"] == 4 and by_arm[arm]["pass"] == 4
            for arm in ARM_ORDER
        )
    )
    end_to_end_pass = (
        len(trials) == 16
        and completion_pass == 16
        and target_fail == 0
    )

    return {
        "experiment_id": spec["experiment_id"],
        "trial_count": len(trials),
        "challenge_pass_count": challenge_pass,
        "completion_pass_count": completion_pass,
        "target_fail": target_fail,
        "by_arm": by_arm,
        "matrix_pass": matrix_pass,
        "end_to_end_pass": end_to_end_pass,
        "probe_coverage": probe_coverage,
        "fully_observed_matrix_pass": (
            matrix_pass and bool(probe_coverage["coverage_pass"])
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
    run.add_argument("--handoff-worker", required=True)
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
            handoff_worker=Path(args.handoff_worker).resolve(),
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
                "matrix_pass": result["matrix_pass"],
                "challenge_pass_count": result["challenge_pass_count"],
                "completion_pass_count": result["completion_pass_count"],
                "end_to_end_pass": result["end_to_end_pass"],
                "fully_observed_matrix_pass": result[
                    "fully_observed_matrix_pass"
                ],
                "probe_coverage_pass": result["probe_coverage"][
                    "coverage_pass"
                ],
                "critical_probe_missed": result["probe_coverage"][
                    "critical_missed"
                ],
                "target_fail": result["target_fail"],
                "by_arm": result["by_arm"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
