import unittest

from finite_ram_lab.hyp002_study import schedule_rows


class Hyp002ScheduleTests(unittest.TestCase):
    def test_full_factorial_per_block(self):
        spec = {
            "memory_high_mib": [160, 162],
            "recent_identities": ["A", "B"],
            "hot_identities": ["A", "B"],
            "base_schedule_seed": 17,
        }
        rows = schedule_rows(spec, 3)
        self.assertEqual(len(rows), 8)

        cells = {
            (
                r["memory_high_mib"],
                r["recent_identity"],
                r["hot_identity"],
            )
            for r in rows
        }
        self.assertEqual(len(cells), 8)

    def test_schedule_deterministic(self):
        spec = {
            "memory_high_mib": [160, 162],
            "recent_identities": ["A", "B"],
            "hot_identities": ["A", "B"],
            "base_schedule_seed": 17,
        }
        self.assertEqual(
            schedule_rows(spec, 4),
            schedule_rows(spec, 4),
        )


if __name__ == "__main__":
    unittest.main()
