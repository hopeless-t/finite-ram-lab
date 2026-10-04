from __future__ import annotations

import json
import unittest

from finite_ram_lab.fr_fp_038_online_multistate_value import (
    run_panel,
)


class OnlineMultistateValueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()
        print(
            "FR_FP_038_RESULT="
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

    def test_online_allocation_changes(self) -> None:
        self.assertGreaterEqual(
            self.result[
                "summary"
            ][
                "unique_warm_sets"
            ],
            2,
        )

    def test_decision_irrelevant_phase_has_zero_action(self) -> None:
        self.assertTrue(
            any(
                phase["phase"] > 1
                and phase[
                    "actuation_count"
                ]
                == 0
                for phase
                in self.result[
                    "phases"
                ]
            )
        )

    def test_online_beats_static(self) -> None:
        self.assertGreater(
            self.result[
                "summary"
            ][
                "expected_penalty_reduction_fraction"
            ],
            0.0,
        )

    def test_claim_ceiling_is_synthetic(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "SYNTHETIC_FIVE_PHASE_ONLINE_REUSE_EVIDENCE_REALLOCATION_ON_ONE_TEN_STATE_EQUAL_SIZE_FIXTURE_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
