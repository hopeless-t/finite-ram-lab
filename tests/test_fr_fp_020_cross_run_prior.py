from __future__ import annotations

import json
import unittest

from finite_ram_lab.fr_fp_020_cross_run_prior import (
    BOOTSTRAPS,
    run_panel,
)


class CrossRunRestorePriorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()
        print(
            "FR_FP_020_RESULT="
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

    def test_zero_new_physical_runs(self) -> None:
        self.assertEqual(
            self.result[
                "source"
            ][
                "new_physical_runs"
            ],
            0,
        )
        self.assertEqual(
            self.result[
                "source"
            ][
                "reused_ci_runs"
            ],
            15,
        )

    def test_cold_cross_run_nonstationarity_is_material(self) -> None:
        self.assertGreater(
            self.result[
                "cold"
            ][
                "max_over_min"
            ],
            30.0,
        )
        self.assertGreater(
            self.result[
                "cold"
            ][
                "log_stdev"
            ],
            self.result[
                "warm"
            ][
                "log_stdev"
            ],
        )

    def test_bootstrap_is_frozen(self) -> None:
        self.assertEqual(
            BOOTSTRAPS,
            20_000,
        )

    def test_claim_ceiling_is_narrow(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "FIFTEEN_REUSED_GITHUB_HOSTED_CI_RUNS_FOR_8MIB_RESTORE_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
