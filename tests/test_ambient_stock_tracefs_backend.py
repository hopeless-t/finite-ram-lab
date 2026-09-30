from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from finite_ram_lab.ambient_stock_tracefs_backend import (
    HistogramSummary,
    cleanup_owner_count_only,
    configure_owner_count_only,
    event_filter,
    hist_trigger,
    histogram_receipt,
    parse_histogram,
)


HIST = """
# trigger info: hist:keys=nr_pages:vals=hitcount:size=2048 [active]

{ nr_pages: 1 } hitcount: 7
{ nr_pages: 3 } hitcount: 2

Totals:
    Hits: 9
    Entries: 2
    Dropped: 0
"""


class AmbientTracefsBackendTests(unittest.TestCase):
    def test_histogram_parser_sums_pages(self):
        summary = parse_histogram(HIST)
        self.assertEqual(summary.hits, 9)
        self.assertEqual(summary.entries, 2)
        self.assertEqual(summary.dropped, 0)
        self.assertEqual(summary.pages, 13)
        self.assertEqual(summary.buckets, {1: 7, 3: 2})

    def test_histogram_total_mismatch_rejected(self):
        with self.assertRaises(ValueError):
            parse_histogram(HIST.replace("Hits: 9", "Hits: 8"))

    def test_filters_are_owner_scoped(self):
        self.assertEqual(
            event_filter(
                "consume",
                owner_memcg="0xaaa",
                owner_counter="0xbbb",
            ),
            "memcg == 0xaaa && ret != 0",
        )
        self.assertEqual(
            event_filter(
                "q64",
                owner_memcg="0xaaa",
                owner_counter="0xbbb",
            ),
            "counter == 0xbbb && nr_pages == 64",
        )

    def test_hist_triggers_have_inline_filters(self):
        self.assertEqual(
            hist_trigger("refill", "0xaaa"),
            "hist:keys=nr_pages if memcg == 0xaaa",
        )
        self.assertEqual(
            hist_trigger("consume", "0xaaa"),
            "hist:keys=nr_pages if memcg == 0xaaa && ret != 0",
        )
        self.assertEqual(
            hist_trigger("uncharge", "0xbbb"),
            "hist:keys=nr_pages if counter == 0xbbb",
        )

    def test_histogram_receipt_emits_pages_and_dropped(self):
        rows = histogram_receipt(
            session_id="s1",
            kind="CONSUME_SUCCESS",
            summary=HistogramSummary(
                hits=2,
                entries=1,
                dropped=0,
                pages=2,
                buckets={1: 2},
            ),
        )
        self.assertEqual(rows[0]["kind"], "CONSUME_SUCCESS")
        self.assertEqual(rows[0]["pages"], 2)
        self.assertEqual(rows[1]["kind"], "HISTOGRAM")
        self.assertEqual(rows[1]["dropped"], 0)

    def test_count_only_configuration_keeps_hist_events_disabled(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            trace = root / "trace"
            trace.write_text("", encoding="utf-8")
            for event in (
                "frl_refill_stock",
                "frl_consume_stock_ret",
                "frl_pc_uncharge_owner",
                "frl_pc_try64",
            ):
                probe = root / "events" / "kprobes" / event
                probe.mkdir(parents=True)
                (probe / "enable").write_text("0\n", encoding="utf-8")
                (probe / "filter").write_text("", encoding="utf-8")
                (probe / "trigger").write_text("", encoding="utf-8")

            configure_owner_count_only(
                trace,
                owner_memcg="0xaaa",
                owner_counter="0xbbb",
            )

            for event in (
                "frl_refill_stock",
                "frl_consume_stock_ret",
                "frl_pc_uncharge_owner",
            ):
                probe = root / "events" / "kprobes" / event
                self.assertEqual(
                    (probe / "enable").read_text(encoding="utf-8"),
                    "0\n",
                )
                self.assertIn(
                    "hist:keys=nr_pages",
                    (probe / "trigger").read_text(encoding="utf-8"),
                )

            q64 = root / "events" / "kprobes" / "frl_pc_try64"
            self.assertEqual(
                (q64 / "enable").read_text(encoding="utf-8"),
                "1\n",
            )

            cleanup_owner_count_only(trace)
            self.assertEqual(
                (q64 / "enable").read_text(encoding="utf-8"),
                "0\n",
            )


if __name__ == "__main__":
    unittest.main()
