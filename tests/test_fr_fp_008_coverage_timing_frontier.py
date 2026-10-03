from __future__ import annotations

import unittest

from finite_ram_lab.fr_fp_008_coverage_timing_frontier import (
    run_panel,
)


class CoverageTimingFrontierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()
        cls.refs = cls.result[
            "reference_cells"
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

    def test_timing_only_has_coverage_floor(self) -> None:
        row = self.refs[
            "timing_only"
        ]

        self.assertAlmostEqual(
            row[
                "semantic_oom_rate"
            ],
            0.194,
        )

    def test_full_coverage_alone_is_not_enough(self) -> None:
        row = self.refs[
            "coverage_only"
        ]

        self.assertEqual(
            row[
                "coverage"
            ],
            1.0,
        )
        self.assertGreater(
            row[
                "semantic_oom_rate"
            ],
            0.30,
        )

    def test_joint_repair_crosses_frontier(self) -> None:
        row = self.refs[
            "combined"
        ]

        self.assertEqual(
            row[
                "coverage"
            ],
            1.0,
        )
        self.assertEqual(
            row[
                "semantic_oom_rate"
            ],
            0.0,
        )

    def test_claim_ceiling_is_synthetic(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "SYNTHETIC_COVERAGE_TIMING_INTERACTION_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
