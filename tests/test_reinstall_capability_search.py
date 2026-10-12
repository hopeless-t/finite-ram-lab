from __future__ import annotations

import unittest

from finite_ram_lab.reinstall_capability_search import run_search


class CapabilitySearchTests(unittest.TestCase):
    def test_bounded_search_and_parity(self) -> None:
        result = run_search(
            max_loops=4,
            min_loops=4,
            stale_limit=99,
            length=300,
            universe=29,
            capacity=7,
            seed=10,
        )
        self.assertEqual(result["loops_executed"], 4)
        self.assertLessEqual(result["loops_executed"], result["max_loops"])
        self.assertGreater(result["parity_cases"], 0)
        self.assertTrue(all(r["outputs_ok"] for r in result["records"]))


if __name__ == "__main__":
    unittest.main()
