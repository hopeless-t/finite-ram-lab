from __future__ import annotations

import unittest
from unittest.mock import patch

from finite_ram_lab.local_adapter_bootstrap import FINGERPRINT_SCHEMA
from finite_ram_lab.local_calibration_explore import (
    BALANCED_ORDERS,
    run_local_exploration,
)


def fp(kernel: str = "k1") -> dict:
    return {
        "schema": FINGERPRINT_SCHEMA,
        "system": "Linux",
        "kernel_release": kernel,
        "machine": "x86_64",
        "python_version": "3.12.0",
        "page_size_bytes": 4096,
        "cpu_model": "cpu",
        "mem_total": "16000000 kB",
        "libc": {"name": "glibc", "version": "2.39"},
        "cgroup_v2_present": True,
    }


class LocalCalibrationExploreTests(unittest.TestCase):
    def test_eight_orders_balance_each_q_across_each_position(self):
        positions = {q: [] for q in (1,2,4,7)}
        for order in BALANCED_ORDERS:
            for position,q in enumerate(order):
                positions[q].append(position)
        for q in positions:
            self.assertEqual(sorted(positions[q]), [0,0,1,1,2,2,3,3])

    def test_exploration_rebuilds_pareto_without_hosted_q1_exclusion(self):
        profiles = {
            1: (90, 1.10),
            2: (100, 0.90),
            4: (120, 0.80),
            7: (140, 0.70),
        }

        def fake_child(**kwargs):
            peak,work = profiles[kwargs["q"]]
            return {
                "semantic_exact": True,
                "normalized_peak_growth_bytes": peak,
                "work_seconds": work,
                "output_sha256": "same",
            }

        with patch(
            "finite_ram_lab.local_calibration_explore.local_host_fingerprint",
            return_value=fp(),
        ), patch(
            "finite_ram_lab.local_calibration_explore._run_fresh_child",
            side_effect=fake_child,
        ):
            result = run_local_exploration(
                samples_per_q=8,
                size=64,
                target_rank_coverage=0.95,
            )

        self.assertEqual(result["local_pareto_q"], [1,2,4,7])
        self.assertFalse(result["hosted_threshold_imported"])
        self.assertFalse(result["policy_promotion_allowed"])
        self.assertEqual(result["physical_observations"], 32)
        self.assertAlmostEqual(result["current_rank_max_coverage_floor"], 8/9)
        self.assertTrue(all(
            row["additional_samples_required"] == 11
            for row in result["promotion_rows"]
        ))

    def test_locally_dominated_q_can_be_removed_by_local_evidence(self):
        profiles = {
            1: (100, 1.00),
            2: (100, 0.90),
            4: (120, 0.80),
            7: (140, 0.70),
        }

        def fake_child(**kwargs):
            peak,work = profiles[kwargs["q"]]
            return {
                "semantic_exact": True,
                "normalized_peak_growth_bytes": peak,
                "work_seconds": work,
                "output_sha256": "same",
            }

        with patch(
            "finite_ram_lab.local_calibration_explore.local_host_fingerprint",
            return_value=fp(),
        ), patch(
            "finite_ram_lab.local_calibration_explore._run_fresh_child",
            side_effect=fake_child,
        ):
            result = run_local_exploration(samples_per_q=8,size=64)

        self.assertEqual(result["local_pareto_q"], [2,4,7])

    def test_fingerprint_change_during_panel_fails_closed(self):
        states = [fp("k1"), fp("k2")]

        def fake_child(**kwargs):
            return {
                "semantic_exact": True,
                "normalized_peak_growth_bytes": 100,
                "work_seconds": 1.0,
                "output_sha256": "same",
            }

        with patch(
            "finite_ram_lab.local_calibration_explore.local_host_fingerprint",
            side_effect=states,
        ), patch(
            "finite_ram_lab.local_calibration_explore._run_fresh_child",
            side_effect=fake_child,
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "local_environment_fingerprint_changed_during_panel",
            ):
                run_local_exploration(samples_per_q=1,size=64)


if __name__=="__main__":
    unittest.main()
