from __future__ import annotations

import json
import unittest

from finite_ram_lab.fr_fp_059_decision_relevant_lookup_validity import (
    run_panel,
)


class DecisionRelevantLookupValidityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()
        print(
            "FR_FP_059_RESULT="
            + json.dumps(
                cls.result,
                sort_keys=True,
            ),
            flush=True,
        )

    def test_panel_passes(self) -> None:
        self.assertEqual(
            self.result["status"],
            "PASS",
        )
        self.assertTrue(
            all(
                self.result[
                    "checks"
                ].values()
            )
        )

    def test_irrelevant_evidence_mutations_keep_lookup(self) -> None:
        for name in self.result[
            "keep_cases"
        ]:
            self.assertEqual(
                self.result[
                    "mutation_cases"
                ][name]["action"],
                "KEEP_HOT_LOOKUP",
            )

    def test_surface_mutations_invalidate_lookup(self) -> None:
        for name in self.result[
            "invalidate_cases"
        ]:
            self.assertEqual(
                self.result[
                    "mutation_cases"
                ][name]["action"],
                "INVALIDATE_AND_RECOMPILE_LOOKUP",
            )

    def test_claim_ceiling_is_narrow(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "DECISION_SURFACE_VALIDITY_GATE_FOR_THE_FP058_SCALAR_MEMORY_RENT_LOOKUP_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
