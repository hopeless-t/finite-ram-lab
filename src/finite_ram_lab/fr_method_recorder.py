from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable

from finite_ram_lab.fr_method_telemetry import aggregate, normalize_event

SCHEMA = "finite-ram-lab.fr-meta-003-method-recorder/v0.1"
EVENT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def canonical_bytes(event: dict[str, Any]) -> bytes:
    row = normalize_event(event)
    payload = json.dumps(
        row,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return (payload + "\n").encode("utf-8")


def record_event(
    output_dir: str | Path,
    event: dict[str, Any],
) -> dict[str, Any]:
    row = normalize_event(event)
    event_id = str(row["event_id"])

    if not EVENT_ID_RE.fullmatch(event_id):
        raise ValueError("invalid_event_id")

    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)

    path = root / f"{event_id}.json"
    payload = canonical_bytes(row)
    digest = hashlib.sha256(payload).hexdigest()

    # Exclusive creation preserves append-only semantics. Existing evidence,
    # including an empty file, is never overwritten.
    with path.open("xb") as handle:
        handle.write(payload)
        handle.flush()

    return {
        "schema": SCHEMA,
        "status": "RECORDED",
        "event_id": event_id,
        "path": path.name,
        "sha256": digest,
        "bytes": len(payload),
    }


def read_events(
    input_dir: str | Path,
) -> list[dict[str, Any]]:
    root = Path(input_dir)
    events = []

    for path in sorted(root.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        events.append(normalize_event(data))

    return events


def aggregate_directory(
    input_dir: str | Path,
) -> dict[str, Any]:
    events = read_events(input_dir)
    return {
        "schema": SCHEMA,
        "status": "PASS",
        "event_count": len(events),
        "aggregate": aggregate(events),
    }


def write_fixture_set(
    output_dir: str | Path,
    events: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        record_event(output_dir, event)
        for event in events
    ]


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    record = sub.add_parser("record")
    record.add_argument("event_json")
    record.add_argument("--out-dir", required=True)

    summary = sub.add_parser("aggregate")
    summary.add_argument("input_dir")

    args = parser.parse_args()

    if args.command == "record":
        event = json.loads(
            Path(args.event_json).read_text(encoding="utf-8")
        )
        result = record_event(args.out_dir, event)
    else:
        result = aggregate_directory(args.input_dir)

    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
