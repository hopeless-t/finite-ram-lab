from __future__ import annotations

import json
import unittest

from finite_ram_lab.fr_fp_034_multistate_budget_allocation import (
    run_panel,
)


class MultiStateBudgetAllocationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()
        print(
            "FR_FP_034_RESULT="
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

    def test_budget5_matches_exact_optimum(self) -> None:
        row = self.result[
            "frontier"
        ][
            "5"
        ]
        self.assertTrue(
            row[
                "matches_exact"
            ]
        )
        self.assertEqual(
            len(
                row[
                    "greedy"
                ][
                    "warm_ids"
                ]
            ),
            5,
        )

    def test_shadow_price_is_endogenous(self) -> None:
        interval = self.result[
            "frontier"
        ][
            "5"
        ][
            "greedy"
        ][
            "lambda_interval_ms_per_mib"
        ]
        self.assertLessEqual(
            interval[
                "lower"
            ],
            interval[
                "upper"
            ],
        )

    def test_claim_ceiling_is_shadow_only(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "SYNTHETIC_TEN_STATE_EQUAL_SIZE_ALLOCATION_USING_ONE_HOSTED_BASELINE_AND_REUSED_RESTORE_PRIORS_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
