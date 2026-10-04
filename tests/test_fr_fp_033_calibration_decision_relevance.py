from __future__ import annotations

import json
import unittest

from finite_ram_lab.fr_fp_033_calibration_decision_relevance import (
    run_panel,
)


class CalibrationDecisionRelevanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()
        print(
            "FR_FP_033_RESULT="
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

    def test_early_stop_is_safe_in_backtest(self) -> None:
        summary = self.result[
            "summary"
        ]
        self.assertGreater(
            summary[
                "early_stop_runs"
            ],
            0,
        )
        self.assertEqual(
            summary[
                "unsafe_early_stops"
            ],
            0,
        )

    def test_second_probe_can_still_matter(self) -> None:
        self.assertGreater(
            self.result[
                "summary"
            ][
                "surface_change_runs"
            ],
            0,
        )

    def test_claim_ceiling_is_narrow(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "LEAVE_ONE_RUN_OUT_EARLY_STOP_BACKTEST_ON_FIFTEEN_8MIB_HOSTED_RESTORE_RUNS_AND_ONE_POLICY_POINT_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
