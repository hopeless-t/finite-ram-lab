from __future__ import annotations

import unittest

from finite_ram_lab.fr_meta_011_recursive_panel_fixture import run_panel


class RecursivePanelFixtureTests(unittest.TestCase):
    def test_panel(self) -> None:
        result = run_panel()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(
            result["decision"],
            "SHARE_RECURSIVE_RESEARCH_PANEL_WITHIN_TEST_CLASS",
        )
        self.assertEqual(result["baseline_run_panel_calls"], 2)
        self.assertEqual(result["candidate_run_panel_calls"], 1)
        self.assertEqual(result["meta_meta_perturbations_per_panel"], 300)


if __name__ == "__main__":
    unittest.main()
