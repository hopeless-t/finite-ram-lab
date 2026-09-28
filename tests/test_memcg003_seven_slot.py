from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from finite_ram_lab.memcg003_seven_slot import analyze_trials


ROOT = Path(__file__).resolve().parents[1]
SPEC = json.loads(
    (ROOT / "specs/MEMCG-003-SEVEN-SLOT-EVICTION-v1.json")
    .read_text(encoding="utf-8")
)


def trial(block: int, arm: str, event_at: int | None) -> dict:
    max_m = 6 if arm == "six_only" else 8
    rows = []
    for m in range(1, max_m + 1):
        event = event_at == m
        rows.append({
            "m": m,
            "actor": arm,
            "pre_current_bytes": 0,
            "post_probe_current_bytes": 0,
            "stock_drop_pages": 56 if event else 0,
            "probe_delta_pages": 64 if event else 0,
            "eviction_evidence": event,
        })
    return {
        "experiment_id": SPEC["experiment_id"],
        "block": block,
        "arm": arm,
        "cpu": 0,
        "page_size": 4096,
        "wash_count": 7,
        "records": rows,
    }


class Memcg003Tests(unittest.TestCase):
    def matrix(self, distinct_event: int | None, same_event: int | None = None):
        trials = []
        for b in range(4):
            trials.extend([
                trial(b, "distinct_churn", distinct_event),
                trial(b, "same_memcg_activity", same_event),
                trial(b, "six_only", None),
                trial(b, "no_churn", None),
            ])
        return trials

    def test_exact_k7_support(self) -> None:
        result = analyze_trials(SPEC, self.matrix(7))
        self.assertEqual(result["decision"], "SUPPORT_K7_SLOT_MODEL")
        self.assertEqual(result["thresholds"], [7, 7, 7, 7])
        self.assertEqual(result["best_k_by_absolute_error"], 7)
        self.assertEqual(result["posterior_mode_k"], 7)
        self.assertTrue(all(
            f["trained_k"] == 7 for f in result["leave_one_block_out"]
        ))

    def test_controls_can_reject(self) -> None:
        result = analyze_trials(SPEC, self.matrix(7, same_event=3))
        self.assertEqual(result["decision"], "REJECT_K7_SLOT_MODEL")

    def test_alternative_k_is_detected(self) -> None:
        result = analyze_trials(SPEC, self.matrix(4))
        self.assertEqual(result["decision"], "REJECT_K7_SLOT_MODEL")
        self.assertEqual(result["best_k_by_absolute_error"], 4)
        self.assertEqual(result["posterior_mode_k"], 4)

    def test_worker_compiles_when_gcc_available(self) -> None:
        gcc = shutil.which("gcc")
        if not gcc:
            self.skipTest("gcc unavailable")
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "holder"
            subprocess.run(
                [
                    gcc, "-O2", "-Wall", "-Wextra", "-std=c11",
                    str(ROOT / "experiments/memcg003_holder.c"),
                    "-o", str(out),
                ],
                check=True,
            )
            self.assertTrue(out.exists())


if __name__ == "__main__":
    unittest.main()
