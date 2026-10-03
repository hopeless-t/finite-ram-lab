from __future__ import annotations

import json
import unittest

from finite_ram_lab.fr_fp_019_restore_observability import (
    BLOCKS,
    PRE_FEATURES,
    run_panel,
)


class RestoreObservabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()
        print(
            "FR_FP_019_RESULT="
            + json.dumps(
                cls.result,
                sort_keys=True,
            ),
            flush=True,
        )

    def test_panel_passes(self) -> None:
        self.assertEqual(
            self.result[
                "status"
            ],
            "PASS",
        )
        self.assertTrue(
            all(
                self.result[
                    "checks"
                ].values()
            )
        )

    def test_trace_count(self) -> None:
        warm = [
            row
            for row in self.result[
                "rows"
            ]
            if row[
                "arm"
            ]
            == "WARM_PAGECACHE"
        ]
        cold = [
            row
            for row in self.result[
                "rows"
            ]
            if row[
                "arm"
            ]
            == "COLD_DONTNEED"
        ]

        self.assertEqual(
            len(warm),
            BLOCKS,
        )
        self.assertEqual(
            len(cold),
            BLOCKS,
        )

    def test_pre_features_are_predeclared(self) -> None:
        self.assertEqual(
            set(
                self.result[
                    "pre_restore_predictive_analysis"
                ][
                    "features"
                ]
            ),
            set(
                PRE_FEATURES
            ),
        )

    def test_claim_ceiling_is_pilot(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "HOSTED_RESTORE_OBSERVABILITY_PILOT_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
