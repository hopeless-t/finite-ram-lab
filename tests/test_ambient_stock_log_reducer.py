from __future__ import annotations

import json
import unittest

from finite_ram_lab.ambient_stock_log_reducer import (
    reduce_catcher_records,
    reduce_jsonl,
)


def session(events):
    rows = [
        {
            "kind": "SESSION_START",
            "session_id": "s1",
            "normalized": True,
            "initial_residual": 31,
        },
        {
            "kind": "HEALTH",
            "session_id": "s1",
            "trace_complete": True,
            "worker_ok": True,
            "cpu_stable": True,
            "pte_stable": True,
        },
        {"kind": "COVERAGE", "session_id": "s1", "probe": "consume", "missed": 0},
        {"kind": "COVERAGE", "session_id": "s1", "probe": "refill", "missed": 0},
        {"kind": "COVERAGE", "session_id": "s1", "probe": "uncharge", "missed": 0},
        {"kind": "COVERAGE", "session_id": "s1", "probe": "q64", "missed": 0},
        {"kind": "HISTOGRAM", "session_id": "s1", "dropped": 0},
        *events,
        {"kind": "SESSION_END", "session_id": "s1"},
    ]
    return rows


class AmbientStockLogReducerTests(unittest.TestCase):
    def test_stable_session(self):
        result = reduce_catcher_records(session([
            {"kind": "BOUNDARY", "session_id": "s1", "observed": True, "T": 64},
        ]))
        self.assertEqual(result["structural_errors"], [])
        self.assertEqual(
            result["classification"]["classification"],
            "STABLE_RESIDUAL",
        )

    def test_hidden_consume31_replays_t33(self):
        result = reduce_catcher_records(session([
            {"kind": "CONSUME_SUCCESS", "session_id": "s1", "pages": 31},
            {"kind": "BOUNDARY", "session_id": "s1", "observed": True, "T": 33},
        ]))
        self.assertEqual(
            result["classification"]["classification"],
            "DIRECT_STOCK_CONSUMPTION_FINGERPRINT",
        )
        self.assertTrue(
            result["classification"]["exact_mechanistic_fingerprint"]
        )

    def test_direct_drain_requires_explicit_drain_coverage(self):
        rows = session([
            {"kind": "DRAIN_ATTRIBUTED", "session_id": "s1", "pages": 31},
            {"kind": "OWNER_UNCHARGE", "session_id": "s1", "pages": 31},
            {"kind": "BOUNDARY", "session_id": "s1", "observed": True, "T": 33},
        ])
        result = reduce_catcher_records(rows)
        self.assertEqual(
            result["classification"]["classification"],
            "UNKNOWN_COMPLETE",
        )

        rows.insert(
            6,
            {"kind": "COVERAGE", "session_id": "s1", "probe": "drain", "missed": 0},
        )
        result = reduce_catcher_records(rows)
        self.assertEqual(
            result["classification"]["classification"],
            "DIRECT_SLOT_EVICTION_FINGERPRINT",
        )

    def test_r2_block2_shape_remains_unattributed(self):
        result = reduce_catcher_records(session([
            {"kind": "OWNER_UNCHARGE", "session_id": "s1", "pages": 31},
            {"kind": "BOUNDARY", "session_id": "s1", "observed": True, "T": 33},
        ]))
        self.assertEqual(
            result["classification"]["classification"],
            "UNATTRIBUTED_OWNER_UNCHARGE",
        )

    def test_unknown_record_forces_structural_hold(self):
        result = reduce_catcher_records(session([
            {"kind": "FUTURE_UNKNOWN", "session_id": "s1", "pages": 1},
            {"kind": "BOUNDARY", "session_id": "s1", "observed": True, "T": 64},
        ]))
        self.assertIn("unknown_record_type", result["structural_errors"])
        self.assertEqual(
            result["classification"]["classification"],
            "OBSERVATION_HOLD",
        )

    def test_duplicate_coverage_forces_structural_hold(self):
        rows = session([
            {"kind": "BOUNDARY", "session_id": "s1", "observed": True, "T": 64},
        ])
        rows.insert(
            6,
            {"kind": "COVERAGE", "session_id": "s1", "probe": "consume", "missed": 0},
        )
        result = reduce_catcher_records(rows)
        self.assertIn("coverage_duplicate", result["structural_errors"])
        self.assertEqual(
            result["classification"]["classification"],
            "OBSERVATION_HOLD",
        )

    def test_missing_required_coverage_is_instrumentation_hold(self):
        rows = [
            row for row in session([
                {"kind": "BOUNDARY", "session_id": "s1", "observed": True, "T": 64},
            ])
            if not (row.get("kind") == "COVERAGE" and row.get("probe") == "consume")
        ]
        result = reduce_catcher_records(rows)
        self.assertEqual(result["structural_errors"], [])
        self.assertIsNone(
            result["observation"]["critical_probe_missed"]["consume"]
        )
        self.assertEqual(
            result["classification"]["classification"],
            "INSTRUMENTATION_HOLD",
        )

    def test_jsonl_parser(self):
        rows = session([
            {"kind": "BOUNDARY", "session_id": "s1", "observed": True, "T": 64},
        ])
        text = "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n"
        result = reduce_jsonl(text)
        self.assertEqual(
            result["classification"]["classification"],
            "STABLE_RESIDUAL",
        )

    def test_censored_boundary_is_preserved(self):
        result = reduce_catcher_records(session([
            {"kind": "BOUNDARY", "session_id": "s1", "observed": False, "T": None},
        ]))
        self.assertEqual(
            result["classification"]["classification"],
            "BOUNDARY_CENSORED",
        )

    def test_target_touch_contamination_is_detected(self):
        result = reduce_catcher_records(session([
            {"kind": "AMBIENT_TARGET_TOUCH", "session_id": "s1", "count": 1},
            {"kind": "BOUNDARY", "session_id": "s1", "observed": True, "T": 63},
        ]))
        self.assertEqual(
            result["classification"]["classification"],
            "CANARY_CONTAMINATED",
        )


if __name__ == "__main__":
    unittest.main()
