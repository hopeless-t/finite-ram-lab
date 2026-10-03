from __future__ import annotations

import unittest

from finite_ram_lab.fr_fp_007_reclaimability_coverage import (
    run_panel,
)


class ReclaimabilityCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()
        cls.sweep = cls.result[
            "safe_shift_sweep"
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

    def test_timing_acceleration_reduces_oom(self) -> None:
        self.assertGreater(
            self.sweep["0"][
                "semantic_oom_rate"
            ],
            self.sweep["4"][
                "semantic_oom_rate"
            ],
        )
        self.assertGreater(
            self.sweep["4"][
                "semantic_oom_rate"
            ],
            self.sweep["8"][
                "semantic_oom_rate"
            ],
        )

    def test_never_safe_trajectories_create_floor(self) -> None:
        safe = self.result[
            "safe_reclaimability"
        ]
        asymptotic = self.sweep[
            "10"
        ][
            "semantic_oom_rate"
        ]

        self.assertEqual(
            safe["never_safe"],
            194,
        )
        self.assertAlmostEqual(
            safe[
                "never_safe_fraction"
            ],
            0.194,
        )
        self.assertAlmostEqual(
            asymptotic,
            safe[
                "never_safe_fraction"
            ],
        )

    def test_timing_is_not_coverage(self) -> None:
        self.assertIn(
            "TIMING_GAP",
            self.result[
                "failure_domains"
            ],
        )
        self.assertIn(
            "COVERAGE_GAP",
            self.result[
                "failure_domains"
            ],
        )

    def test_claim_ceiling_is_synthetic(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "SYNTHETIC_RECLAIMABILITY_TIMING_AND_COVERAGE_DECOMPOSITION_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
