import unittest

from finite_ram_lab.val_replicate import make_block_schedule


class ValReplicateTests(unittest.TestCase):
    def test_block_schedule_complete(self):
        spec = {
            "memory_high_mib": [160, 164, 168],
            "repeats_per_level": 2,
            "base_schedule_seed": 100,
        }
        rows = make_block_schedule(spec, 3)
        self.assertEqual(len(rows), 6)
        pairs = {(r["memory_high_mib"], r["repeat"]) for r in rows}
        self.assertEqual(len(pairs), 6)

    def test_different_blocks_use_different_order(self):
        spec = {
            "memory_high_mib": [160, 164, 168, 172],
            "repeats_per_level": 2,
            "base_schedule_seed": 100,
        }
        a = make_block_schedule(spec, 0)
        b = make_block_schedule(spec, 1)
        self.assertNotEqual(a, b)


if __name__ == "__main__":
    unittest.main()
