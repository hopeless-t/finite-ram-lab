from __future__ import annotations

import json
import unittest

from finite_ram_lab.fr_fp_025_risk_aware_tier_frontier import (
    run_panel,
)


class RiskAwareTierFrontierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()
        print(
            "FR_FP_025_RESULT="
            + json.dumps(
                cls.result,
                sort_keys=True,
            ),
            flush=True,
        )

    def test_panel_passes(self) -> None:
        self.assertEqual(
            self.result["status"],
            "PASS",
        )
        self.assertTrue(
            all(
                self.result[
                    "checks"
                ].values()
            )
        )

    def test_two_constraints_remain_separate(self) -> None:
        law = self.result["law"]
        self.assertIn(
            "lambda_star",
            law[
                "expected_break_even_shadow_price"
            ],
        )
        self.assertIn(
            "q_D",
            law[
                "deadline_risk"
            ],
        )

    def test_slow_high_reuse_is_expensive(self) -> None:
        rep = self.result[
            "representative"
        ]
        self.assertGreater(
            rep[
                "slow_high_reuse"
            ][
                "lambda_star_ms_per_mib"
            ],
            rep[
                "fast_low_reuse"
            ][
                "lambda_star_ms_per_mib"
            ],
        )

    def test_claim_ceiling_is_narrow(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "EMPIRICAL_FRONTIER_FROM_REUSED_8MIB_HOSTED_RESTORE_EVIDENCE_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
