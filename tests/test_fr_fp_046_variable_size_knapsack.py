from __future__ import annotations

import json
import unittest

from finite_ram_lab.fr_fp_046_variable_size_knapsack import (
    run_panel,
)


class VariableSizeKnapsackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()
        print(
            "FR_FP_046_RESULT="
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

    def test_exact_dp_matches_exhaustive(self) -> None:
        self.assertTrue(
            all(
                row[
                    "dp_matches_exhaustive"
                ]
                for row in self.result[
                    "frontier"
                ].values()
            )
        )

    def test_mandatory_budget_fails_closed(self) -> None:
        row = self.result[
            "frontier"
        ][
            "24"
        ][
            "dp_exact"
        ]
        self.assertFalse(
            row[
                "feasible"
            ]
        )
        self.assertEqual(
            row[
                "reason"
            ],
            "MANDATORY_WARM_BYTES_EXCEED_BUDGET",
        )

    def test_claim_ceiling_is_narrow(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "SYNTHETIC_VARIABLE_SIZE_ALLOCATION_USING_FP034_VALUES_AND_ONE_FROZEN_SIZE_VECTOR_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
