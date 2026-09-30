from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .transaction_trace_observer import (
    TX_MARKER_RE,
    _event_row,
    _lru_release_stack,
)


PAIR_WINDOW_NS = 100_000


@dataclass(frozen=True)
class MarkerInterval:
    pre_ns: int
    post_ns: int


def _inside_any(ts: int, intervals: list[MarkerInterval]) -> bool:
    return any(x.pre_ns <= ts <= x.post_ns for x in intervals)


def _parse_epoch_timeline(
    text: str,
    *,
    trial_id: str,
    epoch: int,
) -> tuple[list[MarkerInterval], list[dict[str, Any]]]:
    """Parse all relevant trace events, including events between FRL_TX windows."""
    intervals: list[MarkerInterval] = []
    active_key: tuple[str, int, str, int] | None = None
    active_pre_ns: int | None = None
    events: list[dict[str, Any]] = []
    active_stack: list[str] | None = None

    for line in text.splitlines():
        marker = TX_MARKER_RE.search(line)
        if marker:
            key = (
                marker.group("trial"),
                int(marker.group("epoch")),
                marker.group("phase"),
                int(marker.group("touch")),
            )
            edge = marker.group("edge")
            row = _event_row(line)
            ts = row.get("timestamp_ns")

            if key[0] == trial_id and key[1] == int(epoch):
                if edge == "PRE":
                    active_key = key
                    active_pre_ns = int(ts) if ts is not None else None
                elif (
                    edge == "POST"
                    and active_key == key
                    and active_pre_ns is not None
                    and ts is not None
                ):
                    intervals.append(
                        MarkerInterval(active_pre_ns, int(ts))
                    )
                    active_key = None
                    active_pre_ns = None
            active_stack = None
            continue

        kind: str | None = None
        row = _event_row(line)

        if "frl_drain_stock:" in line:
            kind = "DRAIN_STOCK"
        elif "frl_memcg_uncharge:" in line:
            kind = "MEMCG_UNCHARGE"
        elif "frl_refill_stock:" in line:
            if int(row.get("nr_pages", 0)) == 63:
                kind = "REFILL63"
        elif "frl_pc_try64:" in line:
            if int(row.get("nr_pages", 0)) == 64:
                kind = "PC_TRY64"
        elif "frl_pc_uncharge17:" in line:
            if int(row.get("nr_pages", 0)) == 17:
                kind = "PC_UNCHARGE17"
                row["stack"] = []
                active_stack = row["stack"]
        elif active_stack is not None:
            stripped = line.strip()
            if stripped:
                active_stack.append(stripped)
            continue

        if kind is not None:
            row["kind"] = kind
            events.append(row)
            if kind != "PC_UNCHARGE17":
                active_stack = None

    return intervals, events


def _pair_drains(
    drains: list[dict[str, Any]],
    memcg_uncharges: list[dict[str, Any]],
) -> list[tuple[dict[str, Any], dict[str, Any] | None]]:
    """Pair each drain with the nearest unused following memcg_uncharge."""
    unused = set(range(len(memcg_uncharges)))
    pairs: list[tuple[dict[str, Any], dict[str, Any] | None]] = []

    for drain in sorted(
        drains,
        key=lambda row: int(row.get("timestamp_ns") or -1),
    ):
        drain_ts = drain.get("timestamp_ns")
        drain_cpu = drain.get("cpu")
        best_i: int | None = None
        best_delta: int | None = None

        if drain_ts is not None and drain_cpu is not None:
            for i in list(unused):
                event = memcg_uncharges[i]
                event_ts = event.get("timestamp_ns")
                if (
                    event_ts is None
                    or event.get("cpu") != drain_cpu
                ):
                    continue
                delta = int(event_ts) - int(drain_ts)
                if not (0 <= delta <= PAIR_WINDOW_NS):
                    continue
                if best_delta is None or delta < best_delta:
                    best_delta = delta
                    best_i = i

        if best_i is None:
            pairs.append((drain, None))
        else:
            unused.remove(best_i)
            pairs.append((drain, memcg_uncharges[best_i]))

    return pairs


