from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from finite_ram_lab.cross_repo_receipt import (
    CrossRepoReceiptError,
    load_receipt,
    receipt_summary,
    validate_receipt,
)


RECEIPT = (
    ROOT
    / "evidence"
    / "cross_repo"
    / "FR_META_023_DECISION_RELEVANCE_RECEIPT.json"
)


class CrossRepoDecisionRelevanceReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.doc = load_receipt(RECEIPT)

    def test_three_independent_planes_are_preserved(self) -> None:
        self.assertEqual(len(self.doc["evidence_planes"]), 3)
        self.assertTrue(
            all(row["independent_plane"] for row in self.doc["evidence_planes"])
        )
        self.assertEqual(
            {row["plane_id"] for row in self.doc["evidence_planes"]},
            {
                "reuse-monitoring",
                "cold-calibration-measurement",
                "physical-multistate-placement",
            },
        )

    def test_reuse_plane_preserves_decision_and_removes_resident_cost(self) -> None:
        row = self.doc["evidence_planes"][0]
        self.assertEqual(
            row["comparator"]["evidenceful_resident_mib_opportunity_integral"],
            40.0,
        )
        self.assertEqual(
            row["comparator"]["pruned_resident_mib_opportunity_integral"],
            0.0,
        )
        self.assertEqual(row["comparator"]["restore_count_both"], 17)
        self.assertEqual(row["comparator"]["storage_read_mib_both"], 136.0)
        self.assertTrue(row["decision_equivalence_verified"])

    def test_calibration_plane_preserves_negative_result(self) -> None:
        row = self.doc["evidence_planes"][1]
        comparator = row["comparator"]
        self.assertEqual(comparator["backtest_runs"], 15)
        self.assertEqual(comparator["early_stop_runs"], 2)
        self.assertEqual(comparator["unsafe_early_stops"], 0)
        self.assertEqual(comparator["second_probe_surface_change_runs"], 4)
        self.assertAlmostEqual(
            row["cost_delta"]["counterfactual_probe_latency_saved_ms"],
            23.969,
            places=3,
        )

    def test_placement_plane_keeps_physical_comparator_explicit(self) -> None:
        row = self.doc["evidence_planes"][2]
        comparator = row["comparator"]
        self.assertEqual(comparator["observed_minimal_delta_actions"], 24)
        self.assertEqual(comparator["full_reenforcement_reference_actions"], 40)
        self.assertAlmostEqual(comparator["action_reduction_fraction"], 0.4)
        self.assertEqual(
            comparator["decision_irrelevant_zero_action_transitions"],
            1,
        )

    def test_cost_dimensions_are_not_scalarized(self) -> None:
        summary = receipt_summary(self.doc)
        self.assertIsNone(summary["scalar_gain"])
        self.assertIn(
            "resident_mib_opportunity_saved",
            summary["cost_dimensions"],
        )
        self.assertIn(
            "counterfactual_probe_latency_saved_ms",
            summary["cost_dimensions"],
        )
        self.assertIn(
            "actions_avoided_vs_full_reenforcement",
            summary["cost_dimensions"],
        )

    def test_scalar_gain_smuggling_fails_closed(self) -> None:
        bad = copy.deepcopy(self.doc)
        bad["scalar_gain"] = 1.0
        with self.assertRaisesRegex(
            CrossRepoReceiptError,
            "heterogeneous_costs_must_not_be_scalarized",
        ):
            validate_receipt(bad)

    def test_meta_compilation_has_zero_skill_growth(self) -> None:
        meta = self.doc["meta_compilation"]
        self.assertEqual(
            meta["resident_skill"],
            "PRUNE_PROVEN_DECISION_IRRELEVANT_WORK",
        )
        self.assertEqual(meta["resident_skill_count"], 17)
        self.assertEqual(meta["skill_count_growth"], 0)
        self.assertEqual(meta["catalog_budget_gate"], "PASS")

    def test_export_does_not_claim_new_execution(self) -> None:
        self.assertTrue(self.doc["no_new_physical_run_for_export"])
        self.assertEqual(self.doc["authority_effect"], "NONE")
        self.assertFalse(self.doc["canonical_write"])
        self.assertFalse(self.doc["promotion"])


if __name__ == "__main__":
    unittest.main()
