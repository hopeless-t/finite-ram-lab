from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Iterable


_EVENT_RE = re.compile(
    r"^(?P<prefix>.*?)\[(?P<cpu>\d+)\].*?"
    r"(?P<ts>\d+\.\d+):\s+"
    r"(?P<event>frl_obs_[A-Za-z0-9_]+):\s+"
    r"(?P<body>.*)$"
)

_PID_RE = re.compile(r"-(?P<pid>\d+)\s+\[")
_FIELD_RE = re.compile(
    r"(?P<key>[A-Za-z_][A-Za-z0-9_]*)="
    r"(?P<value>0x[0-9a-fA-F]+|[0-9a-fA-F]{12,16}|-?\d+)"
)
_STACK_RE = re.compile(
    r"^\s*(?:=>|<=>)\s+(?P<symbol>[A-Za-z0-9_.$]+)"
)


@dataclass
class TraceEvent:
    event: str
    timestamp: float
    cpu: int
    pid: int | None
    fields: dict[str, int | str] = field(default_factory=dict)
    stack: list[str] = field(default_factory=list)
    raw: str = ""


@dataclass(frozen=True)
class ProbeDefinition:
    event: str
    definition: str


def probe_definitions() -> tuple[ProbeDefinition, ...]:
    """Linux v7-style dynamic-kprobe definitions.

    $argN is documented by Linux kprobe-event tracing and keeps this
    definition independent of the x86 register ABI. Runtime capability
    probing is still mandatory because distro kernels may omit symbols
    or CONFIG_KPROBE_EVENTS.
    """
    return (
        ProbeDefinition(
            "try_charge",
            "p:frl_obs/try_charge try_charge_memcg "
            "memcg=$arg1:x64 request_pages=$arg3:u32",
        ),
        ProbeDefinition(
            "consume",
            "r:frl_obs/consume consume_stock "
            "memcg=$arg1:x64 request_pages=$arg2:u32 "
            "ret=$retval:u64",
        ),
        ProbeDefinition(
            "refill",
            "p:frl_obs/refill refill_stock "
            "memcg=$arg1:x64 pages=$arg2:u32",
        ),
        ProbeDefinition(
            "uncharge",
            "p:frl_obs/uncharge memcg_uncharge "
            "memcg=$arg1:x64 pages=$arg2:u32",
        ),
    )


def required_symbols() -> tuple[str, ...]:
    return (
        "try_charge_memcg",
        "consume_stock",
        "refill_stock",
        "memcg_uncharge",
    )


def _parse_int(value: str) -> int | str:
    if value.startswith("0x"):
        return int(value, 16)
    # Kernel pointer values printed with x64 often have no 0x prefix.
    if (
        len(value) >= 12
        and any(ch in "abcdefABCDEF" for ch in value)
    ):
        return int(value, 16)
    try:
        return int(value, 10)
    except ValueError:
        return value


def parse_trace(text: str) -> list[TraceEvent]:
    events: list[TraceEvent] = []
    current: TraceEvent | None = None

    for line in text.splitlines():
        match = _EVENT_RE.match(line)
        if match:
            prefix = match.group("prefix")
            pid_match = _PID_RE.search(line)
            fields: dict[str, int | str] = {}
            for item in _FIELD_RE.finditer(match.group("body")):
                fields[item.group("key")] = _parse_int(
                    item.group("value")
                )
            current = TraceEvent(
                event=match.group("event"),
                timestamp=float(match.group("ts")),
                cpu=int(match.group("cpu")),
                pid=(
                    int(pid_match.group("pid"))
                    if pid_match
                    else None
                ),
                fields=fields,
                raw=line,
            )
            events.append(current)
            continue

        stack = _STACK_RE.match(line)
        if stack and current is not None:
            current.stack.append(stack.group("symbol"))

    return events


def discover_target_memcg(
    events: Iterable[TraceEvent],
    *,
    worker_pid: int,
) -> int:
    candidates: list[int] = []
    for event in events:
        if event.event != "frl_obs_try_charge":
            continue
        if event.pid != worker_pid:
            continue
        memcg = event.fields.get("memcg")
        if isinstance(memcg, int):
            candidates.append(memcg)

    unique = sorted(set(candidates))
    if len(unique) != 1:
        raise ValueError(
            "expected exactly one target memcg pointer for worker "
            f"pid={worker_pid}, got {unique}"
        )
    return unique[0]


def classify_uncharge_stack(stack: Iterable[str]) -> str:
    symbols = list(stack)

    if "drain_stock" in symbols:
        if "refill_stock" in symbols:
            return "STOCK_SLOT_EVICTION_OR_OVERFLOW"
        if (
            "drain_local_memcg_stock" in symbols
            or "drain_all_stock" in symbols
        ):
            return "STOCK_GLOBAL_DRAIN"
        return "STOCK_DRAIN_OTHER"

    if "uncharge_batch" in symbols:
        return "FOLIO_UNCHARGE_BATCH"

    if "__mem_cgroup_uncharge_folios" in symbols:
        return "FOLIO_UNCHARGE_BATCH"

    if "__mem_cgroup_uncharge" in symbols:
        return "FOLIO_UNCHARGE_SINGLE"

    if "obj_cgroup_release" in symbols:
        return "OBJCG_RELEASE"

    if "refill_stock" in symbols:
        return "REFILL_DIRECT_UNCHARGE"

    return "OTHER_UNCHARGE"


def target_uncharge_events(
    events: Iterable[TraceEvent],
    *,
    target_memcg: int,
) -> list[TraceEvent]:
    out: list[TraceEvent] = []
    for event in events:
        if event.event != "frl_obs_uncharge":
            continue
        if event.fields.get("memcg") == target_memcg:
            out.append(event)
    return out


def summarize_target_uncharge(
    events: Iterable[TraceEvent],
    *,
    target_memcg: int,
) -> dict[str, object]:
    selected = target_uncharge_events(
        events,
        target_memcg=target_memcg,
    )
    by_origin: dict[str, dict[str, int]] = {}
    total_pages = 0

    for event in selected:
        origin = classify_uncharge_stack(event.stack)
        pages = event.fields.get("pages")
        amount = pages if isinstance(pages, int) else 0
        total_pages += amount
        bucket = by_origin.setdefault(
            origin,
            {"events": 0, "pages": 0},
        )
        bucket["events"] += 1
        bucket["pages"] += amount

    return {
        "events": len(selected),
        "pages": total_pages,
        "by_origin": dict(sorted(by_origin.items())),
    }


def successful_stock_consumes(
    events: Iterable[TraceEvent],
    *,
    target_memcg: int,
) -> list[TraceEvent]:
    out: list[TraceEvent] = []
    for event in events:
        if event.event != "frl_obs_consume":
            continue
        if event.fields.get("memcg") != target_memcg:
            continue
        if event.fields.get("ret") == 1:
            out.append(event)
    return out


def target_refills(
    events: Iterable[TraceEvent],
    *,
    target_memcg: int,
) -> list[TraceEvent]:
    return [
        event
        for event in events
        if event.event == "frl_obs_refill"
        and event.fields.get("memcg") == target_memcg
    ]
