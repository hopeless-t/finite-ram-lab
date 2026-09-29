from __future__ import annotations

import inspect
import unittest

from finite_ram_lab.obs001_uncharge_trace import (
    _measured_touch,
    classify_touch,
    parse_trace_windows,
    run_trial,
)


class OBS001Tests(unittest.TestCase):
    def test_worker_uid_is_routed_at_trial_boundary(self) -> None:
        self.assertIn("worker_uid", inspect.signature(run_trial).parameters)
        self.assertNotIn(
            "worker_uid",
            inspect.signature(_measured_touch).parameters,
        )

    def test_trace_window_stock_drain(self) -> None:
        text = """
task-1 [001] 1.000: tracing_mark_write: FRL_OBS001 trial=0:2 touch=14 PRE
kworker-2 [001] 1.001: frl_drain_stock: (drain_stock+0x0/0x1) stock=1 slot=2
kworker-2 [001] 1.002: frl_page_counter_uncharge: (page_counter_uncharge+0x0/0x1) counter=2 nr_pages=17
task-1 [001] 1.003: tracing_mark_write: FRL_OBS001 trial=0:2 touch=14 POST
"""
        windows = parse_trace_windows(text)
        trace = windows[("0:2", 14)]
        self.assertEqual(trace["drain_stock_events"], 1)
        self.assertEqual(trace["page_counter_uncharge_17_events"], 1)
        self.assertEqual(
            classify_touch({"delta_pages": -17.0}, trace),
            "STOCK_DRAIN",
        )

    def test_other_uncharge(self) -> None:
        trace = {
            "drain_stock_events": 0,
            "page_counter_uncharge_17_events": 1,
            "refill_stock_events": 0,
            "raw_event_lines": [],
        }
        self.assertEqual(
            classify_touch({"delta_pages": -17.0}, trace),
            "OTHER_UNCHARGE",
        )

    def test_uncorrelated(self) -> None:
        trace = {
            "drain_stock_events": 0,
            "page_counter_uncharge_17_events": 0,
            "refill_stock_events": 0,
            "raw_event_lines": [],
        }
        self.assertEqual(
            classify_touch({"delta_pages": -17.0}, trace),
            "UNCORRELATED",
        )

    def test_non_negative_is_not_classified(self) -> None:
        self.assertIsNone(
            classify_touch(
                {"delta_pages": 0.0},
                {
                    "drain_stock_events": 1,
                    "page_counter_uncharge_17_events": 1,
                },
            )
        )


if __name__ == "__main__":
    unittest.main()
