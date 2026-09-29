from __future__ import annotations

import re
from typing import Any

from .transactional_receipt_adapter import apply_packet
from .transactional_reprime import State, Transaction


TX_MARKER_RE = re.compile(
    r"FRL_TX trial=(?P<trial>\d+:\d+) "
    r"epoch=(?P<epoch>\d+) "
    r"phase=(?P<phase>NORMALIZE|CONSUME|TARGET) "
    r"touch=(?P<touch>\d+) "
    r"(?P<edge>PRE|POST)"
)
TRACE_TS_RE = re.compile(r"(?P<seconds>\d+\.\d+):")
CPU_RE = re.compile(r"\[(?P<cpu>\d+)\]")
COUNTER_RE = re.compile(r"\bcounter=(?P<counter>0x[0-9a-fA-F]+)")
NR_RE = re.compile(r"\bnr=(?P<nr>\d+)")
NR_PAGES_RE = re.compile(r"\bnr_pages=(?P<nr_pages>\d+)")
COMM_RE = re.compile(r'\bcomm="(?P<comm>[^"]+)"')


def _timestamp_ns(line: str) -> int | None:
    matches = list(TRACE_TS_RE.finditer(line))
    if not matches:
        return None
    value = matches[-1].group("seconds")
    whole, frac = value.split(".", 1)
    frac = (frac + "000000000")[:9]
    return int(whole) * 1_000_000_000 + int(frac)


def _event_row(line: str) -> dict[str, Any]:
    row: dict[str, Any] = {
        "line": line.strip(),
        "timestamp_ns": _timestamp_ns(line),
    }
    if (m := CPU_RE.search(line)):
        row["cpu"] = int(m.group("cpu"))
    if (m := COUNTER_RE.search(line)):
        row["counter"] = m.group("counter").lower()
    if (m := NR_RE.search(line)):
        row["nr"] = int(m.group("nr"))
    if (m := NR_PAGES_RE.search(line)):
        row["nr_pages"] = int(m.group("nr_pages"))
    if (m := COMM_RE.search(line)):
        row["comm"] = m.group("comm")
    return row


def _empty_window() -> dict[str, Any]:
    return {
        "pre_count": 0,
        "post_count": 0,
        "pre_ns": None,
        "post_ns": None,
        "marker_error_count": 0,
        "pc_try64": [],
        "refill63": [],
        "pc_uncharge17": [],
        "pc_uncharge17_stacks": [],
        "lru_flush": [],
        "folios_put": [],
        "drain_stock": [],
    }


def parse_transaction_trace(
    text: str,
) -> dict[tuple[str, int, str, int], dict[str, Any]]:
    """Parse FRL_TX windows and source-grounded events inside them.

    Marker structure is fail-closed. page_counter_uncharge(17) stack lines
    are retained so release attribution need not require a flush event to fall
    inside the exact same PRE/POST window.
    """
    windows: dict[tuple[str, int, str, int], dict[str, Any]] = {}
    active: tuple[str, int, str, int] | None = None
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
            item = windows.setdefault(key, _empty_window())
            edge = marker.group("edge")
            ts = _timestamp_ns(line)

            if edge == "PRE":
                if active is not None:
                    windows.setdefault(active, _empty_window())[
                        "marker_error_count"
                    ] += 1
                    item["marker_error_count"] += 1
                item["pre_count"] += 1
                item["pre_ns"] = ts
                active = key
                active_stack = None
            else:
                item["post_count"] += 1
                item["post_ns"] = ts
                if active != key:
                    item["marker_error_count"] += 1
                    if active is not None:
                        windows.setdefault(active, _empty_window())[
                            "marker_error_count"
                        ] += 1
                active = None
                active_stack = None
            continue

        if active is None:
            continue

        item = windows[active]
        row = _event_row(line)

        if "frl_pc_try64:" in line:
            if int(row.get("nr_pages", 0)) == 64:
                item["pc_try64"].append(row)
            active_stack = None
        elif "frl_refill_stock:" in line:
            if int(row.get("nr_pages", 0)) == 63:
                item["refill63"].append(row)
            active_stack = None
        elif "frl_pc_uncharge17:" in line:
            if int(row.get("nr_pages", 0)) == 17:
                item["pc_uncharge17"].append(row)
                stack: list[str] = []
                item["pc_uncharge17_stacks"].append(stack)
                active_stack = stack
        elif "frl_lru_flush:" in line:
            item["lru_flush"].append(row)
            active_stack = None
        elif "frl_folios_put:" in line:
            item["folios_put"].append(row)
            active_stack = None
        elif "frl_drain_stock:" in line:
            item["drain_stock"].append(row)
            active_stack = None
        elif active_stack is not None:
            stripped = line.strip()
            if stripped:
                active_stack.append(stripped)

    if active is not None:
        windows.setdefault(active, _empty_window())["marker_error_count"] += 1

    return windows


