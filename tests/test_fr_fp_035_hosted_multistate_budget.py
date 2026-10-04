from __future__ import annotations

import json
import unittest

from finite_ram_lab.fr_fp_035_hosted_multistate_budget import (
    run_panel,
)


class HostedMultiStateBudgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()
        print(
            "FR_FP_035_RESULT="
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

    def test_same_capacity_but_fewer_cold_restores(self) -> None:
        value = self.result[
            "value_risk_allocator"
        ]
        anti = self.result[
            "anti_value_control"
        ]
        self.assertEqual(
            value[
                "warm_mib"
            ],
            anti[
                "warm_mib"
            ],
        )
        self.assertLess(
            value[
                "cold_restores"
            ],
            anti[
                "cold_restores"
            ],
        )

    def test_physical_tier_separation(self) -> None:
        for arm in (
            "value_risk_allocator",
            "anti_value_control",
        ):
            row = self.result[
                arm
            ]
            self.assertGreaterEqual(
                row[
                    "warm_restore_pre_residency_median"
                ],
                0.95,
            )
            self.assertLessEqual(
                row[
                    "cold_restore_pre_residency_median"
                ],
                0.10,
            )

    def test_claim_ceiling_is_hosted_pilot(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "HOSTED_PHYSICAL_TEN_STATE_EQUAL_SIZE_SAME_CAPACITY_ALLOCATION_ON_ONE_SYNTHETIC_REUSE_TRACE_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
