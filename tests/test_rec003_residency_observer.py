from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from finite_ram_lab.rec003_residency_observer import (
    PHASES,
    schedule_rows,
    summarize,
    write_schedule,
)


SPEC = {
    "experiment_id": "REC-003-RESIDENCY-OBSERVER-FOOTPRINT-v1",
    "runner": "ubuntu-26.04",
    "runner_blocks": 4,
    "base_schedule_seed": 2026092903,
    "file_sizes_mib": [96, 192, 384],
    "prepare_chunk_mib": 4,
    "expected_trials": 12,
    "settle_seconds": 0.05,
    "memory_stat_fields": [
        "anon",
        "file",
        "kernel",
        "pagetables",
        "slab",
        "sock",
        "shmem",
    ],
}


def fake_trial(block: int, size: int) -> dict:
    base = 1000
    scale = size * 1024
    deltas = {}
    for i, phase in enumerate(PHASES):
        deltas[phase] = {
            "memory_current_delta": scale + i,
            "memory_stat_delta": {
                "anon": 1,
                "file": 0,
                "kernel": 2,
                "pagetables": size,
                "slab": 0,
                "sock": 0,
                "shmem": 0,
            },
        }
    return {
        "status": "PASS",
        "block": block,
        "size_mib": size,
        "mincore_vector_bytes": size * 256,
        "resident_fraction": 0.0,
        "deltas": deltas,
        "derived": {
            "max_observed_phase_current_delta_bytes": scale + 7,
            "post_cleanup_current_delta_bytes": scale + 6,
            "post_gc_settle_current_delta_bytes": scale + 7,
            "final_memory_peak_minus_baseline_current_bytes": scale + 8,
        },
    }


class Rec003Tests(unittest.TestCase):
    def test_schedule_complete_and_deterministic(self) -> None:
        rows = schedule_rows(SPEC, 0)
        self.assertEqual(rows, schedule_rows(SPEC, 0))
        self.assertEqual(
            {r["size_mib"] for r in rows},
            {96, 192, 384},
        )

    def test_schedule_lf_only(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "schedule.csv"
            write_schedule(SPEC, 0, p)
            raw = p.read_bytes()
        self.assertNotIn(b"\r", raw)
        self.assertEqual(raw.count(b"\n"), 4)

    def test_summary_matrix(self) -> None:
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
        self.assertEqual(result["cells"]["96"]["trial_count"], 4)
        self.assertLess(
            result["cells"]["96"]["median_post_gc_settle_delta_bytes"],
            result["cells"]["384"]["median_post_gc_settle_delta_bytes"],
        )

    def test_workflow_contract(self) -> None:
        workflow = Path(
            ".github/workflows/rec-003-residency-observer.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("runs-on: ubuntu-26.04", workflow)
        self.assertIn("Run observer-only trials", workflow)
        self.assertIn(
            'SPEC="$GITHUB_WORKSPACE/specs/REC-003-RESIDENCY-OBSERVER-FOOTPRINT-v1.json"',
            workflow,
        )
        self.assertIn("-p MemoryAccounting=yes", workflow)
        self.assertNotIn("MemoryHigh=", workflow)
        self.assertNotIn("MemoryMax=", workflow)


if __name__ == "__main__":
    unittest.main()
