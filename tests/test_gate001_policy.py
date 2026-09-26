import unittest

import numpy as np

from finite_ram_lab.gate001_policy import break_even_accuracy, gate_cost


class Gate001PolicyTests(unittest.TestCase):
    def test_break_even_symmetric(self):
        arr = {
            "A_N": np.array([1.0]),
            "A_W": np.array([3.0]),
            "M_N": np.array([3.0]),
            "M_C": np.array([1.0]),
        }
        self.assertAlmostEqual(break_even_accuracy(arr, 0.5), 0.5)

    def test_gate_mapping(self):
        arr = {
            "A_N": np.array([10.0]),
            "A_W": np.array([100.0]),
            "M_N": np.array([80.0]),
            "M_C": np.array([20.0]),
        }
        # Perfect signal: aligned -> NO_HINT, misaligned -> CORRECT.
        value = gate_cost(arr, q=0.5, a=1.0)
        self.assertAlmostEqual(float(value[0]), 15.0)
        # Always wrong signal: aligned -> WRONG, misaligned -> NO_HINT.
        value = gate_cost(arr, q=0.5, a=0.0)
        self.assertAlmostEqual(float(value[0]), 90.0)


if __name__ == "__main__":
    unittest.main()
