from __future__ import annotations

import unittest

from finite_ram_lab.semantic_oom_observable_dependence import (
    run_panel,
)


class SemanticOomObservableDependenceTests(
    unittest.TestCase
):
    @classmethod
    def setUpClass(cls):
        cls.result = run_panel()
        cls.independent = cls.result["arms"][
            "INDEPENDENT"
        ]
        cls.shared = cls.result["arms"][
            "SHARED_BAD"
        ]

    def test_analyzer_uses_no_latent_labels(self):
        self.assertFalse(
            self.result[
                "latent_labels_used_by_analyzer"
            ]
        )
        self.assertFalse(
            self.independent[
                "latent_labels_used"
            ]
        )
        self.assertFalse(
            self.shared[
                "latent_labels_used"
            ]
        )

    def test_marginal_tail_counts_match(self):
        self.assertEqual(
            set(
                self.independent[
                    "marginal_tail_count"
                ].values()
            ),
            {164},
        )
        self.assertEqual(
            set(
                self.shared[
                    "marginal_tail_count"
                ].values()
            ),
            {164},
        )

    def test_independent_trace_is_iid_compatible(self):
        self.assertEqual(
            self.independent[
                "observed_pair_cofailure_total"
            ],
            5,
        )
        self.assertEqual(
            self.independent[
                "permutation_p_upper"
            ],
            0.587,
        )
        self.assertEqual(
            self.independent[
                "classification"
            ],
            "IID_COMPATIBLE",
        )

    def test_shared_trace_shows_dependence(self):
        self.assertEqual(
            self.shared[
                "observed_pair_cofailure_total"
            ],
            492,
        )
        self.assertEqual(
            self.shared[
                "permutation_p_upper"
            ],
            0.001,
        )
        self.assertEqual(
            self.shared[
                "classification"
            ],
            "CROSS_ACTION_DEPENDENCE_EVIDENCE",
        )

    def test_shared_trace_has_deeper_cofailure(self):
        self.assertEqual(
            self.independent[
                "multi_action_tail_episodes"
            ],
            5,
        )
        self.assertEqual(
            self.shared[
                "multi_action_tail_episodes"
            ],
            164,
        )
        self.assertLess(
            self.independent[
                "mean_pairwise_phi"
            ],
            0.01,
        )
        self.assertEqual(
            self.shared[
                "mean_pairwise_phi"
            ],
            1.0,
        )

    def test_null_calibration_is_frozen(self):
        self.assertEqual(
            self.independent[
                "null_pair_cofailure_p95"
            ],
            9,
        )
        self.assertEqual(
            self.independent[
                "null_pair_cofailure_p99"
            ],
            11,
        )
        self.assertEqual(
            self.shared[
                "null_pair_cofailure_p95"
            ],
            9,
        )
        self.assertEqual(
            self.shared[
                "null_pair_cofailure_p99"
            ],
            11,
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
            "SYNTHETIC_OBSERVABLE_DEPENDENCE_INFERENCE_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
