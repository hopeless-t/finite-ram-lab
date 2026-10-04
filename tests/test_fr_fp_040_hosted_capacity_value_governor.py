from __future__ import annotations

import json
import unittest

from finite_ram_lab.fr_fp_040_hosted_capacity_value_governor import (
    CAPACITY_SCHEDULE,
    run_panel,
)


class HostedCapacityValueGovernorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()
        print(
            "FR_FP_040_RESULT="
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

    def test_capacity_schedule_is_observed(self) -> None:
        self.assertEqual(
            self.result[
                "fixture"
            ][
                "capacity_schedule_slots"
            ],
            list(
                CAPACITY_SCHEDULE
            ),
        )

    def test_physical_actions_match_shadow(self) -> None:
        self.assertEqual(
            self.result[
                "summary"
            ][
                "physical_actuations"
            ],
            self.result[
                "shadow"
            ][
                "summary"
            ][
                "minimal_delta_actuations"
            ],
        )

    def test_claim_ceiling_is_narrow(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "HOSTED_PHYSICAL_COMBINED_CAPACITY_VALUE_CONTROL_ON_ONE_TEN_STATE_EQUAL_SIZE_FIVE_PHASE_FIXTURE_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
