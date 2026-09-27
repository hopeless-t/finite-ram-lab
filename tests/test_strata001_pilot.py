from __future__ import annotations

import unittest

import pandas as pd

from finite_ram_lab.strata001_pilot_study import paired_effects, schedule_rows


SPEC = {
    "trials_per_cell_per_block": 1,
    "memory_high_mib": [160, 168],
    "arms": ["mmap", "buffered_pread", "direct_pread"],
    "base_schedule_seed": 2026092801,
}


class Strata001PilotTests(unittest.TestCase):
    def test_schedule_complete(self) -> None:
        rows = schedule_rows(SPEC, 0)
        self.assertEqual(len(rows), 6)
        cells = {(r["memory_high_mib"], r["arm"]) for r in rows}
        self.assertEqual(
            cells,
            {
                (160, "mmap"),
                (160, "buffered_pread"),
                (160, "direct_pread"),
                (168, "mmap"),
                (168, "buffered_pread"),
                (168, "direct_pread"),
            },
        )

    def test_schedule_is_deterministic_and_block_specific(self) -> None:
        self.assertEqual(schedule_rows(SPEC, 3), schedule_rows(SPEC, 3))
        self.assertNotEqual(schedule_rows(SPEC, 3), schedule_rows(SPEC, 4))

    def test_paired_effects(self) -> None:
        df = pd.DataFrame([
            {"block": 0, "memory_high_mib": 160, "arm": "mmap",
             "hot_resident_fraction": 0.7, "hot_retouch_ms": 20.0,
             "work_ms": 30.0, "file_post_fraction": 1.0},
            {"block": 0, "memory_high_mib": 160, "arm": "buffered_pread",
             "hot_resident_fraction": 0.6, "hot_retouch_ms": 10.0,
             "work_ms": 20.0, "file_post_fraction": 1.0},
            {"block": 0, "memory_high_mib": 160, "arm": "direct_pread",
             "hot_resident_fraction": 0.9, "hot_retouch_ms": 5.0,
             "work_ms": 15.0, "file_post_fraction": 0.0},
        ])
        p = paired_effects(df).iloc[0]
        self.assertAlmostEqual(
            p["hot_residency_diff_direct_minus_buffered"], 0.3
        )
        self.assertAlmostEqual(p["work_ratio_direct_over_buffered"], 0.75)
        self.assertAlmostEqual(p["file_cache_diff_direct_minus_buffered"], -1.0)
        self.assertLess(
            p["log_hot_retouch_ratio_direct_over_buffered"], 0.0
        )


if __name__ == "__main__":
    unittest.main()
