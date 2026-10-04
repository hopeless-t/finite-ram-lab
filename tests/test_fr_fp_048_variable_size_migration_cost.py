from __future__ import annotations

import json
import unittest

from finite_ram_lab.fr_fp_048_variable_size_migration_cost import (
    REPEATS,
    STATE_SIZES_MIB,
    run_panel,
)


class VariableSizeMigrationCostTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()
        print(
            "FR_FP_048_RESULT="
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

    def test_full_measurement_matrix(self) -> None:
        self.assertEqual(
            self.result[
                "fixture"
            ][
                "physical_action_count"
            ],
            2
            * len(
                STATE_SIZES_MIB
            )
            * REPEATS,
        )

    def test_models_are_cross_validated(self) -> None:
        for direction in (
            "promote",
            "evict",
        ):
            row = self.result[
                direction
            ]
            self.assertGreater(
                row[
                    "constant_loo_mae_ms"
                ],
                0.0,
            )
            self.assertGreater(
                row[
                    "affine_loo_mae_ms"
                ],
                0.0,
            )
            self.assertIn(
                row[
                    "preferred_by_lower_loo_mae"
                ],
                {
                    "CONSTANT_PER_ACTION",
                    "AFFINE_BYTES",
                },
            )

    def test_claim_ceiling_is_physical(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "HOSTED_PHYSICAL_DIRECTIONAL_MIGRATION_COST_ON_SEVEN_STATE_SIZES_AND_THREE_REPEATS_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
