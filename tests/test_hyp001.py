import unittest

from finite_ram_lab.hyp001_study import schedule_rows


class Hyp001ScheduleTests(unittest.TestCase):
    def test_primary_is_exactly_balanced(self):
        spec = {
            "primary_level_mib": 164,
            "primary_repeats_per_arm_per_block": 6,
            "primary_arms": ["aligned", "misaligned"],
            "control_levels_mib": [160, 168],
            "base_schedule_seed": 11,
        }
        rows = schedule_rows(spec, 0)
        primary = [r for r in rows if r["memory_high_mib"] == 164]
        self.assertEqual(len(primary), 12)
        for arm in ("aligned", "misaligned"):
            arm_rows = [r for r in primary if r["arm"] == arm]
            self.assertEqual(len(arm_rows), 6)
            self.assertEqual(sum(r["recent_identity"] == "A" for r in arm_rows), 3)
            self.assertEqual(sum(r["recent_identity"] == "B" for r in arm_rows), 3)

    def test_controls_present(self):
        spec = {
            "primary_level_mib": 164,
            "primary_repeats_per_arm_per_block": 6,
            "primary_arms": ["aligned", "misaligned"],
            "control_levels_mib": [160, 168],
            "base_schedule_seed": 11,
        }
        rows = schedule_rows(spec, 2)
        self.assertEqual(sum(r["memory_high_mib"] == 160 for r in rows), 1)
        self.assertEqual(sum(r["memory_high_mib"] == 168 for r in rows), 1)


if __name__ == "__main__":
    unittest.main()
