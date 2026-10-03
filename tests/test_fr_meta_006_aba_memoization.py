from __future__ import annotations

import unittest

from finite_ram_lab.fr_meta_006_aba_memoization import run_panel


class AbaMemoizationTests(unittest.TestCase):
    def test_panel(self) -> None:
        result = run_panel()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(
            result["decision"],
            "MEMOIZE_DETERMINISTIC_SEGMENT_MEANS",
        )
        self.assertFalse(result["monte_carlo"]["used"])
        self.assertEqual(result["baseline_segment_evaluations"], 98304)
        self.assertEqual(result["candidate_unique_segment_means"], 40960)
        self.assertGreater(result["structural_reduction_fraction"], 0.58)


if __name__ == "__main__":
    unittest.main()
