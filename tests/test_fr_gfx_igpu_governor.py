from __future__ import annotations

import unittest

from finite_ram_lab.fr_gfx_igpu_governor import (
    run_panel,
)


class FrGfxIgpuGovernorTests(
    unittest.TestCase
):
    @classmethod
    def setUpClass(cls):
        cls.result = run_panel()
        cls.policies = cls.result[
            "policies"
        ]

    def test_native_static_hits_uma_pressure(self):
        self.assertGreater(
            self.policies[
                "NATIVE_STATIC"
            ]["memory_violations"],
            0,
        )

    def test_static_upscale_avoids_uma_violation(self):
        self.assertEqual(
            self.policies[
                "UPSCALE_STATIC"
            ]["memory_violations"],
            0,
        )

    def test_bounded_probe_reduces_local_tail(self):
        self.assertLess(
            self.policies[
                "BOUNDED_PROBE_4"
            ]["deadline_misses"],
            self.policies[
                "LOCAL_ONLY"
            ]["deadline_misses"],
        )

    def test_bounded_probe_is_much_cheaper_than_full_scan(self):
        self.assertLess(
            self.policies[
                "BOUNDED_PROBE_4"
            ]["control_evaluations"],
            self.policies[
                "EXPERT_FULL_SCAN"
            ]["control_evaluations"],
        )

    def test_bounded_probe_preserves_memory_safety(self):
        self.assertEqual(
            self.policies[
                "BOUNDED_PROBE_4"
            ]["memory_violations"],
            0,
        )

    def test_claim_ceiling_is_synthetic(self):
        self.assertTrue(
            self.result[
                "synthetic_only"
            ]
        )
        self.assertFalse(
            self.result[
                "live_game_claim"
            ]
        )
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "SYNTHETIC_UMA_IGPU_GOVERNOR_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
