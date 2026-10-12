from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest


class FastCliTests(unittest.TestCase):
    def run_cli(self, *args: str) -> dict:
        env = dict(os.environ)
        env["PYTHONPATH"] = "src"
        proc = subprocess.run(
            [sys.executable, "-m", "finite_ram_lab", *args],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        return json.loads(proc.stdout)

    def test_doctor_fast_path(self) -> None:
        self.assertEqual(self.run_cli("cache-doctor")["engine"], "adaptive-cache-v1")

    def test_analyze_fast_path(self) -> None:
        data = self.run_cli("cache-analyze", "--length", "300", "--universe", "29", "--capacity-anchor", "7")
        self.assertEqual(data["engine"], "adaptive-cache-v1")

    def test_general_help_still_works(self) -> None:
        env = dict(os.environ)
        env["PYTHONPATH"] = "src"
        proc = subprocess.run([sys.executable, "-m", "finite_ram_lab", "--help"], env=env, stdout=subprocess.PIPE, text=True, check=True)
        self.assertIn("Finite RAM Lab", proc.stdout)


if __name__ == "__main__":
    unittest.main()
