from __future__ import annotations

import unittest

from finite_ram_lab.fr_p9_008_online_joint_replan import (
    ResourceObservation,
    admit_plan,
    frozen_measurement_fixture,
    measurement_certificate,
    plans_from_measurement,
    resource_certificate,
    run_panel,
    select_plan,
)


class FrP9008OnlineJointReplanTests(unittest.TestCase):
    def setUp(self) -> None:
        self.plans = plans_from_measurement(frozen_measurement_fixture())

    def test_panel_passes(self) -> None:
        result = run_panel()
        self.assertEqual(result["status"], "PASS")
        self.assertTrue(all(result["checks"].values()))
        self.assertIsNone(result["scalar_gain"])
        self.assertEqual(result["authority_effect"], "NONE")
        self.assertFalse(result["retry_authority"])

    def test_irrelevant_epoch_change_keeps_certificate(self) -> None:
        before = ResourceObservation(epoch=1, pss_cap_kib=50_000, capability_available=True)
        after = ResourceObservation(epoch=2, pss_cap_kib=50_000, capability_available=True)
        self.assertEqual(resource_certificate(before), resource_certificate(after))
        plan = select_plan(self.plans, before)
        self.assertIsNotNone(plan)
        assert plan is not None
        self.assertEqual(
            admit_plan(plan, after, self.plans),
            "RESOURCE_PLAN_VALID_AUTHORITY_STILL_REQUIRED",
        )

    def test_cap_tightening_replans_from_four_to_two_workers(self) -> None:
        before = ResourceObservation(epoch=1, pss_cap_kib=50_000, capability_available=True)
        after = ResourceObservation(epoch=2, pss_cap_kib=40_000, capability_available=True)
        old = select_plan(self.plans, before)
        new = select_plan(self.plans, after)
        self.assertIsNotNone(old)
        self.assertIsNotNone(new)
        assert old is not None and new is not None
        self.assertEqual(old.plan_id, "N4:KEEP_WARM")
        self.assertEqual(new.plan_id, "N2:KEEP_WARM")
        self.assertEqual(admit_plan(old, after, self.plans), "REPLAN_REQUIRED")
        self.assertEqual(old.job_digests, new.job_digests)

    def test_topology_loss_fails_closed(self) -> None:
        observation = ResourceObservation(epoch=3, pss_cap_kib=40_000, capability_available=False)
        self.assertIsNone(select_plan(self.plans, observation))

    def test_measurement_surface_is_bound_into_plan(self) -> None:
        observation = ResourceObservation(epoch=1, pss_cap_kib=50_000, capability_available=True)
        plan = select_plan(self.plans, observation)
        self.assertIsNotNone(plan)
        assert plan is not None
        first = self.plans[0]
        drifted = first.__class__(
            plan_id=first.plan_id,
            workers=first.workers,
            mode=first.mode,
            prestart_pss_kib=first.prestart_pss_kib,
            active_pss_kib=first.active_pss_kib + 1,
            joint_resume_ns=first.joint_resume_ns,
            work_wall_ns=first.work_wall_ns,
            p95_sojourn_ns=first.p95_sojourn_ns,
            logical_fault_span_bytes=first.logical_fault_span_bytes,
            idle_capability_byte_seconds=first.idle_capability_byte_seconds,
            job_digests=first.job_digests,
        )
        drifted_plans = (drifted,) + self.plans[1:]
        self.assertNotEqual(measurement_certificate(self.plans), measurement_certificate(drifted_plans))
        self.assertEqual(
            admit_plan(plan, observation, drifted_plans),
            "REMEASURE_OR_REPLAN_REQUIRED",
        )

    def test_semantic_mismatch_is_rejected_before_planning(self) -> None:
        fixture = frozen_measurement_fixture()
        fixture["summaries"][0]["job_digests"] = {"0": "different"}
        with self.assertRaisesRegex(ValueError, "job_semantics_differ"):
            plans_from_measurement(fixture)


if __name__ == "__main__":
    unittest.main()
