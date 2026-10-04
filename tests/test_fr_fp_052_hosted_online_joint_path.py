from __future__ import annotations

import json
import unittest

from finite_ram_lab.fr_fp_052_hosted_online_joint_path import (
    run_panel,
)


class HostedOnlineJointPathTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()
        print(
            "FR_FP_052_RESULT="
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

    def test_joint_beats_semantic_tracking_physically(self) -> None:
        joint = self.result[
            "joint"
        ]
        semantic = self.result[
            "migration_blind_semantic"
        ]
        self.assertLess(
            joint[
                "physical_actions"
            ],
            semantic[
                "physical_actions"
            ],
        )
        self.assertLess(
            joint[
                "physical_hybrid_total_ms"
            ],
            semantic[
                "physical_hybrid_total_ms"
            ],
        )

    def test_claim_ceiling_is_narrow(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "HOSTED_PHYSICAL_FIVE_PHASE_VARIABLE_SIZE_JOINT_PATH_ON_ONE_FROZEN_ONLINE_TRACE_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
