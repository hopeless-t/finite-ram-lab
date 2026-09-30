from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from finite_ram_lab.startup_stock_seed_cpuset_falsifier import (
    _causal_class,
    _parse_cpu_set,
    aggregate,
)


class StartupStockSeedCpusetFalsifierTests(unittest.TestCase):
    def test_parse_cpu_set(self) -> None:
        self.assertEqual(
            _parse_cpu_set("1,3-5,7"),
            {1, 3, 4, 5, 7},
        )

    def test_control_seed_requires_delay(self) -> None:
        self.assertEqual(
            _causal_class(
                arm="CONTROL",
                startup_q64=7,
                startup_refill=7,
                release_q64=0,
                release_refill=0,
                first_q64_touch=44,
                valid=True,
            ),
            "CONTROL_SEED",
        )

    def test_cpuset_suppressed_requires_clean_gap_and_t1(self) -> None:
        self.assertEqual(
            _causal_class(
                arm="CPUSET_PREP_ONLY",
                startup_q64=0,
                startup_refill=0,
                release_q64=0,
                release_refill=0,
                first_q64_touch=1,
                valid=True,
            ),
            "CPUSET_SUPPRESSED",
        )

    def test_cpuset_startup_leak_precedes_t(self) -> None:
        self.assertEqual(
            _causal_class(
                arm="CPUSET_PREP_ONLY",
                startup_q64=1,
                startup_refill=1,
                release_q64=0,
                release_refill=0,
                first_q64_touch=1,
                valid=True,
            ),
            "CPUSET_STARTUP_LEAK",
        )

    def test_release_gap_seed_is_not_suppression(self) -> None:
        self.assertEqual(
            _causal_class(
                arm="CPUSET_PREP_ONLY",
                startup_q64=0,
                startup_refill=0,
                release_q64=1,
                release_refill=1,
                first_q64_touch=40,
                valid=True,
            ),
            "CPUSET_RELEASE_GAP_SEED",
        )

    def test_high_t_without_seed_is_falsifier(self) -> None:
        self.assertEqual(
            _causal_class(
                arm="CPUSET_PREP_ONLY",
                startup_q64=0,
                startup_refill=0,
                release_q64=0,
                release_refill=0,
                first_q64_touch=2,
                valid=True,
            ),
            "CPUSET_HIGH_T_WITHOUT_SEED",
        )

    def test_aggregate_supports_causal_intervention(self) -> None:
        spec = {
            "experiment_id":
                "TX-STARTUP-STOCK-SEED-CPUSET-FALSIFIER-v1",
            "design": {
                "arms": ["CONTROL", "CPUSET_PREP_ONLY"],
                "total_identities": 4,
                "n_per_arm": 2,
            },
        }
        rows = [
            {
                "trial_id": "0:0",
                "arm": "CONTROL",
                "valid": True,
                "causal_classification": "CONTROL_SEED",
                "startup_stock_cpu_q64_count": 7,
                "startup_stock_cpu_refill63_count": 7,
                "release_gap_stock_cpu_q64_count": 0,
                "release_gap_stock_cpu_refill63_count": 0,
                "first_q64_touch": 44,
            },
            {
                "trial_id": "0:2",
                "arm": "CONTROL",
                "valid": True,
                "causal_classification": "CONTROL_NO_SEED",
                "startup_stock_cpu_q64_count": 0,
                "startup_stock_cpu_refill63_count": 0,
                "release_gap_stock_cpu_q64_count": 0,
                "release_gap_stock_cpu_refill63_count": 0,
                "first_q64_touch": 1,
            },
            {
                "trial_id": "0:1",
                "arm": "CPUSET_PREP_ONLY",
                "valid": True,
                "causal_classification": "CPUSET_SUPPRESSED",
                "startup_stock_cpu_q64_count": 0,
                "startup_stock_cpu_refill63_count": 0,
                "release_gap_stock_cpu_q64_count": 0,
                "release_gap_stock_cpu_refill63_count": 0,
                "first_q64_touch": 1,
            },
            {
                "trial_id": "0:3",
                "arm": "CPUSET_PREP_ONLY",
                "valid": True,
                "causal_classification": "CPUSET_SUPPRESSED",
                "startup_stock_cpu_q64_count": 0,
                "startup_stock_cpu_refill63_count": 0,
                "release_gap_stock_cpu_q64_count": 0,
                "release_gap_stock_cpu_refill63_count": 0,
                "first_q64_touch": 1,
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

        self.assertTrue(result["causal_support"])
        self.assertEqual(result["control_seed_count"], 1)
        self.assertEqual(
            result["intervention_suppressed_count"],
            2,
        )

    def test_aggregate_rejects_clean_high_t_intervention(self) -> None:
        spec = {
            "experiment_id":
                "TX-STARTUP-STOCK-SEED-CPUSET-FALSIFIER-v1",
            "design": {
                "arms": ["CONTROL", "CPUSET_PREP_ONLY"],
                "total_identities": 2,
                "n_per_arm": 1,
            },
        }
        rows = [
            {
                "trial_id": "0:0",
                "arm": "CONTROL",
                "valid": True,
                "causal_classification": "CONTROL_SEED",
                "startup_stock_cpu_q64_count": 7,
                "startup_stock_cpu_refill63_count": 7,
                "release_gap_stock_cpu_q64_count": 0,
                "release_gap_stock_cpu_refill63_count": 0,
                "first_q64_touch": 44,
            },
            {
                "trial_id": "0:1",
                "arm": "CPUSET_PREP_ONLY",
                "valid": True,
                "causal_classification":
                    "CPUSET_HIGH_T_WITHOUT_SEED",
                "startup_stock_cpu_q64_count": 0,
                "startup_stock_cpu_refill63_count": 0,
                "release_gap_stock_cpu_q64_count": 0,
                "release_gap_stock_cpu_refill63_count": 0,
                "first_q64_touch": 2,
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

        self.assertFalse(result["causal_support"])


if __name__ == "__main__":
    unittest.main()
