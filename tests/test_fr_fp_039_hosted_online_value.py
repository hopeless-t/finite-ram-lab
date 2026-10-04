from __future__ import annotations

import json
import unittest

from finite_ram_lab.fr_fp_039_hosted_online_value import (
    run_panel,
)


class HostedOnlineValueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()
        print(
            "FR_FP_039_RESULT="
            + json.dumps(
                cls.result,
                sort_keys=True,
            ),
            flush=True,
        )

    def test_panel_passes(self) -> None:
        self.assertEqual(
            self.result["status"],
            "PASS",
        )
        self.assertTrue(
            all(
                self.result[
                    "checks"
                ].values()
            )
        )

    def test_shadow_and_physical_actuation_match(self) -> None:
        self.assertEqual(
            self.result[
                "summary"
            ][
                "physical_actuations"
            ],
            self.result[
                "shadow"
            ][
                "minimal_delta_actuations"
            ],
        )

    def test_zero_action_evidence_phase_is_physical_noop(self) -> None:
        self.assertGreater(
            self.result[
                "summary"
            ][
                "zero_action_transition_count"
            ],
            0,
        )

    def test_claim_ceiling_is_hosted(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "HOSTED_PHYSICAL_FIVE_PHASE_ONLINE_VALUE_REALLOCATION_ON_ONE_TEN_STATE_EQUAL_SIZE_FIXTURE_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
