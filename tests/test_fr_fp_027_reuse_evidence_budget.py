from __future__ import annotations

import json
import unittest

from finite_ram_lab.fr_fp_027_reuse_evidence_budget import (
    clopper_pearson_upper,
    run_panel,
    zero_reuse_closed_form,
)


class ReuseEvidenceBudgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()
        print(
            "FR_FP_027_RESULT="
            + json.dumps(
                cls.result,
                sort_keys=True,
            ),
            flush=True,
        )

    def test_panel_passes(self) -> None:
        self.assertEqual(
            self.result[
                "status"
            ],
            "PASS",
        )
        self.assertTrue(
            all(
                self.result[
                    "checks"
                ].values()
            )
        )

    def test_zero_reuse_formula_matches_exact(self) -> None:
        for n in (
            5,
            11,
            29,
            35,
        ):
            self.assertAlmostEqual(
                clopper_pearson_upper(
                    reused=0,
                    observations=n,
                    confidence=0.95,
                ),
                zero_reuse_closed_form(
                    observations=n,
                    confidence=0.95,
                ),
            )

    def test_reference_sample_budgets(self) -> None:
        table = self.result[
            "table"
        ]
        self.assertEqual(
            table[
                "REFERENCE_10PCT"
            ]["0.95"]["0"][
                "observations"
            ],
            29,
        )
        self.assertEqual(
            table[
                "REFERENCE_25PCT"
            ]["0.95"]["0"][
                "observations"
            ],
            11,
        )
        self.assertEqual(
            table[
                "REFERENCE_50PCT"
            ]["0.95"]["0"][
                "observations"
            ],
            5,
        )

    def test_claim_ceiling_is_statistical(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "EXACT_BINOMIAL_EVIDENCE_BUDGET_UNDER_STABLE_BERNOULLI_REUSE_ASSUMPTION_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
