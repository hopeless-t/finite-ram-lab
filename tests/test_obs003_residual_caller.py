from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from finite_ram_lab.obs003_residual_caller import (
    aggregate,
    classify_negative,
    parse_trace_windows,
)


class OBS003Tests(unittest.TestCase):
    def test_lru_batch_class(self) -> None:
        trace = {
            "drain_stock": [],
            "lru_flush": [{"nr": 31}],
            "folios_put": [{"nr": 31}],
            "pc_uncharge_17": [{"nr_pages": 17}],
            "pc_uncharge_17_stacks": [[]],
        }
        self.assertEqual(classify_negative(trace), "LRU_BATCH")

    def test_stock_drain_class(self) -> None:
        trace = {
            "drain_stock": [{"line": "drain"}],
            "lru_flush": [],
            "folios_put": [],
            "pc_uncharge_17": [{"nr_pages": 17}],
            "pc_uncharge_17_stacks": [[]],
        }
        self.assertEqual(classify_negative(trace), "STOCK_DRAIN")

    def test_other_stack_class(self) -> None:
        trace = {
            "drain_stock": [],
            "lru_flush": [],
            "folios_put": [],
            "pc_uncharge_17": [{"nr_pages": 17}],
            "pc_uncharge_17_stacks": [["other_fn+0x1/0x2"]],
        }
        self.assertEqual(classify_negative(trace), "OTHER_STACK")

    def test_trace_miss_class(self) -> None:
        trace = {
            "drain_stock": [],
            "lru_flush": [],
            "folios_put": [],
            "pc_uncharge_17": [],
            "pc_uncharge_17_stacks": [],
        }
        self.assertEqual(classify_negative(trace), "TRACE_MISS")

    def test_aggregate_stack(self) -> None:
        trace = """
python-1 [000] ...: tracing_mark_write: FRL_OBS001 trial=0:0 touch=1 PRE
worker-2 [003] ...: frl_pc_uncharge: (page_counter_uncharge+0x0/0x1) counter=0x1 nr_pages=17
 => other_release+0x1/0x2
 => do_anonymous_page+0x3/0x4
python-1 [000] ...: tracing_mark_write: FRL_OBS001 trial=0:0 touch=1 POST
"""
        trial = {
            "block": 0,
            "identity": 0,
            "post_migration_current_pages": 116.0,
            "touches": [
                {
                    "touch_number": 1,
                    "delta_pages": -17.0,
                    "vmrss_kib_pre": 100,
                    "vmrss_kib_post": 104,
                    "vmpte_kib_pre": 48,
                    "vmpte_kib_post": 48,
                }
            ],
        }
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "trial-0-0.json").write_text(
                json.dumps(trial),
                encoding="utf-8",
            )
            result = aggregate(root, trace)

        self.assertEqual(
            result["classification_counts"],
            {"OTHER_STACK": 1},
        )
        self.assertIn(
            "other_release+0x1/0x2",
            result["exact_minus17_specimens"][0][
                "page_counter_uncharge_17_stack_lines"
            ][0],
        )


if __name__ == "__main__":
    unittest.main()
