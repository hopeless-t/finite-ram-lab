import unittest
from finite_ram_lab.val002_study import schedule

class Val002Tests(unittest.TestCase):
    def test_schedule_complete_and_deterministic(self):
        s={
            "base_schedule_seed":10,
            "conditions":[
                {"memory_high_mib":164,"mincore_mode":"full","repeats_per_block":2},
                {"memory_high_mib":164,"mincore_mode":"none","repeats_per_block":2},
            ],
        }
        a=schedule(s,0); b=schedule(s,0)
        self.assertEqual(a,b)
        self.assertEqual(len(a),4)
        self.assertEqual(sum(x["mincore_mode"]=="full" for x in a),2)
        self.assertEqual(sum(x["mincore_mode"]=="none" for x in a),2)

    def test_block_order_changes(self):
        s={
            "base_schedule_seed":10,
            "conditions":[
                {"memory_high_mib":160,"mincore_mode":"full","repeats_per_block":1},
                {"memory_high_mib":164,"mincore_mode":"full","repeats_per_block":2},
                {"memory_high_mib":164,"mincore_mode":"none","repeats_per_block":2},
                {"memory_high_mib":168,"mincore_mode":"none","repeats_per_block":1},
            ],
        }
        self.assertNotEqual(schedule(s,0),schedule(s,1))

if __name__=="__main__":
    unittest.main()
