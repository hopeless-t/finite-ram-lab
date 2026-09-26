import unittest

import numpy as np

from finite_ram_lab.exp003_study import (
    exact_signflip_one_sided,
    schedule_rows,
)


class Exp003Tests(unittest.TestCase):
    def _spec(self):
        return {
            "complete_repeats_per_block": 1,
            "memory_high_mib": [160, 162],
            "fault_orders": ["lower_upper", "upper_lower"],
            "hot_positions": ["lower", "upper"],
            "arms": [
                "correct_pageout",
                "no_hint",
                "wrong_pageout",
            ],
            "base_schedule_seed": 2026092634,
        }

    def test_schedule_complete_factorial(self):
        rows = schedule_rows(self._spec(), 0)
        self.assertEqual(len(rows), 24)
        cells = {
            (
                r["memory_high_mib"],
                r["fault_order"],
                r["hot_position"],
                r["arm"],
            )
            for r in rows
        }
        self.assertEqual(len(cells), 24)

    def test_schedule_has_balanced_alignment_strata(self):
        rows = schedule_rows(self._spec(), 2)
        aligned = 0
        misaligned = 0
        for r in rows:
            second = r["fault_order"].split("_")[1]
            if r["hot_position"] == second:
                aligned += 1
            else:
                misaligned += 1
        self.assertEqual(aligned, 12)
        self.assertEqual(misaligned, 12)

    def test_schedule_is_deterministic_per_block(self):
        self.assertEqual(
            schedule_rows(self._spec(), 3),
            schedule_rows(self._spec(), 3),
        )
        self.assertNotEqual(
            schedule_rows(self._spec(), 3),
            schedule_rows(self._spec(), 4),
        )

    def test_exact_signflip_known_answer_less(self):
        result = exact_signflip_one_sided(
            np.array([-1.0, -1.0]),
            "less",
        )
        self.assertEqual(result["exact_permutations"], 4)
        self.assertAlmostEqual(result["one_sided_p"], 0.25)
        self.assertLess(result["geometric_mean_ratio"], 1.0)

    def test_exact_signflip_known_answer_greater(self):
        result = exact_signflip_one_sided(
            np.array([1.0, 1.0]),
            "greater",
        )
        self.assertEqual(result["exact_permutations"], 4)
        self.assertAlmostEqual(result["one_sided_p"], 0.25)
        self.assertGreater(result["geometric_mean_ratio"], 1.0)


if __name__ == "__main__":
    unittest.main()
