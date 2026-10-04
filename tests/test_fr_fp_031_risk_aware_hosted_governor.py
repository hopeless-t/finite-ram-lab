from __future__ import annotations

import json
import unittest

from finite_ram_lab.fr_fp_031_risk_aware_hosted_governor import (
    run_panel,
)


class RiskAwareHostedGovernorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()
        print(
            "FR_FP_031_RESULT="
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

    def test_current_run_calibration_is_physical(self) -> None:
        calibration = self.result[
            "calibration"
        ]
        self.assertEqual(
            len(
                calibration[
                    "rows"
                ]
            ),
            2,
        )
        self.assertTrue(
            calibration[
                "all_pre_restore_cold"
            ]
        )

    def test_risk_policy_is_explicit(self) -> None:
        fixture = self.result[
            "fixture"
        ]
        self.assertGreater(
            fixture[
                "memory_shadow_price_ms_per_mib"
            ],
            0.0,
        )
        self.assertGreater(
            fixture[
                "deadline_ms"
            ],
            0.0,
        )

    def test_claim_ceiling_is_pilot(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "HOSTED_PHYSICAL_RISK_AWARE_TIER_ACTUATION_ON_ONE_SYNTHETIC_REUSE_TRACE_AND_ONE_POLICY_POINT_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
