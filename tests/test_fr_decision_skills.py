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

    def test_semantic_oom_survival_law_requires_complete_facts(self) -> None:
        unknown = compile_decision_context(
            {
                "semantic_oom_question": True,
            }
        )
        self.assertEqual(
            unknown["primary_action"],
            "NO_COMPILED_DECISION",
        )
        self.assertIn(
            "transfer_lead_fixed_integer",
            unknown["unresolved"],
        )

    def test_semantic_oom_survival_law_skill(self) -> None:
        result = compile_decision_context(
            {
                "semantic_oom_question": True,
                "state_arrival_one_per_step": True,
                "always_preemptive_transfer": True,
                "transfer_initiation_one_per_step": True,
                "transfer_lead_fixed_integer": True,
                "transfer_failure_present": False,
                "safe_reclaimability_collapses_history": True,
            }
        )
        self.assertEqual(
            result["primary_action"],
            "USE_ANALYTIC_SURVIVAL_LAW",
        )
        self.assertEqual(
            result["skills"][0]["mc"],
            "SKIP",
        )
        self.assertEqual(
            result["skills"][0]["maturity"],
            "QUALIFIED",
        )

    def test_semantic_oom_survival_law_invalidates_on_failure(self) -> None:
        result = compile_decision_context(
            {
                "semantic_oom_question": True,
                "state_arrival_one_per_step": True,
                "always_preemptive_transfer": True,
                "transfer_initiation_one_per_step": True,
                "transfer_lead_fixed_integer": True,
                "transfer_failure_present": True,
                "safe_reclaimability_collapses_history": True,
            }
        )
        self.assertEqual(
            result["primary_action"],
            "NO_COMPILED_DECISION",
        )

    def test_cold_restore_one_probe_calibration_skill(self) -> None:
        result = compile_decision_context(
            {
                "cold_restore_baseline_question": True,
                "state_size_mib_8": True,
                "cross_run_restore_prior_available": True,
            }
        )
        self.assertEqual(
            result["primary_action"],
            "ONE_PROBE_BASELINE_OPTIONAL_TWO_PROBE_MIN_IF_WORTH_COST_KEEP_TAIL_PRIOR",
        )

    def test_calibration_unknown_fails_closed(self) -> None:
        result = compile_decision_context(
            {
                "cold_restore_baseline_question": True,
            }
        )
        self.assertEqual(
            result["primary_action"],
            "NO_COMPILED_DECISION",
        )
        self.assertIn(
            "state_size_mib_8",
            result["unresolved"],
        )

    def test_negative_result_updates_ci_contract(self) -> None:
        result = compile_decision_context(
            {
                "qualified_negative_result": True,
                "ci_requires_rejected_shape": True,
            }
        )
        self.assertEqual(
            result["primary_action"],
            "REMOVE_REJECTED_SHAPE_FROM_CI_GATE_BEFORE_CHILD_QUALIFICATION",
        )

    def test_catalog_compression(self) -> None:
        stats = catalog_stats()
        self.assertEqual(stats["skill_count"], 16)
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
