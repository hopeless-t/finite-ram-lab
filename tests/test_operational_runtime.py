from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from finite_ram_lab.operational_runtime import activate_wheel, runtime_status


class OperationalRuntimeTests(unittest.TestCase):
    def test_rejects_nonwheel(self) -> None:
        with self.assertRaises(ValueError):
            activate_wheel(__file__, smoke=False)

    def test_empty_status(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "runtime"
            launcher = Path(td) / "bin" / "frl"
            status = runtime_status(root=root, launcher=launcher)
            self.assertEqual(status["artifact_count"], 0)
            self.assertIsNone(status["current"])
            self.assertIsNone(status["control"])

    def test_prune_unreachable_artifact(self) -> None:
        from finite_ram_lab.operational_runtime import prune_runtime

        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "runtime"
            artifacts = root / "artifacts"
            artifacts.mkdir(parents=True)
            keep = artifacts / "keep.whl"
            old = artifacts / "old.whl"
            keep.write_bytes(b"keep")
            old.write_bytes(b"old")
            current = root / "current.whl"
            current.symlink_to(Path("artifacts") / keep.name)
            dry = prune_runtime(root=root, apply=False)
            self.assertEqual(dry["candidate_count"], 1)
            self.assertTrue(old.exists())
            applied = prune_runtime(root=root, apply=True)
            self.assertEqual(len(applied["removed"]), 1)
            self.assertFalse(old.exists())
            self.assertTrue(keep.exists())

    def test_launcher_routes_runtime_to_control_plane(self) -> None:
        from finite_ram_lab.operational_runtime import _launcher_text

        text = _launcher_text(Path("/x/runtime"), "/usr/bin/python3")
        self.assertIn("runtime-*)", text)
        self.assertIn("control.whl", text)
        self.assertIn("current.whl", text)

    def test_runtime_benchmark_requires_active_source(self) -> None:
        from finite_ram_lab.operational_runtime import benchmark_runtime

        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(RuntimeError):
                benchmark_runtime(root=Path(td), launcher=Path(td) / "frl", loops=1, process_repeats=1)


if __name__ == "__main__":
    unittest.main()
