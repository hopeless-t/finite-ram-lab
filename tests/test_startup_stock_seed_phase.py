from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from finite_ram_lab.startup_stock_seed_phase import (
    aggregate,
    classify_startup_seed,
    prepare_startup_probes,
    bind_measured_q64_probe,
    close_probes,
)


class StartupStockSeedPhaseTests(unittest.TestCase):
    def test_classifies_pre_exec_seed(self) -> None:
        result = classify_startup_seed(
            q64_rows=[
                {
                    "on_stock_cpu": True,
                    "timestamp_ns": 100,
                }
            ],
            refill_rows=[
                {
                    "on_stock_cpu": True,
                    "timestamp_ns": 110,
                }
            ],
            exec_ns=200,
        )
        self.assertEqual(result, "STARTUP_STOCK_SEED_PRE_EXEC")

    def test_classifies_post_exec_seed(self) -> None:
        result = classify_startup_seed(
            q64_rows=[
                {
                    "on_stock_cpu": True,
                    "timestamp_ns": 300,
                }
            ],
            refill_rows=[
                {
                    "on_stock_cpu": True,
                    "timestamp_ns": 310,
                }
            ],
            exec_ns=200,
        )
        self.assertEqual(result, "STARTUP_STOCK_SEED_POST_EXEC")

    def test_no_stock_cpu_q64_is_no_seed(self) -> None:
        result = classify_startup_seed(
            q64_rows=[
                {
                    "on_stock_cpu": False,
                    "timestamp_ns": 100,
                }
            ],
            refill_rows=[],
            exec_ns=200,
        )
        self.assertEqual(result, "NO_STARTUP_SEED")

    def test_q64_without_refill_fails_seed_promotion(self) -> None:
        result = classify_startup_seed(
            q64_rows=[
                {
                    "on_stock_cpu": True,
                    "timestamp_ns": 100,
                }
            ],
            refill_rows=[],
            exec_ns=200,
        )
        self.assertEqual(
            result,
            "STARTUP_Q64_WITHOUT_REFILL_RECEIPT",
        )

    def test_probe_lifecycle_light_and_measured_binding(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            trace = root / "trace"
            for event in ["frl_pc_try64", "frl_refill_stock"]:
                probe = root / "events" / "kprobes" / event
                probe.mkdir(parents=True)
                for name in ["enable", "filter", "trigger"]:
                    (probe / name).write_text("", encoding="utf-8")

            prepare_startup_probes(trace, stack=False)
            q64 = root / "events" / "kprobes" / "frl_pc_try64"
            refill = root / "events" / "kprobes" / "frl_refill_stock"
            self.assertEqual(
                (q64 / "filter").read_text(encoding="utf-8"),
                "nr_pages == 64\n",
            )
            self.assertEqual(
                (refill / "filter").read_text(encoding="utf-8"),
                "nr_pages == 63\n",
            )
            self.assertEqual(
                (q64 / "enable").read_text(encoding="utf-8"),
                "1\n",
            )
            self.assertEqual(
                (refill / "enable").read_text(encoding="utf-8"),
                "1\n",
            )

            bind_measured_q64_probe(trace, target_pid=222)
            self.assertEqual(
                (q64 / "filter").read_text(encoding="utf-8"),
                "nr_pages == 64 && common_pid == 222\n",
            )
            self.assertEqual(
                (refill / "enable").read_text(encoding="utf-8"),
                "0\n",
            )

            close_probes(trace)
            self.assertEqual(
                (q64 / "enable").read_text(encoding="utf-8"),
                "0\n",
            )

    def test_aggregate_promotes_complete_seed_specimen(self) -> None:
        spec = {
            "experiment_id": "TX-STARTUP-STOCK-SEED-PHASE-v1",
            "design": {
                "total_identities": 2,
                "observer_arms": ["LIGHT", "STACK"],
            },
        }
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rows = [
                {
                    "trial_id": "0:0",
                    "observer_arm": "LIGHT",
                    "startup_classification":
                        "STARTUP_STOCK_SEED_PRE_EXEC",
                    "startup_stock_cpu_q64_count": 1,
                    "startup_stock_cpu_refill63_count": 1,
                    "startup_q64_profile": {"hits": 1, "missed": 0},
                    "startup_refill_profile": {"hits": 1, "missed": 0},
                    "startup_stack_receipt_complete": True,
                    "first_q64_touch": 40,
                    "classification": "WITHIN_BOUND",
                    "pid": 100,
                    "cgroup_procs": [100],
                    "startup_q64": [],
                },
                {
                    "trial_id": "0:1",
                    "observer_arm": "STACK",
                    "startup_classification": "NO_STARTUP_SEED",
                    "startup_stock_cpu_q64_count": 0,
                    "startup_stock_cpu_refill63_count": 0,
                    "startup_q64_profile": {"hits": 0, "missed": 0},
                    "startup_refill_profile": {"hits": 0, "missed": 0},
                    "startup_stack_receipt_complete": True,
                    "first_q64_touch": 1,
                    "classification": "WITHIN_BOUND",
                    "pid": 101,
                    "cgroup_procs": [101],
                    "startup_q64": [],
                },
            ]
            for i, row in enumerate(rows):
                (root / f"trial-0-{i}.json").write_text(
                    json.dumps(row),
                    encoding="utf-8",
                )

            result = aggregate(spec, root)

        self.assertTrue(result["experiment_pass"])
        self.assertEqual(result["startup_seed_promoted_count"], 1)
        self.assertEqual(
            result["startup_seed_promoted_trials"],
            ["0:0"],
        )


if __name__ == "__main__":
    unittest.main()
