import mmap
import os
import unittest

from finite_ram_lab.obs002_study import schedule_rows
from finite_ram_lab.region_workload import PAGE_SIZE, _mapping, residency


class Obs002Tests(unittest.TestCase):
    def test_schedule_shape(self):
        spec = {
            "base_schedule_seed": 1,
            "conditions": [
                {"memory_high_mib": 160, "repeats_per_block": 1},
                {"memory_high_mib": 164, "repeats_per_block": 4},
                {"memory_high_mib": 168, "repeats_per_block": 1},
            ],
        }
        rows = schedule_rows(spec, 0)
        self.assertEqual(len(rows), 6)
        levels = [r["memory_high_mib"] for r in rows]
        self.assertEqual(levels.count(160), 1)
        self.assertEqual(levels.count(164), 4)
        self.assertEqual(levels.count(168), 1)

    def test_mincore_tracks_touched_anonymous_pages(self):
        size = PAGE_SIZE * 16
        mm = _mapping(size)
        try:
            before = residency(mm, size)
            for i in range(0, size, PAGE_SIZE):
                mm[i] = 1
            after = residency(mm, size)
            self.assertEqual(after["resident_pages"], 16)
            self.assertGreaterEqual(after["resident_pages"], before["resident_pages"])
        finally:
            mm.close()


if __name__ == "__main__":
    unittest.main()
