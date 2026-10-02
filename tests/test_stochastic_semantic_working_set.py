from __future__ import annotations

import unittest

from finite_ram_lab.stochastic_semantic_working_set import (
    evaluate_replicated_policy,
    first_qualified_budget,
    noisy_key_aware_indices,
    run_panel,
    wilson_interval,
)
from finite_ram_lab.semantic_working_set import corpus


class StochasticSemanticWorkingSetTests(unittest.TestCase):
    def test_wilson_interval_bounds_rate(self):
        lower, upper = wilson_interval(95, 100)
        self.assertLess(lower, 0.95)
        self.assertGreater(upper, 0.95)

    def test_noisy_selection_is_deterministic_for_same_identity(self):
        case = corpus()[0]
        first = noisy_key_aware_indices(
            case,
            2,
            replicate=123,
        )
        second = noisy_key_aware_indices(
            case,
            2,
            replicate=123,
        )
        self.assertEqual(first, second)

    def test_append_truncate_qualified_knee_remains_eight(self):
        self.assertEqual(
            first_qualified_budget("APPEND_TRUNCATE"),
            8,
        )

    def test_noisy_key_aware_qualified_knee_is_two(self):
        self.assertEqual(
            first_qualified_budget("NOISY_KEY_AWARE"),
            2,
        )

    def test_rare_failures_are_captured_at_budget_two(self):
        row = evaluate_replicated_policy(
            "NOISY_KEY_AWARE",
            2,
        )
        self.assertEqual(row["observations"], 2048)
        self.assertEqual(row["failure_count"], 17)
        self.assertGreater(len(row["failure_biopsies"]), 0)
        self.assertLessEqual(len(row["failure_biopsies"]), 16)
        self.assertGreaterEqual(row["wilson95"]["lower"], 0.95)

    def test_panel_claim_ceiling_remains_synthetic(self):
        result = run_panel()
        self.assertTrue(result["synthetic_only"])
        self.assertFalse(result["empirical_model_claim"])
        self.assertEqual(
            result["qualified_knees"]["APPEND_TRUNCATE"],
            8,
        )
        self.assertEqual(
            result["qualified_knees"]["NOISY_KEY_AWARE"],
            2,
        )
        self.assertEqual(
            result["rare_event_probe"]["failure_count"],
            17,
        )
        self.assertEqual(
            result["claim_ceiling"],
            "SYNTHETIC_STOCHASTIC_SEMANTIC_WORKING_SET_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
