from __future__ import annotations

import json
import unittest

from finite_ram_lab.fr_fp_021_few_shot_calibration import (
    run_panel,
)


class FewShotCalibrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()
        print(
            "FR_FP_021_RESULT="
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

    def test_zero_new_physical_runs(self) -> None:
        self.assertEqual(
            self.result[
                "source"
            ][
                "new_physical_runs"
            ],
            0,
        )

    def test_three_probe_improves_baseline_estimate(self) -> None:
        three = self.result[
            "evaluations"
        ][
            "3"
        ]
        self.assertGreater(
            three[
                "few_shot"
            ][
                "mean_error_reduction_vs_loo_prior"
            ],
            0.80,
        )

    def test_tail_risk_remains(self) -> None:
        three = self.result[
            "evaluations"
        ][
            "3"
        ]
        self.assertGreater(
            three[
                "future_any_25ms_tail"
            ][
                "fn"
            ],
            0,
        )

    def test_claim_ceiling_is_narrow(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "FIFTEEN_REUSED_RUNS_SIX_TRIALS_EACH_FOR_8MIB_FEW_SHOT_CALIBRATION_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
