from __future__ import annotations

import json
import unittest

from finite_ram_lab.fr_fp_022_baseline_estimator_frontier import (
    run_panel,
)


class BaselineEstimatorFrontierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()
        print(
            "FR_FP_022_RESULT="
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

    def test_one_probe_is_minimum_useful_candidate(self) -> None:
        one = self.result[
            "candidates"
        ][
            "1:FIRST"
        ]
        self.assertEqual(
            one[
                "baseline_classification_errors"
            ],
            0,
        )

    def test_two_probe_min_beats_two_probe_median(self) -> None:
        candidates = self.result[
            "candidates"
        ]
        self.assertLess(
            candidates[
                "2:MIN"
            ][
                "mean_abs_log_error"
            ],
            candidates[
                "2:MEDIAN"
            ][
                "mean_abs_log_error"
            ],
        )

    def test_more_probes_are_not_monotonic(self) -> None:
        candidates = self.result[
            "candidates"
        ]
        self.assertLess(
            candidates[
                "1:FIRST"
            ][
                "max_abs_log_error"
            ],
            candidates[
                "3:MEDIAN"
            ][
                "max_abs_log_error"
            ],
        )

    def test_claim_ceiling_is_narrow(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "ESTIMATOR_FRONTIER_ON_FIFTEEN_REUSED_8MIB_COLD_RESTORE_RUNS_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
