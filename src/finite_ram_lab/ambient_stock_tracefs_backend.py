from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

EVENTS = {
    "refill": "frl_refill_stock",
    "consume": "frl_consume_stock_ret",
    "uncharge": "frl_pc_uncharge_owner",
    "q64": "frl_pc_try64",
}

# Reuse the already-qualified probe identities rather than widening the
# dynamic-probe surface for ambient observation.
PROBE_DEFINITIONS = {
    "refill": (
        "p:frl_refill_stock refill_stock "
        "memcg=$arg1:x64 nr_pages=$arg2:u32 comm=$comm"
    ),
    "consume": (
        "r:frl_consume_stock_ret consume_stock "
        "memcg=$arg1:x64 nr_pages=$arg2:u32 ret=$retval:u8 comm=$comm"
    ),
    "uncharge": (
        "p:frl_pc_uncharge_owner page_counter_uncharge "
        "counter=$arg1:x64 nr_pages=$arg2:u64 comm=$comm"
    ),
    "q64": (
        "p:frl_pc_try64 page_counter_try_charge "
        "counter=$arg1:x64 nr_pages=$arg2:u64 comm=$comm"
    ),
}

ROW_RE = re.compile(
    r"\{\s*nr_pages:\s*(?P<pages>\d+)\s*\}\s*"
    r"hitcount:\s*(?P<hits>\d+)"
)
HITS_RE = re.compile(r"\bHits:\s*(?P<value>\d+)\b")
ENTRIES_RE = re.compile(r"\bEntries:\s*(?P<value>\d+)\b")
DROPPED_RE = re.compile(r"\bDropped:\s*(?P<value>\d+)\b")


@dataclass(frozen=True)
class HistogramSummary:
    hits: int
    entries: int
    dropped: int
    pages: int
    buckets: dict[int, int]


def event_dir(trace_path: Path, logical_name: str) -> Path:
    if logical_name not in EVENTS:
        raise ValueError("event_denied")
    return (
        trace_path.parent
        / "events"
        / "kprobes"
        / EVENTS[logical_name]
    )


def hist_trigger(logical_name: str, identity: str) -> str:
    if logical_name == "refill":
        return f"hist:keys=nr_pages if memcg == {identity}"
    if logical_name == "consume":
        return (
            f"hist:keys=nr_pages if memcg == {identity} && ret != 0"
        )
    if logical_name == "uncharge":
        return f"hist:keys=nr_pages if counter == {identity}"
    raise ValueError("histogram_not_supported")


def event_filter(
    logical_name: str,
    *,
    owner_memcg: str,
    owner_counter: str,
) -> str:
    if logical_name == "refill":
        return f"memcg == {owner_memcg}"
    if logical_name == "consume":
        return f"memcg == {owner_memcg} && ret != 0"
    if logical_name == "uncharge":
        return f"counter == {owner_counter}"
    if logical_name == "q64":
        return f"counter == {owner_counter} && nr_pages == 64"
    raise ValueError("event_denied")


def parse_histogram(text: str) -> HistogramSummary:
    buckets: dict[int, int] = {}
    for match in ROW_RE.finditer(text):
        pages = int(match.group("pages"))
        hits = int(match.group("hits"))
        buckets[pages] = buckets.get(pages, 0) + hits

    hits_match = HITS_RE.search(text)
    entries_match = ENTRIES_RE.search(text)
    dropped_match = DROPPED_RE.search(text)
    if (
        hits_match is None
        or entries_match is None
        or dropped_match is None
    ):
        raise ValueError("histogram_totals_missing")

    hits = int(hits_match.group("value"))
    entries = int(entries_match.group("value"))
    dropped = int(dropped_match.group("value"))
    bucket_hits = sum(buckets.values())
    if bucket_hits != hits:
        raise ValueError("histogram_hit_total_mismatch")
    if len(buckets) != entries:
        raise ValueError("histogram_entry_total_mismatch")

    return HistogramSummary(
        hits=hits,
        entries=entries,
        dropped=dropped,
        pages=sum(pages * count for pages, count in buckets.items()),
        buckets=dict(sorted(buckets.items())),
    )


def configure_owner_count_only(
    trace_path: Path,
    *,
    owner_memcg: str,
    owner_counter: str,
) -> None:
    """Configure low-rate owner histograms; ordinary logging stays disabled."""
    identities = {
        "refill": owner_memcg,
        "consume": owner_memcg,
        "uncharge": owner_counter,
    }
    for logical_name, identity in identities.items():
        probe = event_dir(trace_path, logical_name)
        (probe / "enable").write_text("0\n", encoding="utf-8")
        try:
            (probe / "trigger").write_text(
                "!hist:keys=nr_pages\n",
                encoding="utf-8",
            )
        except OSError:
            pass
        (probe / "filter").write_text(
            event_filter(
                logical_name,
                owner_memcg=owner_memcg,
                owner_counter=owner_counter,
            ) + "\n",
            encoding="utf-8",
        )
        (probe / "trigger").write_text(
            hist_trigger(logical_name, identity) + "\n",
            encoding="utf-8",
        )

    q64 = event_dir(trace_path, "q64")
    (q64 / "enable").write_text("0\n", encoding="utf-8")
    (q64 / "filter").write_text(
        event_filter(
            "q64",
            owner_memcg=owner_memcg,
            owner_counter=owner_counter,
        ) + "\n",
        encoding="utf-8",
    )
    (q64 / "enable").write_text("1\n", encoding="utf-8")


def cleanup_owner_count_only(trace_path: Path) -> None:
    for logical_name in ("refill", "consume", "uncharge"):
        probe = event_dir(trace_path, logical_name)
        try:
            (probe / "enable").write_text("0\n", encoding="utf-8")
        except OSError:
            pass
        try:
            (probe / "trigger").write_text(
                "!hist:keys=nr_pages\n",
                encoding="utf-8",
            )
        except OSError:
            pass

    try:
        q64 = event_dir(trace_path, "q64")
        (q64 / "enable").write_text("0\n", encoding="utf-8")
    except OSError:
        pass


def histogram_receipt(
    *,
    session_id: str,
    kind: str,
    summary: HistogramSummary,
) -> list[dict[str, Any]]:
    if kind not in {"CONSUME_SUCCESS", "REFILL", "OWNER_UNCHARGE"}:
        raise ValueError("receipt_kind_denied")
    rows: list[dict[str, Any]] = []
    if summary.pages > 0:
        rows.append({
            "kind": kind,
            "session_id": session_id,
            "pages": summary.pages,
            "event_count": summary.hits,
            "buckets": summary.buckets,
        })
    rows.append({
        "kind": "HISTOGRAM",
        "session_id": session_id,
        "dropped": summary.dropped,
        "source": kind,
    })
    return rows
