from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from finite_ram_lab.small_residual_refill_spectrum import (
    _marker_intervals,
    _phase_bucket,
    aggregate,
    classify_small_residual,
)


def refill(size: int, phase: str = "STARTUP") -> dict:
    return {
        "nr_pages": size,
        "phase_bucket": phase,
    }


class SmallResidualRefillSpectrumTests(unittest.TestCase):
    def test_t2_refill1_explains_delay(self) -> None:
        self.assertEqual(
            classify_small_residual(
                first_q64_touch=2,
                owner_small_refills=[refill(1)],
                owner_refill63_preboundary=[],
            ),
            "SMALL_REFILL_EXPLAINS_DELAY",
        )

    def test_t2_without_refill_remains_unexplained(self) -> None:
        self.assertEqual(
            classify_small_residual(
                first_q64_touch=2,
                owner_small_refills=[],
                owner_refill63_preboundary=[],
            ),
            "HIGH_T_WITHOUT_SMALL_REFILL",
        )

    def test_insufficient_small_refill_is_partial(self) -> None:
        self.assertEqual(
            classify_small_residual(
                first_q64_touch=5,
                owner_small_refills=[refill(1), refill(1)],
                owner_refill63_preboundary=[],
            ),
            "SMALL_REFILL_PARTIAL",
        )

    def test_classic_refill63_precedes_small_model(self) -> None:
        self.assertEqual(
            classify_small_residual(
                first_q64_touch=2,
                owner_small_refills=[refill(1)],
                owner_refill63_preboundary=[refill(63)],
            ),
            "CLASSIC_REFILL63_LEAK",
        )

    def test_t1_without_small_refill(self) -> None:
        self.assertEqual(
            classify_small_residual(
                first_q64_touch=1,
                owner_small_refills=[],
                owner_refill63_preboundary=[],
            ),
            "T1_NO_SMALL_REFILL",
        )

    def test_phase_buckets(self) -> None:
        trace = """
x-1 [000] ... 10.000000000: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=OBSERVE touch=91 PRE
x-1 [000] ... 10.100000000: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=OBSERVE touch=91 POST
x-1 [000] ... 10.200000000: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=OBSERVE touch=92 PRE
x-1 [000] ... 10.300000000: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=OBSERVE touch=92 POST
x-1 [000] ... 10.400000000: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=NORMALIZE touch=1 PRE
x-1 [000] ... 10.410000000: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=NORMALIZE touch=1 POST
x-1 [000] ... 10.500000000: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=NORMALIZE touch=2 PRE
x-1 [000] ... 10.510000000: tracing_mark_write: FRL_TX trial=0:0 epoch=0 phase=NORMALIZE touch=2 POST
"""
        intervals = _marker_intervals(trace, trial_id="0:0")

        self.assertEqual(
            _phase_bucket(
                timestamp_ns=10_050_000_000,
                intervals=intervals,
                first_q64_touch=2,
            ),
            "STARTUP",
        )
        self.assertEqual(
            _phase_bucket(
                timestamp_ns=10_250_000_000,
                intervals=intervals,
                first_q64_touch=2,
            ),
            "RELEASE_GAP",
        )
        self.assertEqual(
            _phase_bucket(
                timestamp_ns=10_350_000_000,
                intervals=intervals,
                first_q64_touch=2,
            ),
            "TAIL_GAP_AFTER_RELEASE",
        )
        self.assertEqual(
            _phase_bucket(
                timestamp_ns=10_450_000_000,
                intervals=intervals,
                first_q64_touch=2,
            ),
            "MEASURED_PREBOUNDARY_TOUCHES",
        )

    def test_aggregate_discovery_separate_from_panel_coverage(self) -> None:
        spec = {
            "experiment_id":
                "TX-SMALL-RESIDUAL-REFILL-SPECTRUM-v1",
            "design": {"total_identities": 3},
        }
        rows = [
            {
                "trial_id": "0:0",
                "valid": True,
                "classification":
                    "SMALL_REFILL_EXPLAINS_DELAY",
                "first_q64_touch": 2,
                "owner_small_refill_sizes": [1],
                "owner_small_refills_preboundary": [
                    refill(1, "STARTUP")
                ],
            },
            {
                "trial_id": "0:1",
                "valid": True,
                "classification": "T1_NO_SMALL_REFILL",
                "first_q64_touch": 1,
                "owner_small_refill_sizes": [],
                "owner_small_refills_preboundary": [],
            },
            {
                "trial_id": "0:2",
                "valid": False,
                "classification": "INVALID_OBSERVER",
                "first_q64_touch": 1,
                "owner_small_refill_sizes": [],
                "owner_small_refills_preboundary": [],
            },
        ]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for i, row in enumerate(rows):
                (root / f"trial-{i}.json").write_text(
                    json.dumps(row),
                    encoding="utf-8",
                )
            result = aggregate(spec, root)

        self.assertTrue(result["discovery_pass"])
        self.assertFalse(result["panel_coverage_pass"])
        self.assertEqual(result["small_refill_promoted_count"], 1)
        self.assertEqual(
            result["owner_small_refill_size_histogram"],
            {1: 1},
        )


if __name__ == "__main__":
    unittest.main()
