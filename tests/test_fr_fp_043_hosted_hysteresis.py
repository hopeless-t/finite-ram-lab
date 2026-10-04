from __future__ import annotations

import json
import unittest

from finite_ram_lab.fr_fp_043_hosted_hysteresis import (
    run_panel,
)


class HostedHysteresisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()
        print(
            "FR_FP_043_RESULT="
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

    def test_both_hold_and_migrate_are_exercised(self) -> None:
        decisions = self.result[
            "decisions"
        ]
        self.assertTrue(
            any(
                row[
                    "migrated"
                ]
                for row in decisions
            )
        )
        self.assertTrue(
            any(
                not row[
                    "migrated"
                ]
                for row in decisions
            )
        )

    def test_hysteresis_reduces_physical_actions(self) -> None:
        self.assertLess(
            self.result[
                "hysteretic"
            ][
                "physical_actions"
            ],
            self.result[
                "immediate"
            ][
                "physical_actions"
            ],
        )

    def test_claim_ceiling_is_hosted_physical(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "HOSTED_PHYSICAL_HYSTERESIS_ON_ONE_FIVE_PHASE_EQUAL_SIZE_FIXED_CAPACITY_H100_FIXTURE_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
