from __future__ import annotations

import json
import unittest

from finite_ram_lab.fr_fp_042_migration_hysteresis import (
    run_panel,
)


class MigrationHysteresisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()
        print(
            "FR_FP_042_RESULT="
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

    def test_cost_model_cross_validates(self) -> None:
        self.assertLess(
            max(
                row[
                    "absolute_relative_error"
                ]
                for row in self.result[
                    "cost_model"
                ][
                    "validation"
                ]
            ),
            0.05,
        )

    def test_hysteresis_beats_immediate_total(self) -> None:
        self.assertLess(
            self.result[
                "hysteretic"
            ][
                "total_ms"
            ],
            self.result[
                "immediate_optimum"
            ][
                "observed_total_ms"
            ],
        )

    def test_claim_ceiling_is_narrow(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "CROSS_VALIDATED_COST_MODEL_AND_HYSTERESIS_ON_FP037_038_039_EQUAL_SIZE_FIXED_CAPACITY_EVIDENCE_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
