from __future__ import annotations

import json
import unittest

from finite_ram_lab.fr_fp_011_hosted_rss_calibration import (
    SAFE_FRONTIERS,
    STATE_KIB,
    run_panel,
)


class HostedRssCalibrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()
        print(
            "FR_FP_011_RESULT="
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

    def test_frontiers_are_preserved(self) -> None:
        self.assertEqual(
            [
                row[
                    "peak_live_states"
                ]
                for row in self.result[
                    "rows"
                ]
            ],
            list(
                SAFE_FRONTIERS
            ),
        )

    def test_rss_calibration_is_linear(self) -> None:
        fit = self.result[
            "rss_fit"
        ]

        self.assertGreater(
            fit["r2"],
            0.999,
        )
        self.assertGreaterEqual(
            fit["slope"],
            0.90,
        )
        self.assertLessEqual(
            fit["slope"],
            1.10,
        )

    def test_state_byte_estimate_matches_fixture(self) -> None:
        observed = self.result[
            "median_peak_rss_kib_per_live_state"
        ]

        self.assertGreaterEqual(
            observed,
            0.90 * STATE_KIB,
        )
        self.assertLessEqual(
            observed,
            1.10 * STATE_KIB,
        )

    def test_claim_ceiling_is_hosted_physical(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "HOSTED_LINUX_ANONYMOUS_MMAP_LIVE_STATE_RSS_CALIBRATION_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
