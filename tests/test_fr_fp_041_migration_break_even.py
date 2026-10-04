from __future__ import annotations

import json
import unittest

from finite_ram_lab.fr_fp_041_migration_break_even import (
    OBSERVATIONS_PER_PHASE,
    run_panel,
)


class MigrationBreakEvenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()
        print(
            "FR_FP_041_RESULT="
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

    def test_no_value_swap_pays_back_within_phase(self) -> None:
        moving = [
            row
            for row in self.result[
                "transitions"
            ]
            if row[
                "placement_changed"
            ]
        ]
        self.assertTrue(
            all(
                row[
                    "break_even_rounds"
                ]
                > OBSERVATIONS_PER_PHASE
                for row in moving
            )
        )

    def test_migration_cost_dominates_aggregate_phase_benefit(self) -> None:
        summary = self.result[
            "summary"
        ]
        self.assertLess(
            summary[
                "benefit_to_migration_ratio"
            ],
            1.0,
        )

    def test_claim_ceiling_is_reused_physical(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "REUSED_HOSTED_ACTUATION_COST_BREAK_EVEN_ON_FP038_039_FIXED_CAPACITY_TRACE_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
