from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from finite_ram_lab.strata005_external_validity import (
    schedule_rows,
    summarize,
    write_schedule,
)

SPEC = {
    "experiment_id": "STRATA-005-EXTERNAL-VALIDITY-v1",
    "runner_blocks_per_pressure": 4,
    "base_schedule_seed": 2026092807,
    "memory_high_mib": [144, 176],
    "memory_max_mib": 320,
    "hot_anon_mib": 64,
    "cold_file_mib": 96,
    "read_chunk_mib": 4,
    "arms": [
        "buffered",
        "dontneed_48m",
        "dontneed_64m",
        "dontneed_80m",
        "dontneed_96m",
    ],
    "release_interval_mib": {
        "buffered": None,
        "dontneed_48m": 48,
        "dontneed_64m": 64,
        "dontneed_80m": 80,
        "dontneed_96m": 96,
    },
    "expected_trials": 40,
}


def trial(high: int, block: int, arm: str) -> dict:
    release = SPEC["release_interval_mib"][arm]
    threshold = 80 if high == 144 else 96
    events = int(release is not None and release >= threshold)
    peak = int(high * 1024 * 1024 * (1.01 if events else 0.95))
    return {
        "status": "PASS",
        "memory_high_mib": high,
        "block": block,
        "arm": arm,
        "metrics": {
            "memory_high_events": events,
            "max_scan_memory_bytes": peak,
            "post_scan_memory_bytes": 80 * 1024 * 1024,
            "file_post_fraction": 0.0,
            "scan_elapsed_ns": 100,
            "pgscan": events * 10,
            "pgsteal": events * 10,
        },
        "normalized": {
            "release_fraction_of_high": (
                None if release is None else release / high
            ),
            "peak_fraction_of_high": peak / (high * 1024 * 1024),
            "headroom_over_hot_mib": high - 64,
        },
        "recorder": {"jsonl_bytes": 6000},
    }


class Strata005Tests(unittest.TestCase):
    def test_schedule_complete_deterministic(self) -> None:
        self.assertEqual(
            schedule_rows(SPEC, 144, 0),
            schedule_rows(SPEC, 144, 0),
        )
        self.assertEqual(
            {row["arm"] for row in schedule_rows(SPEC, 144, 0)},
            set(SPEC["arms"]),
        )

    def test_schedule_lf_only(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "schedule.csv"
            write_schedule(SPEC, 144, 0, path)
            raw = path.read_bytes()
        self.assertNotIn(b"\r", raw)
        self.assertEqual(raw.count(b"\n"), 6)

    def test_summary_full_matrix_and_onset(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            i = 0
            for high in SPEC["memory_high_mib"]:
                for block in range(SPEC["runner_blocks_per_pressure"]):
                    for arm in SPEC["arms"]:
                        path = root / f"trial-{i}-{arm}.json"
                        path.write_text(
                            __import__("json").dumps(trial(high, block, arm)),
                            encoding="utf-8",
                        )
                        i += 1
            result = summarize(SPEC, root)

        self.assertEqual(result["trial_count"], 40)
        onset = {
            row["memory_high_mib"]: row
            for row in result["onset_screen"]
        }
        self.assertEqual(
            onset[144]["first_positive_median_release_mib"],
            80,
        )
        self.assertEqual(
            onset[176]["first_positive_median_release_mib"],
            96,
        )

    def test_summary_rejects_missing_trial(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for i in range(39):
                high = 144 if i < 20 else 176
                block = (i // 5) % 4
                arm = SPEC["arms"][i % 5]
                (root / f"trial-{i}-{arm}.json").write_text(
                    __import__("json").dumps(trial(high, block, arm)),
                    encoding="utf-8",
                )
            with self.assertRaises(ValueError):
                summarize(SPEC, root)


if __name__ == "__main__":
    unittest.main()
