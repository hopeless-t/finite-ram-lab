from __future__ import annotations

import json
import unittest

from finite_ram_lab.fr_fp_026_reuse_ceiling import (
    run_panel,
)


class ReuseCeilingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()
        print(
            "FR_FP_026_RESULT="
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

    def test_exact_reduction_matches_direct_frontier(self) -> None:
        grid = self.result[
            "grid"
        ]
        self.assertGreaterEqual(
            grid[
                "comparisons"
            ],
            10_000,
        )
        self.assertEqual(
            grid[
                "mismatches"
            ],
            0,
        )

    def test_workload_signal_is_only_upper_bound(self) -> None:
        direction = self.result[
            "governor_direction"
        ]
        self.assertEqual(
            direction[
                "needed_workload_signal"
            ],
            "UPPER_CONFIDENCE_BOUND_ON_REUSE_PROBABILITY",
        )
        self.assertEqual(
            direction[
                "not_required"
            ],
            "EXACT_REUSE_PROBABILITY_POINT_ESTIMATE",
        )

    def test_claim_ceiling_is_narrow(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "ANALYTIC_REDUCTION_OF_FR_FP_025_EMPIRICAL_8MIB_FRONTIER_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
