from __future__ import annotations

import unittest

from finite_ram_lab.semantic_oom_latent_detector import (
    run_panel,
)


class SemanticOomLatentDetectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run_panel()
        cls.psi = cls.result["detectors"][
            "PSI_ONLY"
        ]
        cls.multi = cls.result["detectors"][
            "MULTI_SIGNAL"
        ]

    def test_frozen_latent_counts(self):
        self.assertEqual(
            self.result["train_bad_count"],
            308,
        )
        self.assertEqual(
            self.result["test_bad_count"],
            305,
        )

    def test_train_thresholds_hit_recall_target(self):
        self.assertGreaterEqual(
            self.psi["train"]["recall"],
            0.95,
        )
        self.assertGreaterEqual(
            self.multi["train"]["recall"],
            0.95,
        )

    def test_heldout_recall_is_matched(self):
        self.assertEqual(
            self.psi["test"]["true_positive"],
            287,
        )
        self.assertEqual(
            self.multi["test"]["true_positive"],
            287,
        )
        self.assertEqual(
            self.psi["test"]["false_negative"],
            18,
        )
        self.assertEqual(
            self.multi["test"]["false_negative"],
            18,
        )

    def test_multi_signal_reduces_false_escalation(self):
        self.assertEqual(
            self.psi["test"]["false_positive"],
            2447,
        )
        self.assertEqual(
            self.multi["test"]["false_positive"],
            152,
        )
        self.assertGreater(
            self.psi["test"][
                "false_positive_rate"
            ],
            0.60,
        )
        self.assertLess(
            self.multi["test"][
                "false_positive_rate"
            ],
            0.05,
        )

    def test_multi_signal_reduces_synthetic_semantic_cost(self):
        self.assertEqual(
            self.psi["test"][
                "false_escalation_semantic_delta"
            ],
            12235,
        )
        self.assertEqual(
            self.multi["test"][
                "false_escalation_semantic_delta"
            ],
            760,
        )

    def test_failure_biopsies_retained(self):
        for detector in (
            self.psi,
            self.multi,
        ):
            self.assertIsNotNone(
                detector["test"][
                    "first_false_positive"
                ]
            )
            self.assertIsNotNone(
                detector["test"][
                    "first_false_negative"
                ]
            )

    def test_claim_ceiling_is_synthetic(self):
        self.assertTrue(
            self.result["synthetic_only"]
        )
        self.assertFalse(
            self.result["live_control_claim"]
        )
        self.assertEqual(
            self.result["claim_ceiling"],
            "SYNTHETIC_LATENT_PRESSURE_DETECTOR_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
