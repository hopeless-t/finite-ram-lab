from __future__ import annotations

from dataclasses import asdict
import json
from typing import Any, Iterable, Mapping

from .ambient_stock_catcher import (
    AmbientObservation,
    classify_ambient_stock,
)

SCHEMA = "ambient-stock-catcher-reduction-v1"
REQUIRED_COVERAGE = ("consume", "refill", "uncharge", "q64")
KNOWN_RECORDS = frozenset({
    "SESSION_START",
    "HEALTH",
    "COVERAGE",
    "HISTOGRAM",
    "AMBIENT_TARGET_TOUCH",
    "AMBIENT_OWNER_Q64",
    "CONSUME_SUCCESS",
    "REFILL",
    "DRAIN_ATTRIBUTED",
    "OWNER_UNCHARGE",
    "BOUNDARY",
    "SESSION_END",
})


def parse_jsonl(text: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, raw in enumerate(text.splitlines(), 1):
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"jsonl_invalid_line:{line_number}") from exc
        if type(row) is not dict:
            raise ValueError(f"jsonl_non_object_line:{line_number}")
        rows.append(row)
    return rows


def _int(value: Any, name: str, *, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise ValueError(f"{name}_invalid")
    return value


def _bool(value: Any, name: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{name}_invalid")
    return value


def reduce_catcher_records(
    records: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    session_id: str | None = None
    normalized = False
    initial_residual = 0
    ambient_target_touch_count = 0
    ambient_owner_q64_count = 0

    health = {
        "trace_complete": False,
        "worker_ok": False,
        "cpu_stable": False,
        "pte_stable": False,
    }
    health_seen = 0

    coverage: dict[str, int | None] = {}
    coverage_duplicates: list[str] = []
    hist_dropped = 0
    histogram_seen = 0

    owner_refill_pages = 0
    owner_consume_pages = 0
    target_drain_pages = 0
    owner_uncharge_pages = 0

    boundary_seen = 0
    boundary_observed = False
    final_boundary_T: int | None = None

    start_seen = 0
    end_seen = 0
    unknown_record_types: list[str] = []
    session_mismatches = 0
    records_seen = 0

    for index, record in enumerate(records):
        records_seen += 1
        if not isinstance(record, Mapping):
            raise ValueError(f"record_not_mapping:{index}")

        kind = record.get("kind")
        if not isinstance(kind, str):
            raise ValueError(f"record_kind_invalid:{index}")

        row_session = record.get("session_id")
        if row_session is not None and not isinstance(row_session, str):
            raise ValueError(f"session_id_invalid:{index}")

        if kind not in KNOWN_RECORDS:
            unknown_record_types.append(kind)
            continue

        if kind == "SESSION_START":
            start_seen += 1
            if start_seen == 1:
                if not row_session:
                    raise ValueError("session_start_id_missing")
                session_id = row_session
                normalized = _bool(
                    record.get("normalized"),
                    "normalized",
                )
                initial_residual = _int(
                    record.get("initial_residual"),
                    "initial_residual",
                )
            continue

        if session_id is None:
            session_mismatches += 1
        elif row_session != session_id:
            session_mismatches += 1

        if kind == "HEALTH":
            health_seen += 1
            health = {
                "trace_complete": _bool(
                    record.get("trace_complete"),
                    "trace_complete",
                ),
                "worker_ok": _bool(record.get("worker_ok"), "worker_ok"),
                "cpu_stable": _bool(
                    record.get("cpu_stable"),
                    "cpu_stable",
                ),
                "pte_stable": _bool(
                    record.get("pte_stable"),
                    "pte_stable",
                ),
            }
        elif kind == "COVERAGE":
            probe = record.get("probe")
            if not isinstance(probe, str) or not probe:
                raise ValueError("coverage_probe_invalid")
            missed_raw = record.get("missed")
            missed = (
                None
                if missed_raw is None
                else _int(missed_raw, "coverage_missed")
            )
            if probe in coverage:
                coverage_duplicates.append(probe)
            coverage[probe] = missed
        elif kind == "HISTOGRAM":
            histogram_seen += 1
            hist_dropped += _int(
                record.get("dropped"),
                "histogram_dropped",
            )
        elif kind == "AMBIENT_TARGET_TOUCH":
            ambient_target_touch_count += _int(
                record.get("count", 1),
                "ambient_target_touch_count",
                minimum=1,
            )
        elif kind == "AMBIENT_OWNER_Q64":
            ambient_owner_q64_count += _int(
                record.get("count", 1),
                "ambient_owner_q64_count",
                minimum=1,
            )
        elif kind == "CONSUME_SUCCESS":
            owner_consume_pages += _int(
                record.get("pages"),
                "consume_pages",
                minimum=1,
            )
        elif kind == "REFILL":
            owner_refill_pages += _int(
                record.get("pages"),
                "refill_pages",
                minimum=1,
            )
        elif kind == "DRAIN_ATTRIBUTED":
            target_drain_pages += _int(
                record.get("pages"),
                "drain_pages",
                minimum=1,
            )
        elif kind == "OWNER_UNCHARGE":
            owner_uncharge_pages += _int(
                record.get("pages"),
                "owner_uncharge_pages",
                minimum=1,
            )
        elif kind == "BOUNDARY":
            boundary_seen += 1
            boundary_observed = _bool(
                record.get("observed"),
                "boundary_observed",
            )
            if boundary_observed:
                final_boundary_T = _int(
                    record.get("T"),
                    "final_boundary_T",
                    minimum=1,
                )
            else:
                if record.get("T") is not None:
                    raise ValueError("censored_boundary_has_T")
                final_boundary_T = None
        elif kind == "SESSION_END":
            end_seen += 1

    structural_errors: list[str] = []
    if start_seen != 1:
        structural_errors.append("session_start_count")
    if end_seen != 1:
        structural_errors.append("session_end_count")
    if health_seen != 1:
        structural_errors.append("health_count")
    if histogram_seen < 1:
        structural_errors.append("histogram_missing")
    if boundary_seen != 1:
        structural_errors.append("boundary_count")
    if session_mismatches:
        structural_errors.append("session_id_mismatch")
    if coverage_duplicates:
        structural_errors.append("coverage_duplicate")
    if unknown_record_types:
        structural_errors.append("unknown_record_type")

    for probe in REQUIRED_COVERAGE:
        coverage.setdefault(probe, None)

    trace_complete = (
        bool(health["trace_complete"])
        and not structural_errors
    )

    observation = AmbientObservation(
        normalized=normalized,
        initial_residual=initial_residual,
        ambient_target_touch_count=ambient_target_touch_count,
        ambient_owner_q64_count=ambient_owner_q64_count,
        trace_complete=trace_complete,
        worker_ok=bool(health["worker_ok"]),
        cpu_stable=bool(health["cpu_stable"]),
        pte_stable=bool(health["pte_stable"]),
        critical_probe_missed=dict(sorted(coverage.items())),
        hist_dropped=hist_dropped,
        owner_refill_pages=owner_refill_pages,
        owner_consume_pages=owner_consume_pages,
        target_drain_pages=target_drain_pages,
        owner_uncharge_pages=owner_uncharge_pages,
        boundary_observed=boundary_observed,
        final_boundary_T=final_boundary_T,
    )
    classification = classify_ambient_stock(observation)

    return {
        "schema": SCHEMA,
        "session_id": session_id,
        "records_seen": records_seen,
        "structural_errors": structural_errors,
        "unknown_record_types": sorted(set(unknown_record_types)),
        "coverage_duplicates": sorted(set(coverage_duplicates)),
        "observation": asdict(observation),
        "classification": classification,
    }


def reduce_jsonl(text: str) -> dict[str, Any]:
    return reduce_catcher_records(parse_jsonl(text))
