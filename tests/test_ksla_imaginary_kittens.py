from __future__ import annotations

import unittest

from finite_ram_lab.ksla_imaginary_kittens import (
    run_panel,
)


class KslaImaginaryKittenTests(
    unittest.TestCase
):
    @classmethod
    def setUpClass(cls):
        cls.result = run_panel()
        cls.filtered = cls.result[
            "filtered_swarms"
        ]

    def test_every_filtered_swarm_reaches_exact_solution(self):
        for row in self.filtered.values():
            self.assertTrue(
                row["exact_solution"]
            )
            self.assertEqual(
                row["final_residual_norm"],
                0,
            )

    def test_batch8_reduces_depth_and_total_proposals_vs_single(self):
        single = self.filtered[
            "BATCH_1"
        ]
        swarm = self.filtered[
            "BATCH_8"
        ]

        self.assertLess(
            swarm["rounds"],
            single["rounds"],
        )
        self.assertLess(
            swarm["proposals"],
            single["proposals"],
        )

    def test_unfiltered_chaos_does_not_solve_system(self):
        chaos = self.result[
            "unfiltered_chaos"
        ]

        self.assertFalse(
            chaos["exact_solution"]
        )
        self.assertGreater(
            chaos["final_residual_norm"],
            chaos["start_residual_norm"],
        )

    def test_exhaustive_scan_uses_many_more_candidate_evaluations_than_batch8(self):
        exhaustive = self.result[
            "exhaustive_validator"
        ]
        batch8 = self.filtered[
            "BATCH_8"
        ]

        self.assertEqual(
            exhaustive["rounds"],
            124,
        )
        self.assertEqual(
            exhaustive["proposals"],
            47_616,
        )
        self.assertLess(
            batch8["proposals"],
            exhaustive["proposals"],
        )

    def test_imaginary_kitten_has_no_intelligence_contract(self):
        self.assertEqual(
            self.result[
                "kitten_definition"
            ],
            "STATELESS_RANDOM_ACTION_PROPOSAL_NOT_A_PROCESS_AGENT_OR_LLM",
        )

        scale = self.result[
            "scale_model"
        ]

        self.assertFalse(
            scale[
                "proposal_knows_gradient"
            ]
        )
        self.assertFalse(
            scale[
                "proposal_knows_objective"
            ]
        )
        self.assertFalse(
            scale[
                "physical_worker_required"
            ]
        )
        self.assertFalse(
            scale[
                "llm_required"
            ]
        )

    def test_sparse_validator_touch_is_local(self):
        scale = self.result[
            "scale_model"
        ]

        self.assertEqual(
            scale[
                "max_residual_entries_touched_per_proposal"
            ],
            3,
        )
        self.assertEqual(
            scale[
                "proposal_touch_fraction"
            ],
            3 / 1_000_000,
        )

    def test_claim_ceiling_is_synthetic(self):
        self.assertTrue(
            self.result["synthetic_only"]
        )
        self.assertFalse(
            self.result[
                "live_parallel_runtime_claim"
            ]
        )
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "SYNTHETIC_IMAGINARY_KITTEN_RANDOM_ACTION_SOLVER_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
