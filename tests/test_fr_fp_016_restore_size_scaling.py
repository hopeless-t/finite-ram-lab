from __future__ import annotations

import json
import unittest

from finite_ram_lab.fr_fp_016_restore_size_scaling import (
    STATE_SIZES_MIB,
    run_panel,
)


class RestoreSizeScalingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()
        print(
            "FR_FP_016_RESULT="
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

    def test_cold_is_slower_at_every_size(self) -> None:
        for size_mib in (
            STATE_SIZES_MIB
        ):
            self.assertGreater(
                self.result[
                    "cold_over_warm_median_read_ratios"
                ][
                    str(
                        size_mib
                    )
                ],
                1.0,
            )

    def test_warm_linear_but_cold_single_line_is_rejected(self) -> None:
        self.assertGreater(
            self.result[
                "fits"
            ][
                "WARM_PAGECACHE"
            ][
                "r2"
            ],
            0.95,
        )
        self.assertLess(
            self.result[
                "fits"
            ][
                "COLD_DONTNEED"
            ][
                "r2"
            ],
            0.95,
        )

    def test_cold_knee_replicates(self) -> None:
        piece = self.result[
            "cold_piecewise"
        ]

        self.assertGreater(
            piece[
                "slope_8_to_16_ns_per_mib"
            ],
            5.0
            * piece[
                "slope_4_to_8_ns_per_mib"
            ],
        )

    def test_claim_ceiling_is_physical_scaling(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "HOSTED_LINUX_WARM_COLD_RESTORE_SIZE_SCALING_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
