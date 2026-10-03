from __future__ import annotations

import unittest

from finite_ram_lab.fr_gap_selector import (
    run_panel,
)


class FrGapSelectorTests(
    unittest.TestCase
):
    @classmethod
    def setUpClass(cls):
        cls.result = run_panel()

    def test_all_gap_classes_are_distinct(self):
        cases = self.result[
            "cases"
        ]

        self.assertEqual(
            cases[
                "evidence_gap"
            ]["classification"],
            "EVIDENCE_GAP",
        )

        self.assertEqual(
            cases[
                "model_gap"
            ]["classification"],
            "MODEL_GAP",
        )

        self.assertEqual(
            cases[
                "capability_gap"
            ]["classification"],
            "CAPABILITY_GAP",
        )

        self.assertEqual(
            cases[
                "contract_gap"
            ]["classification"],
            "CONTRACT_GAP",
        )

    def test_only_capability_gap_opens_new_mechanism_lane(self):
        self.assertEqual(
            self.result[
                "summary"
            ][
                "new_mechanism_cases"
            ],
            1,
        )

    def test_frontier_reached_stops_research_sprawl(self):
        row = self.result[
            "cases"
        ][
            "frontier_reached"
        ]

        self.assertEqual(
            row[
                "classification"
            ],
            "FRONTIER_REACHED",
        )

        self.assertEqual(
            row["next_step"],
            "NO_NEW_RESEARCH",
        )

    def test_claim_ceiling(self):
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "SYNTHETIC_GAP_CLASSIFICATION_AND_RESEARCH_ROUTING_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
