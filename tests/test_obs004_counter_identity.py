from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from finite_ram_lab.obs004_counter_identity import (
    aggregate,
    classify_negative,
    parse_trace,
)


class OBS004Tests(unittest.TestCase):
    def test_external_counter_is_not_attributed(self) -> None:
        trace = {
            "lru_flush": [],
            "folios_put": [],
            "drain_stock": [],
            "pc_uncharge_17": [
                {"counter": "0xbbb", "nr_pages": 17, "comm": ".NET Tiered Com"}
            ],
            "pc_uncharge_17_stacks": [["=> shmem_fault"]],
        }
        cls, _ = classify_negative(
            worker_counters=["0xaaa"],
            touch_trace=trace,
        )
        self.assertEqual(cls, "EXTERNAL_COINCIDENCE")

    def test_same_counter_lru_batch(self) -> None:
        trace = {
            "lru_flush": [{"nr": 31}],
            "folios_put": [{"nr": 31}],
            "drain_stock": [],
            "pc_uncharge_17": [
                {"counter": "0xaaa", "nr_pages": 17, "comm": "memcg005gc_spaw"}
            ],
            "pc_uncharge_17_stacks": [["=> folio_batch_move_lru"]],
        }
        cls, idx = classify_negative(
            worker_counters=["0xaaa"],
            touch_trace=trace,
        )
        self.assertEqual(cls, "WORKER_LRU_BATCH")
        self.assertEqual(idx, [0])

    def test_same_counter_stock_stack(self) -> None:
        trace = {
            "lru_flush": [],
            "folios_put": [],
            "drain_stock": [{"line": "drain"}],
            "pc_uncharge_17": [
                {"counter": "0xaaa", "nr_pages": 17, "comm": "swapper/1"}
            ],
            "pc_uncharge_17_stacks": [["=> drain_stock", "=> refill_stock"]],
        }
        cls, _ = classify_negative(
            worker_counters=["0xaaa"],
            touch_trace=trace,
        )
        self.assertEqual(cls, "STOCK_DRAIN_SAME_COUNTER")

    def test_trial_marker_captures_worker_counter(self) -> None:
        text = """
python-1 [000] ...: tracing_mark_write: FRL_TRIAL trial=0:0 START
memcg005gc_spaw-20 [001] ...: frl_pc_try: (page_counter_try_charge+0x0/0x1) counter=0xaaa nr_pages=64 comm="memcg005gc_spaw"
python-1 [000] ...: tracing_mark_write: FRL_TRIAL trial=0:0 READY pid=20
python-1 [000] ...: tracing_mark_write: FRL_OBS001 trial=0:0 touch=1 PRE
other-30 [002] ...: frl_pc_uncharge: (page_counter_uncharge+0x0/0x1) counter=0xbbb nr_pages=17 comm=".NET Tiered Com"
 => shmem_fault
python-1 [000] ...: tracing_mark_write: FRL_OBS001 trial=0:0 touch=1 POST
python-1 [000] ...: tracing_mark_write: FRL_TRIAL trial=0:0 END
"""
        parsed = parse_trace(text)
        self.assertEqual(parsed["0:0"]["worker_counters"], ["0xaaa"])
        self.assertEqual(parsed["0:0"]["worker_pid"], 20)
        self.assertEqual(
            parsed["0:0"]["touches"][1]["pc_uncharge_17"][0]["counter"],
            "0xbbb",
        )

    def test_aggregate_external_coincidence(self) -> None:
        text = """
python-1 [000] ...: tracing_mark_write: FRL_TRIAL trial=0:0 START
memcg005gc_spaw-20 [001] ...: frl_pc_try: (page_counter_try_charge+0x0/0x1) counter=0xaaa nr_pages=64 comm="memcg005gc_spaw"
python-1 [000] ...: tracing_mark_write: FRL_TRIAL trial=0:0 READY pid=20
python-1 [000] ...: tracing_mark_write: FRL_OBS001 trial=0:0 touch=1 PRE
other-30 [002] ...: frl_pc_uncharge: (page_counter_uncharge+0x0/0x1) counter=0xbbb nr_pages=17 comm=".NET Tiered Com"
 => shmem_fault
python-1 [000] ...: tracing_mark_write: FRL_OBS001 trial=0:0 touch=1 POST
python-1 [000] ...: tracing_mark_write: FRL_TRIAL trial=0:0 END
"""
        trial = {
            "block": 0,
            "identity": 0,
            "worker_pid": 20,
            "post_migration_current_pages": 115.0,
            "touches": [
                {
                    "touch_number": 1,
                    "delta_pages": -17.0,
                }
            ],
        }
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "trial-0-0.json").write_text(
                json.dumps(trial), encoding="utf-8"
            )
            result = aggregate(root, text)

        self.assertEqual(
            result["classification_counts"],
            {"EXTERNAL_COINCIDENCE": 1},
        )


if __name__ == "__main__":
    unittest.main()
