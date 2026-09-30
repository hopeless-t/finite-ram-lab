from __future__ import annotations

import unittest

from finite_ram_lab.owner_refill_hist_pilot import _hist_hits


class OwnerRefillHistPilotTests(unittest.TestCase):
    def test_hist_hits_parses_totals(self) -> None:
        text = """
# trigger info: hist:keys=nr_pages:vals=hitcount:size=2048 [active]

{ nr_pages: 1 } hitcount: 7
{ nr_pages: 63 } hitcount: 3

Totals:
    Hits: 10
    Entries: 2
    Dropped: 0
"""
        self.assertEqual(_hist_hits(text), 10)

    def test_hist_hits_missing_returns_none(self) -> None:
        self.assertIsNone(_hist_hits("no totals here"))


if __name__ == "__main__":
    unittest.main()
