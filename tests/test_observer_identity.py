from __future__ import annotations

import unittest

from finite_ram_lab.observer_identity import (
    STRATA004_OBSERVER,
    STRATA005_OBSERVER,
    capacity_pair_identity_check,
    observer_semantics_equal,
)


class ObserverIdentityTests(unittest.TestCase):
    def test_strata004_and_005_observers_are_not_semantically_equal(self):
        self.assertFalse(
            observer_semantics_equal(
                STRATA004_OBSERVER,
                STRATA005_OBSERVER,
            )
        )

    def test_cross_study_three_point_merge_holds_on_observer_drift(self):
        result = capacity_pair_identity_check(
            workload_bytes_equal=False,
            runner_equal=True,
            python_equal=True,
            cgroup_controls_equal_except_capacity=True,
            arm_semantics_equal=True,
            observer_left=STRATA004_OBSERVER,
            observer_right=STRATA005_OBSERVER,
        )
        self.assertEqual(result["status"], "IDENTITY_HOLD")
        self.assertIn("WORKLOAD_IMPLEMENTATION_DRIFT", result["failures"])
        self.assertIn("OBSERVER_SEMANTICS_DRIFT", result["failures"])

    def test_same_observer_contract_can_pass(self):
        result = capacity_pair_identity_check(
            workload_bytes_equal=True,
            runner_equal=True,
            python_equal=True,
            cgroup_controls_equal_except_capacity=True,
            arm_semantics_equal=True,
            observer_left=STRATA005_OBSERVER,
            observer_right=STRATA005_OBSERVER,
        )
        self.assertEqual(result["status"], "IDENTITY_PASS")
        self.assertEqual(result["failures"], ())


if __name__ == "__main__":
    unittest.main()
