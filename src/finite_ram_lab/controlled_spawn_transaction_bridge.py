from __future__ import annotations

from typing import Any, Iterable

from .memcg005gc_controlled_spawn import expected_pattern


def _count(observer: dict[str, Any], key: str) -> int:
    return int(observer.get(key, 0))


def _trace_complete(observer: dict[str, Any]) -> bool:
    return bool(observer.get("trace_complete", False)) and _count(
        observer, "unknown_emission_count"
    ) == 0


def packet_from_touch(
    *,
    epoch: int,
    phase: str,
    touch_number: int,
    touch: dict[str, Any],
    observer: dict[str, Any],
    stock_cpu: int,
    target_match: bool | None = None,
) -> dict[str, Any]:
    """Normalize one controlled-spawn touch into the B400 packet schema.

    observer is intentionally already source-grounded. This bridge does
    not infer release-only semantics from memory.current.
    """
    worker_ok = int(touch.get("worker_error", 0)) == 0
    cpu_match = int(touch.get("observed_cpu", -1)) == int(stock_cpu)

    return {
        "schema_version": "transaction-receipt-packet-v1",
        "epoch": int(epoch),
        "phase": str(phase),
        "touch": int(touch_number),
        "trace_complete": _trace_complete(observer),
        "cpu_match": cpu_match,
        "worker_ok": worker_ok,
        "vmpte_delta_kib": int(touch.get("vmpte_delta_kib", 0)),
        "page_counter_try_charge_64_count": _count(
            observer, "page_counter_try_charge_64_count"
        ),
        "refill_stock_63_count": _count(observer, "refill_stock_63_count"),
        "drain_stock_count": _count(observer, "drain_stock_count"),
        "classified_release_only_count": _count(
            observer, "classified_release_only_count"
        ),
        "target_match": target_match,
        "notes": observer.get("notes"),
    }


def transition_token(observer: dict[str, Any]) -> str:
    """Classify one measured data-page stock transition.

    Net memory.current is deliberately ignored. A Q64 token requires one
    complete direct charge/refill pair. A source-grounded release-only
    emission is orthogonal and does not change the token.
    """
    if not _trace_complete(observer):
        return "INCOMPLETE"

    charge = _count(observer, "page_counter_try_charge_64_count")
    refill = _count(observer, "refill_stock_63_count")

    if charge == 0 and refill == 0:
        return "ZERO"
    if charge == 1 and refill == 1:
        return "Q64"
    if bool(charge) != bool(refill):
        return "INCOMPLETE"
    return "OTHER"


def _first_nonzero_vmpte(touches: Iterable[dict[str, Any]]) -> int:
    for touch in touches:
        delta = int(touch.get("vmpte_delta_kib", 0))
        if delta != 0:
            return delta
    return 0


def target_bundle_packet(
    *,
    epoch: int,
    arm_id: str,
    touches: list[dict[str, Any]],
    observers: list[dict[str, Any]],
    stock_cpu: int,
    touch_number: int,
) -> dict[str, Any]:
    """Collapse the arm-specific terminal sequence into one TARGET packet.

    Each constituent touch is checked before the arm-level match is emitted.
    This permits an expected terminal Q64 to be represented as a target
    transition rather than being mistaken for an unexpected refill during
    ordinary CONSUME.
    """
    expected = expected_pattern(arm_id)
    if len(touches) != len(expected) or len(observers) != len(expected):
        return {
            "schema_version": "transaction-receipt-packet-v1",
            "epoch": int(epoch),
            "phase": "TARGET",
            "touch": int(touch_number),
            "trace_complete": False,
            "cpu_match": False,
            "worker_ok": False,
            "vmpte_delta_kib": 0,
            "page_counter_try_charge_64_count": 0,
            "refill_stock_63_count": 0,
            "drain_stock_count": 0,
            "classified_release_only_count": 0,
            "target_match": None,
            "notes": "terminal bundle length mismatch",
        }

    trace_complete = all(_trace_complete(obs) for obs in observers)
    cpu_match = all(
        int(touch.get("observed_cpu", -1)) == int(stock_cpu) for touch in touches
    )
    worker_ok = all(int(touch.get("worker_error", 0)) == 0 for touch in touches)
    vmpte_delta = _first_nonzero_vmpte(touches)
    drain_count = sum(_count(obs, "drain_stock_count") for obs in observers)
    release_count = sum(
        _count(obs, "classified_release_only_count") for obs in observers
    )
    charge_count = sum(
        _count(obs, "page_counter_try_charge_64_count") for obs in observers
    )
    refill_count = sum(_count(obs, "refill_stock_63_count") for obs in observers)

    tokens = [transition_token(obs) for obs in observers]
    if "INCOMPLETE" in tokens:
        trace_complete = False

    target_match: bool | None
    if not trace_complete:
        target_match = None
    else:
        target_match = tokens == expected

    return {
        "schema_version": "transaction-receipt-packet-v1",
        "epoch": int(epoch),
        "phase": "TARGET",
        "touch": int(touch_number),
        "trace_complete": trace_complete,
        "cpu_match": cpu_match,
        "worker_ok": worker_ok,
        "vmpte_delta_kib": vmpte_delta,
        "page_counter_try_charge_64_count": charge_count,
        "refill_stock_63_count": refill_count,
        "drain_stock_count": drain_count,
        "classified_release_only_count": release_count,
        "target_match": target_match,
        "notes": f"arm={arm_id} expected={expected} observed={tokens}",
    }


def observer_receipt(
    *,
    trace_complete: bool = True,
    charge64: int = 0,
    refill63: int = 0,
    drain: int = 0,
    releases: int = 0,
    unknown: int = 0,
    notes: str | None = None,
) -> dict[str, Any]:
    """Small construction helper used by tests and offline replay tools."""
    return {
        "trace_complete": bool(trace_complete),
        "page_counter_try_charge_64_count": int(charge64),
        "refill_stock_63_count": int(refill63),
        "drain_stock_count": int(drain),
        "classified_release_only_count": int(releases),
        "unknown_emission_count": int(unknown),
        "notes": notes,
    }
