from __future__ import annotations

import json
import unittest

from finite_ram_lab.fr_fp_014_warm_cold_restore import (
    BLOCKS,
    run_panel,
)


class WarmColdRestoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()
        print(
            "FR_FP_014_RESULT="
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

    def test_eight_paired_blocks(self) -> None:
        self.assertEqual(
            self.result[
                "summary"
            ][
                "WARM_PAGECACHE"
            ][
                "trials"
            ],
            BLOCKS,
        )
        self.assertEqual(
            self.result[
                "summary"
            ][
                "COLD_DONTNEED"
            ][
                "trials"
            ],
            BLOCKS,
        )

    def test_residency_tiers_are_physically_distinct(self) -> None:
        warm = self.result[
            "summary"
        ][
            "WARM_PAGECACHE"
        ]
        cold = self.result[
            "summary"
        ][
            "COLD_DONTNEED"
        ]

        self.assertGreaterEqual(
            warm[
                "median_pre_restore_resident_fraction"
            ],
            0.95,
        )
        self.assertLessEqual(
            cold[
                "median_pre_restore_resident_fraction"
            ],
            0.10,
        )

    def test_latency_is_measured_not_assumed(self) -> None:
        self.assertGreater(
            self.result[
                "median_paired_cold_over_warm_read_ratio"
            ],
            0.0,
        )

    def test_claim_ceiling_is_pilot(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "HOSTED_LINUX_WARM_COLD_RESTORE_PILOT_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
