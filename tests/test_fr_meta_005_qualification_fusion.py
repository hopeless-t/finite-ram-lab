from __future__ import annotations

import unittest

from finite_ram_lab.fr_meta_005_qualification_fusion import run_panel


class QualificationFusionTests(unittest.TestCase):
    def test_panel(self) -> None:
        result = run_panel()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(
            result["decision"],
            "FUSE_META_QUALIFICATION_INTO_GENERAL_CI",
        )
        self.assertFalse(result["monte_carlo"]["used"])
        self.assertAlmostEqual(result["exact"]["reduction_vs_historical"], 0.7)
        self.assertAlmostEqual(result["exact"]["reduction_vs_atomic_dedicated"], 0.25)


if __name__ == "__main__":
    unittest.main()
