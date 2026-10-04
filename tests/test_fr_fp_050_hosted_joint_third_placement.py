from __future__ import annotations

import json
import unittest

from finite_ram_lab.fr_fp_050_hosted_joint_third_placement import (
    run_panel,
)


class HostedJointThirdPlacementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()
        print(
            "FR_FP_050_RESULT="
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

    def test_joint_beats_semantic_physically(self) -> None:
        self.assertTrue(
            all(
                row[
                    "joint_beats_semantic"
                ]
                for row in self.result[
                    "contexts"
                ]
            )
        )

    def test_claim_ceiling_is_physical(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "HOSTED_PHYSICAL_VALIDATION_OF_TWO_FP049_THIRD_PLACEMENT_CONTEXTS_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
