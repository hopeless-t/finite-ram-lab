from __future__ import annotations

import tempfile
import unittest

from finite_ram_lab.meta_qualifier import discover_modules, qualify_changed


class MetaQualifierTests(unittest.TestCase):
    def test_discovery_is_convention_bounded(self) -> None:
        paths = [
            "src/finite_ram_lab/fr_meta_005_qualification_fusion.py",
            "src/finite_ram_lab/fr_loop_speed_governor.py",
            "docs/FR-META-005.md",
        ]
        self.assertEqual(
            discover_modules(paths),
            ["fr_meta_005_qualification_fusion"],
        )

    def test_changed_module_is_qualified_and_written(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            summary = qualify_changed(
                ["src/finite_ram_lab/fr_meta_005_qualification_fusion.py"],
                tmp,
            )
            self.assertEqual(summary["status"], "PASS")
            self.assertEqual(summary["qualified_count"], 1)
            self.assertEqual(
                summary["modules"],
                ["fr_meta_005_qualification_fusion"],
            )

    def test_no_meta_module_is_clean_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            summary = qualify_changed(["README.md"], tmp)
            self.assertEqual(summary["status"], "PASS")
            self.assertEqual(summary["qualified_count"], 0)


if __name__ == "__main__":
    unittest.main()
