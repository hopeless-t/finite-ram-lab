from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class StealGovernorToyTests(unittest.TestCase):
    def test_hysteresis_reduces_noisy_threshold_chatter(self) -> None:
        r = subprocess.run(
            [sys.executable, str(ROOT / "analysis" / "steal_governor_hysteresis_toy.py")],
            check=False, capture_output=True, text=True,
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("STEAL_GOVERNOR_HYSTERESIS_TOY=PASS", r.stdout)
        self.assertIn('"hysteresis_transitions":0', r.stdout)

if __name__ == "__main__":
    unittest.main()
