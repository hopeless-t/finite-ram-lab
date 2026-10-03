from __future__ import annotations

import unittest

from finite_ram_lab.fr_gfx_signal_ablation import (
    run_panel,
)


class FrGfxSignalAblationTests(
    unittest.TestCase
):
    @classmethod
    def setUpClass(cls):
        cls.result = run_panel()
        cls.rows = cls.result[
            "signal_sets"
        ]

    def test_memory_signals_help(self):
        self.assertGreater(
            self.rows[
                "FRAME_MEM"
            ]["action_accuracy"],
            self.rows[
                "FRAME"
            ]["action_accuracy"],
        )

    def test_gpu_plus_memory_eliminates_false_downscale(self):
        self.assertEqual(
            self.rows[
                "FRAME_GPU_MEM"
            ][
                "gpu_downscale_false_positive_rate"
            ],
            0.0,
        )

    def test_full_is_highest_accuracy(self):
        best = max(
            self.rows,
            key=lambda name: (
                self.rows[
                    name
                ]["action_accuracy"]
            ),
        )

        self.assertEqual(
            best,
            "FULL",
        )

    def test_minimum_safe_signal_set(self):
        self.assertEqual(
            self.result[
                "selection_rules"
            ][
                "minimum_safe"
            ]["selected"],
            "FRAME_GPU_MEM",
        )

    def test_minimum_high_accuracy_signal_set(self):
        self.assertEqual(
            self.result[
                "selection_rules"
            ][
                "minimum_high_accuracy"
            ]["selected"],
            "FULL",
        )

    def test_cost_is_abstract_not_live_overhead(self):
        self.assertIn(
            "not measured CPU overhead",
            self.result[
                "cost_semantics"
            ],
        )

    def test_claim_ceiling(self):
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "SYNTHETIC_SIGNAL_ABLATION_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
