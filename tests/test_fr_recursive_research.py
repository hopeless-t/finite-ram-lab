from __future__ import annotations

import unittest

from finite_ram_lab.fr_recursive_research import (
    MIXED_POLICY,
    evaluate_mixed_policy,
    evaluate_protocol,
    invariant_violations,
    run_panel,
)


class RecursiveResearchTests(unittest.TestCase):
    def test_panel_passes(self) -> None:
        result = run_panel()
        self.assertEqual(result["status"], "PASS")
        self.assertTrue(result["promotion_gate"]["pass"])
        self.assertTrue(result["council"]["converged"])

    def test_mixed_policy_preserves_capability_holdout(self) -> None:
        baseline = evaluate_protocol(
            "FIXED_V1",
            scenarios=["CAPABILITY_GAP"],
            trials=2000,
            seed=20261005,
        )
        candidate = evaluate_mixed_policy(
            scenarios=["CAPABILITY_GAP"],
            trials=2000,
            seed=20261005,
        )
        self.assertEqual(MIXED_POLICY["CAPABILITY_GAP"], "FIXED_V1")
        self.assertEqual(baseline, candidate)

    def test_candidate_reduces_expected_cost_without_large_quality_loss(self) -> None:
        baseline = evaluate_protocol("FIXED_V1")
        candidate = evaluate_mixed_policy()
        self.assertLess(candidate["mean_cost"], baseline["mean_cost"])
        self.assertGreater(candidate["mean_utility"], baseline["mean_utility"])
        self.assertGreaterEqual(candidate["correct_rate"], baseline["correct_rate"] - 0.01)
        self.assertGreaterEqual(candidate["rare_capture_rate"], baseline["rare_capture_rate"] - 0.10)
        self.assertGreaterEqual(candidate["mean_progress"], baseline["mean_progress"] - 0.01)

    def test_goodhart_control_is_not_promotable(self) -> None:
        violations = invariant_violations("RISKY_FAST")
        self.assertIn("EXPERIMENT_WITHOUT_COUNCIL", violations)
        self.assertIn("MISSING_EVIDENCE_TREATED_AS_ZERO", violations)
        result = run_panel()
        self.assertFalse(result["meta_meta"]["risky_promotable"])
        self.assertGreaterEqual(result["meta_meta"]["candidate_win_rate"], 0.90)
        self.assertGreater(result["meta_meta"]["min_utility_delta"], 0.0)


if __name__ == "__main__":
    unittest.main()
