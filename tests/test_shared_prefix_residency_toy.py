from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class SharedPrefixResidencyToyTests(unittest.TestCase):
    def test_known_logical_savings(self) -> None:
        r = subprocess.run(
            [sys.executable, str(ROOT / "analysis" / "shared_prefix_residency_toy.py")],
            check=False, capture_output=True, text=True,
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("SHARED_PREFIX_RESIDENCY_TOY=PASS", r.stdout)
        self.assertIn('"logical_savings":0.75', r.stdout)

if __name__ == "__main__":
    unittest.main()
