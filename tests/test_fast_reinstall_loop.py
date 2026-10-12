from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path

from finite_ram_lab.fast_reinstall_loop import ARMS, schedule, summarize, tree_bytes


class FastReinstallLoopTests(unittest.TestCase):
    def test_schedule_is_complete_and_deterministic(self) -> None:
        a = schedule(5, 123)
        b = schedule(5, 123)
        self.assertEqual(a, b)
        self.assertEqual(len(a), 5 * len(ARMS))
        for block in range(5):
            self.assertEqual(
                {arm for bno, _order, arm in a if bno == block},
                set(ARMS),
            )

    def test_tree_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "a").write_bytes(b"abc")
            (root / "d").mkdir()
            (root / "d" / "b").write_bytes(b"12345")
            self.assertEqual(tree_bytes(root), 8)

    def test_summary_detects_semantic_parity_and_speedup(self) -> None:
        trials = []
        elapsed = {"pip_source": 300_000_000, "pip_wheel": 120_000_000, "wheel_extract": 10_000_000}
        for block in range(2):
            for arm in ARMS:
                trials.append(
                    {
                        "arm": arm,
                        "reconstruct": {
                            "elapsed_ns": elapsed[arm],
                            "peak_rss_kib": 1000,
                            "runtime_bytes": 1234,
                        },
                        "workload": {
                            "elapsed_ns": 20_000_000,
                            "payload": {"semantic_sha256": "same", "ru_maxrss_kib": 2000},
                        },
                        "discard": {
                            "elapsed_ns": 2_000_000,
                            "bytes_after": 0,
                            "target_exists_after": False,
                        },
                    }
                )
        result = summarize(trials)
        self.assertTrue(result["semantic_parity"])
        self.assertTrue(result["all_discarded_cleanly"])
        self.assertEqual(result["trial_count"], 6)
        self.assertAlmostEqual(
            result["arms"]["wheel_extract"]["reconstruct_speedup_vs_pip_source"],
            30.0,
        )


if __name__ == "__main__":
    unittest.main()
