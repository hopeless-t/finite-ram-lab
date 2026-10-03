from __future__ import annotations

import json
import unittest

from finite_ram_lab.fr_fp_017_cold_latency_trace import (
    BLOCKS,
    run_panel,
)


class ColdLatencyTraceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_panel()
        print(
            "FR_FP_017_RESULT="
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

    def test_trace_length(self) -> None:
        self.assertEqual(
            self.result[
                "warm"
            ][
                "count"
            ],
            BLOCKS,
        )
        self.assertEqual(
            self.result[
                "cold"
            ][
                "count"
            ],
            BLOCKS,
        )

    def test_cold_tail_is_recorded(self) -> None:
        cold = self.result[
            "cold"
        ]
        self.assertLessEqual(
            cold["p50_ms"],
            cold["p95_ms"],
        )
        self.assertLessEqual(
            cold["p95_ms"],
            cold["max_ms"],
        )

    def test_claim_ceiling_is_pilot(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "HOSTED_8MIB_COLD_RESTORE_TEMPORAL_TRACE_PILOT_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
