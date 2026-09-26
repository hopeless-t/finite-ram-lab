import unittest
from finite_ram_lab.env004_study import schedule_rows

class Env004ScheduleTests(unittest.TestCase):
    def test_balanced(self):
        spec={
            "arms":["pageout_only","pageout_plus_reclaim"],
            "repeats_per_arm_per_block":2,
            "base_seed":1
        }
        rows=schedule_rows(spec,0)
        self.assertEqual(len(rows),4)
        for arm in spec["arms"]:
            self.assertEqual(sum(r["arm"]==arm for r in rows),2)

if __name__=="__main__":
    unittest.main()
