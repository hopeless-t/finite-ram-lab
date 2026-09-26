import unittest

from finite_ram_lab.exp002_study import schedule_rows


class Exp002ScheduleTests(unittest.TestCase):
    def test_balance(self):
        spec = {
            "repeats_per_arm_per_block": 6,
            "arms": ["correct_pageout", "wrong_pageout", "no_hint"],
            "base_schedule_seed": 7,
        }
        rows = schedule_rows(spec, 2)
        self.assertEqual(len(rows), 18)
        for arm in spec["arms"]:
            g = [r for r in rows if r["arm"] == arm]
            self.assertEqual(len(g), 6)
            self.assertEqual(sum(r["hot_identity"] == "A" for r in g), 3)
            self.assertEqual(sum(r["hot_identity"] == "B" for r in g), 3)


if __name__ == "__main__":
    unittest.main()
