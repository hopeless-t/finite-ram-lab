from __future__ import annotations

import unittest

from finite_ram_lab.next_run_proposer import propose_next_run


def source() -> dict:
    return {
        "schema": "finite-ram-lab.b465-result/v0.1",
        "status": "PASS",
        "effect_classification": "PEAK_EFFECT_UNRESOLVED_WITH_LATENCY_COST",
        "mode": "PROBE",
        "dataset_partition": "EXPERIMENTAL_INTERVENTION",
        "same_run_model_update": False,
        "pair_count": 4,
        "semantic_match_count": 4,
        "changed_variables": [["tile_rows", 64, 32]],
        "median_selected_minus_baseline_peak_bytes": -2048,
        "median_latency_ratio_selected_over_baseline": 1.0158,
        "telemetry_sha256": "3" * 64,
        "workflow_run_id": 123,
    }


class NextRunProposerTests(unittest.TestCase):
    def test_unresolved_small_tile_proposes_opposite_side(self):
        proposal = propose_next_run(source(), "a" * 64)
        self.assertEqual(proposal["status"], "PROPOSAL_ONLY")
        self.assertFalse(proposal["execute_now"])
        self.assertEqual(
            proposal["proposal_action"],
            "PROBE_OPPOSITE_TILE_DIRECTION",
        )
        self.assertEqual(proposal["changed_variables"], [["tile_rows", 64, 128]])
        self.assertEqual(
            proposal["selected_variables"]["tile_rows"],
            128,
        )
        self.assertEqual(proposal["source_result_sha256"], "a" * 64)

    def test_incomplete_semantics_fail_closed(self):
        payload = source()
        payload["semantic_match_count"] = 3
        with self.assertRaisesRegex(RuntimeError, "source_semantic_gate_incomplete"):
            propose_next_run(payload, "a" * 64)

    def test_unsupported_geometry_fail_closed(self):
        payload = source()
        payload["changed_variables"] = [["lane_count", 7, 5]]
        with self.assertRaisesRegex(RuntimeError, "unsupported_probe_geometry"):
            propose_next_run(payload, "a" * 64)

    def test_nonmatching_result_holds(self):
        payload = source()
        payload["median_selected_minus_baseline_peak_bytes"] = -5_000_000
        proposal = propose_next_run(payload, "a" * 64)
        self.assertEqual(proposal["proposal_action"], "HOLD_FOR_MANUAL_REVIEW")
        self.assertEqual(proposal["changed_variables"], [])


if __name__ == "__main__":
    unittest.main()
