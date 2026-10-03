from __future__ import annotations

import unittest

from finite_ram_lab.ksla_real_state_idiocy import (
    run_panel,
)


class KslaRealStateIdiocyTests(
    unittest.TestCase
):
    @classmethod
    def setUpClass(cls):
        cls.result = run_panel()
        cls.summary = cls.result[
            "policy_summary"
        ]

    def test_adaptive_is_exact(self):
        self.assertEqual(
            self.summary[
                "STALL_ADAPTIVE"
            ]["success_rate"],
            1.0,
        )

    def test_adaptive_is_cheaper_than_expert_heavy(self):
        self.assertLess(
            self.summary[
                "STALL_ADAPTIVE"
            ]["mean_work_cost"],
            self.summary[
                "EXPERT_HEAVY"
            ]["mean_work_cost"],
        )

    def test_adaptive_uses_half_resident_view(self):
        self.assertEqual(
            self.summary[
                "STALL_ADAPTIVE"
            ][
                "peak_resident_coordinates"
            ],
            8,
        )
        self.assertEqual(
            self.summary[
                "EXPERT_HEAVY"
            ][
                "peak_resident_coordinates"
            ],
            16,
        )

    def test_adaptive_reduces_refresh_work(self):
        self.assertLess(
            self.summary[
                "STALL_ADAPTIVE"
            ][
                "mean_refresh_evaluations"
            ],
            self.summary[
                "EXPERT_HEAVY"
            ][
                "mean_refresh_evaluations"
            ],
        )

    def test_expert_heavy_is_still_faster_in_rounds(self):
        self.assertLess(
            self.summary[
                "EXPERT_HEAVY"
            ]["mean_rounds"],
            self.summary[
                "STALL_ADAPTIVE"
            ]["mean_rounds"],
        )

    def test_pure_idiot_fails_reliability_floor(self):
        self.assertLess(
            self.summary[
                "IDIOT_ONLY"
            ]["success_rate"],
            1.0,
        )

    def test_claim_ceiling(self):
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "SYNTHETIC_REAL_STATE_FINITE_VIEW_EXPERIMENT_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
