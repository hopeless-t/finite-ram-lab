from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from finite_ram_lab.wheel_projection import HOT_MODULES_V1


class WheelProjectionTests(unittest.TestCase):
    def test_hotset_is_small_and_operational(self) -> None:
        self.assertLessEqual(len(HOT_MODULES_V1), 10)
        self.assertIn("finite_ram_lab/cli.py", HOT_MODULES_V1)
        self.assertIn("finite_ram_lab/adaptive_cache_engine.py", HOT_MODULES_V1)


if __name__ == "__main__":
    unittest.main()
