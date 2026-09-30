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
    """Parse target-relevant events both inside and between FRL_TX windows."""
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
        elif "frl_pc_uncharge_any:" in line:
            kind = "PC_UNCHARGE_ANY"
            if int(row.get("nr_pages", 0)) == 17:
                row["stack"] = []
                active_stack = row["stack"]
        elif "frl_memcg_uncharge:" in line:
            # Legacy/fallback evidence only.
            kind = "MEMCG_UNCHARGE"
        elif "frl_refill_stock:" in line:
            if int(row.get("nr_pages", 0)) == 63:
                kind = "REFILL63"
        elif "frl_pc_try64:" in line:
            if int(row.get("nr_pages", 0)) == 64:
                kind = "PC_TRY64"
        elif active_stack is not None:
            stripped = line.strip()
            if stripped:
                active_stack.append(stripped)
            continue

        if kind is not None:
            row["kind"] = kind
            events.append(row)
            if not (
                kind == "PC_UNCHARGE_ANY"
                and int(row.get("nr_pages", 0)) == 17
            ):
                active_stack = None

    return intervals, events


def _pair_nearest_following(
    left: list[dict[str, Any]],
    right: list[dict[str, Any]],
) -> tuple[
    list[tuple[dict[str, Any], dict[str, Any] | None]],
    set[int],
]:
    """Pair same-CPU events within a narrow causal window, without reuse."""
    unused = set(range(len(right)))
    pairs: list[tuple[dict[str, Any], dict[str, Any] | None]] = []
    used_right: set[int] = set()

    for event in sorted(
        left,
        key=lambda row: int(row.get("timestamp_ns") or -1),
    ):
        event_ts = event.get("timestamp_ns")
        event_cpu = event.get("cpu")
        best_i: int | None = None
        best_delta: int | None = None

        if event_ts is not None and event_cpu is not None:
            for i in list(unused):
                candidate = right[i]
                candidate_ts = candidate.get("timestamp_ns")
                if (
                    candidate_ts is None
                    or candidate.get("cpu") != event_cpu
                ):
                    continue
                delta = int(candidate_ts) - int(event_ts)
                if not (0 <= delta <= PAIR_WINDOW_NS):
                    continue
                if best_delta is None or delta < best_delta:
                    best_delta = delta
                    best_i = i

        if best_i is None:
            pairs.append((event, None))
        else:
            unused.remove(best_i)
            used_right.add(best_i)
            pairs.append((event, right[best_i]))

    return pairs, used_right


def _matches_grounded_release(
    uncharge: dict[str, Any],
    *,
    owner_counter: str,
) -> bool:
    return (
        str(uncharge.get("counter", "")).lower() == owner_counter
        and int(uncharge.get("nr_pages", 0)) == 17
        and _lru_release_stack(list(uncharge.get("stack", [])))
    )


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
    """Classify target-relevant events outside measured PRE/POST windows.

    Counter identity is the primary continuity backbone:
      - target page_counter_try_charge(...,64) in a gap => state change;
      - target page_counter_uncharge paired with drain_stock => target drain;
      - other-counter drain => not target-state mutation;
      - unpaired target-counter uncharge => known LRU release only when the
        same all-counter event carries the grounded 17-page LRU stack;
        otherwise fail closed.

    memcg/refill evidence remains enrichment/fallback, not the primary proof.
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
            "schema_version": "epoch-gap-continuity-v2",
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
    end_ns = max([x.post_ns for x in intervals] + event_timestamps)

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
    counter_uncharges = [
        row
        for row in relevant
        if row["kind"] == "PC_UNCHARGE_ANY"
        and int(row.get("cpu", -1)) == int(stock_cpu)
    ]

    drain_pairs, paired_uncharge_indices = _pair_nearest_following(
        drains,
        counter_uncharges,
    )

    target_drains: list[dict[str, Any]] = []
    other_counter_drains: list[dict[str, Any]] = []
    unresolved_drains: list[dict[str, Any]] = []

    for drain, uncharge in drain_pairs:
        if uncharge is None:
            unresolved_drains.append(drain)
            continue
        item = {
            "drain": drain,
            "page_counter_uncharge": uncharge,
        }
        if str(uncharge.get("counter", "")).lower() == owner_counter:
            target_drains.append(item)
        else:
            other_counter_drains.append(item)

    unpaired_owner_uncharges = [
        row
        for i, row in enumerate(counter_uncharges)
        if i not in paired_uncharge_indices
        and str(row.get("counter", "")).lower() == owner_counter
    ]
    grounded_releases = [
        row
        for row in unpaired_owner_uncharges
        if _matches_grounded_release(
            row,
            owner_counter=owner_counter,
        )
    ]
    unknown_owner_uncharges = [
        row
        for row in unpaired_owner_uncharges
        if not _matches_grounded_release(
            row,
            owner_counter=owner_counter,
        )
    ]

    target_charge64 = [
        row
        for row in relevant
        if row["kind"] == "PC_TRY64"
        and int(row.get("cpu", -1)) == int(stock_cpu)
        and str(row.get("counter", "")).lower() == owner_counter
    ]

    target_refills = [
        row
        for row in relevant
        if row["kind"] == "REFILL63"
        and int(row.get("cpu", -1)) == int(stock_cpu)
        and str(row.get("memcg", "")).lower() == owner_memcg
    ]

    unknown_count = (
        len(unresolved_drains)
        + len(unknown_owner_uncharges)
    )
    state_change_count = (
        len(target_drains)
        + len(target_charge64)
    )

    return {
        "schema_version": "epoch-gap-continuity-v2",
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
        "target_charge64_count": len(target_charge64),
        "target_refill_count": len(target_refills),
        "other_counter_drain_count": len(other_counter_drains),
        "unresolved_drain_count": len(unresolved_drains),
        "grounded_release_only_count": len(grounded_releases),
        "unknown_owner_uncharge_count": len(unknown_owner_uncharges),
        "state_change_count": state_change_count,
        "unknown_count": unknown_count,
        "gap_clean": state_change_count == 0 and unknown_count == 0,
        "target_drains": target_drains,
        "target_charge64": target_charge64,
        "target_refills": target_refills,
        "other_counter_drains": other_counter_drains,
        "unresolved_drains": unresolved_drains,
        "grounded_releases": grounded_releases,
        "unknown_owner_uncharges": unknown_owner_uncharges,
    }
