import unittest

from finite_ram_lab.voi001 import accuracy_threshold


class Voi001Tests(unittest.TestCase):
    def test_accuracy_threshold(self):
        self.assertAlmostEqual(accuracy_threshold(0.5, 1.0), 0.5)
        self.assertAlmostEqual(accuracy_threshold(0.5, 4.0), 0.875)
        self.assertAlmostEqual(accuracy_threshold(0.25, 2.0), 0.875)

    def test_accuracy_threshold_bounds(self):
        with self.assertRaises(ValueError):
            accuracy_threshold(-0.1, 1.0)
        with self.assertRaises(ValueError):
            accuracy_threshold(0.5, 0.0)


if __name__ == "__main__":
    unittest.main()
