from __future__ import annotations

import json
import unittest

from finite_ram_lab.fr_fp_055_hosted_endogenous_residency import (
    run_panel,
)


class HostedEndogenousResidencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()
        print(
            "FR_FP_055_RESULT="
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

    def test_physical_residency_falls_with_rent(self) -> None:
        values = [
            arm[
                "physical_resident_mib_round"
            ]
            for arm in self.result[
                "arms"
            ]
        ]
        self.assertTrue(
            all(
                left > right
                for left, right
                in zip(
                    values[:-1],
                    values[1:],
                )
            )
        )

    def test_high_rent_can_choose_zero_residency(self) -> None:
        high = self.result[
            "arms"
        ][-1]
        self.assertTrue(
            all(
                row[
                    "snapshot"
                ][
                    "resident_mib"
                ]
                <= 0.75
                for row in high[
                    "phase_rows"
                ]
            )
        )

    def test_claim_ceiling_is_physical(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "HOSTED_PHYSICAL_RESIDENT_RENT_ACTUATION_AT_FOUR_POLICY_POINTS_ON_ONE_VARIABLE_SIZE_FIVE_PHASE_FIXTURE_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
