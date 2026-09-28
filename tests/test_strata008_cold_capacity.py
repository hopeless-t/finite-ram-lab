from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from finite_ram_lab.strata008_cold_capacity import (
    schedule_rows,
    summarize,
    write_schedule,
)


SPEC = {
    "experiment_id": "STRATA-008-COLD-CAPACITY-v1",
    "runner": "ubuntu-26.04",
    "runner_blocks": 4,
    "base_schedule_seed": 2026092823,
    "memory_high_mib": 160,
    "memory_max_mib": 320,
    "hot_anon_mib": 64,
    "cold_file_mib": 192,
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
    "anchor": {},
}


def trial(block: int, arm: str) -> dict:
    release = SPEC["release_interval_mib"][arm]
    events = int(release is not None and release >= 88)
    return {
        "status": "PASS",
        "block": block,
        "arm": arm,
        "metrics": {
            "memory_high_events": events,
            "max_scan_memory_bytes": 150 * 1024 * 1024,
            "post_scan_memory_bytes": 77 * 1024 * 1024,
            "file_post_fraction": 0.0,
            "scan_elapsed_ns": 100,
            "advice_calls": 3 if release == 64 else 2,
            "logical_span_bytes": 192 * 1024 * 1024,
        },
        "normalized": {"post_scan_non_hot_floor_mib": 13.0},
        "recorder": {"jsonl_bytes": 12000},
    }


class Strata008Tests(unittest.TestCase):
    def test_schedule_complete_deterministic(self) -> None:
        self.assertEqual(schedule_rows(SPEC, 0), schedule_rows(SPEC, 0))
        self.assertEqual(
            {row["arm"] for row in schedule_rows(SPEC, 0)},
            set(SPEC["arms"]),
        )

    def test_summary_full_matrix(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            i = 0
            for block in range(4):
                for arm in SPEC["arms"]:
                    (root / f"trial-{i}-{arm}.json").write_text(
                        json.dumps(trial(block, arm)),
                        encoding="utf-8",
                    )
                    i += 1
            result = summarize(SPEC, root)
        self.assertEqual(result["trial_count"], 24)
        self.assertEqual(
            result["onset_screen"]["raw_release_interval_bracket"],
            "80 MiB < onset <= 88 MiB",
        )
        self.assertEqual(
            result["cells"]["dontneed_64m"]["median_logical_span_bytes"],
            192 * 1024 * 1024,
        )

    def test_schedule_lf_only(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "schedule.csv"
            write_schedule(SPEC, 0, p)
            raw = p.read_bytes()
        self.assertNotIn(b"\r", raw)
        self.assertEqual(raw.count(b"\n"), 7)

    def test_workflow_contract(self) -> None:
        workflow = Path(
            ".github/workflows/strata-008-cold-capacity.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("runs-on: ubuntu-26.04", workflow)
        self.assertIn("_prepare_file(p, 192 * 1024 * 1024", workflow)
        self.assertIn("systemd_version=$(systemd-run --version | head -n1)", workflow)
        self.assertIn(
            'SPEC="$GITHUB_WORKSPACE/specs/STRATA-008-COLD-CAPACITY-v1.json"',
            workflow,
        )


if __name__ == "__main__":
    unittest.main()
