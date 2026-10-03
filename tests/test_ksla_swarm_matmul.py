from __future__ import annotations

import unittest

from finite_ram_lab.ksla_swarm_matmul import (
    run_panel,
)


class KslaSwarmMatmulTests(
    unittest.TestCase
):
    @classmethod
    def setUpClass(cls):
        cls.result = run_panel()
        cls.micro = cls.result[
            "micro_exact_fixture"
        ]
        cls.scale = cls.result[
            "scale_model"
        ]

    def test_unverified_swarm_is_wrong(self):
        self.assertFalse(
            self.micro[
                "unverified_matches_exact"
            ]
        )
        self.assertFalse(
            self.micro[
                "initial_global_verifier_pass"
            ]
        )

    def test_verifier_localizes_all_injected_faults(self):
        self.assertEqual(
            self.micro[
                "fault_task_count"
            ],
            4,
        )
        self.assertEqual(
            self.micro[
                "localized_fault_count"
            ],
            4,
        )

    def test_selective_recompute_restores_exact_result(self):
        self.assertTrue(
            self.micro[
                "repaired_matches_exact"
            ]
        )
        self.assertTrue(
            self.micro[
                "final_global_verifier_pass"
            ]
        )
        self.assertEqual(
            self.micro[
                "recomputed_task_count"
            ],
            4,
        )

    def test_one_weak_task_is_tiny(self):
        self.assertEqual(
            self.scale[
                "single_task_multiply_fraction"
            ],
            1.0 / 4096.0,
        )
        self.assertEqual(
            self.scale[
                "single_task_working_set_fraction"
            ],
            1.0 / 256.0,
        )

    def test_verification_and_repair_overhead_is_small_in_scale_model(self):
        self.assertGreater(
            self.scale[
                "verified_swarm_work_ratio"
            ],
            1.03,
        )
        self.assertLess(
            self.scale[
                "verified_swarm_work_ratio"
            ],
            1.04,
        )

    def test_communication_tax_is_explicit(self):
        self.assertEqual(
            self.scale[
                "raw_task_return_amplification_vs_output"
            ],
            16.0,
        )
        self.assertTrue(
            self.scale[
                "reducer_required"
            ]
        )

    def test_claim_ceiling_is_synthetic(self):
        self.assertTrue(
            self.result["synthetic_only"]
        )
        self.assertFalse(
            self.result[
                "live_distributed_execution_claim"
            ]
        )
        self.assertEqual(
            self.result["claim_ceiling"],
            "SYNTHETIC_VERIFIED_SWARM_MATMUL_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
