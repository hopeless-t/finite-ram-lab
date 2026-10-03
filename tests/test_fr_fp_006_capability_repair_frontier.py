from __future__ import annotations

import unittest

from finite_ram_lab.fr_fp_006_capability_repair_frontier import (
    run_panel,
)


class CapabilityRepairFrontierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()
        cls.frontier = cls.result[
            "repair_frontier"
        ]

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

    def test_one_step_faster_transfer_repairs_baseline(self) -> None:
        row = self.frontier[
            "transfer_lead"
        ]

        self.assertEqual(
            row[
                "absolute_reduction_steps"
            ],
            1,
        )
        self.assertEqual(
            row[
                "required_lead_steps"
            ],
            3,
        )

    def test_two_more_hot_slots_repairs_baseline(self) -> None:
        row = self.frontier[
            "hot_capacity"
        ]

        self.assertEqual(
            row[
                "absolute_increase_states"
            ],
            2,
        )
        self.assertEqual(
            row[
                "required_budget_states"
            ],
            6,
        )

    def test_state_size_mapping_is_not_physical_claim(self) -> None:
        row = self.frontier[
            "state_size"
        ]

        self.assertAlmostEqual(
            row[
                "minimum_state_size_reduction_fraction"
            ],
            1.0 / 3.0,
        )
        self.assertEqual(
            row[
                "evidence_class"
            ],
            "GEOMETRIC_EQUIVALENCE_ONLY",
        )

    def test_reclaimability_timing_remains_model_gap(self) -> None:
        row = self.frontier[
            "reclaimability_timing"
        ]

        self.assertEqual(
            row[
                "classification"
            ],
            "MODEL_GAP",
        )
        self.assertIsNone(
            row[
                "minimum_shift_steps"
            ]
        )

    def test_no_cross_lever_ranking_without_cost_model(self) -> None:
        self.assertEqual(
            self.result[
                "comparison_policy"
            ],
            "DO_NOT_RANK_HETEROGENEOUS_LEVERS_WITHOUT_A_FROZEN_COMMON_COST_MODEL",
        )


if __name__ == "__main__":
    unittest.main()
