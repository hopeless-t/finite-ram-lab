from __future__ import annotations

import unittest

from finite_ram_lab.frontier_resampling import (
    bootstrap_frontier_loss,
    leave_one_block_out_frontiers,
)


SMALL = {
    "0": {
        "a": {"peak": 1.0, "lat": 4.0},
        "b": {"peak": 2.0, "lat": 1.0},
    },
    "1": {
        "a": {"peak": 1.0, "lat": 3.0},
        "b": {"peak": 2.0, "lat": 2.0},
    },
    "2": {
        "a": {"peak": 1.0, "lat": 4.0},
        "b": {"peak": 2.0, "lat": 1.0},
    },
    "3": {
        "a": {"peak": 1.0, "lat": 3.0},
        "b": {"peak": 2.0, "lat": 2.0},
    },
}

LARGE = {
    "0": {
        "a": {"peak": 1.0, "lat": 1.0},
        "b": {"peak": 2.0, "lat": 2.0},
    },
    "1": {
        "a": {"peak": 1.0, "lat": 1.0},
        "b": {"peak": 2.0, "lat": 2.0},
    },
    "2": {
        "a": {"peak": 1.0, "lat": 1.0},
        "b": {"peak": 2.0, "lat": 2.0},
    },
    "3": {
        "a": {"peak": 1.0, "lat": 1.0},
        "b": {"peak": 2.0, "lat": 2.0},
    },
}


class FrontierResamplingTests(unittest.TestCase):
    def test_leave_one_out_frontier_is_stable_in_small_example(self):
        result = leave_one_block_out_frontiers(
            SMALL,
            ("peak", "lat"),
        )
        self.assertTrue(
            all(frontier == ("a", "b") for frontier in result.values())
        )

    def test_bootstrap_detects_target_loss(self):
        result = bootstrap_frontier_loss(
            SMALL,
            LARGE,
            ("peak", "lat"),
            target_plan_id="b",
            iterations=1000,
            seed=442,
        )
        self.assertGreater(result.loss_probability, 0.9)
        self.assertEqual(result.large_membership_probability, 0.0)

    def test_peak_only_has_no_target_membership(self):
        result = bootstrap_frontier_loss(
            SMALL,
            LARGE,
            ("peak",),
            target_plan_id="b",
            iterations=1000,
            seed=442,
        )
        self.assertEqual(result.loss_probability, 0.0)
        self.assertEqual(result.small_membership_probability, 0.0)
        self.assertEqual(result.large_membership_probability, 0.0)


if __name__ == "__main__":
    unittest.main()
