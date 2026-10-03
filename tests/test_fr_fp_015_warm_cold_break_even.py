from __future__ import annotations

import unittest

from finite_ram_lab.fr_fp_015_warm_cold_break_even import (
    break_even_reuse_probability,
    break_even_shadow_price_ns_per_mib,
    choose_tier,
    run_panel,
)


class WarmColdBreakEvenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()

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

    def test_break_even_scales_with_reuse_probability(self) -> None:
        full = (
            break_even_shadow_price_ns_per_mib(
                1.0
            )
        )
        half = (
            break_even_shadow_price_ns_per_mib(
                0.5
            )
        )

        self.assertAlmostEqual(
            half,
            0.5 * full,
        )

    def test_inverse_frontier(self) -> None:
        price = (
            break_even_shadow_price_ns_per_mib(
                0.25
            )
        )
        probability = (
            break_even_reuse_probability(
                price
            )
        )

        self.assertAlmostEqual(
            probability,
            0.25,
        )

    def test_same_memory_price_can_choose_different_tiers_by_reuse(self) -> None:
        low = choose_tier(
            reuse_probability=0.05,
            shadow_price_ns_per_mib=(
                50_000.0
            ),
        )
        high = choose_tier(
            reuse_probability=0.50,
            shadow_price_ns_per_mib=(
                50_000.0
            ),
        )

        self.assertEqual(
            low,
            "COLD",
        )
        self.assertEqual(
            high,
            "WARM",
        )

    def test_claim_ceiling_is_narrow(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "ANALYTIC_BREAK_EVEN_FRONTIER_FROM_SINGLE_HOSTED_RESTORE_PILOT_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
