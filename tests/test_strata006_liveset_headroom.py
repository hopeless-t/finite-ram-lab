from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from finite_ram_lab.strata006_liveset_headroom import (
    schedule_rows,
    summarize,
    write_schedule,
)


SPEC = {
    "experiment_id": "STRATA-006-LIVESET-HEADROOM-v1",
    "runner_blocks_per_hot": 4,
    "base_schedule_seed": 2026092813,
    "memory_high_mib": 160,
    "memory_max_mib": 320,
    "hot_anon_mib": [56, 72],
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
    "expected_trials": 48,
}


def trial(hot: int, block: int, arm: str) -> dict:
    release = SPEC["release_interval_mib"][arm]
    threshold = 96 if hot == 56 else 80
    events = int(release is not None and release >= threshold)
    peak = int(
        SPEC["memory_high_mib"]
        * 1024
        * 1024
        * (1.001 if events else 0.95)
    )
    return {
        "status": "PASS",
        "memory_high_mib": 160,
        "hot_anon_mib": hot,
        "block": block,
        "arm": arm,
        "metrics": {
            "memory_high_events": events,
            "max_scan_memory_bytes": peak,
            "post_scan_memory_bytes": (hot + 13) * 1024 * 1024,
            "file_post_fraction": 0.0,
            "scan_elapsed_ns": 100,
            "pgscan": events * 10,
            "pgsteal": events * 10,
        },
        "normalized": {
            "peak_fraction_of_high": peak / (160 * 1024 * 1024),
            "headroom_over_hot_mib": 160 - hot,
            "post_scan_live_floor_mib": hot + 13,
        },
        "recorder": {"jsonl_bytes": 6000},
    }


class Strata006Tests(unittest.TestCase):
    def test_schedule_complete_deterministic(self) -> None:
        self.assertEqual(
            schedule_rows(SPEC, 56, 0),
            schedule_rows(SPEC, 56, 0),
        )
        self.assertEqual(
            {row["arm"] for row in schedule_rows(SPEC, 56, 0)},
            set(SPEC["arms"]),
        )

    def test_schedule_lf_only(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "schedule.csv"
            write_schedule(SPEC, 56, 0, path)
            raw = path.read_bytes()
        self.assertNotIn(b"\r", raw)
        self.assertEqual(raw.count(b"\n"), 7)

    def test_summary_full_matrix_and_transformed_onset(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            i = 0
            for hot in SPEC["hot_anon_mib"]:
                for block in range(SPEC["runner_blocks_per_hot"]):
                    for arm in SPEC["arms"]:
                        path = root / f"trial-{i}-{arm}.json"
                        path.write_text(
                            json.dumps(trial(hot, block, arm)),
                            encoding="utf-8",
                        )
                        i += 1
            result = summarize(SPEC, root)

        self.assertEqual(result["trial_count"], 48)
        onset = {row["hot_anon_mib"]: row for row in result["onset_screen"]}
        self.assertEqual(
            onset[56]["raw_release_interval_bracket"],
            "88 MiB < onset <= 96 MiB",
        )
        self.assertEqual(
            onset[56]["knee_plus_hot_bracket"],
            "144 MiB < K+hot <= 152 MiB",
        )
        self.assertEqual(
            onset[72]["raw_release_interval_bracket"],
            "72 MiB < onset <= 80 MiB",
        )
        self.assertEqual(
            onset[72]["knee_plus_hot_bracket"],
            "144 MiB < K+hot <= 152 MiB",
        )

    def test_summary_rejects_missing_trial(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            i = 0
            for hot in SPEC["hot_anon_mib"]:
                for block in range(SPEC["runner_blocks_per_hot"]):
                    for arm in SPEC["arms"]:
                        if i == 47:
                            break
                        (root / f"trial-{i}-{arm}.json").write_text(
                            json.dumps(trial(hot, block, arm)),
                            encoding="utf-8",
                        )
                        i += 1
            with self.assertRaises(ValueError):
                summarize(SPEC, root)

    def test_workflow_uses_absolute_spec_path_inside_systemd(self) -> None:
        workflow = Path(
            ".github/workflows/strata-006-liveset-headroom.yml"
        ).read_text(encoding="utf-8")
        self.assertIn(
            'SPEC="$GITHUB_WORKSPACE/specs/STRATA-006-LIVESET-HEADROOM-v1.json"',
            workflow,
        )
        panel = workflow.split("- name: Run six-arm panel with Recorder", 1)[1]
        panel = panel.split("- uses: actions/upload-artifact@v7", 1)[0]
        self.assertIn('--spec "$SPEC"', panel)
        self.assertNotIn(
            "--spec specs/STRATA-006-LIVESET-HEADROOM-v1.json",
            panel,
        )


if __name__ == "__main__":
    unittest.main()
