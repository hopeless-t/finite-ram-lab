from __future__ import annotations

import unittest

from finite_ram_lab.ksla_world_claim_gate import (
    run_panel,
)


class KslaWorldClaimGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run_panel()

    def test_ksla_remains_exact(self):
        self.assertTrue(
            self.result[
                "world_claim_gate"
            ][
                "exact_solution_all_sizes"
            ]
        )

    def test_standard_world_speed_claim_is_rejected(self):
        self.assertFalse(
            self.result[
                "world_claim_gate"
            ][
                "standard_sparse_spd_world_best"
            ]
        )
        self.assertEqual(
            self.result[
                "world_claim_gate"
            ][
                "standard_sparse_spd_verdict"
            ],
            "NOT_SUPPORTED",
        )

    def test_local_touch_contract(self):
        self.assertTrue(
            self.result[
                "world_claim_gate"
            ][
                "zero_intelligence_local_touch_contract"
            ]
        )

    def test_all_sizes_present(self):
        self.assertEqual(
            [
                row["n"]
                for row in self.result[
                    "sizes"
                ]
            ],
            [
                64,
                256,
                1024,
                4096,
            ],
        )


if __name__ == "__main__":
    unittest.main()
