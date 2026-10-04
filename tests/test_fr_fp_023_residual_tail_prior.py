from __future__ import annotations

import json
import unittest

from finite_ram_lab.fr_fp_023_residual_tail_prior import (
    run_panel,
)


class ResidualTailPriorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()
        print(
            "FR_FP_023_RESULT="
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

    def test_normalization_reduces_cross_run_dispersion(self) -> None:
        dispersion = self.result[
            "cross_run_dispersion"
        ]
        self.assertGreater(
            dispersion[
                "relative_reduction"
            ],
            0.50,
        )

    def test_deadline_brier_improves(self) -> None:
        for row in self.result[
            "deadline_brier"
        ].values():
            self.assertLess(
                row[
                    "normalized_brier"
                ],
                row[
                    "raw_brier"
                ],
            )

    def test_tail_is_not_erased(self) -> None:
        residual = self.result[
            "residual"
        ]
        self.assertGreater(
            residual[
                "gt_2x_rate"
            ],
            0.10,
        )
        self.assertGreater(
            residual[
                "gt_5x_rate"
            ],
            0.05,
        )

    def test_claim_ceiling_is_narrow(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "LEAVE_ONE_RUN_OUT_RESIDUAL_TAIL_MODEL_ON_FIFTEEN_REUSED_8MIB_COLD_RUNS_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
