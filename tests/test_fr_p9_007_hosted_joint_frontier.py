import unittest

from finite_ram_lab.fr_p9_007_hosted_joint_frontier import (
    _pareto_ids,
    run_synthetic_panel,
)


class FrP9007HostedJointFrontierTests(unittest.TestCase):
    def test_synthetic_panel_passes(self) -> None:
        panel = run_synthetic_panel()
        self.assertEqual(panel["status"], "PASS")
        self.assertEqual(
            panel["pareto_plan_ids"],
            ["N1:FAULT_IN", "N1:KEEP_WARM"],
        )
        self.assertIsNone(panel["scalar_gain"])

    def test_dominance_can_remove_strictly_worse_plan(self) -> None:
        summaries = [
            {
                "mode": "KEEP_WARM",
                "workers": 1,
                "median_prestart_pss_kib": 10,
                "median_active_pss_kib": 20,
                "median_joint_resume_ns": 1,
                "median_work_wall_ns": 100,
                "median_p95_sojourn_ns": 100,
                "logical_fault_span_bytes": 0,
                "median_idle_capability_byte_seconds": 8.0,
            },
            {
                "mode": "KEEP_WARM",
                "workers": 2,
                "median_prestart_pss_kib": 20,
                "median_active_pss_kib": 30,
                "median_joint_resume_ns": 2,
                "median_work_wall_ns": 110,
                "median_p95_sojourn_ns": 110,
                "logical_fault_span_bytes": 0,
                "median_idle_capability_byte_seconds": 8.0,
            },
        ]
        self.assertEqual(_pareto_ids(summaries), ["N1:KEEP_WARM"])

    def test_tradeoff_preserves_both_modes(self) -> None:
        summaries = [
            {
                "mode": "KEEP_WARM",
                "workers": 1,
                "median_prestart_pss_kib": 20,
                "median_active_pss_kib": 20,
                "median_joint_resume_ns": 0,
                "median_work_wall_ns": 100,
                "median_p95_sojourn_ns": 100,
                "logical_fault_span_bytes": 0,
                "median_idle_capability_byte_seconds": 8.0,
            },
            {
                "mode": "FAULT_IN",
                "workers": 1,
                "median_prestart_pss_kib": 10,
                "median_active_pss_kib": 20,
                "median_joint_resume_ns": 10,
                "median_work_wall_ns": 100,
                "median_p95_sojourn_ns": 100,
                "logical_fault_span_bytes": 8,
                "median_idle_capability_byte_seconds": 0.0,
            },
        ]
        self.assertEqual(
            _pareto_ids(summaries),
            ["N1:FAULT_IN", "N1:KEEP_WARM"],
        )


if __name__ == "__main__":
    unittest.main()
