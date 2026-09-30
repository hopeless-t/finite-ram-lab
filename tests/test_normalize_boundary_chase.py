from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from finite_ram_lab.normalize_boundary_chase import (
    aggregate,
    classify_boundary,
    _target_q64_rows_from_text,
)


class NormalizeBoundaryChaseTests(unittest.TestCase):
    def test_classify_within_bound(self) -> None:
        self.assertEqual(
            classify_boundary(
                first_q64_touch=64,
                invalidation_reason=None,
            ),
            "WITHIN_BOUND",
        )

    def test_classify_max_stock_boundary(self) -> None:
        self.assertEqual(
            classify_boundary(
                first_q64_touch=65,
                invalidation_reason=None,
            ),
            "MAX_STOCK_BOUNDARY",
        )

    def test_classify_violation_candidate(self) -> None:
        self.assertEqual(
            classify_boundary(
                first_q64_touch=66,
                invalidation_reason=None,
            ),
            "STOCK_BOUND_VIOLATION_CANDIDATE",
        )

    def test_invalidation_precedes_boundary_class(self) -> None:
        self.assertEqual(
            classify_boundary(
                first_q64_touch=65,
                invalidation_reason="PTE_GROWTH",
            ),
            "PTE_GROWTH",
        )

    def test_pid_attribution_ignores_background_q64(self) -> None:
        trace = """
background-111 [003] ... 10.000000000: frl_pc_try64: counter=0xaaa nr_pages=64 comm="background"
frltx405-222 [007] ... 10.000000010: frl_pc_try64: counter=0xbbb nr_pages=64 comm="frltx405"
"""
        rows = _target_q64_rows_from_text(
            trace,
            target_pid=222,
            stock_cpu=7,
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["counter"], "0xbbb")
        self.assertEqual(rows[0]["pid"], 222)
        self.assertEqual(rows[0]["cpu"], 7)

    def test_aggregate_accepts_32_clean_boundaries_with_zero_miss(self) -> None:
        spec = {
            "experiment_id": "TX-NORMALIZE-BOUNDARY-CHASE-v1",
            "total_identities": 32,
        }
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for block in range(4):
                b = root / f"block-{block}"
                b.mkdir()
                (b / "kprobe-profile.txt").write_text(
                    "frl_pc_try64 100 0\n",
                    encoding="utf-8",
                )
                for identity in range(8):
                    t = 65 if (block == 0 and identity == 0) else 64
                    row = {
                        "classification": (
                            "MAX_STOCK_BOUNDARY"
                            if t == 65
                            else "WITHIN_BOUND"
                        ),
                        "first_q64_touch": t,
                    }
                    (b / f"trial-{block}-{identity}.json").write_text(
                        json.dumps(row),
                        encoding="utf-8",
                    )
            result = aggregate(spec, root)

        self.assertEqual(result["trial_count"], 32)
        self.assertEqual(result["valid_trial_count"], 32)
        self.assertTrue(result["coverage_pass"])
        self.assertTrue(result["stock_bound_pass"])
        self.assertTrue(result["max_stock_boundary_observed"])
        self.assertEqual(result["max_observed_first_q64_touch"], 65)

    def test_probe_miss_blocks_stock_bound_pass(self) -> None:
        spec = {
            "experiment_id": "TX-NORMALIZE-BOUNDARY-CHASE-v1",
            "total_identities": 1,
        }
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "kprobe-profile.txt").write_text(
                "frl_pc_try64 10 1\n",
                encoding="utf-8",
            )
            (root / "trial-0-0.json").write_text(
                json.dumps(
                    {
                        "classification": "WITHIN_BOUND",
                        "first_q64_touch": 64,
                    }
                ),
                encoding="utf-8",
            )
            result = aggregate(spec, root)

        self.assertFalse(result["coverage_pass"])
        self.assertFalse(result["stock_bound_pass"])


if __name__ == "__main__":
    unittest.main()
