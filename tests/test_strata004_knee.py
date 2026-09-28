from __future__ import annotations

import unittest

import pandas as pd

from finite_ram_lab.strata004_knee_study import paired_effects, schedule_rows
from finite_ram_lab.strata004_knee_workload import RELEASE_MIB


SPEC = {
    "trials_per_arm_per_block": 1,
    "arms": [
        "buffered",
        "dontneed_32m",
        "dontneed_48m",
        "dontneed_64m",
        "dontneed_72m",
        "dontneed_80m",
        "dontneed_88m",
        "dontneed_96m",
    ],
    "base_schedule_seed": 2026092805,
}


class Strata004KneeTests(unittest.TestCase):
    def test_schedule_complete(self) -> None:
        rows = schedule_rows(SPEC, 0)
        self.assertEqual(len(rows), 8)
        self.assertEqual({r["arm"] for r in rows}, set(SPEC["arms"]))

    def test_schedule_is_deterministic_and_block_specific(self) -> None:
        self.assertEqual(schedule_rows(SPEC, 2), schedule_rows(SPEC, 2))
        self.assertNotEqual(schedule_rows(SPEC, 2), schedule_rows(SPEC, 3))

    def test_release_intervals(self) -> None:
        self.assertIsNone(RELEASE_MIB["buffered"])
        self.assertEqual(RELEASE_MIB["dontneed_32m"], 32)
        self.assertEqual(RELEASE_MIB["dontneed_48m"], 48)
        self.assertEqual(RELEASE_MIB["dontneed_64m"], 64)
        self.assertEqual(RELEASE_MIB["dontneed_72m"], 72)
        self.assertEqual(RELEASE_MIB["dontneed_80m"], 80)
        self.assertEqual(RELEASE_MIB["dontneed_88m"], 88)
        self.assertEqual(RELEASE_MIB["dontneed_96m"], 96)

    def test_paired_metrics(self) -> None:
        rows = [{
            "block": 0, "arm": "buffered", "memory_high_events": 6,
            "max_scan_memory_mib": 160.0, "post_scan_memory_mib": 159.0,
            "scan_ms": 100.0, "advice_calls": 0,
        }]
        for arm, peak, events, calls in [
            ("dontneed_32m", 110.0, 0, 3),
            ("dontneed_48m", 126.0, 0, 2),
            ("dontneed_64m", 142.0, 0, 2),
            ("dontneed_72m", 150.0, 0, 2),
            ("dontneed_80m", 158.0, 1, 2),
            ("dontneed_88m", 160.0, 4, 2),
            ("dontneed_96m", 160.0, 6, 1),
        ]:
            rows.append({
                "block": 0, "arm": arm, "memory_high_events": events,
                "max_scan_memory_mib": peak, "post_scan_memory_mib": 76.0,
                "scan_ms": 101.0, "advice_calls": calls,
            })
        p = paired_effects(pd.DataFrame(rows))
        x = p[p["arm"] == "dontneed_80m"].iloc[0]
        self.assertAlmostEqual(x["pressure_avoidance_efficiency"], 5.0 / 6.0)
        self.assertAlmostEqual(x["transient_footprint_reduction"], 1.0 - 158.0 / 160.0)
        self.assertAlmostEqual(x["advice_density_calls_per_gib"], 2.0 / (96.0 / 1024.0))


if __name__ == "__main__":
    unittest.main()
