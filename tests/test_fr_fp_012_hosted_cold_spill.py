from __future__ import annotations

import json
import unittest

from finite_ram_lab.fr_fp_012_hosted_cold_spill import (
    HOT_STATE_BUDGET,
    RSS_BUDGET_KIB,
    STATE_BYTES,
    STATE_KIB,
    run_panel,
)


class HostedColdSpillTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()
        print(
            "FR_FP_012_RESULT="
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

    def test_calibrated_budget_is_four_states(self) -> None:
        self.assertEqual(
            HOT_STATE_BUDGET,
            4,
        )
        self.assertEqual(
            RSS_BUDGET_KIB,
            4 * STATE_KIB,
        )

    def test_hot_rss_budget_is_respected(self) -> None:
        spill = self.result[
            "spill"
        ]

        self.assertLessEqual(
            spill[
                "peak_hot_states"
            ],
            HOT_STATE_BUDGET,
        )
        self.assertLessEqual(
            spill[
                "peak_rss_delta_kib"
            ],
            RSS_BUDGET_KIB
            + 4096,
        )

    def test_cold_spill_is_durable_before_hot_unmap(self) -> None:
        self.assertEqual(
            self.result[
                "spilled_states"
            ],
            5,
        )
        self.assertEqual(
            self.result[
                "spilled_bytes"
            ],
            5 * STATE_BYTES,
        )
        self.assertTrue(
            all(
                row[
                    "verified"
                ]
                for row
                in self.result[
                    "spill"
                ][
                    "spill_rows"
                ]
            )
        )

    def test_safe_collapse_returns_to_one_hot_state(self) -> None:
        spill = self.result[
            "spill"
        ]

        self.assertEqual(
            spill[
                "final_hot_states"
            ],
            1,
        )
        self.assertEqual(
            spill[
                "final_cold_files"
            ],
            0,
        )
        self.assertLessEqual(
            spill[
                "final_rss_delta_kib"
            ],
            STATE_KIB
            + 4096,
        )

    def test_claim_ceiling_is_narrow(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "HOSTED_LINUX_PROCESS_RSS_BUDGET_AND_FILE_COLD_SPILL_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
