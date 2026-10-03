from __future__ import annotations

import unittest

from finite_ram_lab.fr_fp_003_predictive_cold_tier import (
    estimate_safe_eta,
    run_panel,
)


class PredictiveColdTierTests(unittest.TestCase):
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

    def test_predictor_has_no_future_leakage(self) -> None:
        rows = [
            4.0,
            3.0,
            2.2,
            1.7,
            1.3,
            0.9,
        ]
        step = 3

        before = estimate_safe_eta(
            rows,
            step,
        )

        mutated = list(
            rows
        )
        mutated[
            step + 1 :
        ] = [
            1000.0
            for _ in mutated[
                step + 1 :
            ]
        ]

        after = estimate_safe_eta(
            mutated,
            step,
        )

        self.assertEqual(
            before,
            after,
        )

    def test_predictive_beats_reactive_oom(self) -> None:
        reactive = self.matrix[
            "8"
        ][
            "REACTIVE_TRANSFER"
        ]
        predictive = self.matrix[
            "8"
        ][
            "PREDICTIVE_TRANSFER"
        ]

        self.assertGreater(
            reactive[
                "semantic_oom_rate"
            ],
            0.50,
        )
        self.assertEqual(
            predictive[
                "semantic_oom_rate"
            ],
            0.0,
        )

    def test_predictive_uses_less_io_than_always(self) -> None:
        predictive = self.matrix[
            "8"
        ][
            "PREDICTIVE_TRANSFER"
        ]
        always = self.matrix[
            "8"
        ][
            "ALWAYS_PREEMPTIVE"
        ]

        self.assertLess(
            predictive[
                "mean_cold_writes"
            ],
            0.60
            * always[
                "mean_cold_writes"
            ],
        )

    def test_claim_ceiling_is_synthetic(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "SYNTHETIC_PREDICTIVE_TRANSFER_TIMING_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
