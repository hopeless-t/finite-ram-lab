from __future__ import annotations

import json
import unittest

from finite_ram_lab.fr_fp_013_cold_spill_dontneed import (
    run_panel,
)


class ColdSpillDontneedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()
        print(
            "FR_FP_013_RESULT="
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

    def test_dontneed_reduces_cgroup_peak(self) -> None:
        ratio = self.result[
            "cgroup_peak_ratio_dontneed_over_plain"
        ]

        self.assertIsNotNone(
            ratio
        )
        self.assertLess(
            ratio,
            0.75,
        )

    def test_dontneed_is_actually_called(self) -> None:
        rows = self.result[
            "dontneed"
        ][
            "spill_rows"
        ]

        self.assertEqual(
            len(rows),
            5,
        )
        self.assertTrue(
            all(
                row[
                    "advice_called"
                ]
                and row[
                    "advice_error"
                ]
                is None
                for row
                in rows
            )
        )

    def test_claim_ceiling_is_narrow(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "HOSTED_LINUX_CGROUP_PAGE_CACHE_RELEASE_FOR_THIS_COLD_SPILL_FIXTURE_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
