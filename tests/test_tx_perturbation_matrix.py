from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from finite_ram_lab.tx_perturbation_matrix import (
    ARM_ORDER,
    _pte_escape_index,
    aggregate,
)


class TxPerturbationMatrixTests(unittest.TestCase):
    def test_pte_escape_index_selects_different_table(self) -> None:
        geometry = {
            "page_size": 4096,
            "region_addr": 0x10000000,
            "guard_index": 0,
            "safe_start": 0,
            "safe_len": 192,
        }
        index = _pte_escape_index(geometry, max_pages=1024)
        base_page = geometry["region_addr"] // geometry["page_size"]
        guard_table = (base_page + geometry["guard_index"]) // 512
        candidate_table = (base_page + index) // 512
        self.assertNotEqual(candidate_table, guard_table)
        self.assertFalse(
            geometry["safe_start"]
            <= index
            < geometry["safe_start"] + geometry["safe_len"]
        )

    def test_all_16_challenges_pass_matrix(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for block in range(4):
                for identity, arm in enumerate(ARM_ORDER):
                    trial = {
                        "arm": arm,
                        "challenge_pass": True,
                        "final_state": "SUCCESS",
                        "reprimes": 1
                        if arm in {"UNEXPECTED_REFILL", "PTE_GROWTH"}
                        else 0,
                        "epochs": [
                            {"state_after": "SUCCESS"},
                        ],
                    }
                    (root / f"trial-{block}-{identity}.json").write_text(
                        json.dumps(trial),
                        encoding="utf-8",
                    )

            result = aggregate(
                {"experiment_id": "TX-PERTURBATION-MATRIX-v1"},
                root,
            )

        self.assertEqual(result["trial_count"], 16)
        self.assertEqual(result["challenge_pass_count"], 16)
        self.assertEqual(result["target_fail"], 0)
        self.assertTrue(result["matrix_pass"])
        for arm in ARM_ORDER:
            self.assertEqual(result["by_arm"][arm]["n"], 4)
            self.assertEqual(result["by_arm"][arm]["pass"], 4)

    def test_one_failed_challenge_fails_matrix(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for block in range(4):
                for identity, arm in enumerate(ARM_ORDER):
                    passed = not (block == 2 and arm == "RELEASE_ONLY")
                    trial = {
                        "arm": arm,
                        "challenge_pass": passed,
                        "final_state": "SUCCESS" if passed else "INVALIDATED",
                        "reprimes": 0,
                        "epochs": [
                            {
                                "state_after": (
                                    "SUCCESS" if passed else "INVALIDATED"
                                )
                            }
                        ],
                    }
                    (root / f"trial-{block}-{identity}.json").write_text(
                        json.dumps(trial),
                        encoding="utf-8",
                    )

            result = aggregate(
                {"experiment_id": "TX-PERTURBATION-MATRIX-v1"},
                root,
            )

        self.assertEqual(result["challenge_pass_count"], 15)
        self.assertFalse(result["matrix_pass"])


if __name__ == "__main__":
    unittest.main()
