from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from finite_ram_lab.fr_method_recorder import (
    aggregate_directory,
    record_event,
)


def event(event_id: str, calls):
    return {
        "event_id": event_id,
        "bounce_id": event_id,
        "protocol": "MIXED_V3",
        "gap_class": "EVIDENCE_GAP",
        "external_tool_calls": calls,
        "max_calls_between_updates": 2,
        "rehydrate_files": 3,
        "rehydrate_bytes": 12000,
        "durable_transitions": 1,
        "mc_trials": None,
        "failure_specimens": None,
        "branches_opened": 0,
        "branches_closed": 0,
        "frontier_gap_before": None,
        "frontier_gap_after": None,
        "authority_expanded": False,
        "stop_reason": "DURABLE_TRANSITION_COMPLETE",
        "claim_class": "DOGFOOD",
    }


class MethodRecorderTests(unittest.TestCase):
    def test_roundtrip_and_aggregate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt = record_event(tmp, event("DOGFOOD-001", 4))
            self.assertEqual(receipt["status"], "RECORDED")
            self.assertEqual(len(receipt["sha256"]), 64)

            result = aggregate_directory(tmp)
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["event_count"], 1)
            calls = result["aggregate"]["means"]["external_tool_calls"]
            self.assertEqual(calls["value"], 4.0)
            self.assertEqual(calls["coverage"], 1.0)

    def test_existing_event_is_never_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record_event(tmp, event("DOGFOOD-002", 3))
            with self.assertRaises(FileExistsError):
                record_event(tmp, event("DOGFOOD-002", 5))

    def test_unknown_survives_recording(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            record_event(tmp, event("DOGFOOD-003", None))
            stored = json.loads(
                Path(tmp, "DOGFOOD-003.json").read_text(encoding="utf-8")
            )
            self.assertIsNone(stored["external_tool_calls"])

            result = aggregate_directory(tmp)
            calls = result["aggregate"]["means"]["external_tool_calls"]
            self.assertIsNone(calls["value"])
            self.assertEqual(calls["observed"], 0)

    def test_event_id_cannot_escape_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bad = event("../escape", 1)
            with self.assertRaises(ValueError):
                record_event(tmp, bad)


if __name__ == "__main__":
    unittest.main()