def window_trace_complete(window: dict[str, Any]) -> bool:
    return (
        int(window.get("pre_count", 0)) == 1
        and int(window.get("post_count", 0)) == 1
        and int(window.get("marker_error_count", 0)) == 0
        and window.get("pre_ns") is not None
        and window.get("post_ns") is not None
        and int(window["post_ns"]) >= int(window["pre_ns"])
    )


def direct_q64_owner_counter(window: dict[str, Any]) -> str | None:
    """Return the unique page-counter identity for an exact direct Q64 pair."""
    if len(window.get("pc_try64", [])) != 1:
        return None
    if len(window.get("refill63", [])) != 1:
        return None
    counter = window["pc_try64"][0].get("counter")
    return str(counter).lower() if counter else None


def _lru_release_stack(stack: list[str]) -> bool:
    text = "\n".join(stack)
    return (
        "folios_put_refs" in text
        and (
            "folio_batch_move_lru" in text
            or "__folio_batch_add_and_move" in text
        )
    )


def observer_receipt_for_window(
    window: dict[str, Any],
    *,
    owner_counter: str | None,
    stock_cpu: int | None = None,
    phase: str | None = None,
) -> dict[str, Any]:
    """Create a source-grounded B403-compatible observer receipt.

    Release attribution:
      - owner page_counter_uncharge(17), plus either
        a direct LRU stack signature or the legacy same-window 31/31
        flush/put signature.

    Drain attribution:
      - a drain on another CPU cannot mutate the target per-CPU stock;
      - a worker-local drain inside a NORMALIZE direct-Q64 refill is treated
        as slot eviction before the newly verified residual is installed;
      - remaining stock-CPU drains are state invalidators.

    Net memory.current is never authoritative.
    """
    candidate_owner = direct_q64_owner_counter(window)
    effective_owner = owner_counter or candidate_owner
    if effective_owner is not None:
        effective_owner = effective_owner.lower()

    uncharges = list(window.get("pc_uncharge17", []))
    stacks = list(window.get("pc_uncharge17_stacks", []))
    owner_indices = [
        i
        for i, event in enumerate(uncharges)
        if str(event.get("counter", "")).lower() == effective_owner
    ]

    flush31 = any(
        int(event.get("nr", -1)) == 31
        for event in window.get("lru_flush", [])
    )
    put31 = any(
        int(event.get("nr", -1)) == 31
        for event in window.get("folios_put", [])
    )

    grounded_owner_indices: list[int] = []
    for i in owner_indices:
        stack = stacks[i] if i < len(stacks) else []
        if _lru_release_stack(stack) or (flush31 and put31):
            grounded_owner_indices.append(i)

    grounded_release = len(grounded_owner_indices)
    unknown_release = len(owner_indices) - grounded_release

    all_drains = list(window.get("drain_stock", []))
    if stock_cpu is None:
        same_cpu_drains = list(all_drains)
        off_cpu_drains: list[dict[str, Any]] = []
    else:
        same_cpu_drains = [
            event
            for event in all_drains
            if int(event.get("cpu", -1)) == int(stock_cpu)
        ]
        off_cpu_drains = [
            event
            for event in all_drains
            if int(event.get("cpu", -1)) != int(stock_cpu)
        ]

    q64_comm: str | None = None
    if candidate_owner and len(window.get("pc_try64", [])) == 1:
        q64_comm = window["pc_try64"][0].get("comm")

    normalization_internal_drains: list[dict[str, Any]] = []
    invalidating_drains: list[dict[str, Any]] = []
    for event in same_cpu_drains:
        if (
            phase == "NORMALIZE"
            and candidate_owner is not None
            and q64_comm is not None
            and event.get("comm") == q64_comm
        ):
            normalization_internal_drains.append(event)
        else:
            invalidating_drains.append(event)

    notes: list[str] = []
    if candidate_owner and owner_counter and candidate_owner != owner_counter.lower():
        notes.append(
            f"owner_counter_changed:{owner_counter.lower()}->{candidate_owner}"
        )
        unknown_release += 1
    if owner_indices and unknown_release:
        notes.append("owner_uncharge17_without_grounded_lru_path")
    if off_cpu_drains:
        notes.append(f"off_cpu_drain_ignored={len(off_cpu_drains)}")
    if normalization_internal_drains:
        notes.append(
            "normalize_internal_slot_drain_ignored="
            f"{len(normalization_internal_drains)}"
        )

    return {
        "trace_complete": window_trace_complete(window),
        "page_counter_try_charge_64_count": len(window.get("pc_try64", [])),
        "refill_stock_63_count": len(window.get("refill63", [])),
        "drain_stock_count": len(invalidating_drains),
        "classified_release_only_count": grounded_release,
        "unknown_emission_count": unknown_release,
        "owner_counter": effective_owner,
        "discovered_owner_counter": candidate_owner,
        "marker_pre_ns": window.get("pre_ns"),
        "marker_post_ns": window.get("post_ns"),
        "off_cpu_drain_stock_count": len(off_cpu_drains),
        "normalization_internal_drain_count": len(
            normalization_internal_drains
        ),
        "notes": ";".join(notes) or None,
    }


