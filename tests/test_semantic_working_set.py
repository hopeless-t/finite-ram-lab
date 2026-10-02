from __future__ import annotations

import unittest

from finite_ram_lab.semantic_working_set import (
    evaluate_policy,
    first_full_success_budget,
    run_panel,
)


class SemanticWorkingSetTests(unittest.TestCase):
    def test_full_reference_is_exact(self):
        row = evaluate_policy("FULL", 1)
        self.assertEqual(row["exact_rate"], 1.0)

    def test_append_truncate_has_late_pressure_knee(self):
        self.assertEqual(
            first_full_success_budget("APPEND_TRUNCATE"),
            8,
        )
        self.assertEqual(
            evaluate_policy("APPEND_TRUNCATE", 2)["exact_rate"],
            0.25,
        )

    def test_key_aware_preserves_all_cases_at_budget_two(self):
        row = evaluate_policy("KEY_AWARE", 2)
        self.assertEqual(row["exact_rate"], 1.0)
        self.assertEqual(
            first_full_success_budget("KEY_AWARE"),
            2,
        )

    def test_failure_biopsy_records_missing_required_key(self):
        row = evaluate_policy("APPEND_TRUNCATE", 2)
        early = next(
            failure for failure in row["failures"]
            if failure["case"] == "early-single"
        )
        self.assertEqual(
            early["missing_required_keys"],
            ["goal"],
        )

    def test_panel_claim_ceiling_remains_synthetic(self):
        result = run_panel()
        self.assertTrue(result["synthetic_only"])
        self.assertFalse(result["empirical_model_claim"])
        self.assertEqual(
            result["claim_ceiling"],
            "SYNTHETIC_SEMANTIC_WORKING_SET_HARNESS_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
