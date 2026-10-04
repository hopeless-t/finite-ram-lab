from __future__ import annotations

import json
import unittest

from finite_ram_lab.fr_fp_029_reuse_drift_alarm_frontier import (
    run_panel,
)


class ReuseDriftAlarmFrontierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()
        print(
            "FR_FP_029_RESULT="
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

    def test_frontier_has_multiple_choices(self) -> None:
        self.assertGreaterEqual(
            len(
                self.result[
                    "pareto_thresholds"
                ]
            ),
            3,
        )

    def test_k4_trades_delay_for_stability_and_coverage(self) -> None:
        stable = self.result[
            "stable"
        ]
        weak = self.result[
            "drift"
        ][
            "0.15"
        ]

        self.assertLess(
            stable[
                "alarms"
            ]["4"][
                "detection_rate"
            ],
            stable[
                "cumulative"
            ][
                "detection_rate"
            ],
        )
        self.assertGreater(
            weak[
                "alarms"
            ]["4"][
                "detection_rate"
            ],
            weak[
                "cumulative"
            ][
                "detection_rate"
            ],
        )
        self.assertGreater(
            weak[
                "alarms"
            ]["4"][
                "median_delay"
            ],
            weak[
                "cumulative"
            ][
                "median_delay"
            ],
        )

    def test_claim_ceiling_is_synthetic(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "SYNTHETIC_DRIFT_ALARM_FRONTIER_FOR_ONE_REUSE_CEILING_AND_WINDOW_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
