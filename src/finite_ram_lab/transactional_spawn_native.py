from __future__ import annotations

from pathlib import Path
from typing import Any

from .memcg005gc_controlled_spawn import _touch
from .transaction_trace_observer import (
    observer_receipt_for_window,
    parse_transaction_trace,
)


def marker_text(
    *,
    trial_id: str,
    epoch: int,
    phase: str,
    touch_number: int,
    edge: str,
) -> str:
    if phase not in {"NORMALIZE", "CONSUME", "TARGET", "OBSERVE"}:
        raise ValueError(f"unsupported transaction phase {phase}")
    if edge not in {"PRE", "POST"}:
        raise ValueError(f"unsupported marker edge {edge}")
    return (
        f"FRL_TX trial={trial_id} epoch={int(epoch)} "
        f"phase={phase} touch={int(touch_number)} {edge}"
    )


def write_marker(
    path: Path,
    *,
    trial_id: str,
    epoch: int,
    phase: str,
    touch_number: int,
    edge: str,
) -> None:
    with path.open("w", encoding="utf-8") as fh:
        fh.write(
            marker_text(
                trial_id=trial_id,
                epoch=epoch,
                phase=phase,
                touch_number=touch_number,
                edge=edge,
            )
            + "\n"
        )


def touch_with_transaction_marker(
    *,
    unit: dict[str, Any],
    stock_cpu: int,
    page_size: int,
    page_index: int,
    phase: str,
    touch_number: int,
    trial_id: str,
    epoch: int,
    trace_marker: Path,
) -> dict[str, Any]:
    """Wrap one historical controlled-spawn touch with Chapter-II markers.

    The underlying _touch primitive remains unchanged so the Chapter-I runner
    and its frozen evidence semantics are not retroactively modified.
    """
    write_marker(
        trace_marker,
        trial_id=trial_id,
        epoch=epoch,
        phase=phase,
        touch_number=touch_number,
        edge="PRE",
    )
    try:
        row = _touch(
            unit,
            stock_cpu,
            page_size,
            page_index,
            phase,
        )
    finally:
        write_marker(
            trace_marker,
            trial_id=trial_id,
            epoch=epoch,
            phase=phase,
            touch_number=touch_number,
            edge="POST",
        )
    return {"touch_number": int(touch_number), **row}


def observed_window(
    *,
    trace_text: str,
    trial_id: str,
    epoch: int,
    phase: str,
    touch_number: int,
) -> dict[str, Any]:
    windows = parse_transaction_trace(trace_text)
    key = (trial_id, int(epoch), phase, int(touch_number))
    if key not in windows:
        return {
            "pre_count": 0,
            "post_count": 0,
            "pre_ns": None,
            "post_ns": None,
            "marker_error_count": 1,
            "pc_try64": [],
            "refill63": [],
            "pc_uncharge17": [],
            "pc_uncharge17_stacks": [],
            "lru_flush": [],
            "folios_put": [],
            "drain_stock": [],
        }
    return windows[key]


def receipt_after_touch(
    *,
    trace_path: Path,
    trial_id: str,
    epoch: int,
    phase: str,
    touch_number: int,
    owner_counter: str | None,
) -> dict[str, Any]:
    """Read back one completed trace window and create its observer receipt.

    This function is intended for the successor runner's low-rate protocol
    smoke test. It is not used by the frozen historical runner.
    """
    window = observed_window(
        trace_text=trace_path.read_text(
            encoding="utf-8",
            errors="replace",
        ),
        trial_id=trial_id,
        epoch=epoch,
        phase=phase,
        touch_number=touch_number,
    )
    return observer_receipt_for_window(
        window,
        owner_counter=owner_counter,
    )
