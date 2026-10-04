from __future__ import annotations

import json
import unittest

from finite_ram_lab.fr_fp_037_hosted_dynamic_budget import (
    run_panel,
)


class HostedDynamicBudgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()
        print(
            "FR_FP_037_RESULT="
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

    def test_physical_residency_tracks_capacity(self) -> None:
        self.assertEqual(
            self.result[
                "summary"
            ][
                "observed_resident_mib"
            ],
            [
                40.0,
                24.0,
                56.0,
                32.0,
                48.0,
            ],
        )

    def test_infeasible_budget_does_not_mutate_placement(self) -> None:
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
            row[
                "before"
            ],
            row[
                "after"
            ],
        )

    def test_claim_ceiling_is_hosted_dynamic(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "HOSTED_PHYSICAL_DYNAMIC_CAPACITY_ACTUATION_ON_ONE_TEN_STATE_EQUAL_SIZE_FIXTURE_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
