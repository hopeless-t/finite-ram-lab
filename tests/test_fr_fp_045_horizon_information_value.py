from __future__ import annotations

import json
import unittest

from finite_ram_lab.fr_fp_045_horizon_information_value import (
    run_panel,
)


class HorizonInformationValueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()
        print(
            "FR_FP_045_RESULT="
            + json.dumps(
                cls.result,
                sort_keys=True,
            ),
            flush=True,
        )

    def test_panel_passes(self) -> None:
        self.assertEqual(
            self.result["status"],
            "PASS",
        )
        self.assertTrue(
            all(
                self.result[
                    "checks"
                ].values()
            )
        )

    def test_regret_formula_matches_exhaustive_grid(self) -> None:
        self.assertEqual(
            self.result[
                "grid"
            ][
                "mismatches"
            ],
            0,
        )

    def test_measurement_cost_can_prune_ambiguous_measurement(self) -> None:
        rep = self.result[
            "representative"
        ]
        self.assertEqual(
            rep[
                "phase2_cost5"
            ][
                "measurement_decision"
            ],
            "MEASURE_MORE",
        )
        self.assertEqual(
            rep[
                "phase2_cost20"
            ][
                "measurement_decision"
            ],
            "STOP_MEASUREMENT_TAKE_ROBUST_ACTION",
        )

    def test_claim_ceiling_is_analytic(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "ANALYTIC_ROBUST_INFORMATION_VALUE_BOUND_ON_FP044_HORIZON_CONTEXTS_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
