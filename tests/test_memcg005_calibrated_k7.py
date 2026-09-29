from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from finite_ram_lab.memcg005_calibrated_k7 import analyze_trials

ROOT = Path(__file__).resolve().parents[1]
SPEC = json.loads(
    (ROOT / "specs/MEMCG-005-CALIBRATED-K7-v1.json").read_text(encoding="utf-8")
)


def trial(block: int, m: int, state: str, valid: bool = True) -> dict:
    return {
        "experiment_id": SPEC["experiment_id"],
        "block": block,
        "m": m,
        "valid_state": valid,
        "invalid_reason": None if valid else "synthetic-invalid",
        "normalization": {},
        "insertions": [],
        "target_probe": {"delta_pages": 0.0},
        "target_state": state if valid else "INVALID",
    }


def matrix(boundary: int = 7) -> list[dict]:
    out = []
    for b in range(4):
        for m in SPEC["tested_m"]:
            state = "ABSENT" if int(m) >= boundary else "PRESENT"
            out.append(trial(b, int(m), state))
    return out


class Memcg005Tests(unittest.TestCase):
    def test_exact_k7_support(self) -> None:
        r = analyze_trials(SPEC, matrix(7))
        self.assertEqual(r["decision"], "SUPPORT_CALIBRATED_K7")
        self.assertEqual(r["support_blocks"], 4)
        self.assertEqual(r["best_k_by_errors"], [7])
        self.assertEqual(r["best_k_by_mdl"], [7])
        self.assertTrue(all(
            fold["selected_k"] == [7]
            for fold in r["leave_one_block_out"]
        ))

    def test_stable_k8_rejects(self) -> None:
        r = analyze_trials(SPEC, matrix(8))
        self.assertEqual(r["decision"], "REJECT_CALIBRATED_K7")
        self.assertEqual(r["best_k_by_errors"], [8])

    def test_sparse_equivalence_reported(self) -> None:
        r = analyze_trials(SPEC, matrix(3))
        classes = r["candidate_equivalence_classes"]
        first = next(x for x in classes if 1 in x["candidate_k"])
        self.assertEqual(first["candidate_k"], [1,2,3,4,5])

    def test_systematic_invalid_blocks_support(self) -> None:
        rows = matrix(7)
        for t in rows:
            if t["m"] == 7 and t["block"] in {0,1}:
                t["valid_state"] = False
                t["target_state"] = "INVALID"
                t["invalid_reason"] = "synthetic-invalid"
        r = analyze_trials(SPEC, rows)
        self.assertTrue(r["systematic_invalid"])
        self.assertNotEqual(r["decision"], "SUPPORT_CALIBRATED_K7")

    def test_worker_compiles(self) -> None:
        gcc = shutil.which("gcc")
        if not gcc:
            self.skipTest("gcc unavailable")
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "worker"
            subprocess.run([
                gcc, "-O2", "-Wall", "-Wextra", "-std=c11",
                str(ROOT / "experiments/memcg005_worker.c"),
                "-o", str(out),
            ], check=True)
            self.assertTrue(out.exists())


if __name__ == "__main__":
    unittest.main()
