from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest


class CacheCliTests(unittest.TestCase):
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

    def test_doctor(self) -> None:
        data = self.run_cli("cache-doctor")
        self.assertEqual(data["engine"], "adaptive-cache-v1")
        self.assertIn("full_lru_curve", data["capabilities"])

    def test_analyze(self) -> None:
        data = self.run_cli(
            "cache-analyze",
            "--length", "300",
            "--universe", "29",
            "--capacity-anchor", "7",
            "--capacities", "3,7,17",
        )
        self.assertEqual(data["capacities"], [3, 7, 17])
        self.assertEqual(len(data["compare"]), 3)

    def test_benchmark(self) -> None:
        data = self.run_cli(
            "cache-benchmark",
            "--length", "300",
            "--universe", "29",
            "--capacity-anchor", "7",
            "--anchor-capacity", "7",
            "--capacities", "3,7,17",
            "--repeats", "2",
        )
        self.assertEqual(data["parity"]["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
