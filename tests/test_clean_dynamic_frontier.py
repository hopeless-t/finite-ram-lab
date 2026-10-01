from __future__ import annotations

import unittest

from finite_ram_lab.clean_dynamic_frontier import (
    ARMS,
    BLOCKS,
    CAPACITY_POINTS_MIB,
    CleanDynamicTrial,
    derive_clean_frontier_metrics,
    expected_trial_count,
    validate_design_matrix,
)


class CleanDynamicFrontierTests(unittest.TestCase):
    def test_expected_trial_count(self):
        self.assertEqual(expected_trial_count(), 144)

    def test_derived_metrics_keep_observer_separate(self):
        trial = CleanDynamicTrial(
            memory_high_mib=160,
            arm="dontneed_64m",
            max_scan_memory_bytes=150,
            post_scan_pre_observer_bytes=100,
            post_scan_post_observer_bytes=104,
            memory_high_events=0,
            pgscan=0,
            advice_calls=2,
            scan_elapsed_ns=10,
        )
        result = derive_clean_frontier_metrics(trial)
        self.assertEqual(result["ephemeral_excess_bytes"], 50)
        self.assertEqual(result["observer_current_delta_bytes"], 4)

    def test_complete_design_matrix(self):
        identities = {
            (high, block, arm)
            for high in CAPACITY_POINTS_MIB
            for block in range(BLOCKS)
            for arm in ARMS
        }
        self.assertTrue(validate_design_matrix(identities))

    def test_missing_cell_fails_matrix_validation(self):
        identities = {
            (high, block, arm)
            for high in CAPACITY_POINTS_MIB
            for block in range(BLOCKS)
            for arm in ARMS
        }
        identities.remove((144, 0, "buffered"))
        self.assertFalse(validate_design_matrix(identities))


if __name__ == "__main__":
    unittest.main()
