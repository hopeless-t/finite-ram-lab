from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from finite_ram_lab.recorder import (
    DuplicateConflictError,
    EvidenceError,
    EvidenceRecorder,
    ingest_jsonl,
    ingest_many,
)


class RecorderTests(unittest.TestCase):
    def _record_run(self, path: Path, run_id: str = "run-1") -> None:
        with EvidenceRecorder(path, run_id) as recorder:
            recorder.start(
                experiment_id="REC-001-TEST",
                spec_id="rec-001-v0",
                source_commit="deadbeef",
                provenance={"kernel": "test"},
                config={"memory_high_mib": 160},
            )
            recorder.sample("memory.current", 123456, "bytes", phase="scan")
            recorder.event("phase_marker", phase="scan", details={"name": "mid"})
            recorder.summary("peak_memory", 123456, "bytes", method="max")
            recorder.end("PASS")

    def test_round_trip_and_query_projection(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            raw = root / "run.jsonl"
            db = root / "evidence.db"
            self._record_run(raw)

            lines = raw.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 5)
            self.assertIn('"record_type":"event"', lines[2])

            result = ingest_jsonl(raw, db)
            self.assertEqual(result["inserted"], 5)
            self.assertEqual(result["duplicates"], 0)

            with sqlite3.connect(db) as conn:
                self.assertEqual(conn.execute("SELECT count(*) FROM records").fetchone()[0], 5)
                self.assertEqual(conn.execute("SELECT count(*) FROM samples").fetchone()[0], 1)
                self.assertEqual(conn.execute("SELECT count(*) FROM events").fetchone()[0], 1)
                self.assertEqual(conn.execute("SELECT count(*) FROM summaries").fetchone()[0], 1)
                row = conn.execute(
                    "SELECT experiment_id, status FROM runs WHERE run_id = ?",
                    ("run-1",),
                ).fetchone()
                self.assertEqual(row, ("REC-001-TEST", "PASS"))

    def test_reingest_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            raw = root / "run.jsonl"
            db = root / "evidence.db"
            self._record_run(raw)

            ingest_jsonl(raw, db)
            second = ingest_jsonl(raw, db)
            self.assertEqual(second["inserted"], 0)
            self.assertEqual(second["duplicates"], 5)

            with sqlite3.connect(db) as conn:
                self.assertEqual(conn.execute("SELECT count(*) FROM records").fetchone()[0], 5)

    def test_conflicting_duplicate_rolls_back(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            raw = root / "run.jsonl"
            altered = root / "altered.jsonl"
            db = root / "evidence.db"
            self._record_run(raw)
            ingest_jsonl(raw, db)

            records = [json.loads(line) for line in raw.read_text(encoding="utf-8").splitlines()]
            records[1]["value"] = 999999
            altered.write_text(
                "\n".join(json.dumps(r, sort_keys=True, separators=(",", ":")) for r in records)
                + "\n",
                encoding="utf-8",
            )

            with self.assertRaises(DuplicateConflictError):
                ingest_jsonl(altered, db)

            with sqlite3.connect(db) as conn:
                value = conn.execute(
                    "SELECT value FROM samples WHERE run_id = ? AND seq = 1",
                    ("run-1",),
                ).fetchone()[0]
                self.assertEqual(value, 123456)

    def test_malformed_file_is_atomic(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            raw = root / "run.jsonl"
            broken = root / "broken.jsonl"
            db = root / "evidence.db"
            self._record_run(raw)
            broken.write_text(
                raw.read_text(encoding="utf-8") + "{not-json\n",
                encoding="utf-8",
            )

            with self.assertRaises(EvidenceError):
                ingest_jsonl(broken, db)

            with sqlite3.connect(db) as conn:
                self.assertEqual(conn.execute("SELECT count(*) FROM records").fetchone()[0], 0)

    def test_record_after_run_end_is_rejected_atomically(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            raw = root / "run.jsonl"
            poisoned = root / "poisoned.jsonl"
            db = root / "evidence.db"
            self._record_run(raw)

            records = [json.loads(line) for line in raw.read_text(encoding="utf-8").splitlines()]
            tail = dict(records[1])
            tail["seq"] = 5
            tail["monotonic_ns"] = int(records[-1]["monotonic_ns"]) + 1
            poisoned.write_text(
                "\n".join(json.dumps(r, sort_keys=True, separators=(",", ":")) for r in [*records, tail])
                + "\n",
                encoding="utf-8",
            )

            with self.assertRaises(EvidenceError):
                ingest_jsonl(poisoned, db)

            with sqlite3.connect(db) as conn:
                self.assertEqual(conn.execute("SELECT count(*) FROM records").fetchone()[0], 0)

    def test_second_run_end_is_rejected_atomically(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            raw = root / "run.jsonl"
            poisoned = root / "poisoned.jsonl"
            db = root / "evidence.db"
            self._record_run(raw)

            records = [json.loads(line) for line in raw.read_text(encoding="utf-8").splitlines()]
            second_end = dict(records[-1])
            second_end["seq"] = 5
            second_end["monotonic_ns"] = int(records[-1]["monotonic_ns"]) + 1
            poisoned.write_text(
                "\n".join(json.dumps(r, sort_keys=True, separators=(",", ":")) for r in [*records, second_end])
                + "\n",
                encoding="utf-8",
            )

            with self.assertRaises(EvidenceError):
                ingest_jsonl(poisoned, db)

            with sqlite3.connect(db) as conn:
                self.assertEqual(conn.execute("SELECT count(*) FROM records").fetchone()[0], 0)

    def test_sequence_gap_is_rejected_atomically(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            raw = root / "run.jsonl"
            poisoned = root / "poisoned.jsonl"
            db = root / "evidence.db"
            self._record_run(raw)

            records = [json.loads(line) for line in raw.read_text(encoding="utf-8").splitlines()]
            records[2]["seq"] = 3
            poisoned.write_text(
                "\n".join(json.dumps(r, sort_keys=True, separators=(",", ":")) for r in records)
                + "\n",
                encoding="utf-8",
            )

            with self.assertRaises(EvidenceError):
                ingest_jsonl(poisoned, db)

            with sqlite3.connect(db) as conn:
                self.assertEqual(conn.execute("SELECT count(*) FROM records").fetchone()[0], 0)

    def test_mixed_run_ids_are_rejected_atomically(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            raw = root / "run.jsonl"
            poisoned = root / "poisoned.jsonl"
            db = root / "evidence.db"
            self._record_run(raw)

            records = [json.loads(line) for line in raw.read_text(encoding="utf-8").splitlines()]
            records[2]["run_id"] = "other-run"
            poisoned.write_text(
                "\n".join(json.dumps(r, sort_keys=True, separators=(",", ":")) for r in records)
                + "\n",
                encoding="utf-8",
            )

            with self.assertRaises(EvidenceError):
                ingest_jsonl(poisoned, db)

            with sqlite3.connect(db) as conn:
                self.assertEqual(conn.execute("SELECT count(*) FROM records").fetchone()[0], 0)

    def test_incomplete_crash_log_remains_ingestible_as_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            raw = root / "run.jsonl"
            incomplete = root / "incomplete.jsonl"
            db = root / "evidence.db"
            self._record_run(raw)

            lines = raw.read_text(encoding="utf-8").splitlines()
            incomplete.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")

            result = ingest_jsonl(incomplete, db)
            self.assertEqual(result["inserted"], 4)

            with sqlite3.connect(db) as conn:
                status = conn.execute(
                    "SELECT status FROM runs WHERE run_id = ?",
                    ("run-1",),
                ).fetchone()[0]
                self.assertIsNone(status)

    def test_rebuild_projection_from_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            raw1 = root / "run1.jsonl"
            raw2 = root / "run2.jsonl"
            db = root / "evidence.db"
            self._record_run(raw1, "run-1")
            self._record_run(raw2, "run-2")

            first = ingest_many([raw1, raw2], db, rebuild=True)
            self.assertEqual(first["inserted"], 10)

            db.write_bytes(b"not a sqlite database")
            rebuilt = ingest_many([raw1, raw2], db, rebuild=True)
            self.assertEqual(rebuilt["inserted"], 10)

            with sqlite3.connect(db) as conn:
                self.assertEqual(conn.execute("SELECT count(*) FROM runs").fetchone()[0], 2)


if __name__ == "__main__":
    unittest.main()
