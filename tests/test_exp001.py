import unittest

from finite_ram_lab.exp001_study import schedule_rows


class Exp001ScheduleTests(unittest.TestCase):
    def test_exact_balance(self):
        spec = {
            "repeats_per_arm_per_block": 2,
            "arms": ["hot_evict", "cold_evict"],
            "base_schedule_seed": 99,
        }
        rows = schedule_rows(spec, 3)
        self.assertEqual(len(rows), 4)
        for arm in spec["arms"]:
            g = [r for r in rows if r["arm"] == arm]
            self.assertEqual(len(g), 2)
            self.assertEqual({r["hot_identity"] for r in g}, {"A", "B"})


if __name__ == "__main__":
    unittest.main()
