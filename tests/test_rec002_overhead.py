from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from finite_ram_lab.rec002_overhead import ARMS, schedule_rows, summarize_trials, write_schedule


def _trial(block: int, mode: str) -> dict:
    on = mode == "recorder_on"
    return {
        "status": "PASS",
        "block": block,
        "mode": mode,
        "recorder": {"jsonl_bytes": 4096 if on else 0},
        "metrics": {
            "memory_high_events": 1 if on else 0,
            "max_scan_memory_bytes": 158 * 1024 * 1024 + (4096 if on else 0),
            "post_scan_memory_bytes": 76 * 1024 * 1024,
            "scan_elapsed_ns": 110 if on else 100,
            "file_post_fraction": 0.0,
            "hot_retouch_ns": 1000,
        },
    }


class Rec002Tests(unittest.TestCase):
    def test_schedule_is_complete_and_deterministic(self) -> None:
        self.assertEqual(schedule_rows(3), schedule_rows(3))
        self.assertEqual(
            {row["mode"] for row in schedule_rows(3)},
            set(ARMS),
        )
        self.assertEqual(len(schedule_rows(3)), 2)

    def test_schedule_file_uses_unix_line_endings(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "schedule.csv"
            write_schedule(path, 0)
            raw = path.read_bytes()
        self.assertNotIn(b"\r", raw)
        self.assertEqual(raw.count(b"\n"), 3)

    def test_schedule_changes_across_blocks(self) -> None:
        orders = [tuple(row["mode"] for row in schedule_rows(i)) for i in range(8)]
        self.assertGreater(len(set(orders)), 1)

    def test_summary_is_paired(self) -> None:
        trials = [
            _trial(block, mode)
            for block in range(8)
            for mode in ARMS
        ]
        summary = summarize_trials(trials)
        self.assertEqual(summary["trial_count"], 16)
        self.assertEqual(summary["block_count"], 8)
        self.assertEqual(
            summary["paired_medians"]["delta_memory_high_events"],
            1.0,
        )
        self.assertAlmostEqual(
            summary["paired_medians"]["scan_elapsed_ratio_on_over_off"],
            1.1,
        )

    def test_summary_rejects_missing_trial(self) -> None:
        trials = [
            _trial(block, mode)
            for block in range(8)
            for mode in ARMS
        ][:-1]
        with self.assertRaises(ValueError):
            summarize_trials(trials)


if __name__ == "__main__":
    unittest.main()
