from __future__ import annotations

import unittest

from finite_ram_lab.fr_meta_013_pip_cache import run_panel


class PipCacheTests(unittest.TestCase):
    def test_negative_dogfood_result(self) -> None:
        result = run_panel()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(
            result["decision"],
            "DO_NOT_PROMOTE_PIP_CACHE_FOR_CURRENT_STACKED_PR_FLOW",
        )
        self.assertTrue(result["checks"]["implementation_cache_miss_observed"])
        self.assertTrue(result["checks"]["pr_cache_miss_observed"])
        self.assertLess(result["measured_speedup_ratio"], 1.10)


if __name__ == "__main__":
    unittest.main()
