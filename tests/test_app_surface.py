from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from finite_ram_lab.app_surface import (
    NoEligibleConfiguration,
    load_policy,
    select_configuration,
    write_receipt,
)


POLICY_PATH = Path("policies/repaired-governor-v2.1.json")


class AppSurfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = load_policy(POLICY_PATH)

    def test_exact_breakpoints_select_expected_q(self):
        cases = (
            (50_696_192, 2),
            (58_941_440, 4),
            (71_512_064, 7),
        )
        for budget, expected_q in cases:
            with self.subTest(budget=budget):
                receipt = select_configuration(
                    self.policy,
                    peak_budget_bytes=budget,
                    minimum_rank_coverage=0.95,
                )
                self.assertEqual(receipt["decision"]["selected_q"], expected_q)
                self.assertEqual(receipt["decision"]["sample_count"], 27)
                self.assertAlmostEqual(
                    receipt["decision"][
                        "rank_max_one_step_predictive_coverage_floor"
                    ],
                    27 / 28,
                )

    def test_old_q7_boundary_falls_back_to_q4(self):
        receipt = select_configuration(
            self.policy,
            peak_budget_bytes=71_507_968,
            minimum_rank_coverage=0.95,
        )
        self.assertEqual(receipt["decision"]["selected_q"], 4)

    def test_below_q2_and_99_percent_fail_closed(self):
        with self.assertRaises(NoEligibleConfiguration):
            select_configuration(
                self.policy,
                peak_budget_bytes=50_696_191,
                minimum_rank_coverage=0.95,
            )
        with self.assertRaises(NoEligibleConfiguration):
            select_configuration(
                self.policy,
                peak_budget_bytes=100_000_000,
                minimum_rank_coverage=0.99,
            )

    def test_receipt_contains_policy_provenance_and_is_serializable(self):
        receipt = select_configuration(
            self.policy,
            peak_budget_bytes=60_000_000,
            minimum_rank_coverage=0.95,
        )
        self.assertEqual(receipt["status"], "SELECTED")
        self.assertEqual(receipt["policy_version"], "v2.1")
        self.assertEqual(receipt["implementation"], "TILED_WHERE")
        self.assertEqual(
            receipt["evidence"]["source_governor_sha256"],
            "27a1f6c68d64cce30d808748e7befa0b97f99610ab56bcaaf199166fa0cbc859",
        )
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "receipt.json"
            write_receipt(receipt, out)
            loaded = json.loads(out.read_text())
            self.assertEqual(loaded["decision"]["selected_q"], 4)


if __name__ == "__main__":
    unittest.main()
