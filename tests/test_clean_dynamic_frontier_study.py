from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from finite_ram_lab.clean_dynamic_frontier_study import (
    schedule_rows,
    summarize,
)


SPEC = {
    "experiment_id": "CLEAN-DYNAMIC-FRONTIER-v0.1",
    "observer_contract_version": "clean-prepost-v1",
    "memory_high_mib": [144, 160, 176],
    "memory_max_mib": 320,
    "hot_anon_mib": 64,
    "cold_file_mib": 96,
    "read_chunk_mib": 4,
    "runner_blocks_per_pressure": 8,
    "base_schedule_seed": 2026100101,
    "arms": [
        "buffered",
        "dontneed_32m",
        "dontneed_48m",
        "dontneed_64m",
        "dontneed_80m",
        "dontneed_96m",
    ],
    "expected_trials": 144,
    "external_cold_fraction_max": 0.1,
    "post_observer_file_fraction_max": 0.1,
    "qualification": {
        "claim_ceiling": "HOSTED_DIRECTIONAL_DYNAMIC_FRONTIER_ONLY"
    },
}


def fake_trial(high: int, block: int, arm: str) -> dict:
    base = 80 * 1024 * 1024
    release = {
        "buffered": 96,
        "dontneed_32m": 32,
        "dontneed_48m": 48,
        "dontneed_64m": 64,
        "dontneed_80m": 80,
        "dontneed_96m": 96,
    }[arm]
    peak = min(high * 1024 * 1024, base + release * 1024 * 1024)
    floor = 77 * 1024 * 1024
    return {
        "status": "PASS",
        "pressure_mib": high,
        "block": block,
        "arm": arm,
        "metrics": {
            "peak_ram_bytes": peak,
            "clean_floor_bytes": floor,
            "ephemeral_excess_bytes": peak - floor,
            "observer_current_delta_bytes": 0,
            "memory_high_events": int(peak >= high * 1024 * 1024),
            "pgscan": 0,
            "pgsteal": 0,
            "advice_calls": 0 if arm == "buffered" else 1,
            "scan_elapsed_ns": 10,
            "hot_retouch_ns": 5,
        },
    }


class CleanDynamicFrontierStudyTests(unittest.TestCase):
    def test_schedule_is_complete_and_deterministic(self):
        rows = schedule_rows(SPEC, pressure=144, block=0)
        self.assertEqual(rows, schedule_rows(SPEC, pressure=144, block=0))
        self.assertEqual({row["arm"] for row in rows}, set(SPEC["arms"]))

    def test_summary_requires_full_144_trial_matrix(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            i = 0
            for high in SPEC["memory_high_mib"]:
                for block in range(SPEC["runner_blocks_per_pressure"]):
                    for arm in SPEC["arms"]:
                        (root / f"trial-{i}.json").write_text(
                            json.dumps(fake_trial(high, block, arm)),
                            encoding="utf-8",
                        )
                        i += 1
            result = summarize(SPEC, root)
        self.assertEqual(result["trial_count"], 144)
        self.assertEqual(result["execution_status"], "PASS")
        self.assertEqual(
            len(result["cells"]["144"]["dontneed_64m"]["block_rows"]),
            8,
        )

    def test_workflow_has_no_push_trigger_and_requires_explicit_ack(self):
        workflow = Path(
            ".github/workflows/clean-dynamic-frontier.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", workflow)
        self.assertNotIn("\n  push:", workflow)
        self.assertIn("EXPLICITLY_AUTHORIZED", workflow)
        self.assertIn("checkpoint_hook=None", Path(
            "src/finite_ram_lab/clean_dynamic_frontier_study.py"
        ).read_text(encoding="utf-8"))

    def test_workflow_cold_verification_precedes_systemd_run(self):
        workflow = Path(
            ".github/workflows/clean-dynamic-frontier.yml"
        ).read_text(encoding="utf-8")
        cold = workflow.index("Cold preparation/verification")
        systemd = workflow.index("sudo systemd-run", cold)
        self.assertLess(cold, systemd)


if __name__ == "__main__":
    unittest.main()
