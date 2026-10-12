from __future__ import annotations

import unittest

from finite_ram_lab.reinstall_capability_final_bench import run


class FinalBenchTests(unittest.TestCase):
    def test_small_validation(self) -> None:
        result = run(iterations=2, seed=20, rebuild_native=False)
        self.assertEqual(result["parity_seeds"], 10)
        self.assertGreater(result["median_speedup"], 0)
        self.assertEqual(result["functional"]["lru_curve_points"], result["functional"]["profile"]["unique_pages"])


if __name__ == "__main__":
    unittest.main()
