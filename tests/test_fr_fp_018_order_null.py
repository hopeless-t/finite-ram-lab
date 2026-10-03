from __future__ import annotations

import json
import unittest

from finite_ram_lab.fr_fp_018_order_null import (
    SHUFFLES,
    run_panel,
)


class OrderNullTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()
        print(
            "FR_FP_018_RESULT="
            + json.dumps(
                cls.result,
                sort_keys=True,
            ),
            flush=True,
        )

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

    def test_monte_carlo_size(self) -> None:
        self.assertEqual(
            SHUFFLES,
            20_000,
        )

    def test_pvalues_are_probabilities(self) -> None:
        for arm in (
            "warm",
            "cold",
        ):
            for value in self.result[
                arm
            ][
                "pvalues"
            ].values():
                self.assertGreater(
                    value,
                    0.0,
                )
                self.assertLessEqual(
                    value,
                    1.0,
                )

    def test_claim_ceiling_is_single_trace(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "ORDER_STRUCTURE_TEST_ON_ONE_FROZEN_48_SAMPLE_HOSTED_TRACE_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
