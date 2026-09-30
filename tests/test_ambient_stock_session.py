from __future__ import annotations

import tempfile
from pathlib import Path
import unittest
from unittest import mock

from finite_ram_lab.ambient_stock_log_reducer import reduce_catcher_records
from finite_ram_lab import ambient_stock_session as session


def touch_row(worker_touched: int, *, cpu: int = 7, pte: int = 0):
    return {
        "worker_error": 0,
        "worker_touched": worker_touched,
        "observed_cpu": cpu,
        "vmpte_delta_kib": pte,
    }


def window(*, q64: int = 0, counter: str = "0xaaa", cpu: int = 7):
    return {
        "pre_count": 1,
        "post_count": 1,
        "marker_error_count": 0,
        "pc_try64": [
            {
                "counter": counter,
                "cpu": cpu,
                "nr_pages": 64,
            }
            for _ in range(q64)
        ],
    }


class AmbientStockSessionTests(unittest.TestCase):
    def test_preverify_rows_reduce_to_preverify_hold(self):
        rows = session._preverify_rows(
            session_id="s1",
            normalized=False,
            initial_residual=None,
        )
        result = reduce_catcher_records(rows)
        self.assertEqual(
            result["classification"]["classification"],
            "PREVERIFY_HOLD",
        )

    def test_boundary_chase_immediate_q64_is_t33(self):
        with tempfile.TemporaryDirectory() as td:
            trace = Path(td) / "trace"
            marker = Path(td) / "trace_marker"
            trace.write_text("", encoding="utf-8")
            marker.write_text("", encoding="utf-8")

            with mock.patch.object(
                session,
                "touch_with_transaction_marker",
                return_value=touch_row(101),
            ), mock.patch.object(
                session,
                "observed_window",
                return_value=window(q64=1),
            ):
                cursor, measured, result = session._boundary_chase(
                    unit={},
                    sequence=[10, 11, 12],
                    cursor=0,
                    measured_count=100,
                    trace_marker=marker,
                    trace_path=trace,
                    trial_id="0:0",
                    epoch=0,
                    stock_cpu=7,
                    page_size=4096,
                    owner_counter="0xaaa",
                    max_extra=3,
                )

        self.assertEqual(cursor, 1)
        self.assertEqual(measured, 101)
        self.assertTrue(result["boundary_observed"])
        self.assertEqual(result["final_boundary_T"], 33)
        self.assertTrue(result["trace_complete"])
        self.assertTrue(result["worker_ok"])
        self.assertTrue(result["cpu_stable"])
        self.assertTrue(result["pte_stable"])

    def test_boundary_chase_can_be_censored_without_failure(self):
        touches = [
            touch_row(101),
            touch_row(102),
        ]
        with tempfile.TemporaryDirectory() as td:
            trace = Path(td) / "trace"
            marker = Path(td) / "trace_marker"
            trace.write_text("", encoding="utf-8")
            marker.write_text("", encoding="utf-8")

            with mock.patch.object(
                session,
                "touch_with_transaction_marker",
                side_effect=touches,
            ), mock.patch.object(
                session,
                "observed_window",
                return_value=window(q64=0),
            ):
                _, measured, result = session._boundary_chase(
                    unit={},
                    sequence=[10, 11, 12],
                    cursor=0,
                    measured_count=100,
                    trace_marker=marker,
                    trace_path=trace,
                    trial_id="0:0",
                    epoch=0,
                    stock_cpu=7,
                    page_size=4096,
                    owner_counter="0xaaa",
                    max_extra=2,
                )

        self.assertEqual(measured, 102)
        self.assertFalse(result["boundary_observed"])
        self.assertIsNone(result["final_boundary_T"])
        self.assertTrue(result["trace_complete"])
        self.assertEqual(len(result["rows"]), 2)

    def test_boundary_chase_stops_on_cpu_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            trace = Path(td) / "trace"
            marker = Path(td) / "trace_marker"
            trace.write_text("", encoding="utf-8")
            marker.write_text("", encoding="utf-8")

            with mock.patch.object(
                session,
                "touch_with_transaction_marker",
                return_value=touch_row(101, cpu=6),
            ), mock.patch.object(
                session,
                "observed_window",
                return_value=window(q64=0),
            ):
                _, _, result = session._boundary_chase(
                    unit={},
                    sequence=[10, 11],
                    cursor=0,
                    measured_count=100,
                    trace_marker=marker,
                    trace_path=trace,
                    trial_id="0:0",
                    epoch=0,
                    stock_cpu=7,
                    page_size=4096,
                    owner_counter="0xaaa",
                    max_extra=2,
                )

        self.assertFalse(result["cpu_stable"])
        self.assertEqual(len(result["rows"]), 1)

    def test_multiple_q64_in_one_window_invalidates_trace_completeness(self):
        with tempfile.TemporaryDirectory() as td:
            trace = Path(td) / "trace"
            marker = Path(td) / "trace_marker"
            trace.write_text("", encoding="utf-8")
            marker.write_text("", encoding="utf-8")

            with mock.patch.object(
                session,
                "touch_with_transaction_marker",
                return_value=touch_row(101),
            ), mock.patch.object(
                session,
                "observed_window",
                return_value=window(q64=2),
            ):
                _, _, result = session._boundary_chase(
                    unit={},
                    sequence=[10, 11],
                    cursor=0,
                    measured_count=100,
                    trace_marker=marker,
                    trace_path=trace,
                    trial_id="0:0",
                    epoch=0,
                    stock_cpu=7,
                    page_size=4096,
                    owner_counter="0xaaa",
                    max_extra=2,
                )

        self.assertFalse(result["trace_complete"])
        self.assertFalse(result["boundary_observed"])


if __name__ == "__main__":
    unittest.main()
