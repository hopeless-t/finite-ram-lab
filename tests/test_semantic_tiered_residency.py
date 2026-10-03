from __future__ import annotations

import unittest

from finite_ram_lab.semantic_tiered_residency import run_panel


class SemanticTieredResidencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run_panel()
        cls.arms = cls.result["arms"]

    def test_fast_ssd_selects_hybrid_quantize_plus_offload(self):
        row = self.arms["FAST_SSD_TIERED"]
        self.assertEqual(row["choices"]["KV"], "Q8")
        self.assertEqual(row["choices"]["AUX_EXPERTS"], "SSD")
        self.assertEqual(row["choices"]["ACTIVE_TASK"], "KEEP")
        self.assertEqual(row["relief_mib"], 4096)
        self.assertEqual(row["ssd_write_mib"], 3072)
        self.assertAlmostEqual(
            row["migration_ms_at_p05_bandwidth"],
            1244.8,
        )

    def test_ram_only_uses_more_destructive_degradation(self):
        row = self.arms["RAM_ONLY"]
        self.assertEqual(row["choices"]["KV"], "Q4")
        self.assertEqual(row["choices"]["PREFIX"], "DROP")
        self.assertEqual(row["choices"]["BROWSER_CACHE"], "DROP")
        self.assertEqual(row["semantic_loss"], 45)

    def test_fast_ssd_lowers_objective(self):
        fast = self.arms["FAST_SSD_TIERED"]
        ram = self.arms["RAM_ONLY"]
        self.assertLess(fast["objective"], ram["objective"])
        self.assertEqual(fast["semantic_loss"], 12)
        self.assertEqual(ram["semantic_loss"], 45)

    def test_write_budget_forces_smaller_ssd_action(self):
        row = self.arms["WRITE_BUDGET_2G"]
        self.assertEqual(row["choices"]["KV"], "Q4")
        self.assertEqual(row["choices"]["PREFIX"], "SSD")
        self.assertEqual(row["choices"]["BROWSER_CACHE"], "DROP")
        self.assertEqual(row["ssd_write_mib"], 1024)
        self.assertEqual(row["semantic_loss"], 36)

    def test_analytic_bandwidth_knee(self):
        knee = self.result["analytic_boundaries"][
            "fast_hybrid_min_p05_write_mib_s_at_1600ms"
        ]
        self.assertAlmostEqual(knee, 1939.3939393939395)
        self.assertLess(knee, 2500)
        self.assertGreater(knee, 1000)

    def test_phase_map_has_expected_transitions(self):
        phase = self.result["phase_map"]
        self.assertEqual(phase["150"]["5000"], "RAM_FALLBACK")
        self.assertEqual(phase["800"]["1500"], "PREFIX_SSD_MIX")
        self.assertEqual(phase["1600"]["2000"], "KV_Q8_AUX_SSD")
        self.assertEqual(phase["1600"]["3500"], "PREFIX_AUX_SSD")

    def test_slow_ssd_falls_back(self):
        self.assertEqual(
            self.arms["SLOW_SSD_TIERED"]["choices"],
            self.arms["RAM_ONLY"]["choices"],
        )

    def test_short_deadline_falls_back(self):
        self.assertEqual(
            self.arms["EMERGENCY_SHORT_DEADLINE"]["choices"],
            self.arms["RAM_ONLY"]["choices"],
        )

    def test_tail_risk_is_explicit(self):
        fast = self.arms["FAST_SSD_TIERED"]
        self.assertAlmostEqual(fast["expected_restore_ms"], 26.0)
        self.assertAlmostEqual(fast["cvar95_restore_ms"], 260.0)

    def test_claim_ceiling_is_synthetic(self):
        self.assertTrue(self.result["synthetic_only"])
        self.assertFalse(self.result["live_control_claim"])
        self.assertEqual(
            self.result["claim_ceiling"],
            "SYNTHETIC_TIERED_RESIDENCY_SHADOW_PLANNER_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
