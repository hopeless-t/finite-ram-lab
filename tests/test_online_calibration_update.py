from __future__ import annotations

import unittest

from finite_ram_lab.online_calibration_update import update_calibration


def b489() -> dict:
    return {
        "schema":"finite-ram-lab.b489-result/v0.1",
        "summary_rows":[
            {"q":2,"pooled_sample_count":19,"pooled_empirical_max_peak_bytes":100},
            {"q":4,"pooled_sample_count":19,"pooled_empirical_max_peak_bytes":200},
            {"q":7,"pooled_sample_count":19,"pooled_empirical_max_peak_bytes":300},
        ],
    }


def b491() -> dict:
    return {
        "schema":"finite-ram-lab.b491-result/v0.1",
        "boundary_dispatch_checks_pass":True,
        "runner_block_count":8,
        "suspect_q":[],
        "rows":[
            {"q":2,"max_observed_peak_bytes":90,"classification":"NO_EXCEEDANCE"},
            {"q":4,"max_observed_peak_bytes":190,"classification":"NO_EXCEEDANCE"},
            {"q":7,"max_observed_peak_bytes":304,"classification":"TAIL_COMPATIBLE_EXCEEDANCE"},
        ],
    }


class OnlineCalibrationUpdateTests(unittest.TestCase):
    def test_absorbs_non_drift_panel(self):
        result=update_calibration(b489(),b491())
        self.assertEqual(result["status"],"UPDATED")
        for row in result["rows"]:
            self.assertEqual(row["updated_sample_count"],27)
            self.assertAlmostEqual(
                row["updated_rank_max_one_step_predictive_coverage_floor"],
                27/28,
            )
        q7=next(row for row in result["rows"] if row["q"]==7)
        self.assertEqual(q7["updated_empirical_max_peak_bytes"],304)
        self.assertEqual(q7["empirical_max_moved_bytes"],4)

    def test_non_exceeding_max_is_preserved(self):
        result=update_calibration(b489(),b491())
        q2=next(row for row in result["rows"] if row["q"]==2)
        self.assertEqual(q2["updated_empirical_max_peak_bytes"],100)
        self.assertEqual(q2["empirical_max_moved_bytes"],0)

    def test_drift_suspect_fails_closed(self):
        payload=b491()
        payload["suspect_q"]=[4]
        with self.assertRaisesRegex(
            RuntimeError,
            "drift_suspect_blocks_online_update",
        ):
            update_calibration(b489(),payload)

    def test_dispatch_failure_fails_closed(self):
        payload=b491()
        payload["boundary_dispatch_checks_pass"]=False
        with self.assertRaisesRegex(
            RuntimeError,
            "boundary_dispatch_invalid",
        ):
            update_calibration(b489(),payload)


if __name__=="__main__":
    unittest.main()
