from __future__ import annotations

import json
import unittest

from finite_ram_lab.fr_fp_043_hosted_hysteresis_100 import (
    run_panel,
)


class HostedHysteresis100Tests(unittest.TestCase):
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

    def test_mixed_hold_migrate_sequence(self) -> None:
        self.assertEqual(
            [
                row[
                    "migrated"
                ]
                for row in self.result[
                    "hysteresis_plan"
                ][
                    "transitions"
                ]
            ],
            [
                True,
                True,
                False,
                False,
            ],
        )

    def test_hysteresis_beats_immediate_total(self) -> None:
        self.assertLess(
            self.result[
                "hysteretic"
            ][
                "observed_total_ms"
            ],
            self.result[
                "immediate"
            ][
                "observed_total_ms"
            ],
        )

    def test_claim_ceiling_is_narrow(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "HOSTED_PHYSICAL_100_ROUND_HYSTERESIS_ON_FP038_EQUAL_SIZE_FIVE_PHASE_FIXTURE_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
