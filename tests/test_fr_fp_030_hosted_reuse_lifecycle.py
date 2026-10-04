from __future__ import annotations

import json
import unittest

from finite_ram_lab.fr_fp_030_hosted_reuse_lifecycle import (
    run_panel,
)


class HostedReuseLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()
        print(
            "FR_FP_030_RESULT="
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

    def test_governor_uses_real_warm_and_cold_tiers(self) -> None:
        arms = self.result[
            "arms"
        ]
        governor = arms[
            "LIFECYCLE_GOVERNOR"
        ]
        self.assertGreater(
            governor[
                "warm_opportunities"
            ],
            0,
        )
        self.assertGreater(
            governor[
                "cold_opportunities"
            ],
            0,
        )
        self.assertLess(
            governor[
                "cold_restores"
            ],
            arms[
                "ALWAYS_COLD"
            ][
                "cold_restores"
            ],
        )

    def test_semantic_integrity_is_preserved(self) -> None:
        self.assertTrue(
            all(
                arm[
                    "all_restores_verified"
                ]
                for arm
                in self.result[
                    "arms"
                ].values()
            )
        )

    def test_claim_ceiling_is_hosted_physical(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "HOSTED_PHYSICAL_TIER_ACTUATION_ON_ONE_SYNTHETIC_TWO_PHASE_REUSE_TRACE_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
