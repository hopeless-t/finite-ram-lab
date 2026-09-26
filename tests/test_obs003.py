import unittest

from finite_ram_lab.obs003_study import schedule_rows


class Obs003ScheduleTests(unittest.TestCase):
    def test_every_level_has_A_and_B(self):
        spec = {
            "repeats_per_level_per_block": 2,
            "memory_high_mib": [160, 162, 164, 166, 168],
            "base_schedule_seed": 13,
        }
        rows = schedule_rows(spec, 4)
        self.assertEqual(len(rows), 10)

        for level in spec["memory_high_mib"]:
            g = [r for r in rows if r["memory_high_mib"] == level]
            self.assertEqual(len(g), 2)
            self.assertEqual({r["hot_identity"] for r in g}, {"A", "B"})

    def test_schedule_is_deterministic_per_block(self):
        spec = {
            "repeats_per_level_per_block": 2,
            "memory_high_mib": [160, 162, 164],
            "base_schedule_seed": 13,
        }
        self.assertEqual(schedule_rows(spec, 2), schedule_rows(spec, 2))


if __name__ == "__main__":
    unittest.main()
