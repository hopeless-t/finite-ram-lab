from __future__ import annotations

import json
import unittest

from finite_ram_lab.fr_fp_049_joint_migration_aware_knapsack import (
    run_panel,
)


class JointMigrationAwareKnapsackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()
        print(
            "FR_FP_049_RESULT="
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

    def test_dp_matches_exhaustive(self) -> None:
        self.assertTrue(
            self.result[
                "checks"
            ][
                "all_joint_dp_results_match_exhaustive"
            ]
        )

    def test_joint_policy_never_loses_to_two_stage_candidates(self) -> None:
        self.assertTrue(
            self.result[
                "checks"
            ][
                "joint_never_loses_to_semantic_optimum_after_migration_is_priced"
            ]
        )
        self.assertTrue(
            self.result[
                "checks"
            ][
                "joint_never_loses_to_feasible_hold"
            ]
        )

    def test_claim_ceiling_is_reused_evidence(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "SYNTHETIC_JOINT_PLACEMENT_USING_FP046_VALUES_FP047_TRANSITIONS_AND_FP048_COST_MODEL_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
