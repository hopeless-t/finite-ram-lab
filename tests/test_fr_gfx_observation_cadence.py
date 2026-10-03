from __future__ import annotations

import unittest

from finite_ram_lab.fr_gfx_observation_cadence import (
    adaptive_detection_probability,
    event_rate_break_even_vs_fast,
    periodic_detection_probability,
    run_panel,
    trigger_recall_for_target,
)


class FrGfxObservationCadenceTests(
    unittest.TestCase
):
    def test_fixed_detection(self):
        self.assertEqual(
            periodic_detection_probability(
                500.0
            ),
            0.37,
        )

    def test_adaptive_detection(self):
        self.assertEqual(
            adaptive_detection_probability(
                0.90
            ),
            0.937,
        )

    def test_trigger_recall_for_90pct_detection(self):
        self.assertAlmostEqual(
            trigger_recall_for_target(
                0.90
            ),
            0.8412698412698413,
        )

    def test_event_rate_break_even(self):
        self.assertEqual(
            event_rate_break_even_vs_fast(),
            2.0,
        )

    def test_adaptive_dominates_intermediate_fixed_cadences(self):
        result = run_panel()
        adaptive = result[
            "adaptive_sampling"
        ]
        fixed = result[
            "fixed_sampling"
        ]

        for key in (
            "100",
            "250",
        ):
            self.assertGreater(
                adaptive[
                    "detection_probability"
                ],
                fixed[key][
                    "detection_probability"
                ],
            )
            self.assertLess(
                adaptive[
                    "samples_per_second"
                ],
                fixed[key][
                    "samples_per_second"
                ],
            )

    def test_sampling_reduction(self):
        result = run_panel()

        self.assertEqual(
            result[
                "adaptive_sampling"
            ][
                "sampling_reduction_vs_always_fast"
            ],
            0.81,
        )

    def test_claim_ceiling(self):
        result = run_panel()

        self.assertEqual(
            result[
                "claim_ceiling"
            ],
            "SYNTHETIC_OBSERVATION_CADENCE_MODEL_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
