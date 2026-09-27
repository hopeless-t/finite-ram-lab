from __future__ import annotations

import unittest

import pandas as pd

from finite_ram_lab.strata002_pilot_study import paired_effects, schedule_rows
from finite_ram_lab.strata002_pilot_workload import kernel_supports_noreuse_semantics


SPEC = {
    "trials_per_arm_per_block": 1,
    "arms": ["buffered", "buffered_noreuse", "buffered_dontneed", "direct"],
    "base_schedule_seed": 2026092802,
}


class Strata002PilotTests(unittest.TestCase):
    def test_schedule_complete(self) -> None:
        rows = schedule_rows(SPEC, 0)
        self.assertEqual(len(rows), 4)
        self.assertEqual({r["arm"] for r in rows}, set(SPEC["arms"]))

    def test_schedule_is_deterministic_and_block_specific(self) -> None:
        self.assertEqual(schedule_rows(SPEC, 3), schedule_rows(SPEC, 3))
        self.assertNotEqual(schedule_rows(SPEC, 3), schedule_rows(SPEC, 4))

    def test_kernel_noreuse_semantics_boundary(self) -> None:
        self.assertFalse(kernel_supports_noreuse_semantics("6.2.16"))
        self.assertTrue(kernel_supports_noreuse_semantics("6.3.0"))
        self.assertTrue(kernel_supports_noreuse_semantics("6.8.0-1030-azure"))

    def test_paired_effects(self) -> None:
        df = pd.DataFrame([
            {"block": 0, "arm": "buffered", "memory_high_events": 8,
             "memory_current_mib": 160.0, "memory_peak_mib": 161.0,
             "file_post_fraction": 0.9, "scan_ms": 100.0},
            {"block": 0, "arm": "buffered_noreuse", "memory_high_events": 5,
             "memory_current_mib": 150.0, "memory_peak_mib": 160.0,
             "file_post_fraction": 0.8, "scan_ms": 105.0},
            {"block": 0, "arm": "buffered_dontneed", "memory_high_events": 1,
             "memory_current_mib": 90.0, "memory_peak_mib": 120.0,
             "file_post_fraction": 0.1, "scan_ms": 110.0},
            {"block": 0, "arm": "direct", "memory_high_events": 0,
             "memory_current_mib": 76.0, "memory_peak_mib": 90.0,
             "file_post_fraction": 0.0, "scan_ms": 95.0},
        ])
        p = paired_effects(df)
        d = p[p["arm"] == "buffered_dontneed"].iloc[0]
        self.assertEqual(d["high_events_diff_vs_buffered"], -7.0)
        self.assertEqual(d["memory_current_diff_mib_vs_buffered"], -70.0)
        self.assertAlmostEqual(d["scan_ratio_vs_buffered"], 1.1)


if __name__ == "__main__":
    unittest.main()
