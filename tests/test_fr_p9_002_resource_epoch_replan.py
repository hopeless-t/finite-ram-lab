import unittest

from finite_ram_lab.fr_p9_002_resource_epoch_replan import (
    ResourceSnapshot,
    admit_plan,
    plan_projection,
    resource_certificate,
    run_panel,
)


class FrP9002ResourceEpochReplanTests(unittest.TestCase):
    def test_panel_passes(self) -> None:
        panel = run_panel()
        self.assertEqual(panel["status"], "PASS")
        self.assertTrue(all(panel["checks"].values()))

    def test_irrelevant_epoch_change_keeps_certificate(self) -> None:
        a = ResourceSnapshot(1, 8192, True, 2_500_000_000, "a")
        b = ResourceSnapshot(2, 8192, True, 2_500_000_000, "b")
        self.assertNotEqual(a.epoch, b.epoch)
        self.assertEqual(resource_certificate(a), resource_certificate(b))
        plan = plan_projection(a)
        self.assertIsNotNone(plan)
        assert plan is not None
        self.assertEqual(
            admit_plan(plan, b),
            "RESOURCE_PLAN_VALID_AUTHORITY_STILL_REQUIRED",
        )

    def test_materialization_invalidates_startup_plan(self) -> None:
        startup = ResourceSnapshot(7, 8192, True, 2_500_000_000)
        observed = ResourceSnapshot(9, 6144, True, 2_500_000_000)
        plan = plan_projection(startup)
        self.assertIsNotNone(plan)
        assert plan is not None
        self.assertEqual(admit_plan(plan, observed), "REPLAN_REQUIRED")

    def test_replan_preserves_semantic_atoms_and_moves_frozen_cold_pair(self) -> None:
        panel = run_panel()
        moved = panel["materialization_adversary"]["moved_atoms"]
        self.assertEqual(moved, ["checkpoint_manifest", "collision_verifier"])
        self.assertEqual(
            panel["materialization_adversary"]["cost_vector"][
                "current_phase_transfer_bytes"
            ],
            0,
        )
        self.assertEqual(
            panel["materialization_adversary"]["cost_vector"]["ssd_bytes"],
            1920,
        )

    def test_topology_loss_fails_closed(self) -> None:
        snapshot = ResourceSnapshot(10, 6144, False, 0)
        self.assertIsNone(plan_projection(snapshot))

    def test_authority_boundary_is_explicit(self) -> None:
        panel = run_panel()
        self.assertEqual(panel["authority_effect"], "NONE")
        self.assertFalse(panel["retry_authority"])
        self.assertIn(
            "resource freshness != execution authority",
            panel["invariants"],
        )


if __name__ == "__main__":
    unittest.main()
