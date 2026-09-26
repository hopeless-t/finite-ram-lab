import random
import unittest

from finite_ram_lab.mc import run
from finite_ram_lab.sim import generate_trace, lru_faults, opt_faults


class ReplacementTests(unittest.TestCase):
    def test_opt_never_worse_than_lru_known_trace(self):
        trace = [1, 2, 3, 1, 4, 1, 2, 5, 1, 2, 3, 4, 5]
        self.assertLessEqual(opt_faults(trace, 3), lru_faults(trace, 3))

    def test_capacity_covering_working_set(self):
        trace = [1, 2, 3, 1, 2, 3] * 10
        self.assertEqual(3, lru_faults(trace, 3))
        self.assertEqual(3, opt_faults(trace, 3))

    def test_generator_is_deterministic(self):
        a = generate_trace("bursty", random.Random(42), 200, 32, 8)
        b = generate_trace("bursty", random.Random(42), 200, 32, 8)
        self.assertEqual(a, b)

    def test_mc_is_deterministic(self):
        self.assertEqual(run("stable_hotset", 1234, 10), run("stable_hotset", 1234, 10))

    def test_all_families_obey_oracle_bound(self):
        for family in ("stable_hotset", "sequential_scan", "shifting_hotset", "bursty"):
            result = run(family, 99, 10)
            for row in result["rows"]:
                self.assertLessEqual(row["opt_faults"], row["lru_faults"])


if __name__ == "__main__":
    unittest.main()
