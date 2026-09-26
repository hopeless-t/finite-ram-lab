from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from finite_ram_lab.sig001_calibration import calibrate


PROTOCOL = Path("specs/SIG-001-CAL-PROTOCOL-v1.json")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows)
    )


def _dataset(
    root: Path,
    *,
    n_misaligned: int,
    act_misaligned: int,
    n_aligned: int,
    noact_aligned: int,
) -> tuple[Path, Path, Path]:
    predictions: list[dict] = []
    outcomes: list[dict] = []

    index = 0
    for i in range(n_misaligned):
        decision = "ACT" if i < act_misaligned else "ABSTAIN"
        predictions.append(
            {
                "schema_version": 1,
                "event_id": f"e{index}",
                "independence_unit_id": f"u{index}",
                "decision": decision,
                "prediction_time_ns": 2 * index,
            }
        )
        outcomes.append(
            {
                "schema_version": 1,
                "event_id": f"e{index}",
                "true_state": "misaligned",
                "outcome_time_ns": 2 * index + 1,
            }
        )
        index += 1

    for i in range(n_aligned):
        decision = "NO_ACT" if i < noact_aligned else "ACT"
        predictions.append(
            {
                "schema_version": 1,
                "event_id": f"e{index}",
                "independence_unit_id": f"u{index}",
                "decision": decision,
                "prediction_time_ns": 2 * index,
            }
        )
        outcomes.append(
            {
                "schema_version": 1,
                "event_id": f"e{index}",
                "true_state": "aligned",
                "outcome_time_ns": 2 * index + 1,
            }
        )
        index += 1

    pred_path = root / "predictions.jsonl"
    out_path = root / "outcomes.jsonl"
    manifest_path = root / "manifest.json"
    _write_jsonl(pred_path, predictions)
    _write_jsonl(out_path, outcomes)

    digest = hashlib.sha256(pred_path.read_bytes()).hexdigest()
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "protocol_id": "SIG-001-CAL-PROTOCOL-v1",
                "provider_id": "test-provider",
                "provider_version": "v1",
                "decision_rule_id": "fixed-rule",
                "epoch_id": "epoch-1",
                "environment_digest": "sha256:" + "0" * 64,
                "prediction_horizon_id": "next-phase",
                "predictions_sha256": digest,
                "external_seal_ref": "git:test-seal",
            }
        )
    )
    return manifest_path, pred_path, out_path


class Sig001CalibrationTests(unittest.TestCase):
    def test_strong_provider_certifies(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest, predictions, outcomes = _dataset(
                root,
                n_misaligned=250,
                act_misaligned=230,
                n_aligned=750,
                noact_aligned=735,
            )
            result = calibrate(
                protocol_path=PROTOCOL,
                manifest_path=manifest,
                predictions_path=predictions,
                outcomes_path=outcomes,
            )
            self.assertEqual(result["validation_status"], "PASS")
            self.assertEqual(result["decision"], "CERTIFIED")
            self.assertTrue(result["primary"]["certified"])

    def test_unsafe_provider_not_certified(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest, predictions, outcomes = _dataset(
                root,
                n_misaligned=200,
                act_misaligned=180,
                n_aligned=1800,
                noact_aligned=1350,
            )
            result = calibrate(
                protocol_path=PROTOCOL,
                manifest_path=manifest,
                predictions_path=predictions,
                outcomes_path=outcomes,
            )
            self.assertEqual(result["decision"], "NOT_CERTIFIED")
            self.assertFalse(result["primary"]["certified"])

    def test_prediction_digest_mismatch_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest, predictions, outcomes = _dataset(
                root,
                n_misaligned=10,
                act_misaligned=9,
                n_aligned=10,
                noact_aligned=10,
            )
            predictions.write_text(predictions.read_text() + "{}\n")
            with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                calibrate(
                    protocol_path=PROTOCOL,
                    manifest_path=manifest,
                    predictions_path=predictions,
                    outcomes_path=outcomes,
                )

    def test_duplicate_independence_unit_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest, predictions, outcomes = _dataset(
                root,
                n_misaligned=2,
                act_misaligned=2,
                n_aligned=2,
                noact_aligned=2,
            )
            rows = [
                json.loads(line)
                for line in predictions.read_text().splitlines()
            ]
            rows[1]["independence_unit_id"] = rows[0][
                "independence_unit_id"
            ]
            _write_jsonl(predictions, rows)

            manifest_data = json.loads(manifest.read_text())
            manifest_data["predictions_sha256"] = hashlib.sha256(
                predictions.read_bytes()
            ).hexdigest()
            manifest.write_text(json.dumps(manifest_data))

            with self.assertRaisesRegex(
                ValueError, "duplicate independence_unit_id"
            ):
                calibrate(
                    protocol_path=PROTOCOL,
                    manifest_path=manifest,
                    predictions_path=predictions,
                    outcomes_path=outcomes,
                )

    def test_outcome_must_follow_prediction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest, predictions, outcomes = _dataset(
                root,
                n_misaligned=2,
                act_misaligned=2,
                n_aligned=2,
                noact_aligned=2,
            )
            rows = [
                json.loads(line)
                for line in outcomes.read_text().splitlines()
            ]
            rows[0]["outcome_time_ns"] = 0
            _write_jsonl(outcomes, rows)

            with self.assertRaisesRegex(ValueError, "not later"):
                calibrate(
                    protocol_path=PROTOCOL,
                    manifest_path=manifest,
                    predictions_path=predictions,
                    outcomes_path=outcomes,
                )

    def test_modified_protocol_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest, predictions, outcomes = _dataset(
                root,
                n_misaligned=2,
                act_misaligned=2,
                n_aligned=2,
                noact_aligned=2,
            )
            protocol = json.loads(PROTOCOL.read_text())
            protocol["familywise_alpha"] = 0.20
            modified = root / "protocol.json"
            modified.write_text(json.dumps(protocol))

            with self.assertRaisesRegex(
                ValueError, "frozen v1 contract"
            ):
                calibrate(
                    protocol_path=modified,
                    manifest_path=manifest,
                    predictions_path=predictions,
                    outcomes_path=outcomes,
                )


if __name__ == "__main__":
    unittest.main()
