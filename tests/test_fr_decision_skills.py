from __future__ import annotations

import unittest

from finite_ram_lab.fr_decision_skills import (
    catalog_stats,
    compile_decision_context,
    run_panel,
)


class DecisionSkillCompilerTests(unittest.TestCase):
    def test_panel(self) -> None:
        result = run_panel()
        self.assertEqual(result["status"], "PASS")
        self.assertTrue(all(result["checks"].values()))

    def test_exact_reuse_skill(self) -> None:
        result = compile_decision_context(
            {
                "deterministic_duplicate_work": True,
                "scientific_contract_unchanged": True,
                "runtime_is_measurement": False,
            }
        )
        self.assertEqual(
            result["primary_action"],
            "REUSE_EXACT_COMPUTATION",
        )
        self.assertLess(
            result["context_fraction_of_source"],
            0.05,
        )

    def test_runtime_measurement_blocks_reuse_skill(self) -> None:
        result = compile_decision_context(
            {
                "deterministic_duplicate_work": True,
                "scientific_contract_unchanged": True,
                "runtime_is_measurement": True,
            }
        )
        self.assertEqual(
            result["primary_action"],
            "PRESERVE_MEASUREMENT_BODY",
        )
        self.assertNotIn(
            "EXACT_REUSE_BEFORE_SAMPLE_REDUCTION",
            [row["id"] for row in result["skills"]],
        )

    def test_cache_unknown_does_not_guess(self) -> None:
        result = compile_decision_context(
            {"cache_candidate": True}
        )
        self.assertEqual(
            result["primary_action"],
            "NO_COMPILED_DECISION",
        )
        self.assertIn(
            "cache_restore_proven",
            result["unresolved"],
        )

    def test_cache_negative_skill(self) -> None:
        result = compile_decision_context(
            {
                "cache_candidate": True,
                "cache_restore_proven": False,
            }
        )
        self.assertEqual(
            result["primary_action"],
            "REJECT_CACHE_PROMOTION",
        )

    def test_main_ci_is_never_cancelled(self) -> None:
        result = compile_decision_context(
            {
                "same_head_duplicate_ci": True,
                "branch_is_main": True,
            }
        )
        self.assertEqual(
            result["primary_action"],
            "KEEP_MAIN_CI",
        )

    def test_research_ci_can_cancel_superseded_run(self) -> None:
        result = compile_decision_context(
            {
                "same_head_duplicate_ci": True,
                "branch_is_main": False,
            }
        )
        self.assertEqual(
            result["primary_action"],
            "CANCEL_SUPERSEDED_NON_MAIN_CI",
        )

    def test_catalog_compression(self) -> None:
        stats = catalog_stats()
        self.assertEqual(stats["skill_count"], 13)
        self.assertLess(
            stats["catalog_fraction_of_source"],
            0.30,
        )
        self.assertGreater(
            stats["catalog_reduction_fraction"],
            0.70,
        )


if __name__ == "__main__":
    unittest.main()
