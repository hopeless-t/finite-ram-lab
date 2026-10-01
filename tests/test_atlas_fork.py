from __future__ import annotations

import unittest

from finite_ram_lab.atlas_fork import (
    AtlasForkConfig,
    AtlasForkGate,
    cosine_similarity,
    nearest_landmark_familiarity,
)


class AtlasForkTests(unittest.TestCase):
    def test_source_default_gate_constants(self):
        cfg = AtlasForkConfig()
        self.assertEqual(cfg.calibration_batches, 50)
        self.assertAlmostEqual(cfg.familiarity_ratio, 0.85)
        self.assertEqual(cfg.consecutive_below, 3)

    def test_baseline_freezes_after_exact_calibration_window(self):
        gate = AtlasForkGate(AtlasForkConfig(calibration_batches=3))
        gate.observe(1.0)
        gate.observe(0.8)
        self.assertIsNone(gate.baseline_familiarity)
        row = gate.observe(1.2)
        self.assertAlmostEqual(gate.baseline_familiarity, 1.0)
        self.assertAlmostEqual(row.threshold, 0.85)

    def test_two_low_batches_do_not_fork_but_are_withheld(self):
        gate = AtlasForkGate(AtlasForkConfig(calibration_batches=2))
        gate.observe(1.0)
        gate.observe(1.0)
        a = gate.observe(0.84)
        b = gate.observe(0.83)
        self.assertFalse(a.forked)
        self.assertFalse(b.forked)
        self.assertEqual(a.learning_disposition, "WITHHOLD")
        self.assertEqual(b.below_streak, 2)

    def test_third_consecutive_low_batch_forks_and_resets_calibration(self):
        gate = AtlasForkGate(AtlasForkConfig(calibration_batches=2))
        gate.observe(1.0)
        gate.observe(1.0)
        gate.observe(0.84)
        gate.observe(0.83)
        row = gate.observe(0.82)
        self.assertTrue(row.forked)
        self.assertEqual(row.phase, "FORK")
        self.assertEqual(gate.world_index, 1)
        self.assertIsNone(gate.baseline_familiarity)
        next_row = gate.observe(0.82)
        self.assertEqual(next_row.phase, "CALIBRATE")
        self.assertEqual(next_row.world_index, 1)

    def test_stable_batch_breaks_suspect_streak(self):
        gate = AtlasForkGate(AtlasForkConfig(calibration_batches=1))
        gate.observe(1.0)
        gate.observe(0.84)
        row = gate.observe(0.90)
        self.assertEqual(row.phase, "STABLE")
        self.assertEqual(row.below_streak, 0)

    def test_nearest_landmark_familiarity(self):
        self.assertAlmostEqual(cosine_similarity([1, 0], [1, 0]), 1.0)
        score = nearest_landmark_familiarity(
            [[1, 0], [0, 1]],
            [[1, 0], [0, 1]],
        )
        self.assertAlmostEqual(score, 1.0)


if __name__ == "__main__":
    unittest.main()
