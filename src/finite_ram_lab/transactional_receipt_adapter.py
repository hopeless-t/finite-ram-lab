from __future__ import annotations

from typing import Any

from .transactional_reprime import Event, State, Transaction, reduce


def _guard_event(packet: dict[str, Any]) -> Event | None:
    if not bool(packet.get("trace_complete", False)):
        return Event.TRACE_GAP
    if not bool(packet.get("worker_ok", False)):
        return Event.WORKER_ERROR
    if not bool(packet.get("cpu_match", False)):
        return Event.CPU_MISMATCH
    if int(packet.get("vmpte_delta_kib", 0)) != 0:
        return Event.PTE_GROWTH
    if int(packet.get("drain_stock_count", 0)) > 0:
        return Event.DRAIN_STOCK
    return None


def events_for_packet(tx: Transaction, packet: dict[str, Any]) -> list[tuple[Event, dict[str, Any] | None]]:
    if int(packet["epoch"]) != tx.epoch:
        raise ValueError(
            f"stale/future packet epoch={packet['epoch']} current={tx.epoch}"
        )

    guard = _guard_event(packet)
    if guard is not None:
        return [(guard, None)]

    phase = str(packet["phase"])
    charge64 = int(packet.get("page_counter_try_charge_64_count", 0))
    refill63 = int(packet.get("refill_stock_63_count", 0))
    releases = int(packet.get("classified_release_only_count", 0))

    if phase == "NORMALIZE":
        if tx.state is not State.NORMALIZING:
            raise ValueError(f"NORMALIZE packet in state {tx.state.value}")

        if bool(charge64) != bool(refill63):
            return [(Event.TRACE_GAP, None)]

        events: list[tuple[Event, dict[str, Any] | None]] = []
        if charge64 and refill63:
            events.append(
                (
                    Event.DIRECT_Q64,
                    {
                        "page_counter_try_charge_64": True,
                        "refill_stock_63": True,
                        "pte_clean": True,
                        "cpu_match": True,
                        "trace_complete": True,
                    },
                )
            )
        if releases:
            events.append((Event.RELEASE_ONLY, {"count": releases}))
        return events

    if phase == "CONSUME":
        if tx.state not in {State.VERIFIED, State.EXECUTING}:
            raise ValueError(f"CONSUME packet in state {tx.state.value}")
        if charge64 or refill63:
            return [(Event.UNEXPECTED_REFILL, None)]

        events = []
        if releases:
            events.append((Event.RELEASE_ONLY, {"count": releases}))
        events.append((Event.EXPECTED_CONSUME, None))
        return events

    if phase == "TARGET":
        if tx.state not in {State.VERIFIED, State.EXECUTING}:
            raise ValueError(f"TARGET packet in state {tx.state.value}")
        target_match = packet.get("target_match")
        if target_match is None:
            return [(Event.TRACE_GAP, None)]

        events = []
        if releases:
            events.append((Event.RELEASE_ONLY, {"count": releases}))
        events.append(
            (
                Event.TARGET_MATCH if bool(target_match) else Event.TARGET_MISMATCH,
                None,
            )
        )
        return events

    raise ValueError(f"unknown phase {phase}")


def apply_packet(tx: Transaction, packet: dict[str, Any]) -> Transaction:
    out = tx
    for event, payload in events_for_packet(out, packet):
        if event is Event.RELEASE_ONLY:
            count = int((payload or {}).get("count", 1))
            for _ in range(count):
                out = reduce(out, Event.RELEASE_ONLY)
        else:
            out = reduce(out, event, payload)
    return out
