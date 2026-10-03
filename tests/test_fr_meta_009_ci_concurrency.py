from __future__ import annotations

import unittest

from finite_ram_lab.fr_meta_009_ci_concurrency import (
    cancel_in_progress,
    group_key,
    run_panel,
)


class CiConcurrencyTests(unittest.TestCase):
    def test_push_and_pr_use_same_head_branch_group(self) -> None:
        branch = "research/example"
        self.assertEqual(
            group_key("CI", "", branch),
            group_key("CI", branch, "42/merge"),
        )

    def test_main_is_not_cancelled(self) -> None:
        self.assertFalse(cancel_in_progress("main"))
        self.assertTrue(cancel_in_progress("research/example"))

    def test_panel(self) -> None:
        result = run_panel()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(
            result["decision"],
            "CANCEL_SUPERSEDED_NON_MAIN_CI_BY_HEAD_BRANCH",
        )
        self.assertFalse(result["monte_carlo"]["used"])


if __name__ == "__main__":
    unittest.main()
