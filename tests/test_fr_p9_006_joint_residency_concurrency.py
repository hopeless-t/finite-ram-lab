import unittest

from finite_ram_lab.fr_p9_006_joint_residency_concurrency import (
    enumerate_joint_plans,
    independently_selected_plan,
    pareto_plans,
    run_panel,
)


class FrP9006JointResidencyConcurrencyTests(unittest.TestCase):
    def test_panel_passes(self) -> None:
        panel = run_panel()
        self.assertEqual(panel["status"], "PASS")
        self.assertTrue(all(panel["checks"].values()))
        self.assertIsNone(panel["scalar_gain"])

    def test_independent_selection_composes_infeasibly(self) -> None:
        workers, residency = independently_selected_plan()
        self.assertEqual((workers, residency), (4, "KEEP_WARM"))
        plan = next(
            row
            for row in enumerate_joint_plans()
            if row.workers == workers and row.residency_policy == residency
        )
        self.assertFalse(plan.feasible)
        self.assertGreater(plan.prestart_pss_kib, 50_000)

    def test_joint_frontier_has_feasible_alternatives(self) -> None:
        frontier = pareto_plans(enumerate_joint_plans())
        ids = {(row.workers, row.residency_policy) for row in frontier}
        self.assertTrue(frontier)
        self.assertIn((4, "FAULT_IN"), ids)
        self.assertIn((2, "KEEP_WARM"), ids)

    def test_nonpositive_memory_cap_fails_closed(self) -> None:
        with self.assertRaises(ValueError):
            enumerate_joint_plans(memory_cap_kib=0)


if __name__ == "__main__":
    unittest.main()
