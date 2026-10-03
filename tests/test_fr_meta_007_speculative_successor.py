from __future__ import annotations

import unittest

from finite_ram_lab.fr_meta_007_speculative_successor import run_panel, transition


class SpeculativeSuccessorTests(unittest.TestCase):
    def test_panel(self) -> None:
        result = run_panel()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(
            result["decision"],
            "BUILD_AHEAD_DELTA_MATERIALIZE_AFTER_RECEIPT",
        )

    def test_pass_without_receipt_waits(self) -> None:
        row = transition("QUALIFIED_PASS", "DETACHED_PROVISIONAL")
        self.assertEqual(row["decision"], "WAIT_FOR_PARENT_RECEIPT")

    def test_receipt_requires_materialization_not_direct_publish(self) -> None:
        row = transition("RECEIPT_FROZEN", "DETACHED_PROVISIONAL")
        self.assertEqual(
            row["decision"],
            "MATERIALIZE_DELTA_ON_RECEIPT_THEN_PUBLISH",
        )
        self.assertFalse(row["direct_publish_pre_receipt_commit"])

    def test_unknown_is_not_publish_permission(self) -> None:
        row = transition("UNKNOWN", "DETACHED_PROVISIONAL")
        self.assertEqual(row["decision"], "DO_NOT_PUBLISH_CHILD")


if __name__ == "__main__":
    unittest.main()
