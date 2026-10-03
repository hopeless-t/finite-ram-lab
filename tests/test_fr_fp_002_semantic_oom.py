from __future__ import annotations

import unittest

from finite_ram_lab.fr_fp_002_semantic_oom import (
    run_panel,
)


class SemanticOomMonteCarloTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()
        cls.matrix = cls.result[
            "matrix"
        ]

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

    def test_residual_only_corrupts_without_pressure(self) -> None:
        row = self.matrix[
            "16"
        ][
            "RESIDUAL_ONLY"
        ]
        self.assertGreater(
            row[
                "semantic_corruption_rate"
            ],
            0.35,
        )

    def test_validated_endpoint_is_fail_closed(self) -> None:
        unpressured = self.matrix[
            "16"
        ][
            "VALIDATED_ENDPOINT"
        ]
        pressured = self.matrix[
            "8"
        ][
            "VALIDATED_ENDPOINT"
        ]

        self.assertEqual(
            unpressured[
                "semantic_corruption_rate"
            ],
            0.0,
        )
        self.assertGreater(
            pressured[
                "semantic_oom_rate"
            ],
            0.50,
        )

    def test_cold_tier_trades_io_for_survival(self) -> None:
        row = self.matrix[
            "4"
        ][
            "COLD_TIER_VALIDATED"
        ]

        self.assertEqual(
            row[
                "semantic_survival_rate"
            ],
            1.0,
        )
        self.assertEqual(
            row[
                "semantic_oom_rate"
            ],
            0.0,
        )
        self.assertEqual(
            row[
                "semantic_corruption_rate"
            ],
            0.0,
        )
        self.assertGreater(
            row[
                "mean_cold_writes"
            ],
            0.0,
        )

    def test_claim_ceiling_is_synthetic(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "SYNTHETIC_TRAJECTORY_RECLAIMABILITY_AND_SEMANTIC_OOM_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
