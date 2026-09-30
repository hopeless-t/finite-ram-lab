from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from finite_ram_lab.small_residual_refill1_provenance import (
    aggregate,
    classify_identity,
    provenance_class,
)


class Refill1ProvenanceTests(unittest.TestCase):
    def test_objcg_class(self) -> None:
        self.assertEqual(
            provenance_class(
                [
                    "refill_stock",
                    "obj_cgroup_uncharge_pages",
                    "__memcg_slab_free_hook",
                ]
            ),
            "OBJCG_UNCHARGE_REFILL1",
        )

    def test_socket_class(self) -> None:
        self.assertEqual(
            provenance_class(
                [
                    "refill_stock",
                    "mem_cgroup_sk_uncharge",
                    "__sk_mem_reduce_allocated",
                ]
            ),
            "SOCKET_UNCHARGE_REFILL1",
        )

    def test_try_charge_class(self) -> None:
        self.assertEqual(
            provenance_class(
                [
                    "refill_stock",
                    "try_charge_memcg",
                    "charge_memcg",
                ]
            ),
            "TRY_CHARGE_EXCESS_REFILL1",
        )

    def test_unknown_stack_is_retained(self) -> None:
        self.assertEqual(
            provenance_class(
                ["refill_stock", "mystery_caller"]
            ),
            "OTHER_REFILL1_CALLER",
        )

    def test_t2_one_refill1_captures_provenance(self) -> None:
        classification, provenance = classify_identity(
            first_q64_touch=2,
            owner_refill1_rows=[
                {
                    "nr_pages": 1,
                    "frames": [
                        "refill_stock",
                        "obj_cgroup_uncharge_pages",
                    ],
                }
            ],
        )
        self.assertEqual(
            classification,
            "PROVENANCE_CAPTURED",
        )
        self.assertEqual(
            provenance,
            "OBJCG_UNCHARGE_REFILL1",
        )

    def test_stack_missing_does_not_capture(self) -> None:
        classification, provenance = classify_identity(
            first_q64_touch=2,
            owner_refill1_rows=[
                {"nr_pages": 1, "frames": []}
            ],
        )
        self.assertEqual(
            classification,
            "OWNER_REFILL1_STACK_MISSING",
        )
        self.assertIsNone(provenance)

    def test_residual_mismatch_does_not_capture(self) -> None:
        classification, provenance = classify_identity(
            first_q64_touch=3,
            owner_refill1_rows=[
                {
                    "nr_pages": 1,
                    "frames": [
                        "refill_stock",
                        "obj_cgroup_uncharge_pages",
                    ],
                }
            ],
        )
        self.assertEqual(
            classification,
            "OWNER_REFILL1_RESIDUAL_MISMATCH",
        )
        self.assertIsNone(provenance)

    def test_aggregate_resolved_only_for_named_source_class(self) -> None:
        spec = {
            "experiment_id":
                "TX-SMALL-RESIDUAL-REFILL1-PROVENANCE-v1"
        }
        rows = [
            {
                "trial_id": "0:0",
                "valid": True,
                "classification": "PROVENANCE_CAPTURED",
                "provenance_class":
                    "OBJCG_UNCHARGE_REFILL1",
                "first_q64_touch": 2,
                "startup_coverage_ok": True,
                "measured_coverage_ok": True,
            },
            {
                "trial_id": "0:1",
                "valid": True,
                "classification": "PROVENANCE_CAPTURED",
                "provenance_class":
                    "OTHER_REFILL1_CALLER",
                "first_q64_touch": 2,
                "startup_coverage_ok": True,
                "measured_coverage_ok": True,
            },
            {
                "trial_id": "0:2",
                "valid": True,
                "classification": "T1_NO_OWNER_REFILL1",
                "provenance_class": None,
                "first_q64_touch": 1,
                "startup_coverage_ok": True,
                "measured_coverage_ok": True,
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

        self.assertEqual(result["captured_count"], 2)
        self.assertEqual(result["resolved_count"], 1)
        self.assertTrue(result["provenance_resolved"])
        self.assertEqual(
            result["resolved_trials"],
            ["0:0"],
        )


if __name__ == "__main__":
    unittest.main()
