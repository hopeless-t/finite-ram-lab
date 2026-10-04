from __future__ import annotations

import json
import unittest

from finite_ram_lab.fr_fp_054_endogenous_resident_budget import (
    run_panel,
)


class EndogenousResidentBudgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()
        print(
            "FR_FP_054_RESULT="
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

    def test_resident_usage_falls_with_memory_rent(self) -> None:
        usage = [
            row[
                "resident_mib_round"
            ]
            for row in self.result[
                "sweeps"
            ]
        ]
        self.assertTrue(
            all(
                left >= right
                for left, right
                in zip(
                    usage[:-1],
                    usage[1:],
                )
            )
        )

    def test_zero_rent_recovers_parent(self) -> None:
        self.assertTrue(
            self.result[
                "checks"
            ][
                "zero_memory_rent_recovers_fp053_joint_path"
            ]
        )

    def test_claim_ceiling_is_shadow(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "SYNTHETIC_RESIDENT_RENT_FRONTIER_ON_FP051_PHASES_WITH_FP053_CURRENT_RUN_MIGRATION_SCALES_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
