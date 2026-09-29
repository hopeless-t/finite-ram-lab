from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from typing import Any


class State(str, Enum):
    INIT = "INIT"
    NORMALIZING = "NORMALIZING"
    VERIFIED = "VERIFIED"
    EXECUTING = "EXECUTING"
    INVALIDATED = "INVALIDATED"
    COMMIT_READY = "COMMIT_READY"
    SUCCESS = "SUCCESS"
    TARGET_FAIL = "TARGET_FAIL"
    ABORTED = "ABORTED"


class Event(str, Enum):
    ADMIT = "ADMIT"
    DIRECT_Q64 = "DIRECT_Q64"
    RELEASE_ONLY = "RELEASE_ONLY"
    EXPECTED_CONSUME = "EXPECTED_CONSUME"
    TARGET_MATCH = "TARGET_MATCH"
    TARGET_MISMATCH = "TARGET_MISMATCH"
    UNEXPECTED_REFILL = "UNEXPECTED_REFILL"
    DRAIN_STOCK = "DRAIN_STOCK"
    PTE_GROWTH = "PTE_GROWTH"
    CPU_MISMATCH = "CPU_MISMATCH"
    WORKER_ERROR = "WORKER_ERROR"
    TRACE_GAP = "TRACE_GAP"
    NORMALIZE_EXHAUSTED = "NORMALIZE_EXHAUSTED"
    REPRIME = "REPRIME"
    COMMIT = "COMMIT"


INVALIDATING_EVENTS = {
    Event.UNEXPECTED_REFILL,
    Event.DRAIN_STOCK,
    Event.PTE_GROWTH,
    Event.CPU_MISMATCH,
    Event.WORKER_ERROR,
    Event.TRACE_GAP,
}


@dataclass(frozen=True)
class Transaction:
    state: State = State.INIT
    epoch: int = 0
    reprimes: int = 0
    max_reprimes: int = 3
    expected_residual: int | None = None
    direct_q64_seen: bool = False
    pte_clean: bool = True
    cpu_clean: bool = True
    trace_complete: bool = True
    release_only_count: int = 0
    invalidation_reason: str | None = None
    target_result: str | None = None


def _invalidate(tx: Transaction, reason: Event) -> Transaction:
    return replace(
        tx,
        state=State.INVALIDATED,
        expected_residual=None,
        invalidation_reason=reason.value,
        target_result=None,
    )


def reduce(tx: Transaction, event: Event, payload: dict[str, Any] | None = None) -> Transaction:
    payload = payload or {}

    if tx.state in {State.SUCCESS, State.TARGET_FAIL, State.ABORTED}:
        raise ValueError(f"terminal state {tx.state.value} cannot accept {event.value}")

    if event in INVALIDATING_EVENTS:
        if event is Event.PTE_GROWTH:
            tx = replace(tx, pte_clean=False)
        elif event in {Event.CPU_MISMATCH, Event.WORKER_ERROR}:
            tx = replace(tx, cpu_clean=False)
        elif event is Event.TRACE_GAP:
            tx = replace(tx, trace_complete=False)
        return _invalidate(tx, event)

    if event is Event.RELEASE_ONLY:
        if tx.state not in {State.NORMALIZING, State.VERIFIED, State.EXECUTING}:
            raise ValueError("release-only emission outside active transaction")
        return replace(tx, release_only_count=tx.release_only_count + 1)

    if tx.state is State.INIT:
        if event is not Event.ADMIT:
            raise ValueError("INIT accepts only ADMIT")
        return replace(tx, state=State.NORMALIZING)

    if tx.state is State.NORMALIZING:
        if event is Event.DIRECT_Q64:
            if not payload.get("page_counter_try_charge_64", False):
                raise ValueError("DIRECT_Q64 missing page_counter_try_charge(64)")
            if not payload.get("refill_stock_63", False):
                raise ValueError("DIRECT_Q64 missing refill_stock(63)")
            if not payload.get("pte_clean", False):
                return _invalidate(replace(tx, pte_clean=False), Event.PTE_GROWTH)
            if not payload.get("cpu_match", False):
                return _invalidate(replace(tx, cpu_clean=False), Event.CPU_MISMATCH)
            if not payload.get("trace_complete", False):
                return _invalidate(replace(tx, trace_complete=False), Event.TRACE_GAP)
            if not tx.pte_clean or not tx.cpu_clean or not tx.trace_complete:
                return _invalidate(tx, Event.TRACE_GAP)
            return replace(
                tx,
                state=State.VERIFIED,
                expected_residual=63,
                direct_q64_seen=True,
                invalidation_reason=None,
            )
        if event is Event.NORMALIZE_EXHAUSTED:
            return _invalidate(tx, event)
        raise ValueError(f"NORMALIZING cannot accept {event.value}")

    if tx.state is State.VERIFIED:
        if event is Event.EXPECTED_CONSUME:
            return replace(
                tx,
                state=State.EXECUTING,
                expected_residual=max(0, int(tx.expected_residual or 0) - 1),
            )
        if event is Event.TARGET_MATCH:
            return replace(tx, state=State.COMMIT_READY, target_result="MATCH")
        if event is Event.TARGET_MISMATCH:
            return replace(tx, state=State.TARGET_FAIL, target_result="MISMATCH")
        raise ValueError(f"VERIFIED cannot accept {event.value}")

    if tx.state is State.EXECUTING:
        if event is Event.EXPECTED_CONSUME:
            return replace(
                tx,
                expected_residual=max(0, int(tx.expected_residual or 0) - 1),
            )
        if event is Event.TARGET_MATCH:
            return replace(tx, state=State.COMMIT_READY, target_result="MATCH")
        if event is Event.TARGET_MISMATCH:
            return replace(tx, state=State.TARGET_FAIL, target_result="MISMATCH")
        raise ValueError(f"EXECUTING cannot accept {event.value}")

    if tx.state is State.INVALIDATED:
        if event is not Event.REPRIME:
            raise ValueError("INVALIDATED accepts only REPRIME")
        if tx.reprimes >= tx.max_reprimes:
            return replace(tx, state=State.ABORTED)
        return Transaction(
            state=State.NORMALIZING,
            epoch=tx.epoch + 1,
            reprimes=tx.reprimes + 1,
            max_reprimes=tx.max_reprimes,
        )

    if tx.state is State.COMMIT_READY:
        if event is not Event.COMMIT:
            raise ValueError("COMMIT_READY accepts only COMMIT")
        if not (
            tx.direct_q64_seen
            and tx.pte_clean
            and tx.cpu_clean
            and tx.trace_complete
            and tx.target_result == "MATCH"
        ):
            raise ValueError("commit invariant failed")
        return replace(tx, state=State.SUCCESS)

    raise AssertionError(f"unhandled state {tx.state}")


def run(events: list[tuple[Event, dict[str, Any] | None]], *, max_reprimes: int = 3) -> Transaction:
    tx = Transaction(max_reprimes=max_reprimes)
    for event, payload in events:
        tx = reduce(tx, event, payload)
    return tx
