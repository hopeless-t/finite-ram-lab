from __future__ import annotations

import unittest

from finite_ram_lab.fast_reinstall_loop_v2 import ARMS, schedule, summarize


class FastReinstallLoopV2Tests(unittest.TestCase):
    def test_schedule_complete(self) -> None:
        rows = schedule(25, 9)
        self.assertEqual(len(rows), 50)
        for block in range(25):
            self.assertEqual(
                {arm for b, _o, arm in rows if b == block},
                set(ARMS),
            )

    def test_summary_preserves_parity_and_zero_materialization(self) -> None:
        trials = []
        for arm, ns, materialized in [
            ("wheel_extract", 20_000_000, 1000),
            ("wheel_zipimport", 500_000, 0),
        ]:
            for block in range(2):
                trials.append(
                    {
                        "arm": arm,
                        "reconstruct": {
                            "elapsed_ns": ns,
                            "materialized_runtime_bytes": materialized,
                        },
                        "workload": {
                            "elapsed_ns": 10_000_000,
                            "payload": {"semantic_sha256": "same", "ru_maxrss_kib": 123},
                        },
                        "discard": {
                            "elapsed_ns": 1000,
                            "bytes_before": materialized,
                            "bytes_after": 0,
                            "target_exists_after": False,
                        },
                    }
                )
        result = summarize(
            trials,
            {"canonical_residue_delta_bytes": 0},
        )
        self.assertTrue(result["semantic_parity"])
        self.assertEqual(
            result["arms"]["wheel_zipimport"]["median_materialized_runtime_bytes"],
            0.0,
        )
        self.assertAlmostEqual(
            result["arms"]["wheel_zipimport"]["speedup_vs_wheel_extract"],
            40.0,
        )


if __name__ == "__main__":
    unittest.main()
