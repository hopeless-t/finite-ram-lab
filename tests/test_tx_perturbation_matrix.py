from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from finite_ram_lab.tx_perturbation_matrix import (
    ARM_ORDER,
    _bind_owner_probe,
    _close_owner_probe,
    _prepare_owner_probe_global,
    _pte_escape_index,
    _single_helper_scrub_budget,
    aggregate,
)





PROFILE_OK = """
frl_refill_stock 100 12
frl_pc_try64 100 0
frl_pc_uncharge_owner 80 0
frl_drain_stock 20 2
"""

class TxPerturbationMatrixTests(unittest.TestCase):
    def test_owner_probe_lifecycle_is_epoch_scoped(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            trace = root / "trace"
            probe = root / "events" / "kprobes" / "frl_pc_uncharge_owner"
            probe.mkdir(parents=True)
            for name in ["filter", "enable", "trigger"]:
                (probe / name).write_text("", encoding="utf-8")

            _prepare_owner_probe_global(trace)
            self.assertEqual(
                (probe / "filter").read_text(encoding="utf-8"),
                "0\n",
            )
            self.assertEqual(
                (probe / "enable").read_text(encoding="utf-8"),
                "1\n",
            )

            _bind_owner_probe(trace, "0xabc")
            self.assertEqual(
                (probe / "filter").read_text(encoding="utf-8"),
                "counter == 0xabc\n",
            )
            self.assertEqual(
                (probe / "trigger").read_text(encoding="utf-8"),
                "stacktrace\n",
            )

            _close_owner_probe(trace)
            self.assertEqual(
                (probe / "enable").read_text(encoding="utf-8"),
                "0\n",
            )
            self.assertEqual(
                (probe / "filter").read_text(encoding="utf-8"),
                "counter == 0\n",
            )
            self.assertEqual(
                (probe / "trigger").read_text(encoding="utf-8"),
                "!stacktrace\n",
            )

    def test_single_helper_scrub_budget_preserves_trigger_stock(self) -> None:
        self.assertEqual(_single_helper_scrub_budget(14), 49)
        with self.assertRaises(ValueError):
            _single_helper_scrub_budget(63)

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
                        "challenge_classification_pass": True,
                        "recovery_pass": True,
                        "completion_pass": True,
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

            (root / "kprobe-profile.txt").write_text(
                PROFILE_OK,
                encoding="utf-8",
            )
            result = aggregate(
                {"experiment_id": "TX-PERTURBATION-MATRIX-v1"},
                root,
            )

        self.assertEqual(result["trial_count"], 16)
        self.assertEqual(result["challenge_pass_count"], 16)
        self.assertEqual(result["completion_pass_count"], 16)
        self.assertEqual(result["target_fail"], 0)
        self.assertTrue(result["matrix_pass"])
        self.assertTrue(result["end_to_end_pass"])
        self.assertTrue(result["probe_coverage"]["coverage_pass"])
        self.assertTrue(result["fully_observed_matrix_pass"])
        for arm in ARM_ORDER:
            self.assertEqual(result["by_arm"][arm]["n"], 4)
            self.assertEqual(result["by_arm"][arm]["pass"], 4)

    def test_probe_miss_blocks_fully_observed_pass_only(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for block in range(4):
                for identity, arm in enumerate(ARM_ORDER):
                    trial = {
                        "arm": arm,
                        "challenge_pass": True,
                        "challenge_classification_pass": True,
                        "recovery_pass": True,
                        "completion_pass": True,
                        "final_state": "SUCCESS",
                        "reprimes": 0,
                        "epochs": [{"state_after": "SUCCESS"}],
                    }
                    (root / f"trial-{block}-{identity}.json").write_text(
                        json.dumps(trial),
                        encoding="utf-8",
                    )
            (root / "kprobe-profile.txt").write_text(
                PROFILE_OK.replace(
                    "frl_pc_uncharge_owner 80 0",
                    "frl_pc_uncharge_owner 80 1",
                ),
                encoding="utf-8",
            )
            result = aggregate(
                {"experiment_id": "TX-PERTURBATION-MATRIX-v1"},
                root,
            )

        self.assertTrue(result["matrix_pass"])
        self.assertFalse(result["probe_coverage"]["coverage_pass"])
        self.assertFalse(result["fully_observed_matrix_pass"])

    def test_one_failed_challenge_fails_matrix(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for block in range(4):
                for identity, arm in enumerate(ARM_ORDER):
                    passed = not (block == 2 and arm == "RELEASE_ONLY")
                    trial = {
                        "arm": arm,
                        "challenge_pass": passed,
                        "challenge_classification_pass": passed,
                        "recovery_pass": passed,
                        "completion_pass": passed,
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


    def test_challenge_can_pass_while_recovery_completion_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for block in range(4):
                for identity, arm in enumerate(ARM_ORDER):
                    recovery_ok = not (
                        block == 3 and arm == "PTE_GROWTH"
                    )
                    trial = {
                        "arm": arm,
                        "challenge_pass": True,
                        "challenge_classification_pass": True,
                        "recovery_pass": recovery_ok,
                        "completion_pass": recovery_ok,
                        "final_state": (
                            "SUCCESS" if recovery_ok else "INVALIDATED"
                        ),
                        "reprimes": (
                            1
                            if arm in {"UNEXPECTED_REFILL", "PTE_GROWTH"}
                            else 0
                        ),
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

        self.assertEqual(result["challenge_pass_count"], 16)
        self.assertEqual(result["completion_pass_count"], 15)
        self.assertTrue(result["matrix_pass"])
        self.assertFalse(result["end_to_end_pass"])



if __name__ == "__main__":
    unittest.main()
