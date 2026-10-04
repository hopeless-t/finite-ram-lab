from __future__ import annotations

import json
import unittest

from finite_ram_lab.fr_fp_032_decision_relevance_bypass import (
    evidence_relevance,
    run_panel,
)


class DecisionRelevanceBypassTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()
        print(
            "FR_FP_032_RESULT="
            + json.dumps(
                cls.result,
                sort_keys=True,
            ),
            flush=True,
        )

    def test_panel_passes(self) -> None:
        self.assertEqual(
            self.result["status"],
            "PASS",
        )
        self.assertTrue(
            all(
                self.result[
                    "checks"
                ].values()
            )
        )

    def test_p1_skips_evidence(self) -> None:
        self.assertEqual(
            evidence_relevance(1.0),
            "BYPASS_REUSE_EVIDENCE_AND_KEEP_COLD",
        )
        self.assertEqual(
            self.result[
                "bypass"
            ][
                "reuse_evidence_observations"
            ],
            0,
        )

    def test_interior_ceiling_retains_evidence_plane(self) -> None:
        self.assertEqual(
            evidence_relevance(0.10),
            "REUSE_EVIDENCE_REQUIRED",
        )

    def test_claim_ceiling_is_narrow(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "HOSTED_PHYSICAL_P1_REUSE_CEILING_DECISION_RELEVANCE_BYPASS_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
