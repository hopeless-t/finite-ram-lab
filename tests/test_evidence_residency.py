from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from finite_ram_lab.evidence_residency import (
    EvidenceResidencyError,
    build_manifest,
    parse_storage_ref,
    verify_manifest,
    write_manifest,
)


class EvidenceResidencyTests(unittest.TestCase):
    def _bundle(self, root: Path) -> Path:
        bundle = root / "bundle"
        (bundle / "nested").mkdir(parents=True)
        (bundle / "a.txt").write_text("alpha\n", encoding="utf-8")
        (bundle / "nested" / "b.bin").write_bytes(b"\x00\x01\x02")
        return bundle

    def test_manifest_and_verify_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle = self._bundle(root)
            manifest_path = bundle / "evidence-manifest.json"

            manifest = write_manifest(
                bundle,
                manifest_path,
                experiment_id="EXP-TEST",
                run_id="run-1",
                source_commit="deadbeef",
                residency_tier="COLD",
                storage_refs=[
                    {
                        "tier": "COLD",
                        "provider": "google-drive",
                        "locator": "frl-cold/EXP-TEST/run-1",
                    }
                ],
            )

            self.assertEqual(manifest["file_count"], 2)
            self.assertEqual(manifest["total_bytes"], 9)
            self.assertEqual(
                [row["path"] for row in manifest["files"]],
                ["a.txt", "nested/b.bin"],
            )

            result = verify_manifest(bundle, manifest_path)
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["missing"], [])
            self.assertEqual(result["mismatched"], [])
            self.assertEqual(result["extra"], [])

    def test_content_set_digest_is_stable(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle = self._bundle(root)

            first = build_manifest(
                bundle,
                experiment_id="EXP-TEST",
                run_id="run-1",
                source_commit="deadbeef",
                residency_tier="HOT",
            )
            second = build_manifest(
                bundle,
                experiment_id="EXP-TEST",
                run_id="run-1",
                source_commit="deadbeef",
                residency_tier="COLD",
            )

            self.assertEqual(
                first["content_set_sha256"],
                second["content_set_sha256"],
            )
            self.assertEqual(first["files"], second["files"])

    def test_tamper_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle = self._bundle(root)
            manifest_path = root / "manifest.json"
            write_manifest(
                bundle,
                manifest_path,
                experiment_id="EXP-TEST",
                run_id="run-1",
                source_commit="deadbeef",
                residency_tier="WARM",
            )

            (bundle / "a.txt").write_text("tampered\n", encoding="utf-8")
            result = verify_manifest(bundle, manifest_path)
            self.assertEqual(result["status"], "FAIL")
            self.assertEqual(
                [row["path"] for row in result["mismatched"]],
                ["a.txt"],
            )

    def test_missing_and_extra_are_detected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle = self._bundle(root)
            manifest_path = root / "manifest.json"
            write_manifest(
                bundle,
                manifest_path,
                experiment_id="EXP-TEST",
                run_id="run-1",
                source_commit="deadbeef",
                residency_tier="HOT",
            )

            (bundle / "a.txt").unlink()
            (bundle / "extra.txt").write_text("extra\n", encoding="utf-8")
            result = verify_manifest(bundle, manifest_path)
            self.assertEqual(result["status"], "FAIL")
            self.assertEqual(result["missing"], ["a.txt"])
            self.assertEqual(result["extra"], ["extra.txt"])

    def test_allow_extra_only_relaxes_extra_files(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle = self._bundle(root)
            manifest_path = root / "manifest.json"
            write_manifest(
                bundle,
                manifest_path,
                experiment_id="EXP-TEST",
                run_id="run-1",
                source_commit="deadbeef",
                residency_tier="HOT",
            )

            (bundle / "extra.txt").write_text("extra\n", encoding="utf-8")
            result = verify_manifest(
                bundle,
                manifest_path,
                allow_extra=True,
            )
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["extra"], ["extra.txt"])

    def test_storage_ref_parser(self) -> None:
        ref = parse_storage_ref(
            "cold:google-drive:frl-cold/MEMCG-005G-F/36577573774"
        )
        self.assertEqual(
            ref,
            {
                "tier": "COLD",
                "provider": "google-drive",
                "locator": "frl-cold/MEMCG-005G-F/36577573774",
            },
        )

        with self.assertRaises(EvidenceResidencyError):
            parse_storage_ref("google-drive:missing-tier")


if __name__ == "__main__":
    unittest.main()
