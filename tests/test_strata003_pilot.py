from __future__ import annotations

import unittest

import pandas as pd

from finite_ram_lab.strata003_pilot_study import paired_effects, schedule_rows
from finite_ram_lab.strata003_pilot_workload import RELEASE_MIB


SPEC = {
    "trials_per_arm_per_block": 1,
    "arms": [
        "buffered",
        "dontneed_4m",
        "dontneed_8m",
        "dontneed_16m",
        "dontneed_32m",
        "dontneed_96m",
        "direct",
    ],
    "base_schedule_seed": 2026092804,
}


class Strata003PilotTests(unittest.TestCase):
    def test_schedule_complete(self) -> None:
        rows = schedule_rows(SPEC, 0)
        self.assertEqual(len(rows), 7)
        self.assertEqual({r["arm"] for r in rows}, set(SPEC["arms"]))

    def test_schedule_is_deterministic_and_block_specific(self) -> None:
        self.assertEqual(schedule_rows(SPEC, 2), schedule_rows(SPEC, 2))
        self.assertNotEqual(schedule_rows(SPEC, 2), schedule_rows(SPEC, 3))

    def test_release_intervals(self) -> None:
        self.assertIsNone(RELEASE_MIB["buffered"])
        self.assertEqual(RELEASE_MIB["dontneed_4m"], 4)
        self.assertEqual(RELEASE_MIB["dontneed_96m"], 96)
        self.assertIsNone(RELEASE_MIB["direct"])

    def test_paired_metrics(self) -> None:
        df = pd.DataFrame([
            {"block": 0, "arm": "buffered", "memory_high_events": 6,
             "max_scan_memory_mib": 160.0, "post_scan_memory_mib": 159.0,
             "scan_ms": 100.0, "advice_calls": 0},
            {"block": 0, "arm": "dontneed_16m", "memory_high_events": 1,
             "max_scan_memory_mib": 95.0, "post_scan_memory_mib": 80.0,
             "scan_ms": 105.0, "advice_calls": 6},
            {"block": 0, "arm": "dontneed_4m", "memory_high_events": 0,
             "max_scan_memory_mib": 85.0, "post_scan_memory_mib": 76.0,
             "scan_ms": 110.0, "advice_calls": 24},
            {"block": 0, "arm": "dontneed_8m", "memory_high_events": 0,
             "max_scan_memory_mib": 88.0, "post_scan_memory_mib": 77.0,
             "scan_ms": 108.0, "advice_calls": 12},
            {"block": 0, "arm": "dontneed_32m", "memory_high_events": 2,
             "max_scan_memory_mib": 110.0, "post_scan_memory_mib": 82.0,
             "scan_ms": 102.0, "advice_calls": 3},
            {"block": 0, "arm": "dontneed_96m", "memory_high_events": 5,
             "max_scan_memory_mib": 158.0, "post_scan_memory_mib": 78.0,
             "scan_ms": 101.0, "advice_calls": 1},
            {"block": 0, "arm": "direct", "memory_high_events": 0,
             "max_scan_memory_mib": 76.0, "post_scan_memory_mib": 76.0,
             "scan_ms": 98.0, "advice_calls": 0},
        ])
        p = paired_effects(df)
        x = p[p["arm"] == "dontneed_16m"].iloc[0]
        self.assertAlmostEqual(x["pressure_avoidance_efficiency"], 5.0 / 6.0)
        self.assertAlmostEqual(x["transient_footprint_reduction"], 1.0 - 95.0 / 160.0)
        self.assertAlmostEqual(x["final_footprint_reduction"], 1.0 - 80.0 / 159.0)
        self.assertAlmostEqual(x["scan_ratio_vs_buffered"], 1.05)
        self.assertAlmostEqual(x["advice_density_calls_per_gib"], 64.0)


if __name__ == "__main__":
    unittest.main()
