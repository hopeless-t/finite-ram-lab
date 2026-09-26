import unittest

import numpy as np

from finite_ram_lab.char002_study import (
    exact_signflip_two_sided,
    schedule_rows,
)


class Char002Tests(unittest.TestCase):
    def test_schedule_is_complete_and_balanced(self):
        spec = {
            "memory_high_mib": [160, 162],
            "base_schedule_seed": 7,
            "families": {
                "separate": {
                    "creation_orders": ["AB", "BA"],
                    "fault_orders": ["AB", "BA"],
                },
                "shared": {
                    "fault_orders": ["lower_upper", "upper_lower"],
                },
            },
        }
        rows = schedule_rows(spec, 3)
        self.assertEqual(len(rows), 12)
        cells = {
            (
                r["family"],
                r["memory_high_mib"],
                r["creation_order"],
                r["fault_order"],
            )
            for r in rows
        }
        self.assertEqual(len(cells), 12)

    def test_schedule_is_deterministic_per_block(self):
        spec = {
            "memory_high_mib": [160, 162],
            "base_schedule_seed": 7,
            "families": {
                "separate": {
                    "creation_orders": ["AB", "BA"],
                    "fault_orders": ["AB", "BA"],
                },
                "shared": {
                    "fault_orders": ["lower_upper", "upper_lower"],
                },
            },
        }
        self.assertEqual(schedule_rows(spec, 1), schedule_rows(spec, 1))
        self.assertNotEqual(schedule_rows(spec, 1), schedule_rows(spec, 2))

    def test_exact_signflip_known_answer(self):
        result = exact_signflip_two_sided(np.array([1.0, 1.0]))
        self.assertEqual(result["exact_permutations"], 4)
        self.assertAlmostEqual(result["two_sided_p"], 0.5)


if __name__ == "__main__":
    unittest.main()
