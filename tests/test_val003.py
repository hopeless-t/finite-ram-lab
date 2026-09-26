import unittest
import numpy as np

from finite_ram_lab.val003_study import (
    monte_carlo_signflip,
    schedule_rows,
)


class Val003Tests(unittest.TestCase):
    def test_schedule_balance(self):
        spec = {
            "repeats_per_arm_per_block": 10,
            "arms": ["correct_pageout", "no_hint"],
            "base_schedule_seed": 7,
        }
        rows = schedule_rows(spec, 3)
        self.assertEqual(len(rows), 20)
        for arm in spec["arms"]:
            g = [r for r in rows if r["arm"] == arm]
            self.assertEqual(len(g), 10)
            self.assertEqual(sum(r["hot_identity"] == "A" for r in g), 5)
            self.assertEqual(sum(r["hot_identity"] == "B" for r in g), 5)

    def test_randomization_is_deterministic(self):
        values = np.array([-0.2, -0.1, 0.0, 0.1])
        a = monte_carlo_signflip(values, 10000, 42)
        b = monte_carlo_signflip(values, 10000, 42)
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
