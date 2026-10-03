from __future__ import annotations

import unittest

from finite_ram_lab.fr_gfx_observer_aba import (
    run_panel,
)


class FrGfxObserverAbaTests(
    unittest.TestCase
):
    @classmethod
    def setUpClass(cls):
        cls.result = run_panel()

    def test_aba_reduces_null_mae(self):
        row = self.result[
            "arms"
        ][
            "NULL_OBSERVER"
        ][
            "single_block"
        ]

        self.assertLess(
            row["aba_mae_ms"],
            row["naive_mae_ms"],
        )

    def test_single_block_is_too_noisy(self):
        row = self.result[
            "null_false_perturbation_by_blocks"
        ][
            "1"
        ]

        self.assertGreater(
            row[
                "aba_abs_gt_1ms"
            ],
            0.20,
        )

    def test_eight_blocks_remove_frozen_null_false_alarm(self):
        row = self.result[
            "null_false_perturbation_by_blocks"
        ][
            "8"
        ]

        self.assertEqual(
            row[
                "aba_abs_gt_1ms"
            ],
            0.0,
        )

    def test_light_observer_usually_qualifies(self):
        rate = self.result[
            "arms"
        ][
            "LIGHT_OBSERVER"
        ][
            "eight_block_decision"
        ][
            "equivalence_pass_rate"
        ]

        self.assertGreater(
            rate,
            0.93,
        )

    def test_heavy_observer_never_qualifies(self):
        rate = self.result[
            "arms"
        ][
            "HEAVY_OBSERVER"
        ][
            "eight_block_decision"
        ][
            "equivalence_pass_rate"
        ]

        self.assertEqual(
            rate,
            0.0,
        )

    def test_claim_ceiling(self):
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "SYNTHETIC_OBSERVER_PERTURBATION_PROTOCOL_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
