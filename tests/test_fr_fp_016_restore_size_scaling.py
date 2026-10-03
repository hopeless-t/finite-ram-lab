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

    def test_current_warm_fit_is_reasonable(self) -> None:
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

    def test_cold_single_linear_model_failed_twice(self) -> None:
        history = self.result[
            "replication_history"
        ]

        self.assertTrue(
            all(
                row[
                    "cold_r2"
                ]
                < 0.95
                for row
                in history.values()
            )
        )

    def test_specific_knee_did_not_replicate(self) -> None:
        history = self.result[
            "replication_history"
        ]
        first = history[
            "run_37145768871"
        ]
        second = history[
            "run_37145960094"
        ]

        self.assertGreater(
            first[
                "cold_slope_8_to_16_ns_per_mib"
            ],
            5.0
            * first[
                "cold_slope_4_to_8_ns_per_mib"
            ],
        )
        self.assertLess(
            second[
                "cold_slope_8_to_16_ns_per_mib"
            ],
            second[
                "cold_slope_4_to_8_ns_per_mib"
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
