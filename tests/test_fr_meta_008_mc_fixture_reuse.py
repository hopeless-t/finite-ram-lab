from __future__ import annotations

import unittest

from finite_ram_lab.fr_meta_008_mc_fixture_reuse import run_panel


class McFixtureReuseTests(unittest.TestCase):
    def test_panel(self) -> None:
        result = run_panel()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(
            result["decision"],
            "SHARE_CLASS_LEVEL_MONTE_CARLO_FIXTURE",
        )
        self.assertEqual(result["baseline_mc_episode_evaluations"], 600_000)
        self.assertEqual(result["candidate_mc_episode_evaluations"], 200_000)
        self.assertGreaterEqual(result["structural_reduction_fraction"], 2 / 3)


if __name__ == "__main__":
    unittest.main()
