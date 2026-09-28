from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from finite_ram_lab.strata009_dataset_gt_memorymax import (
    schedule_rows,
    summarize,
    write_schedule,
)


SPEC = {
    "experiment_id": "STRATA-009-DATASET-GT-MEMORYMAX-v1",
    "runner": "ubuntu-26.04",
    "runner_blocks": 4,
    "base_schedule_seed": 2026092901,
    "memory_high_mib": 160,
    "memory_max_mib": 320,
    "hot_anon_mib": 64,
    "cold_file_mib": 384,
    "read_chunk_mib": 4,
    "arms": [
        "dontneed_64m",
        "dontneed_72m",
        "dontneed_80m",
        "dontneed_88m",
        "dontneed_96m",
    ],
    "release_interval_mib": {
        "dontneed_64m": 64,
        "dontneed_72m": 72,
        "dontneed_80m": 80,
        "dontneed_88m": 88,
        "dontneed_96m": 96,
    },
    "expected_trials": 20,
    "anchor": {},
}


def fake_trial(block: int, arm: str) -> dict:
    release = SPEC["release_interval_mib"][arm]
    events = 0 if release <= 80 else 7
    return {
        "status": "PASS",
        "block": block,
        "arm": arm,
        "metrics": {
            "memory_high_events": events,
            "max_scan_memory_bytes": 159 * 1024 * 1024,
            "post_scan_memory_bytes": 77 * 1024 * 1024,
            "post_scan_non_hot_floor_mib": 13.0,
            "file_post_fraction": 0.0,
            "logical_span_bytes": 384 * 1024 * 1024,
            "advice_calls": 6,
            "scan_elapsed_ns": 1,
            "pgscan": 0,
            "pgsteal": 0,
            "oom": 0,
            "oom_kill": 0,
        },
    }


class Strata009Tests(unittest.TestCase):
    def test_schedule_has_only_bounded_arms(self) -> None:
        rows = schedule_rows(SPEC, 0)
        self.assertEqual(len(rows), 5)
        self.assertNotIn("buffered", {r["arm"] for r in rows})

    def test_schedule_lf_only(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "schedule.csv"
            write_schedule(SPEC, 0, p)
            raw = p.read_bytes()
        self.assertNotIn(b"\r", raw)
        self.assertEqual(raw.count(b"\n"), 6)

    def test_summary_matrix_and_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            i = 0
            for block in range(4):
                for arm in SPEC["arms"]:
                    (root / f"trial-{i}-{arm}.json").write_text(
                        json.dumps(fake_trial(block, arm)),
                        encoding="utf-8",
                    )
                    i += 1
            result = summarize(SPEC, root)

        self.assertEqual(result["trial_count"], 20)
        self.assertTrue(result["dataset_exceeds_memory_max"])
        self.assertEqual(
            result["onset_screen"]["raw_release_interval_bracket"],
            "80 MiB < onset <= 88 MiB",
        )

    def test_workflow_contract(self) -> None:
        workflow = Path(
            ".github/workflows/strata-009-dataset-gt-memorymax.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("_prepare_file(p, 384 * 1024 * 1024", workflow)
        self.assertIn("MAX_BYTES=$((320 * 1024 * 1024))", workflow)
        self.assertIn("systemd_version=$(systemd-run --version | head -n1)", workflow)
        self.assertIn("Run five bounded-policy arms", workflow)


if __name__ == "__main__":
    unittest.main()
