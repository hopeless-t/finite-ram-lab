from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from finite_ram_lab.label001 import analyze


def _write_fixture(path: Path) -> str:
    rows = [
        # block 0
        dict(block=0, memory_high_mib=160, aligned=False, arm="no_hint",
             hot_fraction=0.2, cold_fraction=0.8,
             hot_first16_fraction=0.2, cold_first16_fraction=0.8,
             hot_retouch_ms=100.0),
        dict(block=0, memory_high_mib=162, aligned=True, arm="no_hint",
             hot_fraction=0.8, cold_fraction=0.2,
             hot_first16_fraction=0.8, cold_first16_fraction=0.2,
             hot_retouch_ms=1.0),
        # block 1: one proxy error each direction
        dict(block=1, memory_high_mib=160, aligned=False, arm="no_hint",
             hot_fraction=0.7, cold_fraction=0.3,
             hot_first16_fraction=0.7, cold_first16_fraction=0.3,
             hot_retouch_ms=2.0),
        dict(block=1, memory_high_mib=162, aligned=True, arm="no_hint",
             hot_fraction=0.3, cold_fraction=0.7,
             hot_first16_fraction=0.3, cold_first16_fraction=0.7,
             hot_retouch_ms=80.0),
    ]
    pd.DataFrame(rows).to_csv(path, index=False)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _spec(digest: str) -> dict:
    return {
        "analysis_id": "LABEL-001",
        "source_run": 1,
        "source_artifact_id": 2,
        "source_artifact_name": "fixture",
        "source_artifact_sha256": "fixture",
        "source_member": "trials.csv",
        "source_member_sha256": digest,
        "required_arm": "no_hint",
        "required_pressures_mib": [160, 162],
        "expected_runner_blocks": 2,
        "expected_trials": 4,
        "cluster_bootstrap_resamples": 256,
        "cluster_bootstrap_seed": 7,
    }


class Label001Tests(unittest.TestCase):
    def test_confusion_and_mechanism(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "trials.csv"
            digest = _write_fixture(path)
            result = analyze(_spec(digest), path)
            c = result["primary_whole_region"]["confusion"]
            self.assertEqual((c["tp"], c["fp"], c["fn"], c["tn"]), (1, 1, 1, 1))
            self.assertEqual(result["status"], "PASS")
            self.assertLess(
                result["primary_whole_region"]["mechanism_association"]["point_spearman_rho"],
                0.0,
            )

    def test_digest_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "trials.csv"
            _write_fixture(path)
            spec = _spec("0" * 64)
            with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                analyze(spec, path)

    def test_intervention_arms_do_not_enter_natural_label(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "trials.csv"
            digest = _write_fixture(path)
            df = pd.read_csv(path)
            extra = df.iloc[[0]].copy()
            extra["arm"] = "wrong_pageout"
            pd.concat([df, extra], ignore_index=True).to_csv(path, index=False)
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            result = analyze(_spec(digest), path)
            self.assertEqual(result["selection"]["trials"], 4)

    def test_tie_is_ambiguous(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "trials.csv"
            digest = _write_fixture(path)
            df = pd.read_csv(path)
            df.loc[0, "hot_fraction"] = 0.5
            df.loc[0, "cold_fraction"] = 0.5
            df.to_csv(path, index=False)
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            result = analyze(_spec(digest), path)
            self.assertEqual(
                result["primary_whole_region"]["confusion"]["ambiguous"], 1
            )


if __name__ == "__main__":
    unittest.main()
