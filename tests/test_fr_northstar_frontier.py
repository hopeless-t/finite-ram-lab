from __future__ import annotations

import unittest

from finite_ram_lab.fr_northstar_frontier import (
    run_panel,
)


class FrNorthStarFrontierTests(
    unittest.TestCase
):
    @classmethod
    def setUpClass(cls):
        cls.result = run_panel()

    def test_north_star_is_contract_gated(self):
        self.assertEqual(
            self.result[
                "north_star"
            ]["name"],
            "QUALIFIED_TASK_SURVIVAL_FRONTIER",
        )

    def test_single_atom_winner_depends_on_failure_domain(self):
        policies = self.result[
            "policies"
        ][
            "SINGLE_ATOM"
        ]

        winners = {
            tuple(
                row[
                    "actions"
                ]
            )
            for row
            in policies.values()
        }

        self.assertGreater(
            len(winners),
            3,
        )

    def test_joint_beats_single_on_geomean_memory(self):
        summary = self.result[
            "summary"
        ]

        self.assertGreater(
            summary[
                "joint_geomean_memory_gain"
            ],
            summary[
                "single_atom_geomean_memory_gain"
            ],
        )

    def test_joint_qualifies_all_at_600_mib(self):
        self.assertEqual(
            self.result[
                "summary"
            ][
                "qualified_workloads_at_600_mib"
            ]["JOINT"],
            6,
        )

    def test_baseline_and_single_do_not_qualify_at_600(self):
        row = self.result[
            "summary"
        ][
            "qualified_workloads_at_600_mib"
        ]

        self.assertEqual(
            row["BASELINE"],
            0,
        )
        self.assertEqual(
            row["SINGLE_ATOM"],
            0,
        )

    def test_claim_ceiling(self):
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "SYNTHETIC_NORTH_STAR_CONTRACT_AND_JOINT_POLICY_TOPOLOGY_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
