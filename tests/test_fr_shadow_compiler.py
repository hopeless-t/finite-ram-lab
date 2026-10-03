from __future__ import annotations

import unittest

from finite_ram_lab.fr_shadow_compiler import (
    run_panel,
)


class FrShadowCompilerTests(
    unittest.TestCase
):
    @classmethod
    def setUpClass(cls):
        cls.result = run_panel()

    def test_causal_path_uses_no_future_evidence(self):
        self.assertEqual(
            self.result[
                "summary"
            ][
                "causal_future_evidence_uses"
            ],
            0,
        )

    def test_nearest_neighbor_leaks_future_once(self):
        self.assertEqual(
            self.result[
                "summary"
            ][
                "leaky_future_evidence_uses"
            ],
            1,
        )

    def test_future_leakage_inflates_frontier(self):
        summary = self.result[
            "summary"
        ]

        self.assertEqual(
            summary[
                "causal_qualified_at_budget"
            ],
            5,
        )

        self.assertEqual(
            summary[
                "leaky_qualified_at_budget"
            ],
            6,
        )

    def test_stale_evidence_fails_closed(self):
        self.assertEqual(
            self.result[
                "stale_evidence_decision"
            ]["status"],
            "INSUFFICIENT_EVIDENCE",
        )

    def test_no_live_action_executes(self):
        self.assertEqual(
            self.result[
                "governance"
            ][
                "live_actions_executed"
            ],
            0,
        )

    def test_claim_ceiling(self):
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "SYNTHETIC_CAUSAL_SHADOW_COMPILER_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