def scan_interwindow_continuity(
    trace_text: str,
    *,
    trial_id: str,
    epoch: int,
    owner_counter: str,
    owner_memcg: str,
    stock_cpu: int,
    verified_at_ns: int,
) -> dict[str, Any]:
    """Classify target-relevant events that occurred outside FRL_TX windows.

    The measured PRE/POST windows are already classified by the transactional
    observer. This scanner covers the previously blind intervals between them.

    A gap is considered clean when it contains:
      - no target-memcg stock drain on the stock CPU;
      - no target-memcg refill63 on the stock CPU;
      - no unresolved same-stock-CPU drain;
      - no ungrounded owner page_counter_uncharge17.

    Positively grounded owner LRU release is state preserving.
    Drains proven to belong to another memcg are recorded but not invalidating.
    """
    owner_counter = owner_counter.lower()
    owner_memcg = owner_memcg.lower()

    intervals, events = _parse_epoch_timeline(
        trace_text,
        trial_id=trial_id,
        epoch=epoch,
    )
    if not intervals:
        return {
            "schema_version": "epoch-gap-continuity-v1",
            "trial_id": trial_id,
            "epoch": int(epoch),
            "coverage": "NO_MARKER_INTERVALS",
            "gap_clean": False,
            "unknown_count": 1,
        }

    event_timestamps = [
        int(row["timestamp_ns"])
        for row in events
        if row.get("timestamp_ns") is not None
        and int(row["timestamp_ns"]) >= int(verified_at_ns)
    ]
    end_ns = max(
        [x.post_ns for x in intervals] + event_timestamps
    )
    relevant = [
        row
        for row in events
        if row.get("timestamp_ns") is not None
        and int(row["timestamp_ns"]) >= int(verified_at_ns)
        and int(row["timestamp_ns"]) <= end_ns
        and not _inside_any(int(row["timestamp_ns"]), intervals)
    ]

    drains = [
        row
        for row in relevant
        if row["kind"] == "DRAIN_STOCK"
        and int(row.get("cpu", -1)) == int(stock_cpu)
    ]
    memcg_uncharges = [
        row
        for row in relevant
        if row["kind"] == "MEMCG_UNCHARGE"
        and int(row.get("cpu", -1)) == int(stock_cpu)
    ]

    target_drains: list[dict[str, Any]] = []
    other_memcg_drains: list[dict[str, Any]] = []
    unresolved_drains: list[dict[str, Any]] = []

    for drain, uncharge in _pair_drains(drains, memcg_uncharges):
        if uncharge is None:
            unresolved_drains.append(drain)
            continue
        memcg = str(uncharge.get("memcg", "")).lower()
        item = {
            "drain": drain,
            "memcg_uncharge": uncharge,
        }
        if memcg == owner_memcg:
            target_drains.append(item)
        else:
            other_memcg_drains.append(item)

    target_refills = [
        row
        for row in relevant
        if row["kind"] == "REFILL63"
        and int(row.get("cpu", -1)) == int(stock_cpu)
        and str(row.get("memcg", "")).lower() == owner_memcg
    ]

    owner_uncharge_rows = [
        row
        for row in relevant
        if row["kind"] == "PC_UNCHARGE17"
        and str(row.get("counter", "")).lower() == owner_counter
    ]
    grounded_releases = [
        row
        for row in owner_uncharge_rows
        if _lru_release_stack(list(row.get("stack", [])))
    ]
    unknown_owner_uncharges = [
        row
        for row in owner_uncharge_rows
        if not _lru_release_stack(list(row.get("stack", [])))
    ]

    unknown_count = (
        len(unresolved_drains)
        + len(unknown_owner_uncharges)
    )
    state_change_count = len(target_drains) + len(target_refills)

    return {
        "schema_version": "epoch-gap-continuity-v1",
        "trial_id": trial_id,
        "epoch": int(epoch),
        "owner_counter": owner_counter,
        "owner_memcg": owner_memcg,
        "stock_cpu": int(stock_cpu),
        "verified_at_ns": int(verified_at_ns),
        "end_ns": int(end_ns),
        "marker_interval_count": len(intervals),
        "gap_event_count": len(relevant),
        "target_drain_count": len(target_drains),
        "target_refill_count": len(target_refills),
        "other_memcg_drain_count": len(other_memcg_drains),
        "unresolved_drain_count": len(unresolved_drains),
        "grounded_release_only_count": len(grounded_releases),
        "unknown_owner_uncharge_count": len(unknown_owner_uncharges),
        "state_change_count": state_change_count,
        "unknown_count": unknown_count,
        "gap_clean": state_change_count == 0 and unknown_count == 0,
        "target_drains": target_drains,
        "target_refills": target_refills,
        "other_memcg_drains": other_memcg_drains,
        "unresolved_drains": unresolved_drains,
        "grounded_releases": grounded_releases,
        "unknown_owner_uncharges": unknown_owner_uncharges,
    }
