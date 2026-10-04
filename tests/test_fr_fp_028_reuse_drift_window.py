from __future__ import annotations

import json
import unittest

from finite_ram_lab.fr_fp_028_reuse_drift_window import (
    run_panel,
)


class ReuseDriftWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()
        print(
            "FR_FP_028_RESULT="
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

    def test_rolling_is_faster_but_noisier(self) -> None:
        stable = self.result[
            "stable"
        ]
        self.assertGreater(
            stable[
                "rolling"
            ][
                "conditional_false_revocation_rate"
            ],
            0.50,
        )
        self.assertLess(
            stable[
                "cumulative"
            ][
                "conditional_false_revocation_rate"
            ],
            0.10,
        )

        for row in self.result[
            "drift"
        ].values():
            self.assertLess(
                row[
                    "rolling"
                ][
                    "median_invalidation_delay"
                ],
                row[
                    "cumulative"
                ][
                    "median_invalidation_delay"
                ],
            )

    def test_claim_ceiling_is_synthetic(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "SYNTHETIC_BERNOULLI_DRIFT_INJECTION_FOR_ONE_10PCT_REUSE_CEILING_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
