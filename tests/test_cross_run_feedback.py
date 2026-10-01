from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from finite_ram_lab.cross_run_feedback import (
    freeze_binding,
    freeze_decision,
    load_and_validate_proposal,
)


def proposal() -> dict:
    return {
        "schema": "finite-ram-lab.next-run-proposal/v0.1",
        "status": "PROPOSAL_ONLY",
        "execute_now": False,
        "requires_new_frozen_decision": True,
        "proposal_action": "PROBE_OPPOSITE_TILE_DIRECTION",
        "hypothesis_id": "H466_TILE_GRANULARITY_OTHER_SIDE",
        "baseline_variables": {
            "strategy": "STREAMED_FOLD",
            "lane_count": 7,
            "tile_rows": 64,
        },
        "selected_variables": {
            "strategy": "STREAMED_FOLD",
            "lane_count": 7,
            "tile_rows": 128,
        },
        "changed_variables": [["tile_rows", 64, 128]],
        "held_constant_variables": [
            ["lane_count", 7],
            ["strategy", "STREAMED_FOLD"],
        ],
        "source_telemetry_sha256": "3" * 64,
        "source_workflow_run_id": 123,
    }


class CrossRunFeedbackTests(unittest.TestCase):
    def test_freeze_decision_preserves_proposal_provenance(self):
        decision = freeze_decision(proposal(), "a" * 64)
        self.assertEqual(decision["changed_variables"], [["tile_rows", 64, 128]])
        self.assertEqual(decision["source_proposal_sha256"], "a" * 64)
        self.assertEqual(decision["selected_plan_id"], "streamed_7_t128")

    def test_binding_pins_decision_digest(self):
        binding = freeze_binding(
            decision_path=Path("runs/B467/decision.json"),
            decision_sha256="b" * 64,
            proposal_sha256="a" * 64,
            source_telemetry_sha256="3" * 64,
        )
        self.assertEqual(binding["expected_decision_sha256"], "b" * 64)
        self.assertFalse(binding["same_run_model_update"])

    def test_load_proposal_fails_on_digest_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "proposal.json"
            path.write_text(json.dumps(proposal()) + "\n")
            with self.assertRaisesRegex(RuntimeError, "proposal_digest_mismatch"):
                load_and_validate_proposal(path, "0" * 64)

    def test_load_proposal_rejects_changed_geometry(self):
        payload = proposal()
        payload["changed_variables"] = [["tile_rows", 64, 32]]
        raw = (json.dumps(payload, sort_keys=True) + "\n").encode()
        digest = hashlib.sha256(raw).hexdigest()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "proposal.json"
            path.write_bytes(raw)
            with self.assertRaisesRegex(RuntimeError, "proposal_geometry_invalid"):
                load_and_validate_proposal(path, digest)


if __name__ == "__main__":
    unittest.main()
