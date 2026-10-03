from __future__ import annotations

import unittest

from finite_ram_lab.fr_fp_010_hosted_residency import (
    SAFE_STEP,
    STATE_MIB,
    STEPS,
    run_panel,
)


class HostedResidencyLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()
        import json
        print(
            "FR_FP_010_RESULT="
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

    def test_fixture_geometry(self) -> None:
        fixture = self.result[
            "fixture"
        ]

        self.assertEqual(
            fixture[
                "full_logical_peak_mib"
            ],
            STATE_MIB * STEPS,
        )
        self.assertEqual(
            fixture[
                "gated_logical_peak_mib"
            ],
            STATE_MIB * SAFE_STEP,
        )

    def test_gated_physical_peak_is_lower(self) -> None:
        self.assertLess(
            self.result[
                "physical_peak_ratio_gated_over_full"
            ],
            0.70,
        )

    def test_gated_closes_to_one_live_state(self) -> None:
        gated = self.result[
            "gated"
        ]

        self.assertEqual(
            gated[
                "peak_live_states"
            ],
            SAFE_STEP,
        )
        self.assertEqual(
            gated[
                "final_live_states"
            ],
            1,
        )

    def test_claim_ceiling_is_hosted_physical(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "HOSTED_LINUX_ANONYMOUS_MMAP_RESIDENCY_LIFECYCLE_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
