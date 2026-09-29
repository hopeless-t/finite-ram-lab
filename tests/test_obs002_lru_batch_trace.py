from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from finite_ram_lab.obs002_lru_batch_trace import (
    aggregate,
    parse_trace_windows,
)


class OBS002Tests(unittest.TestCase):
    def test_parse_flush_chain(self) -> None:
        text = """
python-1 [000] ...: tracing_mark_write: FRL_OBS001 trial=0:0 touch=14 PRE
worker-2 [003] ...: frl_lru_add: (__folio_batch_add_and_move+0x0/0x1) nr=99
worker-2 [003] ...: frl_lru_flush: (folio_batch_move_lru+0x0/0x1) nr=31
worker-2 [003] ...: frl_folios_put: (folios_put_refs+0x0/0x1) nr=31
worker-2 [003] ...: frl_pc_uncharge: (page_counter_uncharge+0x0/0x1) counter=0x1 nr_pages=17
python-1 [000] ...: tracing_mark_write: FRL_OBS001 trial=0:0 touch=14 POST
"""
        windows = parse_trace_windows(text)
        row = windows[("0:0", 14)]
        self.assertEqual(len(row["lru_add"]), 1)
        self.assertEqual(row["lru_flush"][0]["nr"], 31)
        self.assertEqual(row["folios_put"][0]["nr"], 31)
        self.assertEqual(
            row["pc_uncharge_17"][0]["nr_pages"],
            17,
        )

    def test_aggregate_infers_initial_occupancy_from_flush_touch(self) -> None:
        trace_lines = []
        touches = []
        for touch_number in range(1, 15):
            delta = -17.0 if touch_number == 14 else 0.0
            touches.append(
                {
                    "touch_number": touch_number,
                    "delta_pages": delta,
                    "vmrss_kib_pre": 100 + 4 * (touch_number - 1),
                    "vmrss_kib_post": 104 + 4 * (touch_number - 1),
                    "vmpte_kib_pre": 48,
                    "vmpte_kib_post": 48,
                }
            )
            trace_lines.append(
                "python-1 [000] ...: tracing_mark_write: "
                f"FRL_OBS001 trial=0:0 touch={touch_number} PRE"
            )
            trace_lines.append(
                "worker-2 [003] ...: frl_lru_add: "
                "(__folio_batch_add_and_move+0x0/0x1) nr=200"
            )
            if touch_number == 14:
                trace_lines.extend(
                    [
                        "worker-2 [003] ...: frl_lru_flush: "
                        "(folio_batch_move_lru+0x0/0x1) nr=31",
                        "worker-2 [003] ...: frl_folios_put: "
                        "(folios_put_refs+0x0/0x1) nr=31",
                        "worker-2 [003] ...: frl_pc_uncharge: "
                        "(page_counter_uncharge+0x0/0x1) "
                        "counter=0x1 nr_pages=17",
                    ]
                )
            trace_lines.append(
                "python-1 [000] ...: tracing_mark_write: "
                f"FRL_OBS001 trial=0:0 touch={touch_number} POST"
            )

        trial = {
            "block": 0,
            "identity": 0,
            "post_migration_current_pages": 116.0,
            "touches": touches,
        }
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "trial-0-0.json").write_text(
                json.dumps(trial),
                encoding="utf-8",
            )
            result = aggregate(root, "\n".join(trace_lines))

        self.assertTrue(
            result["instrumentation_correction"][
                "all_measured_touches_lru_add_count_exactly_one"
            ]
        )
        self.assertEqual(
            result["negative_events"]["exact_minus17_count"],
            1,
        )
        self.assertEqual(
            result["negative_events"][
                "exact_minus17_with_full_lru_chain"
            ],
            1,
        )
        first = result["first_flush_analysis"]["rows"][0]
        self.assertEqual(first["first_flush_touch"], 14)
        self.assertEqual(
            first["inferred_initial_lru_add_occupancy"],
            17,
        )
        self.assertTrue(first["exact_minus17_at_first_flush"])


if __name__ == "__main__":
    unittest.main()
