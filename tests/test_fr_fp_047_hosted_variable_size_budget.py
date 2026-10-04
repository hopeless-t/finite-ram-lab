from __future__ import annotations

import json
import unittest

from finite_ram_lab.fr_fp_047_hosted_variable_size_budget import (
    run_panel,
)


class HostedVariableSizeBudgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()
        print(
            "FR_FP_047_RESULT="
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

    def test_physical_bytes_match_exact_allocator(self) -> None:
        observed = self.result[
            "summary"
        ][
            "observed_resident_mib"
        ]
        allocated = self.result[
            "summary"
        ][
            "allocated_used_mib"
        ]

        for left, right in zip(
            observed,
            allocated,
        ):
            self.assertAlmostEqual(
                left,
                right,
                delta=0.75,
            )

    def test_infeasible_budget_is_noop(self) -> None:
        row = self.result[
            "infeasible"
        ]
        self.assertEqual(
            row[
                "actuation_count"
            ],
            0,
        )
        self.assertEqual(
            row["before"],
            row["after"],
        )

    def test_claim_ceiling_is_hosted_physical(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "HOSTED_PHYSICAL_VARIABLE_SIZE_ALLOCATION_ON_ONE_TEN_STATE_SIZE_VECTOR_AND_BUDGET_SCHEDULE_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
