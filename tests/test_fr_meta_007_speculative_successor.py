from __future__ import annotations

import unittest

from finite_ram_lab.fr_meta_007_speculative_successor import run_panel, transition


class SpeculativeSuccessorTests(unittest.TestCase):
    def test_panel(self) -> None:
        result = run_panel()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(
            result["decision"],
            "BUILD_AHEAD_DETACHED_PUBLISH_AFTER_PROOF",
        )

    def test_unknown_is_not_publish_permission(self) -> None:
        row = transition("UNKNOWN", "DETACHED_PROVISIONAL")
        self.assertFalse(row["workflow_allowed"])
        self.assertEqual(row["child_authority"], "PROVISIONAL_ONLY")

    def test_pass_allows_publication(self) -> None:
        row = transition("QUALIFIED_PASS", "DETACHED_PROVISIONAL")
        self.assertTrue(row["workflow_allowed"])
        self.assertEqual(row["child_authority"], "CANDIDATE")


if __name__ == "__main__":
    unittest.main()
