from __future__ import annotations

import json
import unittest

from finite_ram_lab.fr_fp_051_online_joint_variable_size import (
    run_panel,
)


class OnlineJointVariableSizeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()
        print(
            "FR_FP_051_RESULT="
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

    def test_online_joint_dp_is_exact(self) -> None:
        self.assertTrue(
            self.result[
                "checks"
            ][
                "all_joint_dp_results_match_exhaustive"
            ]
        )

    def test_joint_beats_migration_blind_tracking(self) -> None:
        self.assertLess(
            self.result[
                "joint"
            ][
                "total_ms"
            ],
            self.result[
                "migration_blind_semantic"
            ][
                "total_ms"
            ],
        )

    def test_claim_ceiling_is_synthetic(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "SYNTHETIC_FIVE_PHASE_VARIABLE_SIZE_DYNAMIC_CAPACITY_JOINT_OPTIMIZATION_USING_REUSED_HOSTED_COST_EVIDENCE_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
