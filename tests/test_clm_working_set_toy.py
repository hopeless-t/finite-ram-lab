from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ClmWorkingSetToyTests(unittest.TestCase):
    def test_expected_knee_moves_under_pressure_price(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "analysis" / "clm_working_set_toy.py")],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("CLM_WORKING_SET_TOY=PASS", result.stdout)
        self.assertIn('"best_k":20', result.stdout)
        self.assertIn('"best_k":9', result.stdout)


if __name__ == "__main__":
    unittest.main()
