from __future__ import annotations

import json
import unittest

from finite_ram_lab.fr_fp_053_current_run_migration_calibration import (
    run_panel,
)


class CurrentRunMigrationCalibrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()
        print(
            "FR_FP_053_RESULT="
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

    def test_holdout_error_improves(self) -> None:
        holdout = self.result[
            "holdout"
        ]
        self.assertLess(
            holdout[
                "scaled"
            ][
                "mae_ms"
            ],
            holdout[
                "unscaled"
            ][
                "mae_ms"
            ],
        )

    def test_path_is_unchanged(self) -> None:
        self.assertFalse(
            self.result[
                "scaled_optimizer"
            ][
                "path_changed"
            ]
        )

    def test_claim_ceiling_is_narrow(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "CURRENT_RUN_DIRECTION_SCALING_AND_REFIT_SKIP_ON_ONE_FP052_HOSTED_TRACE_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
