from __future__ import annotations

import unittest

from finite_ram_lab.semantic_oom_regime_drift import (
    run_panel,
)


class SemanticOomRegimeDriftTests(
    unittest.TestCase
):
    @classmethod
    def setUpClass(cls):
        cls.result = run_panel()
        cls.strategies = (
            cls.result["strategies"]
        )

    def test_window_evidence_sequence(self):
        observed = tuple(
            row["classification"]
            for row
            in self.result[
                "window_evidence"
            ]
        )

        self.assertEqual(
            observed,
            (
                "IID_COMPATIBLE",
                "IID_COMPATIBLE",
                "DEPENDENCE_EVIDENCE",
                "IID_COMPATIBLE",
                "DEPENDENCE_EVIDENCE",
                "DEPENDENCE_EVIDENCE",
                "DEPENDENCE_EVIDENCE",
                "DEPENDENCE_EVIDENCE",
                "IID_COMPATIBLE",
                "IID_COMPATIBLE",
                "IID_COMPATIBLE",
                "IID_COMPATIBLE",
            ),
        )

    def test_static_belief_underreacts(self):
        row = self.strategies[
            "STATIC_INITIAL"
        ]

        self.assertEqual(
            row[
                "current_task_loss_count"
            ],
            101,
        )
        self.assertIsNone(
            row[
                "detection_delay_windows"
            ]
        )

    def test_raw_sliding_reacts_fast_but_churns(self):
        row = self.strategies[
            "RAW_SLIDING"
        ]

        self.assertEqual(
            row[
                "current_task_loss_count"
            ],
            41,
        )
        self.assertEqual(
            row["plan_switches"],
            4,
        )
        self.assertEqual(
            row[
                "unnecessary_background_sacrifice_windows"
            ],
            2,
        )
        self.assertTrue(
            row[
                "post_burst_stale_escalation"
            ]
        )
        self.assertEqual(
            row[
                "detection_delay_windows"
            ],
            1,
        )

    def test_hysteresis_reduces_churn_and_stale_escalation(self):
        row = self.strategies[
            "HYSTERESIS_2_ENTER_1_EXIT"
        ]

        self.assertEqual(
            row[
                "current_task_loss_count"
            ],
            61,
        )
        self.assertEqual(
            row["plan_switches"],
            2,
        )
        self.assertEqual(
            row[
                "unnecessary_background_sacrifice_windows"
            ],
            1,
        )
        self.assertFalse(
            row[
                "post_burst_stale_escalation"
            ]
        )
        self.assertEqual(
            row[
                "detection_delay_windows"
            ],
            2,
        )
        self.assertEqual(
            row[
                "release_delay_windows"
            ],
            1,
        )

    def test_hysteresis_is_tradeoff_not_free_improvement(self):
        raw = self.strategies[
            "RAW_SLIDING"
        ]
        hysteresis = self.strategies[
            "HYSTERESIS_2_ENTER_1_EXIT"
        ]

        self.assertGreater(
            hysteresis[
                "current_task_loss_count"
            ],
            raw[
                "current_task_loss_count"
            ],
        )
        self.assertLess(
            hysteresis[
                "unnecessary_background_sacrifice_windows"
            ],
            raw[
                "unnecessary_background_sacrifice_windows"
            ],
        )

    def test_extreme_tail_remains_visible(self):
        for strategy in (
            "STATIC_INITIAL",
            "RAW_SLIDING",
            "HYSTERESIS_2_ENTER_1_EXIT",
        ):
            self.assertEqual(
                self.strategies[strategy][
                    "p99_9_semantic_loss"
                ],
                290,
            )

    def test_claim_ceiling_is_synthetic(self):
        self.assertTrue(
            self.result["synthetic_only"]
        )
        self.assertFalse(
            self.result[
                "live_control_claim"
            ]
        )
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "SYNTHETIC_REGIME_DRIFT_CONTROL_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
