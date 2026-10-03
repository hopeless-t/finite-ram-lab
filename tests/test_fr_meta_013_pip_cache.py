from __future__ import annotations

import unittest

from finite_ram_lab.fr_meta_013_pip_cache import run_panel


class PipCacheTests(unittest.TestCase):
    def test_panel(self) -> None:
        result = run_panel()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["decision"], "ENABLE_SETUP_PYTHON_PIP_CACHE")
        self.assertGreater(result["observed_uncached_median_seconds"], 15.0)
        self.assertFalse(result["monte_carlo"]["used"])


if __name__ == "__main__":
    unittest.main()
