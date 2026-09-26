import unittest

import numpy as np

from finite_ram_lab.hyp003_study import (
    exact_signflip_one_sided,
    schedule_rows,
)


class Hyp003Tests(unittest.TestCase):
    def test_schedule_complete(self):
        spec = {
            "memory_high_mib": [160, 162],
            "fault_orders": ["lower_upper", "upper_lower"],
            "hot_positions": ["lower", "upper"],
            "base_schedule_seed": 11,
        }
        rows = schedule_rows(spec, 4)
        self.assertEqual(len(rows), 8)
        cells = {
            (
                r["memory_high_mib"],
                r["fault_order"],
                r["hot_position"],
            )
            for r in rows
        }
        self.assertEqual(len(cells), 8)

    def test_schedule_changes_by_block(self):
        spec = {
            "memory_high_mib": [160, 162],
            "fault_orders": ["lower_upper", "upper_lower"],
            "hot_positions": ["lower", "upper"],
            "base_schedule_seed": 11,
        }
        self.assertNotEqual(
            schedule_rows(spec, 1),
            schedule_rows(spec, 2),
        )

    def test_exact_signflip_known_answer(self):
        result = exact_signflip_one_sided(
            np.array([1.0, 1.0]),
            "greater",
        )
        self.assertEqual(result["exact_permutations"], 4)
        self.assertAlmostEqual(result["one_sided_p"], 0.25)


if __name__ == "__main__":
    unittest.main()
