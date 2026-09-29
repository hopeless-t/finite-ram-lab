from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from finite_ram_lab.obs002_lru_batch_trace import aggregate, parse_trace_windows


class OBS002Tests(unittest.TestCase):
    def test_parse_30_to_31_chain(self) -> None:
        text = """
python-1 [000] ...: tracing_mark_write: FRL_OBS001 trial=0:0 touch=14 PRE
worker-2 [003] ...: frl_lru_add: (__folio_batch_add_and_move+0x0/0x1) nr=30 move=lru_add+0x0/0x1
worker-2 [003] ...: frl_lru_flush: (folio_batch_move_lru+0x0/0x1) nr=31 move=lru_add+0x0/0x1
worker-2 [003] ...: frl_folios_put: (folios_put_refs+0x0/0x1) nr=31
worker-2 [003] ...: frl_pc_uncharge: (page_counter_uncharge+0x0/0x1) counter=0x1 nr_pages=17
python-1 [000] ...: tracing_mark_write: FRL_OBS001 trial=0:0 touch=14 POST
"""
        windows = parse_trace_windows(text)
        row = windows[("0:0", 14)]
        self.assertEqual(row["lru_add"][0]["nr"], 30)
        self.assertEqual(row["lru_flush"][0]["nr"], 31)
        self.assertEqual(row["folios_put"][0]["nr"], 31)
        self.assertEqual(row["pc_uncharge_17"][0]["nr_pages"], 17)

    def test_aggregate_exact_chain(self) -> None:
        trace = """
python-1 [000] ...: tracing_mark_write: FRL_OBS001 trial=0:0 touch=1 PRE
worker-2 [003] ...: frl_lru_add: (__folio_batch_add_and_move+0x0/0x1) nr=17 move=lru_add+0x0/0x1
python-1 [000] ...: tracing_mark_write: FRL_OBS001 trial=0:0 touch=1 POST
python-1 [000] ...: tracing_mark_write: FRL_OBS001 trial=0:0 touch=14 PRE
worker-2 [003] ...: frl_lru_add: (__folio_batch_add_and_move+0x0/0x1) nr=30 move=lru_add+0x0/0x1
worker-2 [003] ...: frl_lru_flush: (folio_batch_move_lru+0x0/0x1) nr=31 move=lru_add+0x0/0x1
worker-2 [003] ...: frl_folios_put: (folios_put_refs+0x0/0x1) nr=31
worker-2 [003] ...: frl_pc_uncharge: (page_counter_uncharge+0x0/0x1) counter=0x1 nr_pages=17
python-1 [000] ...: tracing_mark_write: FRL_OBS001 trial=0:0 touch=14 POST
"""
        trial = {
            "block": 0,
            "identity": 0,
            "post_migration_current_pages": 116.0,
            "touches": [
                {
                    "touch_number": 1,
                    "delta_pages": 0.0,
                    "vmrss_kib_pre": 100,
                    "vmrss_kib_post": 104,
                },
                {
                    "touch_number": 14,
                    "delta_pages": -17.0,
                    "vmrss_kib_pre": 148,
                    "vmrss_kib_post": 152,
                },
            ],
        }
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "trial-0-0.json").write_text(json.dumps(trial), encoding="utf-8")
            result = aggregate(root, trace)

        self.assertEqual(result["negative_17_count"], 1)
        self.assertEqual(result["negative_17_exact_30_to_31_chain"], 1)
        self.assertEqual(result["first_touch_lru_add_nr_histogram"], {17: 1})
        self.assertEqual(result["negative_touch_lru_add_nr_histogram"], {30: 1})
        self.assertEqual(result["negative_touch_lru_flush_nr_histogram"], {31: 1})


if __name__ == "__main__":
    unittest.main()