def enrich_packet_v2(
    packet_v1: dict[str, Any],
    *,
    tx_before: Transaction,
    tx_after: Transaction,
    owner_counter: str | None,
    marker_pre_ns: int | None,
    marker_post_ns: int | None,
    verified_at_ns: int | None,
    touch_index_since_verified: int | None,
    unknown_emission_count: int = 0,
) -> dict[str, Any]:
    elapsed: int | None = None
    if (
        verified_at_ns is not None
        and marker_pre_ns is not None
        and marker_pre_ns >= verified_at_ns
    ):
        elapsed = marker_pre_ns - verified_at_ns

    packet = dict(packet_v1)
    packet["schema_version"] = "transaction-receipt-packet-v2"
    packet["touch_index_since_verified"] = touch_index_since_verified
    packet["elapsed_ns_since_verified"] = elapsed
    packet["expected_residual_before"] = tx_before.expected_residual
    packet["expected_residual_after"] = tx_after.expected_residual
    packet["owner_counter"] = owner_counter
    packet["marker_pre_ns"] = marker_pre_ns
    packet["marker_post_ns"] = marker_post_ns
    packet["unknown_emission_count"] = int(unknown_emission_count)
    return packet


def apply_and_enrich_v2(
    tx: Transaction,
    packet_v1: dict[str, Any],
    *,
    owner_counter: str | None,
    marker_pre_ns: int | None,
    marker_post_ns: int | None,
    verified_at_ns: int | None,
    touch_index_since_verified: int | None,
    unknown_emission_count: int = 0,
) -> tuple[Transaction, dict[str, Any], int | None, int | None]:
    """Apply one v1-compatible packet and attach Chapter-II hazard telemetry."""
    tx_after = apply_packet(tx, packet_v1)

    became_verified = (
        tx.state is State.NORMALIZING
        and tx_after.state is State.VERIFIED
    )
    current_verified_at = verified_at_ns
    current_index = touch_index_since_verified

    if became_verified:
        current_verified_at = marker_post_ns
        current_index = 0

    packet_v2 = enrich_packet_v2(
        packet_v1,
        tx_before=tx,
        tx_after=tx_after,
        owner_counter=owner_counter,
        marker_pre_ns=marker_pre_ns,
        marker_post_ns=marker_post_ns,
        verified_at_ns=current_verified_at,
        touch_index_since_verified=current_index,
        unknown_emission_count=unknown_emission_count,
    )
    if became_verified:
        packet_v2["elapsed_ns_since_verified"] = 0

    next_index = current_index
    if (
        tx_after.state in {State.VERIFIED, State.EXECUTING, State.COMMIT_READY}
        and current_index is not None
    ):
        next_index = current_index + 1

    if tx_after.state in {
        State.INVALIDATED,
        State.TARGET_FAIL,
        State.SUCCESS,
        State.ABORTED,
    }:
        next_index = None

    return tx_after, packet_v2, current_verified_at, next_index
