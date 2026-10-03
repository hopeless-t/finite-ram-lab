from __future__ import annotations

import json
from pathlib import Path
import unittest

from finite_ram_lab.semantic_demand_folding import (
    ControllerConfig,
    build_result,
    next_concurrency_hysteresis,
    pressure_signal,
)


SPEC = Path("specs/FR-SOOM-002K.json")


class SemanticDemandFoldingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = json.loads(SPEC.read_text(encoding="utf-8"))
        cls.result = build_result()

    def test_source_atoms_are_frozen(self):
        atoms = self.spec["steal_governor_atoms"]
        self.assertEqual(atoms["default_interval_ms"], 1000)
        self.assertEqual(atoms["default_low_threshold_percent"], 2.0)
        self.assertEqual(atoms["default_high_threshold_percent"], 5.0)
        self.assertEqual(atoms["actuator_step"], "one_core")
        self.assertEqual(atoms["minimum_preferred"], "one_core")
        self.assertTrue(atoms["preferred_subset_of_active"])

    def test_transfer_does_not_copy_literal_thresholds(self):
        controller = self.spec["synthetic_shadow"]["controller"]
        self.assertEqual(controller["high_threshold"], 0.50)
        self.assertEqual(controller["low_threshold"], 0.20)
        self.assertNotEqual(
            controller["high_threshold"],
            self.spec["steal_governor_atoms"][
                "default_high_threshold_percent"
            ],
        )

    def test_hysteresis_deadband(self):
        cfg = ControllerConfig(
            high_threshold=0.50,
            low_threshold=0.20,
        )
        self.assertEqual(
            next_concurrency_hysteresis(6, 0.35, cfg),
            6,
        )
        self.assertEqual(
            next_concurrency_hysteresis(6, 0.60, cfg),
            5,
        )
        self.assertEqual(
            next_concurrency_hysteresis(6, 0.10, cfg),
            7,
        )

    def test_pressure_is_concurrency_sensitive(self):
        self.assertGreater(
            pressure_signal(8, 0.50),
            pressure_signal(4, 0.50),
        )

    def test_shadow_panel_passes(self):
        self.assertEqual(self.result["status"], "PASS")
        self.assertTrue(self.result["synthetic_only"])
        self.assertFalse(self.result["live_control_claim"])

    def test_demand_folding_reduces_severe_pressure(self):
        full = self.result["arms"]["FULL"]
        hys = self.result["arms"]["HYSTERESIS"]
        self.assertLess(
            hys["pressure_gt_0_60_samples"],
            full["pressure_gt_0_60_samples"],
        )
        self.assertGreater(
            hys["total_useful_progress"],
            full["total_useful_progress"],
        )

    def test_hysteresis_reduces_chatter(self):
        hys = self.result["arms"]["HYSTERESIS"]
        single = self.result["arms"]["SINGLE_THRESHOLD"]
        self.assertLess(
            hys["control_transitions"],
            single["control_transitions"],
        )

    def test_progress_floor_invariant(self):
        hys = self.result["arms"]["HYSTERESIS"]
        self.assertGreaterEqual(hys["min_concurrency"], 1)

    def test_action_ladder_places_fold_before_destructive_actions(self):
        ladder = self.spec["fr_soom_action_ladder"]
        self.assertLess(
            ladder.index("DEMAND_FOLD"),
            ladder.index("REPRESENTATION_DOWNSHIFT"),
        )
        self.assertLess(
            ladder.index("DEMAND_FOLD"),
            ladder.index("BACKGROUND_EXIT"),
        )
        self.assertLess(
            ladder.index("BACKGROUND_EXIT"),
            ladder.index("ACTIVE_TASK_KILL"),
        )

    def test_claim_ceiling_is_shadow_only(self):
        self.assertEqual(
            self.result["claim_ceiling"],
            (
                "SOURCE_GROUNDED_STEAL_GOVERNOR_TRANSFER_PLUS_"
                "SYNTHETIC_DEMAND_FOLDING_SHADOW_ONLY"
            ),
        )


if __name__ == "__main__":
    unittest.main()
