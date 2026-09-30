from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from finite_ram_lab.probe_coverage import (
    parse_kprobe_profile_text,
    summarize_probe_coverage,
)


PROFILE_OK = """
  frl_refill_stock        22621 17
  frl_pc_try64             4501 0
  frl_pc_uncharge_owner     12212 0
  frl_drain_stock           220 3
  frl_lru_flush            9000 0
  frl_folios_put          90000 0
"""

PROFILE_MISS = """
  frl_refill_stock        22621 175
  frl_pc_try64             4501 0
  frl_pc_uncharge_owner     12212 1
  frl_drain_stock           220 3
"""


class ProbeCoverageTests(unittest.TestCase):
    def test_parse_profile(self) -> None:
        rows = parse_kprobe_profile_text(PROFILE_OK)
        self.assertEqual(rows["frl_pc_try64"]["hits"], 4501)
        self.assertEqual(rows["frl_pc_try64"]["missed"], 0)

    def test_zero_miss_profiles_pass(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "kprobe-profile.txt"
            p.write_text(PROFILE_OK, encoding="utf-8")
            result = summarize_probe_coverage([p])

        self.assertTrue(result["coverage_pass"])
        self.assertEqual(result["critical_missed_total"], 0)
        self.assertEqual(result["missing_critical_probes"], [])

    def test_nonzero_miss_fails_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "kprobe-profile.txt"
            p.write_text(PROFILE_MISS, encoding="utf-8")
            result = summarize_probe_coverage([p])

        self.assertFalse(result["coverage_pass"])
        self.assertEqual(result["critical_missed"]["frl_pc_uncharge_owner"], 1)
        self.assertGreater(result["critical_missed_total"], 0)

    def test_missing_probe_fails_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "kprobe-profile.txt"
            p.write_text(
                "frl_pc_try64 10 0\n",
                encoding="utf-8",
            )
            result = summarize_probe_coverage([p])

        self.assertFalse(result["coverage_pass"])
        self.assertIn(
            "frl_pc_uncharge_owner",
            result["missing_critical_probes"],
        )


if __name__ == "__main__":
    unittest.main()
