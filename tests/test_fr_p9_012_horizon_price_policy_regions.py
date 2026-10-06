from __future__ import annotations

import unittest
from fractions import Fraction

from finite_ram_lab.fr_p9_012_horizon_price_policy_regions import (
    ANCHORS,
    MIB,
    break_even_price_ns_per_mib,
    compiled_policy,
    direct_policy,
    run_panel,
)


class HorizonPricePolicyRegionTests(unittest.TestCase):
    def test_break_even_price_is_positive_and_rises_with_horizon(self) -> None:
        thresholds = [break_even_price_ns_per_mib(ANCHORS[h]) for h in (1, 2, 4, 8)]
        self.assertTrue(all(value > 0 for value in thresholds))
        self.assertTrue(all(b > a for a, b in zip(thresholds, thresholds[1:])))

    def test_no_external_price_preserves_typed_frontier(self) -> None:
        anchor = ANCHORS[4]
        capacity = anchor["KEEP_WARM"]["memory_peak_bytes"] + MIB
        self.assertEqual(
            compiled_policy(
                anchor,
                capacity_bytes=capacity,
                external_memory_price_ns_per_mib=None,
            ),
            "TYPED_FRONTIER_UNRESOLVED",
        )

    def test_capacity_feasibility_precedes_price(self) -> None:
        anchor = ANCHORS[8]
        capacity = anchor["FAULT_IN"]["memory_peak_bytes"]
        self.assertEqual(
            compiled_policy(
                anchor,
                capacity_bytes=capacity,
                external_memory_price_ns_per_mib=Fraction(0, 1),
            ),
            "FAULT_IN",
        )

    def test_latency_slo_can_force_keep_warm(self) -> None:
        anchor = ANCHORS[2]
        capacity = anchor["KEEP_WARM"]["memory_peak_bytes"] + MIB
        slo = (anchor["KEEP_WARM"]["materialize_ns_total"] + anchor["FAULT_IN"]["materialize_ns_total"]) // 2
        self.assertEqual(
            compiled_policy(
                anchor,
                capacity_bytes=capacity,
                external_memory_price_ns_per_mib=10**12,
                max_materialize_ns=slo,
            ),
            "KEEP_WARM",
        )

    def test_exact_break_even_is_tie(self) -> None:
        anchor = ANCHORS[1]
        capacity = anchor["KEEP_WARM"]["memory_peak_bytes"] + MIB
        threshold = break_even_price_ns_per_mib(anchor)
        self.assertEqual(
            direct_policy(
                anchor,
                capacity_bytes=capacity,
                external_memory_price_ns_per_mib=threshold,
            ),
            "PRICE_TIE",
        )
        self.assertEqual(
            compiled_policy(
                anchor,
                capacity_bytes=capacity,
                external_memory_price_ns_per_mib=threshold,
            ),
            "PRICE_TIE",
        )

    def test_negative_external_price_fails_closed(self) -> None:
        anchor = ANCHORS[1]
        with self.assertRaises(ValueError):
            compiled_policy(
                anchor,
                capacity_bytes=anchor["KEEP_WARM"]["memory_peak_bytes"],
                external_memory_price_ns_per_mib=-1,
            )

    def test_compiled_grid_matches_direct_solver(self) -> None:
        result = run_panel()
        self.assertEqual(result["status"], "PASS")
        self.assertGreaterEqual(result["verification"]["comparisons"], 1000)
        self.assertEqual(result["verification"]["mismatches"], [])
        self.assertTrue(all(result["checks"].values()))


if __name__ == "__main__":
    unittest.main()
