from __future__ import annotations

import json
import unittest

from finite_ram_lab.fr_fp_057_decision_directed_physical_refinement import (
    NEW_PHYSICAL_RENTS,
    run_panel,
)


class DecisionDirectedPhysicalRefinementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()
        print(
            "FR_FP_057_RESULT="
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

    def test_only_four_new_unique_paths_are_measured(self) -> None:
        self.assertEqual(
            len(
                NEW_PHYSICAL_RENTS
            ),
            4,
        )
        self.assertEqual(
            self.result[
                "source"
            ][
                "new_physical_paths"
            ],
            4,
        )

    def test_all_unique_paths_now_have_physical_evidence(self) -> None:
        self.assertEqual(
            self.result[
                "source"
            ][
                "unique_shadow_paths"
            ],
            8,
        )
        self.assertTrue(
            self.result[
                "checks"
            ][
                "all_eight_unique_paths_have_physical_evidence"
            ]
        )

    def test_no_hidden_scalar_gain(self) -> None:
        self.assertIsNone(
            self.result[
                "scalar_gain"
            ]
        )

    def test_claim_ceiling_is_narrow(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "EIGHT_UNIQUE_HOSTED_PHYSICAL_POLICY_PATHS_FROM_THE_FP054_TWELVE_POINT_RENT_SWEEP_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
