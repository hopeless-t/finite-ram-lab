from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from finite_ram_lab.small_residual_refill1_capture import (
    aggregate,
    classify_capture,
)


def row(size: int) -> dict:
    return {"nr_pages": size}


class SmallResidualRefill1CaptureTests(unittest.TestCase):
    def test_t2_owner_refill1_establishes_mechanism(self) -> None:
        self.assertEqual(
            classify_capture(
                first_q64_touch=2,
                owner_refill1_rows=[row(1)],
                owner_refill63_premeasure_rows=[],
            ),
            "SMALL_RESIDUAL_REFILL_ESTABLISHMENT",
        )

    def test_classic_refill63_blocks_pure_small_promotion(self) -> None:
        self.assertEqual(
            classify_capture(
                first_q64_touch=2,
                owner_refill1_rows=[row(1)],
                owner_refill63_premeasure_rows=[row(63)],
            ),
            "CLASSIC_REFILL63_PREMEASURE",
        )

    def test_t2_without_refill1_remains_unexplained(self) -> None:
        self.assertEqual(
            classify_capture(
                first_q64_touch=2,
                owner_refill1_rows=[],
                owner_refill63_premeasure_rows=[],
            ),
            "DELAY_WITHOUT_OWNER_REFILL1",
        )

    def test_partial_refill_does_not_promote(self) -> None:
        self.assertEqual(
            classify_capture(
                first_q64_touch=3,
                owner_refill1_rows=[row(1)],
                owner_refill63_premeasure_rows=[],
            ),
            "OWNER_REFILL1_PARTIAL",
        )

    def test_t1_no_refill(self) -> None:
        self.assertEqual(
            classify_capture(
                first_q64_touch=1,
                owner_refill1_rows=[],
                owner_refill63_premeasure_rows=[],
            ),
            "T1_NO_OWNER_REFILL1",
        )

    def test_aggregate_establishment_independent_of_other_invalids(self) -> None:
        spec = {
            "experiment_id":
                "TX-SMALL-RESIDUAL-REFILL1-CAPTURE-v1"
        }
        rows = [
            {
                "trial_id": "0:0",
                "valid": True,
                "classification":
                    "SMALL_RESIDUAL_REFILL_ESTABLISHMENT",
                "first_q64_touch": 2,
                "premeasure_coverage_ok": True,
                "measured_coverage_ok": True,
            },
            {
                "trial_id": "0:1",
                "valid": True,
                "classification": "T1_NO_OWNER_REFILL1",
                "first_q64_touch": 1,
                "premeasure_coverage_ok": True,
                "measured_coverage_ok": True,
            },
            {
                "trial_id": "0:2",
                "valid": False,
                "classification": "INVALID_OBSERVER",
                "first_q64_touch": 1,
                "premeasure_coverage_ok": False,
                "measured_coverage_ok": True,
            },
        ]

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for i, item in enumerate(rows):
                (root / f"trial-{i}.json").write_text(
                    json.dumps(item),
                    encoding="utf-8",
                )
            result = aggregate(spec, root)

        self.assertTrue(result["establishment_pass"])
        self.assertEqual(result["promoted_count"], 1)
        self.assertEqual(
            result["premeasure_probe_miss_trials"],
            ["0:2"],
        )

    def test_aggregate_no_capture_does_not_pass(self) -> None:
        spec = {
            "experiment_id":
                "TX-SMALL-RESIDUAL-REFILL1-CAPTURE-v1"
        }
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "trial-0.json").write_text(
                json.dumps(
                    {
                        "trial_id": "0:0",
                        "valid": True,
                        "classification":
                            "T1_NO_OWNER_REFILL1",
                        "first_q64_touch": 1,
                        "premeasure_coverage_ok": True,
                        "measured_coverage_ok": True,
                    }
                ),
                encoding="utf-8",
            )
            result = aggregate(spec, root)

        self.assertFalse(result["establishment_pass"])
        self.assertEqual(result["promoted_count"], 0)


if __name__ == "__main__":
    unittest.main()
