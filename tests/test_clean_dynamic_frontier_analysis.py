from __future__ import annotations

import unittest

from finite_ram_lab.clean_dynamic_frontier_analysis import (
    MIB,
    aggregate_frontier,
    analyze_postrun,
    bootstrap_membership,
    bootstrap_transition_loss,
)
from finite_ram_lab.prelaunch_digital_twin import twin_plan


CANDIDATES = [
    "dontneed_32m",
    "dontneed_48m",
    "dontneed_64m",
    "dontneed_80m",
    "dontneed_96m",
]

SPEC = {
    "memory_high_mib": [144, 160, 176],
    "candidate_arms": CANDIDATES,
    "frontier_primary_objectives": [
        {"name": "peak_ram_bytes", "direction": "MINIMIZE"},
        {"name": "ephemeral_excess_bytes", "direction": "MINIMIZE"},
        {"name": "memory_high_events", "direction": "MINIMIZE"},
        {"name": "pgscan", "direction": "MINIMIZE"},
        {"name": "advice_calls", "direction": "MINIMIZE"},
    ],
    "frontier_descriptive_objectives": [
        {"name": "scan_elapsed_ns", "direction": "MINIMIZE"},
    ],
    "qualification": {
        "frontier_stability_threshold": 0.90,
    },
}


def synthetic_summary() -> dict:
    cells = {}
    clean_floor_mib = 76.7
    for high in SPEC["memory_high_mib"]:
        cells[str(high)] = {}
        for arm in CANDIDATES:
            plan = twin_plan(
                arm=arm,
                memory_high_mib=high,
                clean_floor_proxy_mib=clean_floor_mib,
            )
            values = {
                "peak_ram_bytes": int(round(plan.peak_mib * MIB)),
                "ephemeral_excess_bytes": int(
                    round(plan.ephemeral_excess_mib * MIB)
                ),
                "memory_high_events": plan.memory_high_events_proxy,
                "pgscan": plan.pgscan_proxy,
                "advice_calls": plan.advice_calls,
                "scan_elapsed_ns": 100,
                "clean_floor_bytes": int(round(clean_floor_mib * MIB)),
            }
            cell = {
                f"median_{name}": value
                for name, value in values.items()
            }
            cell["block_rows"] = [
                {"block": block, **values}
                for block in range(8)
            ]
            cells[str(high)][arm] = cell
    return {"cells": cells}


class CleanDynamicFrontierAnalysisTests(unittest.TestCase):
    def test_aggregate_frontier_matches_prelaunch_twin(self):
        summary = synthetic_summary()
        for high in SPEC["memory_high_mib"]:
            self.assertEqual(
                aggregate_frontier(
                    summary,
                    SPEC,
                    high=high,
                    include_descriptive=False,
                ),
                (
                    "dontneed_32m",
                    "dontneed_48m",
                    "dontneed_96m",
                ),
            )

    def test_identical_blocks_bootstrap_membership_is_exact(self):
        result = bootstrap_membership(
            synthetic_summary(),
            SPEC,
            high=144,
            include_descriptive=False,
            iterations=200,
            seed=451,
        )
        self.assertEqual(result["dontneed_32m"], 1.0)
        self.assertEqual(result["dontneed_48m"], 1.0)
        self.assertEqual(result["dontneed_96m"], 1.0)
        self.assertEqual(result["dontneed_64m"], 0.0)
        self.assertEqual(result["dontneed_80m"], 0.0)

    def test_capacity_expansion_has_no_loss_in_twin(self):
        result = bootstrap_transition_loss(
            synthetic_summary(),
            SPEC,
            lower_high=144,
            upper_high=160,
            include_descriptive=False,
            iterations=200,
            seed=451,
        )
        self.assertEqual(result["any_loss_probability"], 0.0)
        self.assertTrue(
            all(
                probability == 0.0
                for probability in result["arm_loss_probability"].values()
            )
        )

    def test_full_analyzer_recovers_expected_null_topology(self):
        result = analyze_postrun(
            synthetic_summary(),
            SPEC,
            bootstrap_iterations=200,
            seed=451,
        )
        self.assertTrue(
            all(result["stable_primary_frontier_by_capacity"].values())
        )
        self.assertTrue(
            all(result["prelaunch_twin_match_by_capacity"].values())
        )
        self.assertEqual(
            result["projection_classification"],
            "NO_AGGREGATE_FRONTIER_LOSS",
        )
        self.assertEqual(result["primary_aggregate_losses"], [(), ()])
        self.assertAlmostEqual(
            result["clamp_replay"]["transient_base_mib"],
            78.609,
            places=3,
        )
        self.assertEqual(
            result["clamp_replay"]["pressure_classification_accuracy"],
            1.0,
        )


if __name__ == "__main__":
    unittest.main()
