from __future__ import annotations

import unittest

from finite_ram_lab.dynamic_frontier_contract import (
    DynamicFrontierContract,
    ObjectiveRole,
    ObjectiveSpec,
    qualify_dynamic_frontier_receipt,
)


def strata005_contract() -> DynamicFrontierContract:
    return DynamicFrontierContract(
        experiment_id="B443-STRATA005-REPLAY-CONTRACT",
        capacity_axis="memory.high",
        capacity_units="MiB",
        capacity_points=(144.0, 176.0),
        stable_plan_identity_fields=("arm",),
        objectives=(
            ObjectiveSpec(
                "peak_ram_bytes",
                ObjectiveRole.PRIMARY,
                "MINIMIZE",
                "median maximum memory.current during scan",
            ),
            ObjectiveSpec(
                "memory_high_events",
                ObjectiveRole.PRIMARY,
                "MINIMIZE",
                "median memory.high event delta during scan",
            ),
            ObjectiveSpec(
                "pgscan",
                ObjectiveRole.PRIMARY,
                "MINIMIZE",
                "median pgscan delta during scan",
            ),
            ObjectiveSpec(
                "scan_elapsed_ns",
                ObjectiveRole.DESCRIPTIVE,
                "MINIMIZE",
                "hosted scan elapsed time",
                "original study marked timing noisy/non-monotonic",
            ),
        ),
        independent_resampling_unit="runner_block",
        minimum_independent_units_per_cell=4,
        frontier_stability_threshold=0.95,
        missing_data_rule="FAIL_CLOSED",
        claim_ceiling="DYNAMIC_FRONTIER_DIRECTIONAL_ONLY",
    )


class DynamicFrontierContractTests(unittest.TestCase):
    def test_strata005_primary_no_loss_does_not_promote(self):
        result = qualify_dynamic_frontier_receipt(
            strata005_contract(),
            observed_capacity_points=(144.0, 176.0),
            independent_units_by_capacity={144.0: 4, 176.0: 4},
            primary_objectives_present=(
                "peak_ram_bytes",
                "memory_high_events",
                "pgscan",
            ),
            stable_plan_identity=True,
            workload_identity_stable=True,
            raw_receipts_present=True,
            frontier_loss_probability=0.0,
        )
        self.assertEqual(result["status"], "QUALIFIED")
        self.assertFalse(result["frontier_promotion_eligible"])

    def test_high_stability_primary_loss_can_be_eligible(self):
        result = qualify_dynamic_frontier_receipt(
            strata005_contract(),
            observed_capacity_points=(144.0, 176.0),
            independent_units_by_capacity={144.0: 4, 176.0: 4},
            primary_objectives_present=(
                "peak_ram_bytes",
                "memory_high_events",
                "pgscan",
            ),
            stable_plan_identity=True,
            workload_identity_stable=True,
            raw_receipts_present=True,
            frontier_loss_probability=0.97,
        )
        self.assertEqual(result["status"], "QUALIFIED")
        self.assertTrue(result["frontier_promotion_eligible"])

    def test_missing_raw_receipt_holds(self):
        result = qualify_dynamic_frontier_receipt(
            strata005_contract(),
            observed_capacity_points=(144.0, 176.0),
            independent_units_by_capacity={144.0: 4, 176.0: 4},
            primary_objectives_present=(
                "peak_ram_bytes",
                "memory_high_events",
                "pgscan",
            ),
            stable_plan_identity=True,
            workload_identity_stable=True,
            raw_receipts_present=False,
            frontier_loss_probability=1.0,
        )
        self.assertEqual(result["status"], "QUALIFICATION_HOLD")
        self.assertIn("RAW_RECEIPT_MISSING", result["failures"])
        self.assertFalse(result["frontier_promotion_eligible"])

    def test_missing_primary_holds(self):
        result = qualify_dynamic_frontier_receipt(
            strata005_contract(),
            observed_capacity_points=(144.0, 176.0),
            independent_units_by_capacity={144.0: 4, 176.0: 4},
            primary_objectives_present=("peak_ram_bytes",),
            stable_plan_identity=True,
            workload_identity_stable=True,
            raw_receipts_present=True,
            frontier_loss_probability=1.0,
        )
        self.assertEqual(result["status"], "QUALIFICATION_HOLD")
        self.assertIn("PRIMARY_OBJECTIVE_MISSING", result["failures"])

    def test_insufficient_replication_holds(self):
        result = qualify_dynamic_frontier_receipt(
            strata005_contract(),
            observed_capacity_points=(144.0, 176.0),
            independent_units_by_capacity={144.0: 3, 176.0: 4},
            primary_objectives_present=(
                "peak_ram_bytes",
                "memory_high_events",
                "pgscan",
            ),
            stable_plan_identity=True,
            workload_identity_stable=True,
            raw_receipts_present=True,
            frontier_loss_probability=1.0,
        )
        self.assertEqual(result["status"], "QUALIFICATION_HOLD")
        self.assertIn("INSUFFICIENT_REPLICATION:144.0", result["failures"])


if __name__ == "__main__":
    unittest.main()
