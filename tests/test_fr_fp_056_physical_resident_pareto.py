from __future__ import annotations

import json
import unittest

from finite_ram_lab.fr_fp_056_physical_resident_pareto import (
    run_panel,
)


class PhysicalResidentParetoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()
        print(
            "FR_FP_056_RESULT="
            + json.dumps(
                cls.result,
                sort_keys=True,
            ),
            flush=True,
        )

    def test_panel_passes(self) -> None:
        self.assertEqual(
            self.result[
                "status"
            ],
            "PASS",
        )
        self.assertTrue(
            all(
                self.result[
                    "checks"
                ].values()
            )
        )

    def test_no_hidden_scalar_gain(self) -> None:
        self.assertIsNone(
            self.result[
                "scalar_gain"
            ]
        )

    def test_all_anchors_are_pareto(self) -> None:
        self.assertEqual(
            len(
                self.result[
                    "pareto_policy_labels"
                ]
            ),
            4,
        )

    def test_claim_ceiling_is_four_anchor_only(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "FOUR_ANCHOR_HOSTED_PHYSICAL_PARETO_AND_CANDIDATE_CROSSOVERS_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
