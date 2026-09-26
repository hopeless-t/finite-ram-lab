import unittest

from finite_ram_lab.mc_quality import quantile, wilson_interval


class MonteCarloQualityTests(unittest.TestCase):
    def test_quantile_endpoints(self):
        xs = [1.0, 2.0, 3.0, 4.0]
        self.assertEqual(1.0, quantile(xs, 0.0))
        self.assertEqual(4.0, quantile(xs, 1.0))

    def test_wilson_contains_observed_rate(self):
        lo, hi = wilson_interval(20, 100)
        self.assertLessEqual(lo, 0.2)
        self.assertGreaterEqual(hi, 0.2)

    def test_wilson_bounds(self):
        lo, hi = wilson_interval(0, 100)
        self.assertGreaterEqual(lo, 0.0)
        self.assertLessEqual(hi, 1.0)


if __name__ == "__main__":
    unittest.main()
