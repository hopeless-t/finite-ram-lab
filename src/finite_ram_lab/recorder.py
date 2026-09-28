from __future__ import annotations

import json
import math
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

SCHEMA_VERSION = "rec-001-v0"
RECORD_TYPES = {"run_start", "sample", "event", "summary", "run_end"}


class EvidenceError(ValueError):
    """REC-001 evidence contract violation."""


class DuplicateConflictError(EvidenceError):
    """A (run_id, seq) identity was reused with different content."""


def _wall_time_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def canonical_json(record: dict[str, Any]) -> str:
    return json.dumps(
        record,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _require_string(record: dict[str, Any], key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value:
        raise EvidenceError(f"{key} must be a non-empty string")
    return value


def _require_number(record: dict[str, Any], key: str) -> float | int:
    value = record.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise EvidenceError(f"{key} must be numeric")
    if not math.isfinite(float(value)):
        raise EvidenceError(f"{key} must be finite")
    return value


def validate_record(record: dict[str, Any]) -> None:
    if not isinstance(record, dict):
        raise EvidenceError("record must be a JSON object")
    if record.get("schema_version") != SCHEMA_VERSION:
        raise EvidenceError(f"unsupported schema_version: {record.get('schema_version')!r}")

    record_type = _require_string(record, "record_type")
    if record_type not in RECORD_TYPES:
        raise EvidenceError(f"unsupported record_type: {record_type}")

    _require_string(record, "run_id")
    seq = record.get("seq")
    if isinstance(seq, bool) or not isinstance(seq, int) or seq < 0:
        raise EvidenceError("seq must be a non-negative integer")

    monotonic_ns = record.get("monotonic_ns")
    if isinstance(monotonic_ns, bool) or not isinstance(monotonic_ns, int) or monotonic_ns < 0:
        raise EvidenceError("monotonic_ns must be a non-negative integer")

    _require_string(record, "wall_time_utc")

    if record_type == "run_start":
        if seq != 0:
            raise EvidenceError("run_start must use seq=0")
        _require_string(record, "experiment_id")
        _require_string(record, "spec_id")
        _require_string(record, "source_commit")
        if not isinstance(record.get("provenance", {}), dict):
            raise EvidenceError("provenance must be an object")
        if not isinstance(record.get("config", {}), dict):
            raise EvidenceError("config must be an object")
    elif record_type == "sample":
        _require_string(record, "metric")
        _require_number(record, "value")
        _require_string(record, "unit")
    elif record_type == "event":
        _require_string(record, "event")
        if not isinstance(record.get("details", {}), dict):
            raise EvidenceError("details must be an object")
    elif record_type == "summary":
        _require_string(record, "metric")
        _require_number(record, "value")
        _require_string(record, "unit")
        _require_string(record, "method")
        if not isinstance(record.get("details", {}), dict):
            raise EvidenceError("details must be an object")
    elif record_type == "run_end":
        _require_string(record, "status")
        if not isinstance(record.get("details", {}), dict):
            raise EvidenceError("details must be an object")

    phase = record.get("phase")
    if phase is not None and (not isinstance(phase, str) or not phase):
        raise EvidenceError("phase must be a non-empty string when present")


class StreamContractValidator:
    """Validate one JSONL stream as exactly one ordered run."""

    def __init__(self) -> None:
        self.run_id: str | None = None
        self.expected_seq = 0
        self.ended = False

    def accept(self, record: dict[str, Any], *, context: str = "record") -> None:
        validate_record(record)
        run_id = record["run_id"]
        seq = record["seq"]
        record_type = record["record_type"]

        if self.run_id is None:
            if record_type != "run_start" or seq != 0:
                raise EvidenceError(f"{context}: first record must be run_start seq=0")
            self.run_id = run_id
        elif run_id != self.run_id:
            raise EvidenceError(f"{context}: mixed run_id values in one JSONL file")

        if seq != self.expected_seq:
            raise EvidenceError(f"{context}: expected seq={self.expected_seq}, got seq={seq}")
        if self.ended:
            raise EvidenceError(f"{context}: record appears after run_end")

        self.expected_seq += 1
        if record_type == "run_end":
            self.ended = True


class EvidenceRecorder:
    """Append-only REC-001 JSONL recorder for one run."""

    def __init__(self, path: str | Path, run_id: str, *, buffer_bytes: int = 64 * 1024):
        if not run_id:
            raise EvidenceError("run_id must be non-empty")
        self.path = Path(path)
        self.run_id = run_id
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._fh = self.path.open("x", encoding="utf-8", buffering=buffer_bytes)
        except FileExistsError as exc:
            raise EvidenceError(f"evidence path already claimed: {self.path}") from exc
        self._seq = 0
        self._started = False
        self._ended = False

    def __enter__(self) -> "EvidenceRecorder":
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close()

    def close(self) -> None:
        if not self._fh.closed:
            self._fh.flush()
            self._fh.close()

    def _emit(self, record_type: str, **fields: Any) -> dict[str, Any]:
        if self._ended:
            raise EvidenceError("run already ended")
        record = {
            "schema_version": SCHEMA_VERSION,
            "record_type": record_type,
            "run_id": self.run_id,
            "seq": self._seq,
            "monotonic_ns": time.monotonic_ns(),
            "wall_time_utc": _wall_time_utc(),
            **fields,
        }
        validate_record(record)
        self._fh.write(canonical_json(record) + "\n")
        self._seq += 1
        return record

    def start(
        self,
        *,
        experiment_id: str,
        spec_id: str,
        source_commit: str,
        provenance: dict[str, Any] | None = None,
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if self._started:
            raise EvidenceError("run already started")
        record = self._emit(
            "run_start",
            experiment_id=experiment_id,
            spec_id=spec_id,
            source_commit=source_commit,
            provenance=provenance or {},
            config=config or {},
        )
        self._started = True
        return record

    def _require_started(self) -> None:
        if not self._started:
            raise EvidenceError("run_start must be recorded first")

    def sample(
        self,
        metric: str,
        value: float | int,
        unit: str,
        *,
        phase: str | None = None,
    ) -> dict[str, Any]:
        self._require_started()
        fields: dict[str, Any] = {"metric": metric, "value": value, "unit": unit}
        if phase is not None:
            fields["phase"] = phase
        return self._emit("sample", **fields)

    def event(
        self,
        event: str,
        *,
        phase: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self._require_started()
        fields: dict[str, Any] = {"event": event, "details": details or {}}
        if phase is not None:
            fields["phase"] = phase
        return self._emit("event", **fields)

    def summary(
        self,
        metric: str,
        value: float | int,
        unit: str,
        *,
        method: str,
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self._require_started()
        return self._emit(
            "summary",
            metric=metric,
            value=value,
            unit=unit,
            method=method,
            details=details or {},
        )

    def end(self, status: str, *, details: dict[str, Any] | None = None) -> dict[str, Any]:
        self._require_started()
        record = self._emit("run_end", status=status, details=details or {})
        self._ended = True
        self._fh.flush()
        return record


DDL = """
CREATE TABLE IF NOT EXISTS records (
    run_id TEXT NOT NULL,
    seq INTEGER NOT NULL,
    record_type TEXT NOT NULL,
    monotonic_ns INTEGER NOT NULL,
    wall_time_utc TEXT NOT NULL,
    raw_json TEXT NOT NULL,
    PRIMARY KEY (run_id, seq)
);

CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL,
    spec_id TEXT NOT NULL,
    source_commit TEXT NOT NULL,
    provenance_json TEXT NOT NULL,
    config_json TEXT NOT NULL,
    start_seq INTEGER NOT NULL,
    end_seq INTEGER,
    status TEXT,
    end_details_json TEXT
);

CREATE TABLE IF NOT EXISTS samples (
    run_id TEXT NOT NULL,
    seq INTEGER NOT NULL,
    monotonic_ns INTEGER NOT NULL,
    wall_time_utc TEXT NOT NULL,
    metric TEXT NOT NULL,
    value REAL NOT NULL,
    unit TEXT NOT NULL,
    phase TEXT,
    PRIMARY KEY (run_id, seq),
    FOREIGN KEY (run_id, seq) REFERENCES records(run_id, seq)
);

CREATE TABLE IF NOT EXISTS events (
    run_id TEXT NOT NULL,
    seq INTEGER NOT NULL,
    monotonic_ns INTEGER NOT NULL,
    wall_time_utc TEXT NOT NULL,
    event TEXT NOT NULL,
    phase TEXT,
    details_json TEXT NOT NULL,
    PRIMARY KEY (run_id, seq),
    FOREIGN KEY (run_id, seq) REFERENCES records(run_id, seq)
);

CREATE TABLE IF NOT EXISTS summaries (
    run_id TEXT NOT NULL,
    seq INTEGER NOT NULL,
    monotonic_ns INTEGER NOT NULL,
    wall_time_utc TEXT NOT NULL,
    metric TEXT NOT NULL,
    value REAL NOT NULL,
    unit TEXT NOT NULL,
    method TEXT NOT NULL,
    details_json TEXT NOT NULL,
    PRIMARY KEY (run_id, seq),
    FOREIGN KEY (run_id, seq) REFERENCES records(run_id, seq)
);

CREATE INDEX IF NOT EXISTS idx_records_type ON records(record_type);
CREATE INDEX IF NOT EXISTS idx_records_run_time ON records(run_id, monotonic_ns);
CREATE INDEX IF NOT EXISTS idx_samples_metric ON samples(metric);
CREATE INDEX IF NOT EXISTS idx_samples_phase ON samples(phase);
CREATE INDEX IF NOT EXISTS idx_events_event ON events(event);
CREATE INDEX IF NOT EXISTS idx_events_phase ON events(phase);
CREATE INDEX IF NOT EXISTS idx_summaries_metric ON summaries(metric);
"""


def _init_db(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(DDL)
    conn.commit()


def _run_exists(conn: sqlite3.Connection, run_id: str) -> bool:
    return conn.execute("SELECT 1 FROM runs WHERE run_id = ?", (run_id,)).fetchone() is not None


def _insert_record(conn: sqlite3.Connection, record: dict[str, Any], raw_json: str) -> None:
    run_id = record["run_id"]
    seq = record["seq"]
    conn.execute(
        """
        INSERT INTO records(run_id, seq, record_type, monotonic_ns, wall_time_utc, raw_json)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            seq,
            record["record_type"],
            record["monotonic_ns"],
            record["wall_time_utc"],
            raw_json,
        ),
    )

    record_type = record["record_type"]
    if record_type == "run_start":
        conn.execute(
            """
            INSERT INTO runs(
                run_id, experiment_id, spec_id, source_commit,
                provenance_json, config_json, start_seq
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                record["experiment_id"],
                record["spec_id"],
                record["source_commit"],
                canonical_json(record.get("provenance", {})),
                canonical_json(record.get("config", {})),
                seq,
            ),
        )
    elif record_type == "sample":
        conn.execute(
            """
            INSERT INTO samples(
                run_id, seq, monotonic_ns, wall_time_utc, metric, value, unit, phase
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                seq,
                record["monotonic_ns"],
                record["wall_time_utc"],
                record["metric"],
                record["value"],
                record["unit"],
                record.get("phase"),
            ),
        )
    elif record_type == "event":
        conn.execute(
            """
            INSERT INTO events(
                run_id, seq, monotonic_ns, wall_time_utc, event, phase, details_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                seq,
                record["monotonic_ns"],
                record["wall_time_utc"],
                record["event"],
                record.get("phase"),
                canonical_json(record.get("details", {})),
            ),
        )
    elif record_type == "summary":
        conn.execute(
            """
            INSERT INTO summaries(
                run_id, seq, monotonic_ns, wall_time_utc,
                metric, value, unit, method, details_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                seq,
                record["monotonic_ns"],
                record["wall_time_utc"],
                record["metric"],
                record["value"],
                record["unit"],
                record["method"],
                canonical_json(record.get("details", {})),
            ),
        )
    elif record_type == "run_end":
        conn.execute(
            """
            UPDATE runs
               SET end_seq = ?, status = ?, end_details_json = ?
             WHERE run_id = ?
            """,
            (
                seq,
                record["status"],
                canonical_json(record.get("details", {})),
                run_id,
            ),
        )


def ingest_jsonl(path: str | Path, db_path: str | Path) -> dict[str, int | str]:
    source = Path(path)
    db = Path(db_path)
    db.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db)
    try:
        _init_db(conn)
        inserted = 0
        duplicates = 0
        stream = StreamContractValidator()
        conn.execute("BEGIN")

        with source.open("r", encoding="utf-8") as fh:
            for line_number, line in enumerate(fh, start=1):
                if not line.strip():
                    raise EvidenceError(f"{source}:{line_number}: blank JSONL line")
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise EvidenceError(f"{source}:{line_number}: malformed JSON") from exc

                validate_record(record)
                run_id = record["run_id"]
                seq = record["seq"]
                stream.accept(record, context=f"{source}:{line_number}")

                raw = canonical_json(record)
                existing = conn.execute(
                    "SELECT raw_json FROM records WHERE run_id = ? AND seq = ?",
                    (run_id, seq),
                ).fetchone()
                if existing is not None:
                    if existing[0] != raw:
                        raise DuplicateConflictError(
                            f"conflicting duplicate identity: run_id={run_id} seq={seq}"
                        )
                    duplicates += 1
                    continue

                if record["record_type"] != "run_start" and not _run_exists(conn, run_id):
                    raise EvidenceError(
                        f"run_start must precede {record['record_type']} for run {run_id}"
                    )

                _insert_record(conn, record, raw)
                inserted += 1

        conn.commit()
        return {
            "inserted": inserted,
            "duplicates": duplicates,
            "source": str(source),
            "db": str(db),
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def ingest_many(
    paths: Iterable[str | Path],
    db_path: str | Path,
    *,
    rebuild: bool = False,
) -> dict[str, int | str]:
    db = Path(db_path)
    if rebuild and db.exists():
        db.unlink()

    inserted = 0
    duplicates = 0
    files = 0
    for path in paths:
        result = ingest_jsonl(path, db)
        inserted += int(result["inserted"])
        duplicates += int(result["duplicates"])
        files += 1

    return {
        "files": files,
        "inserted": inserted,
        "duplicates": duplicates,
        "db": str(db),
    }
