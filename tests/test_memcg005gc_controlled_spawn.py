from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

from finite_ram_lab.memcg005gc_controlled_spawn import (
    analyze,
    arm_for,
    classify_failure,
    expected_pattern,
)


ROOT = Path(__file__).resolve().parents[1]
SPEC = json.loads(
    (
        ROOT
        / "specs/MEMCG-005G-C-PTE-PRECONDITIONED-SPAWN-v2.json"
    ).read_text(encoding="utf-8")
)


def touch(
    token: str,
    *,
    cpu: int = 7,
    worker_error: int = 0,
    vmpte_delta: int = 0,
) -> dict:
    delta = 0.0 if token == "ZERO" else 64.0 if token == "Q64" else 1.0
    return {
        "delta_pages": delta,
        "vmpte_delta_kib": vmpte_delta,
        "observed_cpu": cpu,
        "worker_error": worker_error,
    }


def row(
    block: int,
    identity: int,
    *,
    exact: bool = True,
) -> dict:
    arm = arm_for(SPEC, block, identity)
    pattern = expected_pattern(arm["id"])
    observed = [touch(x) for x in pattern]
    failure = None
    if not exact:
        observed[-1] = touch("ZERO")
        failure = "NEXT_PHASE_MISMATCH"
    return {
        "block": block,
        "identity": identity,
        "arm_id": arm["id"],
        "primer_status": "FOUND",
        "primer_touch_number": 1,
        "exact_recovery": exact,
        "failure_class": failure,
        "geometry": {
            "guard_cpu_match": True,
            "same_pte_table": True,
        },
        "stock_cpu": 7,
        "bait_touches": [],
        "observed_pattern_touches": observed,
    }


class ControlledSpawnTests(unittest.TestCase):
    def test_arm_balance(self) -> None:
        for block in range(SPEC["runner_blocks"]):
            ids = [
                arm_for(SPEC, block, identity)["id"]
                for identity in range(SPEC["identities_per_block"])
            ]
            self.assertEqual(ids.count("b62"), 3)
            self.assertEqual(ids.count("b63"), 3)
            self.assertEqual(ids.count("b64"), 3)

    def test_expected_patterns(self) -> None:
        self.assertEqual(expected_pattern("b62"), ["ZERO", "ZERO", "Q64"])
        self.assertEqual(expected_pattern("b63"), ["ZERO", "Q64"])
        self.assertEqual(expected_pattern("b64"), ["Q64"])

    def test_classifier_exact_b63(self) -> None:
        candidate = {
            "arm_id": "b63",
            "geometry": {
                "guard_cpu_match": True,
                "same_pte_table": True,
            },
            "stock_cpu": 7,
            "primer_status": "FOUND",
            "bait_touches": [touch("ZERO") for _ in range(62)],
            "observed_pattern_touches": [
                touch("ZERO"),
                touch("Q64"),
            ],
        }
        self.assertIsNone(classify_failure(SPEC, candidate))

    def test_classifier_catches_pte_contamination(self) -> None:
        candidate = {
            "arm_id": "b63",
            "geometry": {
                "guard_cpu_match": True,
                "same_pte_table": True,
            },
            "stock_cpu": 7,
            "primer_status": "FOUND",
            "bait_touches": [touch("ZERO", vmpte_delta=4)],
            "observed_pattern_touches": [
                touch("ZERO"),
                touch("Q64"),
            ],
        }
        self.assertEqual(
            classify_failure(SPEC, candidate),
            "PTE_CONTAMINATED",
        )

    def test_classifier_catches_cpu_error(self) -> None:
        candidate = {
            "arm_id": "b64",
            "geometry": {
                "guard_cpu_match": True,
                "same_pte_table": True,
            },
            "stock_cpu": 7,
            "primer_status": "FOUND",
            "bait_touches": [],
            "observed_pattern_touches": [
                touch("Q64", cpu=8),
            ],
        }
        self.assertEqual(
            classify_failure(SPEC, candidate),
            "CPU_OR_WORKER_ERROR",
        )

    def test_analyze_complete_matrix(self) -> None:
        rows = [
            row(block, identity)
            for block in range(SPEC["runner_blocks"])
            for identity in range(SPEC["identities_per_block"])
        ]
        result = analyze(SPEC, rows)
        self.assertEqual(result["overall"]["n"], 72)
        self.assertEqual(result["overall"]["exact_recovery"], 72)
        for arm in ("b62", "b63", "b64"):
            self.assertEqual(result["by_arm"][arm]["n"], 24)
            self.assertEqual(result["by_arm"][arm]["exact_recovery"], 24)

    def test_worker_compiles(self) -> None:
        worker = ROOT / "experiments/memcg005gc_spawn_worker.c"
        subprocess.run(
            [
                "gcc",
                "-Wall",
                "-Wextra",
                "-std=c11",
                "-fsyntax-only",
                str(worker),
            ],
            check=True,
            capture_output=True,
            text=True,
        )


if __name__ == "__main__":
    unittest.main()
