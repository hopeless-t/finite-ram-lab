import unittest

from finite_ram_lab.char_sweep import make_schedule


class CharSweepTests(unittest.TestCase):
    def test_schedule_is_deterministic_and_complete(self):
        spec = {
            "memory_high_mib": [96, 128, 192],
            "repeats_per_level": 4,
            "schedule_seed": 42,
        }
        a = make_schedule(spec)
        b = make_schedule(spec)
        self.assertEqual(a, b)
        self.assertEqual(len(a), 12)

        pairs = {
            (
                row["memory_high_mib"],
                row["repeat"],
            )
            for row in a
        }
        self.assertEqual(len(pairs), 12)

    def test_schedule_contains_every_repeat_per_level(self):
        spec = {
            "memory_high_mib": [100, 200],
            "repeats_per_level": 3,
            "schedule_seed": 7,
        }
        rows = make_schedule(spec)
        for level in (100, 200):
            repeats = sorted(
                row["repeat"]
                for row in rows
                if row["memory_high_mib"] == level
            )
            self.assertEqual(repeats, [0, 1, 2])


if __name__ == "__main__":
    unittest.main()
