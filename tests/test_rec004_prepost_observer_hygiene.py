from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from finite_ram_lab.rec004_prepost_observer_hygiene import (
    schedule_rows,
    summarize,
    write_schedule,
)


SPEC = {
    "experiment_id": "REC-004-PREPOST-OBSERVER-HYGIENE-v1",
    "runner": "ubuntu-26.04",
    "runner_blocks": 4,
    "base_schedule_seed": 2026092907,
    "memory_high_mib": 160,
    "memory_max_mib": 320,
    "hot_anon_mib": 64,
    "read_chunk_mib": 4,
    "release_arm": "dontneed_64m",
    "file_sizes_mib": [96, 192, 384],
    "expected_trials": 12,
    "external_cold_fraction_max": 0.1,
}


def fake_trial(block: int, size: int) -> dict:
    observer = 0 if size < 384 else 256 * 1024
    pre = 77 * 1024 * 1024
    return {
        "status": "PASS",
        "block": block,
        "size_mib": size,
        "metrics": {
            "memory_high_events": 0,
            "max_scan_memory_bytes": 140 * 1024 * 1024,
            "pre_observer_current_bytes": pre,
            "post_observer_current_bytes": pre + observer,
            "observer_current_delta_bytes": observer,
            "pre_observer_minus_hot_mib": 13.0,
            "post_observer_minus_hot_mib": 13.0 + observer / (1024 * 1024),
            "observer_anon_delta_bytes": observer,
            "observer_file_delta_bytes": 0,
            "observer_kernel_delta_bytes": 0,
        },
        "file_post_residency": {"resident_fraction": 0.0},
    }


class Rec004Tests(unittest.TestCase):
    def test_schedule_complete(self) -> None:
        rows = schedule_rows(SPEC, 0)
        self.assertEqual(rows, schedule_rows(SPEC, 0))
        self.assertEqual({r["size_mib"] for r in rows}, {96, 192, 384})

    def test_schedule_lf_only(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "schedule.csv"
            write_schedule(SPEC, 0, p)
            raw = p.read_bytes()
        self.assertNotIn(b"\r", raw)
        self.assertEqual(raw.count(b"\n"), 4)

    def test_summary_separates_clean_and_observer_floor(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            i = 0
            for block in range(4):
                for size in SPEC["file_sizes_mib"]:
                    (root / f"trial-{i}-{size}m.json").write_text(
                        json.dumps(fake_trial(block, size)),
                        encoding="utf-8",
                    )
                    i += 1
            result = summarize(SPEC, root)

        self.assertEqual(result["trial_count"], 12)
        self.assertEqual(result["derived"]["pre_observer_floor_span_mib"], 0.0)
        self.assertGreater(
            result["derived"]["post_observer_floor_span_mib"], 0.0
        )
        self.assertEqual(
            result["cells"]["384"]["positive_observer_delta_trials"], 4
        )

    def test_workflow_keeps_cold_check_outside_measured_unit(self) -> None:
        workflow = Path(
            ".github/workflows/rec-004-prepost-observer.yml"
        ).read_text(encoding="utf-8")
        cold = workflow.index("Cold verification deliberately occurs outside")
        systemd = workflow.index("sudo systemd-run", cold)
        self.assertLess(cold, systemd)
        self.assertIn("MemoryHigh=", workflow)
        self.assertIn("MemoryMax=", workflow)


if __name__ == "__main__":
    unittest.main()
