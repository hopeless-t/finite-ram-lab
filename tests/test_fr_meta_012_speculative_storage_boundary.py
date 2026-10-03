from __future__ import annotations

import unittest

from finite_ram_lab.fr_meta_012_speculative_storage_boundary import (
    classify_prepared_storage,
    run_panel,
)


class SpeculativeStorageBoundaryTests(unittest.TestCase):
    def test_panel(self) -> None:
        result = run_panel()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(
            result["decision"],
            "EPHEMERAL_BUILD_AHEAD_DURABLE_MATERIALIZATION_AFTER_RECEIPT",
        )

    def test_unreferenced_git_object_is_not_durable_contract(self) -> None:
        row = classify_prepared_storage("UNREFERENCED_GIT_OBJECT")
        self.assertFalse(row["durable"])
        self.assertFalse(row["canonical"])

    def test_only_post_receipt_commit_is_canonical(self) -> None:
        row = classify_prepared_storage("POST_RECEIPT_COMMIT")
        self.assertTrue(row["durable"])
        self.assertTrue(row["canonical"])


if __name__ == "__main__":
    unittest.main()
