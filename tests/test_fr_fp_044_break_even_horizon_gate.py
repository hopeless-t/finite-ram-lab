from __future__ import annotations

import json
import unittest

from finite_ram_lab.fr_fp_044_break_even_horizon_gate import (
    run_panel,
)


class BreakEvenHorizonGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()
        print(
            "FR_FP_044_RESULT="
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

    def test_interval_gate_matches_direct_policy(self) -> None:
        self.assertEqual(
            self.result[
                "grid"
            ][
                "mismatches"
            ],
            0,
        )

    def test_h100_has_mixed_threshold_regime(self) -> None:
        thresholds = self.result[
            "thresholds"
        ]
        self.assertLess(
            thresholds[
                "PHASE2_A_TO_B"
            ],
            100.0,
        )
        self.assertLess(
            thresholds[
                "PHASE3_B_TO_A"
            ],
            100.0,
        )
        self.assertGreater(
            thresholds[
                "PHASE5_A_TO_B"
            ],
            100.0,
        )

    def test_claim_ceiling_is_analytic(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "ANALYTIC_HORIZON_INTERVAL_REDUCTION_ON_FP042_043_EQUAL_SIZE_MIGRATION_CONTEXTS_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
