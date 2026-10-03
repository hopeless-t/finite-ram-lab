from __future__ import annotations

import json
import unittest

from finite_ram_lab.fr_fp_017_cold_restore_tail import (
    BLOCKS,
    DEADLINES_MS,
    run_panel,
)


class ColdRestoreTailTests(unittest.TestCase):
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

    def test_thirty_two_cold_observations(self) -> None:
        self.assertEqual(
            self.result[
                "summaries"
            ][
                "COLD_DONTNEED"
            ][
                "count"
            ],
            BLOCKS,
        )

    def test_deadline_curve_is_complete(self) -> None:
        curve = self.result[
            "summaries"
        ][
            "COLD_DONTNEED"
        ][
            "deadlines_ms"
        ]

        self.assertEqual(
            set(
                curve
            ),
            {
                str(
                    value
                )
                for value
                in DEADLINES_MS
            },
        )

    def test_cold_tail_exceeds_warm_tail(self) -> None:
        cold = self.result[
            "summaries"
        ][
            "COLD_DONTNEED"
        ]
        warm = self.result[
            "summaries"
        ][
            "WARM_PAGECACHE"
        ]

        self.assertGreater(
            cold[
                "p50_ns"
            ],
            warm[
                "p50_ns"
            ],
        )
        self.assertGreater(
            cold[
                "p95_ns"
            ],
            warm[
                "p95_ns"
            ],
        )

    def test_claim_ceiling_is_trace_only(self) -> None:
        self.assertEqual(
            self.result[
                "claim_ceiling"
            ],
            "HOSTED_LINUX_FIXED_8MIB_RESTORE_TAIL_TRACE_ONLY",
        )


if __name__ == "__main__":
    unittest.main()
