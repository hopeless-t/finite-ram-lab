from __future__ import annotations

import unittest

from finite_ram_lab.location_shift import (
    PER_Q_ALPHA,
    analyze_location_shift,
    exact_two_sided_rank_sum_p,
)


def payload() -> dict:
    return {
        "schema": "finite-ram-lab.location-shift-input/v0.1",
        "provenance": {},
        "reference_batches": {
            "1": [1,2,3,4],
            "2": [10,11,12,13],
            "4": [20,21,22,23],
            "7": [30,31,32,33],
        },
        "future_batches": {
            "1": [1,2,3,4],
            "2": [10,11,12,13],
            "4": [100,101,102,103],
            "7": [30,31,32,33],
        },
        "caveat": "test",
    }


class LocationShiftTests(unittest.TestCase):
    def test_exact_rank_sum_detects_clear_shift(self):
        p, _, count = exact_two_sided_rank_sum_p(
            list(range(10)),
            list(range(100,108)),
        )
        self.assertLess(p, PER_Q_ALPHA)
        self.assertGreater(count, 0)

    def test_identical_groups_are_compatible(self):
        p, _, _ = exact_two_sided_rank_sum_p(
            [1,2,3,4],
            [1,2,3,4],
        )
        self.assertGreater(p, PER_Q_ALPHA)

    def test_analysis_flags_only_shifted_q(self):
        result = analyze_location_shift(payload())
        self.assertEqual(
            result["overall"]["classification"],
            "LOCATION_SHIFT_SUSPECT",
        )
        self.assertEqual(result["overall"]["suspect_q"], [4])
        q4 = next(row for row in result["rows"] if row["q"] == 4)
        self.assertEqual(q4["classification"], "LOCATION_SHIFT_UP_SUSPECT")

    def test_empty_group_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "empty_group"):
            exact_two_sided_rank_sum_p([], [1])


if __name__ == "__main__":
    unittest.main()
