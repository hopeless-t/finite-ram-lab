from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from finite_ram_lab.strata007_cross_image import (
    schedule_rows,
    summarize,
    write_schedule,
)


SPEC = {
    "experiment_id": "STRATA-007-CROSS-IMAGE-v1",
    "runner": "ubuntu-26.04",
    "anchor_runner": "ubuntu-24.04",
    "runner_blocks": 4,
    "base_schedule_seed": 2026092819,
    "memory_high_mib": 160,
    "memory_max_mib": 320,
    "hot_anon_mib": 64,
    "cold_file_mib": 96,
    "read_chunk_mib": 4,
    "arms": [
        "buffered",
        "dontneed_64m",
        "dontneed_72m",
        "dontneed_80m",
        "dontneed_88m",
        "dontneed_96m",
    ],
    "release_interval_mib": {
        "buffered": None,
        "dontneed_64m": 64,
        "dontneed_72m": 72,
        "dontneed_80m": 80,
        "dontneed_88m": 88,
        "dontneed_96m": 96,
    },
    "expected_trials": 24,
    "anchor": {
        "experiment_id": "STRATA-004-KNEE-v1",
        "runner": "ubuntu-24.04",
        "raw_release_interval_bracket": "80 MiB < onset <= 88 MiB",
        "knee_plus_hot_bracket": "144 MiB < K+hot <= 152 MiB",
    },
}


def trial(block: int, arm: str) -> dict:
    release = SPEC["release_interval_mib"][arm]
    events = int(release is not None and release >= 88)
    peak = int(160 * 1024 * 1024 * (1.001 if events else 0.95))
    return {
        "status": "PASS",
        "runner": "ubuntu-26.04",
        "memory_high_mib": 160,
        "hot_anon_mib": 64,
        "block": block,
        "arm": arm,
        "metrics": {
            "memory_high_events": events,
            "max_scan_memory_bytes": peak,
            "post_scan_memory_bytes": 77 * 1024 * 1024,
            "file_post_fraction": 0.0,
            "scan_elapsed_ns": 100,
            "pgscan": events * 10,
            "pgsteal": events * 10,
        },
        "normalized": {
            "peak_fraction_of_high": peak / (160 * 1024 * 1024),
            "headroom_over_hot_mib": 96,
            "post_scan_live_floor_mib": 77.0,
            "post_scan_non_hot_floor_mib": 13.0,
        },
        "recorder": {"jsonl_bytes": 6000},
    }


class Strata007Tests(unittest.TestCase):
    def test_schedule_complete_deterministic(self) -> None:
        self.assertEqual(schedule_rows(SPEC, 0), schedule_rows(SPEC, 0))
        self.assertEqual(
            {row["arm"] for row in schedule_rows(SPEC, 0)},
            set(SPEC["arms"]),
        )

    def test_schedule_lf_only(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "schedule.csv"
            write_schedule(SPEC, 0, path)
            raw = path.read_bytes()
        self.assertNotIn(b"\r", raw)
        self.assertEqual(raw.count(b"\n"), 7)

    def test_summary_full_matrix_and_onset(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            i = 0
            for block in range(SPEC["runner_blocks"]):
                for arm in SPEC["arms"]:
                    (root / f"trial-{i}-{arm}.json").write_text(
                        json.dumps(trial(block, arm)),
                        encoding="utf-8",
                    )
                    i += 1
            result = summarize(SPEC, root)

        self.assertEqual(result["trial_count"], 24)
        onset = result["onset_screen"]
        self.assertEqual(
            onset["raw_release_interval_bracket"],
            "80 MiB < onset <= 88 MiB",
        )
        self.assertEqual(
            onset["knee_plus_hot_bracket"],
            "144 MiB < K+hot <= 152 MiB",
        )

    def test_summary_rejects_missing_trial(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            i = 0
            for block in range(SPEC["runner_blocks"]):
                for arm in SPEC["arms"]:
                    if i == 23:
                        break
                    (root / f"trial-{i}-{arm}.json").write_text(
                        json.dumps(trial(block, arm)),
                        encoding="utf-8",
                    )
                    i += 1
            with self.assertRaises(ValueError):
                summarize(SPEC, root)

    def test_workflow_contract(self) -> None:
        workflow = Path(
            ".github/workflows/strata-007-cross-image.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("runs-on: ubuntu-26.04", workflow)
        self.assertIn('python-version: "3.12"', workflow)
        self.assertIn(
            'SPEC="$GITHUB_WORKSPACE/specs/STRATA-007-CROSS-IMAGE-v1.json"',
            workflow,
        )
        panel = workflow.split("- name: Run six-arm panel with Recorder", 1)[1]
        panel = panel.split("- uses: actions/upload-artifact@v7", 1)[0]
        self.assertIn('--spec "$SPEC"', panel)


if __name__ == "__main__":
    unittest.main()
