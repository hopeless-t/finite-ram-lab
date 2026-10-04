from __future__ import annotations

import json
import unittest

from finite_ram_lab.fr_fp_036_dynamic_budget_transition import (
    run_panel,
)


class DynamicBudgetTransitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()
        print(
            "FR_FP_036_RESULT="
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

    def test_minimal_actuation_reduces_work(self) -> None:
        summary = self.result[
            "summary"
        ]
        self.assertLess(
            summary[
                "minimal_actuations"
            ],
            summary[
                "full_reenforcement_actuations"
            ],
        )

    def test_infeasible_budget_fails_closed(self) -> None:
        self.assertFalse(
            self.result[
                "infeasible"
            ][
                "greedy"
            ][
                "feasible"
            ]
        )
        self.assertEqual(
            self.result[
                "infeasible"
            ][
                "greedy"
            ][
                "reason"
            ],
            "MANDATORY_WARM_EXCEEDS_BUDGET",
        )

    def test_claim_ceiling_is_shadow_transition(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "SYNTHETIC_DYNAMIC_CAPACITY_TRANSITIONS_ON_THE_FR_FP_034_EQUAL_SIZE_TEN_STATE_FIXTURE_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
